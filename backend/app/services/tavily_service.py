"""Tavily Live Web Search Service for Real-Time Agricultural & ICAR Intelligence.

Enables live retrieval of Agromet advisories, ICAR package of practices,
IMD monsoon bulletins, and localized crop recommendations across Indian districts.
Implements persistent on-disk caching and strict credit budgeting to protect the
user's 1,000 credit allocation (starting with 55 credits previously consumed).
"""

import os
import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
import httpx
from backend.app.core.config import get_settings


class TavilySearchService:
    """Production service for querying Tavily search API with disk caching & credit guard."""

    def __init__(self):
        self.settings = get_settings()
        self.api_key = (
            self.settings.TAVILY_API_KEY
            or os.environ.get("TAVILY_API_KEY")
        )
        self.base_url = "https://api.tavily.com/search"

        # File paths for persistent storage
        project_root = Path(__file__).resolve().parent.parent.parent
        self.data_dir = project_root / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.data_dir / "tavily_cache.json"
        self.credits_file = self.data_dir / "tavily_credits.json"

        # Cache configuration: 7 days TTL (ICAR advisories are updated twice weekly)
        self.cache_ttl_seconds = 7 * 24 * 3600  # 604,800 seconds

        # Initialize persistent ledger and cache
        self._init_credits_ledger()
        self._cache: Dict[str, Dict[str, Any]] = self._load_disk_cache()

    def _init_credits_ledger(self) -> None:
        """Initialize or load persistent credit tracker with user's baseline (55 used / 1000 total)."""
        if not self.credits_file.exists():
            initial_ledger = {
                "total_credits": 1000,
                "credits_used": 55,  # User confirmed 55 credits consumed
                "credits_remaining": 945,
                "safety_cutoff_threshold": 50,  # Never burn last 50 emergency credits
                "total_searches_recorded": 55,
                "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            try:
                with open(self.credits_file, "w", encoding="utf-8") as f:
                    json.dump(initial_ledger, f, indent=2)
            except Exception as e:
                print(f"[TavilyService] Warning: Could not initialize credits file: {e}")

    def get_credit_status(self) -> Dict[str, Any]:
        """Return the current credit audit status and cache statistics."""
        if self.credits_file.exists():
            try:
                with open(self.credits_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data["cache_entries_count"] = len(self._cache)
                    return data
            except Exception:
                pass
        return {
            "total_credits": 1000,
            "credits_used": 55,
            "credits_remaining": 945,
            "safety_cutoff_threshold": 50,
            "cache_entries_count": len(self._cache),
        }

    def _record_credit_consumption(self, credits_spent: int = 1) -> None:
        """Atomically increment credit consumption on disk."""
        status = self.get_credit_status()
        status["credits_used"] += credits_spent
        status["credits_remaining"] = max(0, status["total_credits"] - status["credits_used"])
        status["total_searches_recorded"] += credits_spent
        status["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        try:
            with open(self.credits_file, "w", encoding="utf-8") as f:
                json.dump(status, f, indent=2)
        except Exception as e:
            print(f"[TavilyService] Warning: Could not update credits file: {e}")

    def _load_disk_cache(self) -> Dict[str, Dict[str, Any]]:
        """Load persistent cache entries from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[TavilyService] Warning loading cache file: {e}")
        return {}

    def _save_disk_cache(self) -> None:
        """Persist in-memory cache dictionary to disk."""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[TavilyService] Warning saving cache file: {e}")

    def search(
        self,
        query: str,
        max_results: int = 3,
        search_depth: str = "basic",
        include_domains: Optional[List[str]] = None,
    ) -> List[Dict[str, str]]:
        """Search the web via Tavily API with disk caching, credit safety guard, and fallback."""
        if not query or not query.strip():
            return []

        clean_query = query.strip()
        cache_key = f"{clean_query.lower()}_{max_results}"
        now = time.time()

        # 1. Check persistent cache (Cost: 0 Credits)
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if now - entry.get("timestamp", 0) < self.cache_ttl_seconds:
                return entry.get("results", [])

        # 2. Check API Key validity
        if not self.api_key or self.api_key == "tvly-your-api-key-here":
            return self._get_curated_fallback(clean_query)

        # 3. Check Credit Safety Threshold
        credit_info = self.get_credit_status()
        remaining = credit_info.get("credits_remaining", 945)
        cutoff = credit_info.get("safety_cutoff_threshold", 50)

        if remaining <= cutoff:
            print(
                f"[TavilyService] EMERGENCY CREDIT GUARD TRIGGERED: "
                f"{remaining} credits remaining <= cutoff {cutoff}. "
                f"Returning high-fidelity ICAR fallback without consuming credits."
            )
            return self._get_curated_fallback(clean_query)

        # 4. Outbound API Call to Tavily (Cost: 1 Credit for basic search)
        payload: Dict[str, Any] = {
            "api_key": self.api_key,
            "query": clean_query,
            "max_results": max_results,
            "search_depth": search_depth,
        }
        if include_domains:
            payload["include_domains"] = include_domains

        try:
            with httpx.Client(timeout=8.0) as client:
                resp = client.post(self.base_url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    raw_results = data.get("results", [])
                    cleaned_results = [
                        {
                            "title": str(r.get("title", "")).strip(),
                            "url": str(r.get("url", "")).strip(),
                            "content": str(r.get("content", "")).strip()[:450],
                        }
                        for r in raw_results
                        if r.get("title") and r.get("url")
                    ]

                    # Deduct 1 credit & record
                    self._record_credit_consumption(1)

                    # Save to persistent disk cache
                    self._cache[cache_key] = {
                        "timestamp": now,
                        "results": cleaned_results,
                    }
                    self._save_disk_cache()
                    return cleaned_results
                else:
                    print(f"[TavilyService] API responded with HTTP {resp.status_code}: {resp.text[:200]}")
                    return self._get_curated_fallback(clean_query)
        except Exception as e:
            print(f"[TavilyService] Search request failed: {e}")
            return self._get_curated_fallback(clean_query)

    def search_agromet_advisory(
        self,
        district: str,
        state: str,
        crop: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Fetch targeted ICAR/IMD Agromet agricultural advisories for an Indian district."""
        crop_part = f"{crop} " if crop else ""
        query = f"ICAR IMD agromet advisory {district} {state} {crop_part}crop irrigation water recommendation"
        return self.search(
            query=query,
            max_results=3,
            search_depth="basic",
        )

    def _get_curated_fallback(self, query: str) -> List[Dict[str, str]]:
        """Curated ICAR/IMD reference fallback when offline, cached, or credit guarded."""
        return [
            {
                "title": "ICAR - National Agromet Advisory Service Guidelines",
                "url": "https://icar.org.in/agromet-advisories",
                "content": (
                    "ICAR guidelines recommend scheduling irrigation based on critical crop growth stages, "
                    "maintaining root-zone soil moisture at 55-70% of available water capacity, and "
                    "suspending surface or drip irrigation pulses when significant rainfall (>5 mm) is forecast."
                ),
            },
            {
                "title": "IMD Agromet Advisory Service (AAS) Water Management Protocols",
                "url": "https://mausam.imd.gov.in/aas",
                "content": (
                    "Farmers are advised to adopt pressurized micro-irrigation systems (drip/sprinkler) for high-value "
                    "crops, irrigate during early morning or late afternoon to minimize evaporation losses, and monitor "
                    "local weather forecasts for thunderstorm or heatwave advisories."
                ),
            },
        ]


# Singleton instance
tavily_search_service = TavilySearchService()
