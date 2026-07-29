from __future__ import annotations

import logging
from typing import Any, Dict, List

from backend.graph.state import WorkflowState
from backend.rag.retriever import RAGRetriever

logger = logging.getLogger(__name__)


class SymptomAgent:
    def __init__(self, retriever: RAGRetriever | None = None) -> None:
        self.retriever = retriever

    def _build_query(self, state: WorkflowState) -> str:
        parts = []
        if state.get("make"):
            parts.append(f"make: {state['make']}")
        if state.get("model"):
            parts.append(f"model: {state['model']}")
        if state.get("year"):
            parts.append(f"year: {state['year']}")
        if state.get("code"):
            parts.append(f"code: {state['code']}")
        if state.get("symptoms"):
            parts.append(f"symptoms: {state['symptoms']}")

        return " | ".join(parts) if parts else "general automotive troubleshooting"

    def run(self, state: WorkflowState) -> WorkflowState:
        symptoms = (state.get("symptoms") or "").strip()
        if not symptoms:
            return state

        if self.retriever is None:
            try:
                self.retriever = RAGRetriever()
            except Exception as exc:
                logger.exception("Failed to initialize RAG retriever: %s", exc)
                state["symptom_result"] = {
                    "query": symptoms,
                    "context": [],
                    "troubleshooting_hints": [],
                }
                return state

        query = self._build_query(state)
        docs = self.retriever.retrieve(query=query, k=4)

        context_chunks: List[str] = []
        troubleshooting_hints: List[str] = []
        sources = state.get("sources", [])

        for doc in docs:
            text = doc.page_content.strip()
            if text:
                context_chunks.append(text)
                troubleshooting_hints.append(text.split(".")[0].strip())
            metadata = doc.metadata or {}
            sources.append(
                {
                    "source": str(metadata.get("source", "rag_document")),
                    "type": "rag",
                    "page": metadata.get("page", "unknown"),
                }
            )

        if not context_chunks:
            logger.info("No RAG context retrieved for symptom query.")

        state["symptom_result"] = {
            "query": query,
            "context": context_chunks,
            "troubleshooting_hints": troubleshooting_hints[:5],
        }
        state["sources"] = sources
        return state
