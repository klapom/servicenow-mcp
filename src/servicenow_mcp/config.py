"""Settings — extends ``BaseServiceSettings`` from mcp-toolkit-py (ADR-010).

Field names match ``servicenow_mcp.knowledge.config.ServiceNowConfig`` so a
``Settings`` instance can be converted into one without renaming.
"""

from __future__ import annotations

from functools import lru_cache

from mcp_toolkit_py.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    listen_port: int = 32310
    mcp_port: int = 33310

    # vLLM (OpenAI-compatible)
    vllm_base_url: str = "http://localhost:32000/v1"
    vllm_model: str = "qwen36-35b"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "sn_mcp_docs"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "aegis-rag-neo4j-password"

    # Retrieval
    retrieval_top_k: int = 8

    # Docs directory (for lookup_table file reads)
    docs_dir: str = "docs"

    # Embedding proxy (central BGE-M3 service)
    embed_base_url: str = "http://127.0.0.1:8097/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
