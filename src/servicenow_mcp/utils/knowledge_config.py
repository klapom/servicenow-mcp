"""
Configuration for the ServiceNow Knowledge MCP server.
"""

import os
from pydantic import BaseModel, Field


class KnowledgeConfig(BaseModel):
    """Knowledge MCP server configuration."""

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8092)
    debug: bool = Field(default=False)

    # vLLM / LLM backend (OpenAI-compatible)
    vllm_base_url: str = Field(default="http://localhost:18087/v1")
    vllm_model: str = Field(default="qwen35-35b")

    # Qdrant
    qdrant_url: str = Field(default="http://localhost:6333")
    qdrant_collection: str = Field(default="sn_mcp_docs")

    # Neo4j
    neo4j_uri: str = Field(default="bolt://localhost:7687")
    neo4j_user: str = Field(default="neo4j")
    neo4j_password: str = Field(default="aegis-rag-neo4j-password")

    # Retrieval
    retrieval_top_k: int = Field(default=8)

    # Docs directory (for lookup_table file reads)
    docs_dir: str = Field(default="docs")

    @classmethod
    def from_env(cls) -> "KnowledgeConfig":
        return cls(
            host=os.getenv("KNOWLEDGE_HOST", "0.0.0.0"),
            port=int(os.getenv("KNOWLEDGE_PORT", "8092")),
            debug=os.getenv("KNOWLEDGE_DEBUG", "false").lower() == "true",
            vllm_base_url=os.getenv("VLLM_BASE_URL", "http://localhost:18087/v1"),
            vllm_model=os.getenv("VLLM_MODEL", "qwen35-35b"),
            qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            qdrant_collection=os.getenv("QDRANT_COLLECTION", "sn_mcp_docs"),
            neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
            neo4j_password=os.getenv("NEO4J_PASSWORD", "aegis-rag-neo4j-password"),
            retrieval_top_k=int(os.getenv("RETRIEVAL_TOP_K", "8")),
            docs_dir=os.getenv("SN_DOCS_DIR", "docs"),
        )
