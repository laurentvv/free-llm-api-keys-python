# free-llm-api-keys-python

<p align="center">
  <img src="assets/banner.jpg" alt="Free LLM API Keys Banner" width="100%"/>
</p>

<!-- README-I18N:START -->

**English** | [中文](./README.zh.md) | [हिंदी](./README.hi.md) | [Español](./README.es.md) | [Français](./README.fr.md) | [العربية](./README.ar.md) | [বাংলা](./README.bn.md) | [Русский](./README.ru.md) | [Português](./README.pt.md) | [Bahasa Indonesia](./README.id.md)

<!-- README-I18N:END -->

Python module that provides access to **free AI keys** from the
[`alistaitsacle/free-llm-api-keys`](https://github.com/alistaitsacle/free-llm-api-keys)
repository in **OpenAI** format. It downloads, parses, and caches the source `README.md`,
then exposes ready-to-use clients by model type
(**Text**, **Image**, **TTS**, **Embeddings**) that **automatically rotate**
through available keys.

> ⚠️ **Public and shared keys**: they can be exhausted (budget)
> or expired (24–48 h). That is why the client tries all the
> keys for a model one after the other until it finds one that works.

## Features

- 🔄 **Auto-update**: on every launch, refreshes the list from
  GitHub if the cache is stale (1 h TTL), otherwise uses the cache.
- 💾 **Local cache + offline mode**: automatic fallback to the cache
  (even if stale) if the network is unavailable.
- 🔁 **Key auto-rotation**: switches to the next key when a key
  is rejected (budget / expired / rate-limit), with retries on transient
  network errors.
- 🧩 **4 model types**: `chat`, `generate_image`, `tts`, `embeddings`.

## Installation

[uv](https://docs.astral.sh/uv/) project. In your consuming project:

```bash
# from the local path
uv add "C:/path/to/free-llm-api-keys-python"

# or via git
uv add "git+https://github.com/<your-user>/free-llm-api-keys-python.git"
```

Local development:

```bash
git clone <this-repo>
cd free-llm-api-keys-python
uv sync
uv run pytest
```

## Quick Start

```python
from free_llm_api_keys import FreeLLMClient

# Upon instantiation, the catalog updates from GitHub if needed
# (otherwise it uses the local cache).
client = FreeLLMClient(type="texte")

response = client.chat([{"role": "user", "content": "Hello!"}])
print(response)
```

## Usage by model type

### 💬 Text (chat)

```python
from free_llm_api_keys import FreeLLMClient

client = FreeLLMClient(type="texte")
text = client.chat(
    [{"role": "user", "content": "Explain photosynthesis in 2 sentences."}],
    temperature=0.7,
)
print(text)
```

### 🖼️ Image generation

```python
client = FreeLLMClient(type="image")
urls = client.generate_image("A cyberpunk fox in a neon forest", n=1, size="1024x1024")
print(urls[0])  # Generated image URL
```

### 🔊 Text-to-Speech (TTS)

```python
client = FreeLLMClient(type="tts")
audio: bytes = client.tts("Hello, this is a test.", voice="alloy")
Path("output.mp3").write_bytes(audio)
```

### 🧮 Embeddings

```python
client = FreeLLMClient(type="embeddings")
vectors = client.embeddings(["text one", "text two"])
print(len(vectors), len(vectors[0]))  # 2 vectors of dimension N
```

## Available models list

```python
from free_llm_api_keys import Catalog, ModelCategory

catalog = Catalog.load()
print(catalog.list_models())                            # all
print(catalog.list_models(ModelCategory.IMAGE))         # images only
print(len(catalog), "total keys")
```

## Configuration

| Variable / parameter | Default | Role |
|---|---|---|
| `FREE_LLM_CACHE_DIR` (env) | `~/.cache/free-llm-api-keys` | Cache directory |
| Cache TTL | `3600` s (1 h) | `Catalog.load(ttl_seconds=...)` |
| Base URL | `https://aiapiv2.pekpik.com/v1` | `FreeLLMClient(base_url=...)` |

Force an update from GitHub:

```python
catalog = Catalog.load(force_refresh=True)
```

## Network & cache behavior

1. **1st launch**: downloads the `README.md` from GitHub, parses it,
   and writes the local cache.
2. **Subsequent launches** (< 1 h): uses the cache, **no network requests**.
3. **Stale cache** (> 1 h): re-downloads and updates the cache.
4. **Network unavailable**: uses the existing cache (even if stale);
   raises `FetchError` only if no cache exists.

## Exceptions

| Exception | When? |
|---|---|
| `NoKeysAvailableError` | The requested model does not exist in the catalog. |
| `AllKeysExhaustedError` | All keys for the model have failed. |
| `FetchError` | Impossible to download the README and no cache available. |
| `ParseError` | The structure of the README has changed and is no longer parsable. |

## Project structure

```
src/free_llm_api_keys/
├── __init__.py     # Public API
├── fetcher.py      # README download (httpx + ETag)
├── parser.py       # markdown parsing -> KeyEntry
├── classifier.py   # model type (text/image/tts/embeddings)
├── cache.py        # local JSON cache + TTL + offline fallback
├── catalog.py      # fetch + parse + cache orchestration
├── client.py       # FreeLLMClient : OpenAI + auto-rotation + retry
└── exceptions.py
```

## License

See the source repository for the status of the keys. This module is an unofficial
client around these public keys.
