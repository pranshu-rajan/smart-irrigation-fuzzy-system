"""RAG (Retrieval-Augmented Generation) Indexer and Context Assembly for Fuzzy Irrigation Platform.

Indexes:
- All system specifications and mathematical derivations from `docs/`
- Factual telemetry summaries from live simulation runs
- Invariant rules and safety guarantees
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
DOCS_DIR = ROOT_DIR / "docs"


class KnowledgeChunk:
    def __init__(self, doc_name: str, title: str, content: str):
        self.doc_name = doc_name
        self.title = title
        self.content = content

    def __repr__(self):
        return f"<Chunk {self.doc_name} : {self.title}>"


class RAGIndexer:
    def __init__(self, docs_dir: Path = DOCS_DIR):
        self.docs_dir = docs_dir
        self.chunks: List[KnowledgeChunk] = []
        self._build_index()

    def _build_index(self):
        """Parse markdown documents in docs/ into queryable chunks."""
        if not self.docs_dir.exists():
            return

        for md_file in self.docs_dir.glob("*.md"):
            try:
                text = md_file.read_text(encoding="utf-8")
                # Split by markdown headers
                sections = re.split(r"\n(?=#{1,3}\s)", text)
                for sec in sections:
                    lines = sec.strip().split("\n")
                    if not lines or not lines[0]:
                        continue
                    header = lines[0].replace("#", "").strip()
                    body = "\n".join(lines[1:]).strip()
                    if len(body) > 40:  # ignore tiny headers
                        self.chunks.append(
                            KnowledgeChunk(
                                doc_name=md_file.name,
                                title=header,
                                content=body[:1500],  # cap length per chunk
                            )
                        )
            except Exception as e:
                continue

    def retrieve(self, query: str, top_k: int = 3) -> List[KnowledgeChunk]:
        """Retrieve relevant documentation chunks using term matching."""
        if not self.chunks:
            return []

        tokens = re.findall(r"\w+", query.lower())
        if not tokens:
            return self.chunks[:top_k]

        scored_chunks = []
        for chunk in self.chunks:
            score = 0
            chunk_lower = (chunk.title + " " + chunk.content).lower()
            for token in tokens:
                if len(token) > 2:
                    cnt = chunk_lower.count(token)
                    score += cnt * 2 if token in chunk.title.lower() else cnt
            if score > 0:
                scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored_chunks[:top_k]]

    def assemble_context(
        self,
        query: str,
        simulation_summary: Optional[Dict[str, Any]] = None,
        top_k: int = 3,
    ) -> str:
        """Combine retrieved documentation with simulation telemetry."""
        relevant_docs = self.retrieve(query, top_k=top_k)
        
        context_parts = []
        
        if simulation_summary:
            context_parts.append("### CURRENT SIMULATION TELEMETRY CONTEXT:")
            context_parts.append(f"- Scenario: {simulation_summary.get('scenario')}")
            context_parts.append(f"- Total Water Applied: {simulation_summary.get('total_water_applied_l', 0.0):.1f} L")
            context_parts.append(f"- Water Balance Max Residual: {simulation_summary.get('water_balance_residual_max_mm', 0.0):.4f} mm")
            
            zones = simulation_summary.get("zone_metrics", [])
            for zm in zones:
                context_parts.append(
                    f"- Zone {zm.get('zone_id')} ({zm.get('crop')}, {zm.get('soil')}): "
                    f"Applied: {zm.get('total_water_l', 0.0):.1f}L | "
                    f"MAE: {zm.get('mean_absolute_error_pct', 0.0):.2f}% | "
                    f"RMSE: {zm.get('rmse_pct', 0.0):.2f}% | "
                    f"Min Moisture: {zm.get('min_moisture_pct', 0.0):.1f}% | "
                    f"Deficit Hours: {zm.get('stress_duration_hours', 0.0):.1f}h"
                )
            context_parts.append("")

        if relevant_docs:
            context_parts.append("### RELEVANT SYSTEM ENGINEERING KNOWLEDGE BASE:")
            for chunk in relevant_docs:
                context_parts.append(f"Source: {chunk.doc_name} > {chunk.title}\n{chunk.content}\n")

        return "\n".join(context_parts)
