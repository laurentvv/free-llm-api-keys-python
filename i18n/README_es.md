# free-llm-api-keys-python

<p align="center">
  <img src="assets/banner.jpg" alt="Free LLM API Keys Banner" width="100%"/>
</p>

<!-- README-I18N:START -->

[English](../README.md) | [中文](README_zh.md) | [हिंदी](README_hi.md) | **Español** | [Français](README_fr.md) | [العربية](README_ar.md) | [বাংলা](README_bn.md) | [Русский](README_ru.md) | [Português](README_pt.md) | [Bahasa Indonesia](README_id.md)

<!-- README-I18N:END -->

Módulo de Python que proporciona acceso a **claves de IA gratuitas** desde el
repositorio [`alistaitsacle/free-llm-api-keys`](https://github.com/alistaitsacle/free-llm-api-keys)
en formato **OpenAI**. Descarga, analiza y almacena en caché el `README.md` fuente,
luego expone clientes listos para usar por tipo de modelo
(**Text**, **Image**, **TTS**, **Embeddings**) que **rotan automáticamente**
a través de las claves disponibles.

> ⚠️ **Claves públicas y compartidas**: pueden agotarse (presupuesto)
> o expirar (24–48 h). Es por eso que el cliente prueba todas las
> claves para un modelo una tras otra hasta que encuentra una que funciona.

## Características

- 🔄 **Actualización automática**: en cada inicio, actualiza la lista desde
  GitHub si la caché está obsoleta (1 h de TTL), de lo contrario usa la caché.
- 💾 **Caché local + modo sin conexión**: respaldo automático a la caché
  (incluso si está obsoleta) si la red no está disponible.
- 🔁 **Rotación automática de claves**: cambia a la siguiente clave cuando una clave
  es rechazada (presupuesto / caducada / límite de tasa), con reintentos en errores
  transitorios de red.
- 🧩 **4 tipos de modelos**: `chat`, `generate_image`, `tts`, `embeddings`.

## Instalación

Proyecto [uv](https://docs.astral.sh/uv/). En tu proyecto consumidor:

```bash
# from the local path
uv add "C:/path/to/free-llm-api-keys-python"

# or via git
uv add "git+https://github.com/<your-user>/free-llm-api-keys-python.git"
```

Desarrollo local:

```bash
git clone <this-repo>
cd free-llm-api-keys-python
uv sync
uv run pytest
```

## Inicio rápido

```python
from free_llm_api_keys import FreeLLMClient

# Upon instantiation, the catalog updates from GitHub if needed
# (otherwise it uses the local cache).
client = FreeLLMClient(type="texte")

response = client.chat([{"role": "user", "content": "Hello!"}])
print(response)
```

## Uso por tipo de modelo

### 💬 Texto (chat)

```python
from free_llm_api_keys import FreeLLMClient

client = FreeLLMClient(type="texte")
text = client.chat(
    [{"role": "user", "content": "Explain photosynthesis in 2 sentences."}],
    temperature=0.7,
)
print(text)
```

### 🖼️ Generación de imágenes

```python
client = FreeLLMClient(type="image")
urls = client.generate_image("A cyberpunk fox in a neon forest", n=1, size="1024x1024")
print(urls[0])  # Generated image URL
```

### 🔊 Texto a voz (TTS)

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

## Lista de modelos disponibles

```python
from free_llm_api_keys import Catalog, ModelCategory

catalog = Catalog.load()
print(catalog.list_models())                            # all
print(catalog.list_models(ModelCategory.IMAGE))         # images only
print(len(catalog), "total keys")
```

## Configuración

| Variable / parámetro | Por defecto | Rol |
|---|---|---|
| `FREE_LLM_CACHE_DIR` (env) | `~/.cache/free-llm-api-keys` | Directorio de caché |
| TTL de la caché | `3600` s (1 h) | `Catalog.load(ttl_seconds=...)` |
| URL base | `https://aiapiv2.pekpik.com/v1` | `FreeLLMClient(base_url=...)` |

Forzar una actualización desde GitHub:

```python
catalog = Catalog.load(force_refresh=True)
```

## Comportamiento de la red y caché

1. **1er inicio**: descarga el `README.md` desde GitHub, lo analiza,
   y escribe la caché local.
2. **Inicios posteriores** (< 1 h): usa la caché, **sin solicitudes de red**.
3. **Caché obsoleta** (> 1 h): vuelve a descargar y actualiza la caché.
4. **Red no disponible**: usa la caché existente (incluso si está obsoleta);
   lanza `FetchError` solo si no existe caché.

## Excepciones

| Excepción | ¿Cuándo? |
|---|---|
| `NoKeysAvailableError` | El modelo solicitado no existe en el catálogo. |
| `AllKeysExhaustedError` | Todas las claves para el modelo han fallado. |
| `FetchError` | Imposible descargar el README y sin caché disponible. |
| `ParseError` | La estructura del README ha cambiado y ya no se puede analizar. |

## Estructura del proyecto

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

## Licencia

Consulta el repositorio fuente para el estado de las claves. Este módulo es un cliente
no oficial alrededor de estas claves públicas.
