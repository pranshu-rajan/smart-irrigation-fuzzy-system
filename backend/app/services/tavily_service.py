"""Tavily Live Web Search Service for Real-Time Agricultural & ICAR Intelligence.

Enables live retrieval of Agromet advisories, ICAR package of practices,
IMD monsoon bulletins, and localized crop recommendations across Indian districts.
Implements TTL caching to conserve API search credits.
"""

import os
import time
from typing import Dict, List, Optional, Any
import httpx
from backend.app.core.config import get_settings


class TavilySearchService:
    """Production service for querying Tavily search API with caching."""

    def __init__(self):
        self.settings = get_settings()
        self.api_key = (
            self.settings.TAVILY_API_KEY
            or os.environ.get("TAVILY_API_KEY")
        )
        self.base_url = "https://api.tavily.com/search"
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl_seconds = 3600  # 1 hour cache per query to preserve 1000 credits

    def search(
        self,
        query: str,
        max_results: int = 3,
        search_depth: str = "basic",
        include_domains: Optional[List[str]] = None,
    ) -> List[Dict[str, str]]:
        """Search the web via Tavily API with caching and error tolerance."""
        if not query or not query.strip():
            return []

        cache_key = f"{query.strip().lower()}_{max_results}"
        now = time.time()

        # Check cache
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if now - entry["timestamp"] < self._cache_ttl_seconds:
                return entry["results"]

        if not self.api_key or self.api_key == "tvly-your-api-key-here":
            return self._get_curated_fallback(query)

        payload: Dict[str, Any] = {
            "api_key": self.api_key,
            "query": query,
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
                            "content": str(r.get("content", "")).strip()[:400],
                        }
                        for r in raw_results
                        if r.get("title") and r.get("url")
                    ]
                    # Cache result
                    self._cache[cache_key] = {"timestamp": now, "results": cleaned_results}
                    return cleaned_results
                else:
                    return self._get_curated_fallback(query)
        except Exception:
            return self._get_curated_fallback(query)

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
        """Curated ICAR/IMD reference fallback when offline or Tavily unavailable."""
        return [
            {
                "title": "ICAR - National Agromet Advisory Service Guidelines",
                "url": "https://icar.org.in/agromet-advisories",
                "content": (
                    "ICAR guidelines recommend scheduling irrigation based on crop growth stages, "
                    "maintaining root-zone soil moisture at 60-70% of available water capacity, and "
                    "suspending surface/drip applications when significant rainfall is forecast."
                ),
            },
            {
                "title": "IMD Agromet Advisory Service (AAS) Water Management Protocols",
                "url": "https://mausam.imd.gov.in/aas",
                "content": (
                    "Farmers are advised to adopt micro-irrigation systems (drip/sprinkler) for high-water-demanding "
                    "crops, irrigate during morning or late afternoon to minimize evaporation losses, and monitor "
                    "local weather forecasts for thunderstorm or heatwave advisories."
                ),
            },
        ]


# Singleton instance
tavily_search_service = TavilySearchService()
