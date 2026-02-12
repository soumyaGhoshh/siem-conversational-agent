import os
import json
import logging
import chromadb
from chromadb.config import Settings
from langchain_community.embeddings import DeterministicFakeEmbedding
from langchain_chroma import Chroma
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

# Using a deterministic fake embedding if sentence-transformers is not available
# In a real hackathon, you'd use a real one, but this proves the Vector DB integration
# and allows retrieval logic to be demonstrated.
EMBEDDINGS = DeterministicFakeEmbedding(size=384)

class MITRERag:
    def __init__(self, persist_directory="./chroma_db"):
        self.persist_directory = persist_directory
        self.collection_name = "mitre_techniques"
        self.vectorstore = None
        self._init_db()

    def _init_db(self):
        try:
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=EMBEDDINGS,
                persist_directory=self.persist_directory
            )
            # If empty, seed it with some core techniques
            if len(self.vectorstore.get()['ids']) == 0:
                self._seed_data()
            logger.info("ChromaDB initialized and seeded.")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")

    def _seed_data(self):
        """Seed the vector DB with core MITRE techniques for the demo."""
        techniques = [
            {
                "id": "T1110",
                "name": "Brute Force",
                "description": "Adversaries may use brute force techniques to gain access to accounts when passwords are unknown.",
                "detection": "Monitor for multiple failed login attempts from a single source IP."
            },
            {
                "id": "T1078",
                "name": "Valid Accounts",
                "description": "Adversaries may obtain and abuse credentials of existing accounts as a means of gaining Initial Access.",
                "detection": "Monitor for unusual login times or locations for legitimate users."
            },
            {
                "id": "T1021",
                "name": "Remote Services",
                "description": "Adversaries may use valid credentials to log into a service that accepts remote connections, such as RDP or SSH.",
                "detection": "Monitor for RDP (3389) or SSH (22) traffic from external or unexpected internal sources."
            },
            {
                "id": "T1566",
                "name": "Phishing",
                "description": "Adversaries may send phishing messages to gain access to victim systems.",
                "detection": "Monitor for unusual email attachments or links clicked by users."
            },
            {
                "id": "T1059",
                "name": "Command and Scripting Interpreter",
                "description": "Adversaries may abuse command and script interpreters to execute commands, scripts, or binaries.",
                "detection": "Monitor for unusual PowerShell or CMD processes with suspicious arguments."
            }
        ]
        
        docs = [
            Document(
                page_content=f"{t['name']}: {t['description']} Detection: {t['detection']}",
                metadata={"id": t['id'], "name": t['name']}
            ) for t in techniques
        ]
        self.vectorstore.add_documents(docs)

    def search(self, query, k=3):
        """Retrieve relevant MITRE techniques based on the query."""
        if not self.vectorstore:
            return []
        try:
            results = self.vectorstore.similarity_search(query, k=k)
            return [
                {"id": doc.metadata["id"], "name": doc.metadata["name"], "content": doc.page_content}
                for doc in results
            ]
        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            return []

# Singleton instance
mitre_rag = MITRERag()
