"""RAG (Retrieval Augmented Generation) service for KPI and business definitions."""

import os
from typing import List, Dict, Any, Tuple
import numpy as np

from config.logger import get_logger

logger = get_logger(__name__)


class SimpleVectorStore:
    """Lightweight in-memory vector store with cosine similarity."""

    def __init__(self) -> None:
        self.documents: List[str] = []
        self.embeddings: List[np.ndarray] = []
        self.metadata: List[Dict[str, Any]] = []

    def add_document(
        self, text: str, embedding: np.ndarray, metadata: Dict[str, Any] = None
    ) -> None:
        """Add document with embedding."""
        self.documents.append(text)
        self.embeddings.append(embedding)
        self.metadata.append(metadata or {})

    def search(self, query_embedding: np.ndarray, top_k: int = 3) -> List[Tuple[str, float]]:
        """Search for top-k similar documents."""
        if not self.embeddings:
            return []

        similarities = []
        for emb in self.embeddings:
            sim = self._cosine_similarity(query_embedding, emb)
            similarities.append(sim)

        top_indices = np.argsort(similarities)[-top_k:][::-1]
        return [
            (self.documents[i], float(similarities[i]))
            for i in top_indices
            if similarities[i] > 0.3
        ]

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))


class RAGService:
    """Retrieval Augmented Generation for business context."""

    def __init__(self, doc_dir: str = "rag_documents") -> None:
        self.doc_dir = doc_dir
        self.vector_store = SimpleVectorStore()
        self.embedder = None
        self._initialized = False

    def initialize(self) -> None:
        """Load documents and embeddings."""
        try:
            from sentence_transformers import SentenceTransformer
            self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        except ImportError:
            logger.warning("sentence-transformers not installed. RAG disabled.")
            return

        self.load_documents()
        self._initialized = True

    def load_documents(self) -> None:
        """Load documents from disk."""
        if not os.path.exists(self.doc_dir):
            os.makedirs(self.doc_dir)
            self._create_default_documents()

        for filename in os.listdir(self.doc_dir):
            if filename.endswith(".txt"):
                filepath = os.path.join(self.doc_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                        chunks = self._chunk_text(content, chunk_size=300)
                        self.embed_documents(chunks, source=filename)
                    logger.info(f"Loaded {len(chunks)} chunks from {filename}")
                except Exception as e:
                    logger.error(f"Failed to load {filename}: {e}")

    def embed_documents(self, documents: List[str], source: str = "local") -> None:
        """Embed documents and store vectors."""
        if not self.embedder:
            return

        for doc in documents:
            if not doc.strip():
                continue
            emb = self.embedder.encode(doc)
            self.vector_store.add_document(doc, np.array(emb), {"source": source})

    def retrieve_context(self, query: str, top_k: int = 3) -> str:
        """Retrieve relevant context for a query."""
        if not self._initialized or not self.embedder:
            return ""

        try:
            query_emb = np.array(self.embedder.encode(query))
            results = self.vector_store.search(query_emb, top_k)

            if not results:
                return ""

            context_lines = ["Relevant business definitions:\n"]
            for doc, score in results:
                context_lines.append(f"• {doc}\n")

            return "".join(context_lines)
        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}")
            return ""

    def is_definitional_question(self, question: str) -> bool:
        """Heuristic: detect if question asks for definitions/KPI explanations."""
        keywords = [
            "what is",
            "define",
            "meaning of",
            "kpi",
            "metric",
            "how to calculate",
            "explain",
        ]
        lower_q = question.lower()
        return any(kw in lower_q for kw in keywords)

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = 300) -> List[str]:
        """Split text into chunks."""
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i : i + chunk_size])
            chunks.append(chunk)
        return chunks

    @staticmethod
    def _create_default_documents() -> None:
        """Create sample KPI documentation."""
        docs = {
            "kpi_definitions.txt": """
CA (Chiffre d'Affaires) - Total revenue in currency units.
Calculated as: SUM of all sales transactions.

Top Clients - Customers ranked by total sales amount in descending order.
Used for: Identifying key business drivers and concentration risk.

Montant par mois - Monthly aggregation of revenue.
Used for: Trend analysis and seasonal detection.

Clients en retard - Overdue customers with outstanding payments.
Calculated as: WHERE payment_date > due_date AND status != 'paid'.

CA Variation - Year-over-year revenue comparison.
Formula: (Current Year CA - Prior Year CA) / Prior Year CA * 100.
Positive: Growth. Negative: Decline.
            """,
            "business_rules.txt": """
Customer Ledger Entry - Core transaction record for customer interactions.
Fields: Entry No_, Posting Date, Document No_, Amount.

Sales Amount Actual - Actual revenue recognized (vs budgeted).
Classification: Revenue dimension.

Detailed Customer Ledger Entries - Granular transaction records for audit and reconciliation.
Related to: Customer_view and core ledger tables.

Vendor Ledger Entry - Supplier transaction record.
Fields: Entry No_, Posting Date, Credit/Debit Amount.

Global Dimension 1 & 2 - Organizational hierarchy dimensions.
Used for: Multi-level P&L analysis.
            """,
        }

        rag_dir = "rag_documents"
        os.makedirs(rag_dir, exist_ok=True)
        for filename, content in docs.items():
            filepath = os.path.join(rag_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Created default document: {filename}")


_global_rag_service = RAGService()


def get_rag_service() -> RAGService:
    """Get global RAG service singleton."""
    if not _global_rag_service._initialized:
        _global_rag_service.initialize()
    return _global_rag_service
