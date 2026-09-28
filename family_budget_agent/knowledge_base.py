"""Base de conocimientos local de educación financiera (perfil `local`).

Sustituto gratuito y open-source de Vertex AI Search: ChromaDB embebido como
vector store persistente en `.chroma/`. Los embeddings se generan con el
modelo ONNX por defecto de Chroma (all-MiniLM-L6-v2, 100% local) salvo que se
defina `OLLAMA_EMBED_MODEL`, en cuyo caso se usa la API de Ollama.

La colección se siembra con documentos de educación financiera familiar la
primera vez que se consulta.
"""

import logging
from typing import Any, Dict, List

import chromadb

from . import config

logger = logging.getLogger(__name__)

_CHROMA_PATH = ".chroma/family_finance"
_COLLECTION_NAME = "family_finance_guides"

_SEED_DOCUMENTS: List[str] = [
    "Regla 50/30/20: destina el 50% de los ingresos a necesidades básicas "
    "(vivienda, alimentación, transporte), el 30% a gastos discrecionales "
    "(ocio, restaurantes) y el 20% al ahorro y la reducción de deuda.",
    "Fondo de emergencia: acumula entre 3 y 6 meses de gastos esenciales en "
    "una cuenta líquida y separada antes de asumir inversiones de riesgo.",
    "Reducción de gastos en servicios: revisa tarifas de luz y gas una vez al "
    "año, usa programación de termostato, elimina suscripciones sin uso y "
    "sustituye iluminación por LED de bajo consumo.",
    "Ahorro para la educación de los hijos: abre una cuenta de ahorro "
    "específica, automatiza transferencias mensuales el día de cobro y "
    "valora planes de ahorro con ventajas fiscales según tu país.",
    "Control de deudas: paga primero las deudas con mayor interés (método "
    "avalancha) o las de menor saldo para ganar tracción (método bola de "
    "nieve). Evita financiar consumo corriente con tarjetas de crédito.",
    "Presupuesto familiar con sobres: asigna un sobre (físico o digital) a "
    "cada categoría de gasto; cuando un sobre se agota, no se puede gastar "
    "más en esa categoría hasta el mes siguiente.",
    "Revisión presupuestaria mensual: reúne a la familia 30 minutos al mes "
    "para revisar el desglose por categorías, celebrar el ahorro logrado y "
    "ajustar los límites del mes siguiente.",
]

_collection = None


def _ollama_embed(texts: List[str]) -> List[List[float]]:
    """Genera embeddings con la API de Ollama (`/api/embed`)."""
    import httpx

    resp = httpx.post(
        f"{config.OLLAMA_API_BASE}/api/embed",
        json={"model": config.OLLAMA_EMBED_MODEL, "input": texts},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["embeddings"]


def _get_collection():
    """Devuelve la colección ChromaDB, sembrándola la primera vez."""
    global _collection
    if _collection is not None:
        return _collection

    client = chromadb.PersistentClient(path=_CHROMA_PATH)
    use_ollama = bool(config.OLLAMA_EMBED_MODEL)
    embedding_function = None
    if not use_ollama:
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

        embedding_function = DefaultEmbeddingFunction()
    coll = client.get_or_create_collection(
        name=_COLLECTION_NAME, embedding_function=embedding_function
    )

    if coll.count() == 0:
        ids = [f"doc-{i:02d}" for i in range(len(_SEED_DOCUMENTS))]
        if use_ollama:
            coll.add(
                documents=_SEED_DOCUMENTS,
                embeddings=_ollama_embed(_SEED_DOCUMENTS),
                ids=ids,
            )
        else:
            coll.add(documents=_SEED_DOCUMENTS, ids=ids)
        logger.info(
            "[KB] Colección '%s' sembrada con %d documentos.",
            _COLLECTION_NAME,
            len(_SEED_DOCUMENTS),
        )

    _collection = coll
    return coll


def search_family_finance_guides(query: str, max_results: int = 3) -> Dict[str, Any]:
    """Busca en la base de conocimientos local de economía familiar.

    Args:
        query: Consulta en lenguaje natural (ej. "cómo reducir el gasto en
            servicios" o "fondo de emergencia").
        max_results: Número máximo de fragmentos a devolver.

    Returns:
        Diccionario con el estado y la lista de fragmentos relevantes.
    """
    coll = _get_collection()
    if config.OLLAMA_EMBED_MODEL:
        result = coll.query(
            query_embeddings=_ollama_embed([query]), n_results=max_results
        )
    else:
        result = coll.query(query_texts=[query], n_results=max_results)

    documents = (result.get("documents") or [[]])[0]
    return {
        "status": "SUCCESS",
        "query": query,
        "results": documents,
    }
