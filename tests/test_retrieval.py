from backend.rag.ingest import ingest_documents
from backend.rag.retriever import RAGRetriever


def test_ingest_runs_without_crashing() -> None:
    indexed = ingest_documents()
    assert isinstance(indexed, int)
    assert indexed >= 0


def test_retriever_returns_list() -> None:
    retriever = RAGRetriever()
    docs = retriever.retrieve("rough idle diagnosis", k=2)
    assert isinstance(docs, list)
