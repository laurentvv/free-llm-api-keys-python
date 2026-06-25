"""Téléchargement du README depuis GitHub (raw) via httpx, avec ETag.

On utilise le mécanisme ETag pour ne re-télécharger que si le contenu a
changé côté GitHub. En cas d'échec réseau, on lève :class:`FetchError` ;
c'est le catalogue qui décide de basculer sur le cache local.
"""

from __future__ import annotations

import logging

import httpx

from .exceptions import FetchError

logger = logging.getLogger("free_llm_api_keys")

# URL brute du README sur la branche ``main``.
README_URL = (
    "https://raw.githubusercontent.com/alistaitsacle/"
    "free-llm-api-keys/main/README.md"
)

DEFAULT_TIMEOUT = 15.0


def fetch_readme(
    etag: str | None = None,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    url: str = README_URL,
    client: httpx.Client | None = None,
) -> tuple[str, str | None]:
    """Télécharge le contenu du README.

    Args:
        etag: ETag connu (issu du cache). Si fourni et que GitHub répond
            ``304 Not Modified``, aucun corps n'est renvoyé.
        timeout: Délai d'attente réseau, en secondes.
        url: URL de téléchargement (surchageable pour les tests).
        client: Client httpx existant à réutiliser (pratique pour les tests
            avec transport simulé). Si ``None``, un client éphémère est créé.

    Returns:
        Un couple ``(content, new_etag)``. ``content`` est une chaîne vide
        si le contenu n'a pas changé (304), auquel cas ``new_etag == etag``.

    Raises:
        FetchError: En cas d'erreur réseau ou de code HTTP inattendu.
    """
    headers: dict[str, str] = {}
    if etag:
        headers["If-None-Match"] = etag

    owns_client = client is None
    if owns_client:
        client = httpx.Client(timeout=timeout)
    try:
        try:
            response = client.get(url, headers=headers, follow_redirects=True)
        except httpx.HTTPError as exc:
            raise FetchError(f"Échec réseau lors du téléchargement du README : {exc}") from exc

        if response.status_code == 304:
            logger.info("README inchangé côté GitHub (ETag correspond).")
            return "", etag

        if response.status_code != 200:
            raise FetchError(
                f"Réponse HTTP inattendue {response.status_code} pour {url}"
            )

        new_etag = response.headers.get("ETag") or etag
        return response.text, new_etag
    finally:
        if owns_client:
            client.close()
