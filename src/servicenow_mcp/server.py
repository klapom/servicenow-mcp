"""FastMCP server + ServiceNowKnowledgeMCP singleton.

The RAG stack (``servicenow_mcp.knowledge.knowledge_mcp.ServiceNowKnowledgeMCP``)
is instantiated lazily on first tool call — Qdrant/Neo4j/vLLM/Redis clients
are slow to init. Tool wrappers in ``servicenow_mcp.tools.*`` delegate here.

``kb.connect()`` is called in the singleton init — without it,
``_embed_client`` stays ``None`` and embedding-dependent tools crash
(bug seen in fnt/ot-knowledge before this pattern was baked in).
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from servicenow_mcp import __service_name__, __version__
from servicenow_mcp.config import get_settings
from servicenow_mcp.knowledge.config import ServiceNowConfig
from servicenow_mcp.knowledge.knowledge_mcp import ServiceNowKnowledgeMCP

mcp = FastMCP(__service_name__)

# DNS-rebinding off — CF-Tunnel Host header != localhost.
mcp.settings.transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=False,
)

_knowledge: ServiceNowKnowledgeMCP | None = None


def get_knowledge() -> ServiceNowKnowledgeMCP:
    """Lazy singleton — avoids Qdrant/Neo4j/vLLM connection churn on import."""
    global _knowledge
    if _knowledge is None:
        s = get_settings()
        cfg = ServiceNowConfig(
            vllm_base_url=s.vllm_base_url,
            vllm_model=s.vllm_model,
            qdrant_url=s.qdrant_url,
            qdrant_collection=s.qdrant_collection,
            neo4j_uri=s.neo4j_uri,
            neo4j_user=s.neo4j_user,
            neo4j_password=s.neo4j_password,
            retrieval_top_k=s.retrieval_top_k,
            docs_dir=s.docs_dir,
            embed_base_url=s.embed_base_url,
        )
        kb = ServiceNowKnowledgeMCP(cfg)
        kb.connect()
        _knowledge = kb
    return _knowledge


# Tool modules — imports trigger @mcp.tool() registration.
from servicenow_mcp.tools import ask, graph, lookup, search  # noqa: E402, F401

__all__ = ["__service_name__", "__version__", "get_knowledge", "mcp"]
