# free-llm-api-keys-python

Module Python qui donne accès aux **clés IA gratuites** du dépôt
[`alistaitsacle/free-llm-api-keys`](https://github.com/alistaitsacle/free-llm-api-keys)
au format **OpenAI**. Il télécharge, parse et met en cache le `README.md`
source, puis expose des clients prêts à l'emploi par type de modèle
(**Texte**, **Image**, **TTS**, **Embeddings**) qui **rotent automatiquement**
sur les clés disponibles.

> ⚠️ **Clés publiques et partagées** : elles peuvent être épuisées (budget)
> ou expirées (24–48 h). C'est pour cela que le client essaie toutes les
> clés d'un modèle l'une après l'autre jusqu'à en trouver une qui fonctionne.

## Fonctionnalités

- 🔄 **Auto-mise à jour** : à chaque lancement, rafraîchit la liste depuis
  GitHub si le cache est stale (TTL 1 h), sinon utilise le cache.
- 💾 **Cache local + mode hors-ligne** : repli automatique sur le cache
  (même stale) si le réseau est indisponible.
- 🔁 **Auto-rotation des clés** : bascule sur la clé suivante quand une clé
  est refusée (budget / expirée / rate-limit), avec retry sur les erreurs
  réseau transitoires.
- 🧩 **4 types de modèles** : `chat`, `generate_image`, `tts`, `embeddings`.

## Installation

Projet [uv](https://docs.astral.sh/uv/). Dans ton projet consommateur :

```bash
# depuis le chemin local
uv add "C:/chemin/vers/free-llm-api-keys-python"

# ou via git
uv add "git+https://github.com/<ton-user>/free-llm-api-keys-python.git"
```

Développement local :

```bash
git clone <ce-repo>
cd free-llm-api-keys-python
uv sync
uv run pytest
```

## Démarrage rapide

```python
from free_llm_api_keys import FreeLLMClient

# À l'instanciation, le catalogue se met à jour depuis GitHub si besoin
# (sinon il utilise le cache local).
client = FreeLLMClient(model="gpt-5.5")

reponse = client.chat([{"role": "user", "content": "Bonjour !"}])
print(reponse)
```

## Utilisation par type de modèle

### 💬 Texte (chat)

```python
from free_llm_api_keys import FreeLLMClient

client = FreeLLMClient(model="gpt-5.5")
texte = client.chat(
    [{"role": "user", "content": "Explique la photosynthèse en 2 phrases."}],
    temperature=0.7,
)
print(texte)
```

### 🖼️ Génération d'images

```python
client = FreeLLMClient(model="dall-e-3")
urls = client.generate_image("Un renard cyberpunk dans une forêt néon", n=1, size="1024x1024")
print(urls[0])  # URL de l'image générée
```

### 🔊 Synthèse vocale (TTS)

```python
client = FreeLLMClient(model="tts-1-hd")
audio: bytes = client.tts("Bonjour, ceci est un test.", voice="alloy")
Path("sortie.mp3").write_bytes(audio)
```

### 🧮 Embeddings

```python
client = FreeLLMClient(model="text-embedding-3-small")
vecteurs = client.embeddings(["texte un", "texte deux"])
print(len(vecteurs), len(vecteurs[0]))  # 2 vecteurs de dimension N
```

## Liste des modèles disponibles

```python
from free_llm_api_keys import Catalog, ModelCategory

catalog = Catalog.load()
print(catalog.list_models())                            # tous
print(catalog.list_models(ModelCategory.IMAGE))         # images seulement
print(len(catalog), "clés au total")
```

## Configuration

| Variable / paramètre | Défaut | Rôle |
|---|---|---|
| `FREE_LLM_CACHE_DIR` (env) | `~/.cache/free-llm-api-keys` | Dossier du cache |
| TTL du cache | `3600` s (1 h) | `Catalog.load(ttl_seconds=...)` |
| Base URL | `https://aiapiv2.pekpik.com/v1` | `FreeLLMClient(base_url=...)` |

Forcer une mise à jour depuis GitHub :

```python
catalog = Catalog.load(force_refresh=True)
```

## Comportement réseau & cache

1. **1er lancement** : télécharge le `README.md` depuis GitHub, le parse,
   écrit le cache local.
2. **Lancements suivants** (< 1 h) : utilise le cache, **aucune requête**.
3. **Cache stale** (> 1 h) : re-télécharge et met à jour le cache.
4. **Réseau indisponible** : utilise le cache existant (même stale) ;
   lève `FetchError` seulement si aucun cache n'existe.

## Exceptions

| Exception | Quand ? |
|---|---|
| `NoKeysAvailableError` | Le modèle demandé n'existe pas dans le catalogue. |
| `AllKeysExhaustedError` | Toutes les clés du modèle ont échoué. |
| `FetchError` | Impossible de télécharger le README et aucun cache. |
| `ParseError` | La structure du README a changé et n'est plus parsable. |

## Structure du projet

```
src/free_llm_api_keys/
├── __init__.py     # API publique
├── fetcher.py      # téléchargement README (httpx + ETag)
├── parser.py       # parsing markdown -> KeyEntry
├── classifier.py   # type du modèle (texte/image/tts/embeddings)
├── cache.py        # cache JSON local + TTL + fallback hors-ligne
├── catalog.py      # orchestration fetch + parse + cache
├── client.py       # FreeLLMClient : OpenAI + auto-rotation + retry
└── exceptions.py
```

## Licence

Voir le dépôt source pour le statut des clés. Ce module est un client
non officiel autour de ces clés publiques.
