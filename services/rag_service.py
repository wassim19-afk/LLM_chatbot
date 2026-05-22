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
        """Heuristic: detect if question asks for definitions/KPI explanations (FR + EN)."""
        keywords = [
            # English
            "what is", "define", "meaning of", "kpi", "metric",
            "how to calculate", "explain", "what does",
            # French definitions
            "qu'est-ce", "qu est ce", "définition", "definition",
            "signifie", "signification", "comment calculer",
            "c'est quoi", "c est quoi", "expliquer", "expliquez",
            # French contextual natural language
            "comment fonctionne", "que veut dire", "que signifie",
            "donne moi une explication", "explique moi",
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
        """Create rich French business documentation for RAG."""
        docs = {
            "kpi_definitions_fr.txt": """
CA (Chiffre d'Affaires) : Revenu total généré par les ventes. Calculé comme la somme de tous les montants de ventes (SUM of Amount). Utilisé pour mesurer la performance commerciale globale.

Top Clients : Classement des clients selon leur montant total d'achats en ordre décroissant. Requête SQL : SELECT TOP N client, SUM(montant) GROUP BY client ORDER BY SUM(montant) DESC.

Clients fidèles / Loyal customers : Clients avec le plus grand volume d'achats cumulés sur une période. Synonymes : meilleurs clients, clients les plus actifs, high-value customers.

Montant par mois : Agrégation mensuelle du chiffre d'affaires. Utilisé pour l'analyse de tendances et la détection de saisonnalité.

Clients en retard / Overdue : Clients avec des paiements dépassant la date d'échéance. Calculé via la table D_CUSTOMERLEDGERENTRY avec filtre sur DUE DATE et OPEN = true.

Encaissement : Somme des montants reçus (cash in). Table : Fact_CustomerPayementDetail.

Décaissement : Somme des montants payés (cash out). Table fournisseurs.

Achat : Total des achats effectués auprès des fournisseurs.

Variation CA : Comparaison du chiffre d'affaires année sur année. Formule : (CA N - CA N-1) / CA N-1 * 100. Positif = croissance, Négatif = déclin.

Année courante : L'année en cours (YEAR = YEAR(GETDATE())).

Année précédente : L'année précédant l'année courante (YEAR = YEAR(GETDATE()) - 1).
            """,
            "schema_db.txt": """
Tables principales de la base de données SSMS :

D_Customer : Table des clients. Colonnes : No_ (identifiant client), Name (nom client), Address, City, Phone No_, E-Mail.

Fact_CustomerPayementDetail : Faits de paiements clients. Colonnes : Customer No_, Amount (montant), Posting Date (date comptabilisation), Document No_, Entry Type.

D_CUSTOMERLEDGERENTRY : Écritures comptables clients détaillées. Colonnes : Entry No_, Customer No_, Posting Date, Document No_, Amount, Remaining Amount, Due Date, Open (booléen solde ouvert).

D_Vendor : Table des fournisseurs. Colonnes : No_, Name, Address.

D_ValueEntries : Écritures de valeur pour articles. Colonnes : Item No_, Location Code, Valued Quantity, Cost Amount Actual, Posting Date.

Vue CA : Jointure D_Customer + Fact_CustomerPayementDetail regroupée par client et période.

Pour les requêtes de CA par année : utiliser YEAR(Posting Date) = <année> dans WHERE.
Pour les requêtes de CA par mois : utiliser MONTH(Posting Date) = <mois> dans WHERE.
Pour les top clients : utiliser SELECT TOP N ... ORDER BY SUM(Amount) DESC.
            """,
            "business_rules_fr.txt": """
Règles métier importantes :

1. Un client fidèle est défini par le volume total d'achats cumulés (SUM Amount) sur toute la période disponible, trié en ordre décroissant.

2. Le CA (Chiffre d'Affaires) de l'année courante se calcule avec YEAR(Posting Date) = YEAR(GETDATE()).

3. Pour comparer deux années : utiliser CASE WHEN YEAR(...) = 2023 THEN Amount END et CASE WHEN YEAR(...) = 2024 THEN Amount END dans le même SELECT.

4. Les clients en retard : filtre WHERE Open = 1 AND Due Date < GETDATE() sur D_CUSTOMERLEDGERENTRY.

5. Pour les questions sur "combien de clients" : utiliser COUNT(DISTINCT Customer No_).

6. Le montant par mois : GROUP BY YEAR(Posting Date), MONTH(Posting Date) ORDER BY YEAR, MONTH.

7. Questions sur "qui achète le plus" ou "meilleur client" → même requête que top clients.

8. Questions "quel est le CA de janvier 2024" → filtre MONTH = 1 AND YEAR = 2024.

9. Pour les sociétés spécifiques (PEM, SAPEC) : filtre sur Company Name ou Global Dimension.

10. Les montants sont en FCFA (Franc CFA) ou en euros selon la configuration de la société.
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
