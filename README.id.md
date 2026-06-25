# free-llm-api-keys-python

<p align="center">
  <img src="assets/banner.jpg" alt="Free LLM API Keys Banner" width="100%"/>
</p>

<!-- README-I18N:START -->

[English](./README.md) | [中文](./README.zh.md) | [हिंदी](./README.hi.md) | [Español](./README.es.md) | [Français](./README.fr.md) | [العربية](./README.ar.md) | [বাংলা](./README.bn.md) | [Русский](./README.ru.md) | [Português](./README.pt.md) | **Bahasa Indonesia**

<!-- README-I18N:END -->

Modul Python yang menyediakan akses ke **kunci AI gratis** dari repositori [`alistaitsacle/free-llm-api-keys`](https://github.com/alistaitsacle/free-llm-api-keys) dalam format **OpenAI**. Ini mengunduh, mengurai, dan menyimpan sementara (cache) sumber `README.md`, kemudian mengekspos klien siap pakai berdasarkan tipe model (**Teks**, **Gambar**, **TTS**, **Embeddings**) yang **merotasi kunci secara otomatis** dari kunci-kunci yang tersedia.

> ⚠️ **Kunci publik dan bersama**: kunci ini dapat habis (anggaran) atau kedaluwarsa (24–48 jam). Oleh karena itu klien mencoba semua kunci untuk sebuah model satu per satu hingga menemukan yang berfungsi.

## Fitur

- 🔄 **Pembaruan otomatis**: pada setiap peluncuran, menyegarkan daftar dari GitHub jika cache sudah usang (1 jam TTL), jika tidak, menggunakan cache.
- 💾 **Cache lokal + mode luring (offline)**: otomatis kembali ke cache (meskipun usang) jika jaringan tidak tersedia.
- 🔁 **Rotasi kunci otomatis**: beralih ke kunci berikutnya saat kunci ditolak (anggaran / kedaluwarsa / pembatasan laju (rate-limit)), dengan pengulangan (retries) pada kesalahan jaringan sementara.
- 🧩 **4 tipe model**: `chat`, `generate_image`, `tts`, `embeddings`.

## Instalasi

Proyek [uv](https://docs.astral.sh/uv/). Dalam proyek yang Anda gunakan:

```bash
# from the local path
uv add "C:/path/to/free-llm-api-keys-python"

# or via git
uv add "git+https://github.com/<your-user>/free-llm-api-keys-python.git"
```

Pengembangan lokal:

```bash
git clone <this-repo>
cd free-llm-api-keys-python
uv sync
uv run pytest
```

## Mulai Cepat

```python
from free_llm_api_keys import FreeLLMClient

# Upon instantiation, the catalog updates from GitHub if needed
# (otherwise it uses the local cache).
client = FreeLLMClient(type="texte")

response = client.chat([{"role": "user", "content": "Hello!"}])
print(response)
```

## Penggunaan berdasarkan tipe model

### 💬 Teks (chat)

```python
from free_llm_api_keys import FreeLLMClient

client = FreeLLMClient(type="texte")
text = client.chat(
    [{"role": "user", "content": "Explain photosynthesis in 2 sentences."}],
    temperature=0.7,
)
print(text)
```

### 🖼️ Pembuatan gambar

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

## Daftar model yang tersedia

```python
from free_llm_api_keys import Catalog, ModelCategory

catalog = Catalog.load()
print(catalog.list_models())                            # all
print(catalog.list_models(ModelCategory.IMAGE))         # images only
print(len(catalog), "total keys")
```

## Konfigurasi

| Variabel / parameter | Bawaan (Default) | Peran |
|---|---|---|
| `FREE_LLM_CACHE_DIR` (env) | `~/.cache/free-llm-api-keys` | Direktori cache |
| Cache TTL | `3600` s (1 jam) | `Catalog.load(ttl_seconds=...)` |
| Base URL | `https://aiapiv2.pekpik.com/v1` | `FreeLLMClient(base_url=...)` |

Paksa pembaruan dari GitHub:

```python
catalog = Catalog.load(force_refresh=True)
```

## Perilaku jaringan & cache

1. **Peluncuran ke-1**: mengunduh `README.md` dari GitHub, mengurainya, dan menulis cache lokal.
2. **Peluncuran berikutnya** (< 1 jam): menggunakan cache, **tidak ada permintaan jaringan**.
3. **Cache usang** (> 1 jam): mengunduh ulang dan memperbarui cache.
4. **Jaringan tidak tersedia**: menggunakan cache yang ada (meskipun usang); hanya memunculkan `FetchError` jika tidak ada cache.

## Pengecualian

| Pengecualian | Kapan? |
|---|---|
| `NoKeysAvailableError` | Model yang diminta tidak ada dalam katalog. |
| `AllKeysExhaustedError` | Semua kunci untuk model telah gagal. |
| `FetchError` | Tidak mungkin mengunduh README dan tidak ada cache yang tersedia. |
| `ParseError` | Struktur README telah berubah dan tidak dapat diurai lagi. |

## Struktur proyek

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

## Lisensi

Lihat repositori sumber untuk status kunci. Modul ini adalah klien tidak resmi yang membungkus kunci-kunci publik ini.
