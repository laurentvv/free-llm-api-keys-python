# free-llm-api-keys-python

<p align="center">
  <img src="assets/banner.jpg" alt="Free LLM API Keys Banner" width="100%"/>
</p>

<!-- README-I18N:START -->

[English](../README.md) | **中文** | [हिंदी](README_hi.md) | [Español](README_es.md) | [Français](README_fr.md) | [العربية](README_ar.md) | [বাংলা](README_bn.md) | [Русский](README_ru.md) | [Português](README_pt.md) | [Bahasa Indonesia](README_id.md)

<!-- README-I18N:END -->

该 Python 模块以 **OpenAI** 格式提供对
[`alistaitsacle/free-llm-api-keys`](https://github.com/alistaitsacle/free-llm-api-keys)
仓库中**免费 AI 密钥**的访问。它会下载、解析并缓存源 `README.md`，
然后按模型类型（**Text**、**Image**、**TTS**、**Embeddings**）公开即用型客户端，这些客户端会在可用密钥之间**自动轮换**。

> ⚠️ **公共与共享密钥**：它们可能会被耗尽（预算）
> 或过期（24-48 小时）。因此，客户端会依次尝试某个模型的所有密钥，直到找到一个可用的密钥。

## 特性

- 🔄 **自动更新**：每次启动时，如果缓存已过期（1 小时 TTL），则从 GitHub 刷新列表，否则使用缓存。
- 💾 **本地缓存 + 离线模式**：如果网络不可用，自动回退到缓存（即使已过期）。
- 🔁 **密钥自动轮换**：当密钥被拒绝（预算 / 过期 / 速率限制）时切换到下一个密钥，并在遇到短暂的网络错误时重试。
- 🧩 **4 种模型类型**：`chat`、`generate_image`、`tts`、`embeddings`。

## 安装

[uv](https://docs.astral.sh/uv/) 项目。在你的使用项目中：

```bash
# from the local path
uv add "C:/path/to/free-llm-api-keys-python"

# or via git
uv add "git+https://github.com/<your-user>/free-llm-api-keys-python.git"
```

本地开发：

```bash
git clone <this-repo>
cd free-llm-api-keys-python
uv sync
uv run pytest
```

## 快速开始

```python
from free_llm_api_keys import FreeLLMClient

# Upon instantiation, the catalog updates from GitHub if needed
# (otherwise it uses the local cache).
client = FreeLLMClient(type="texte")

response = client.chat([{"role": "user", "content": "Hello!"}])
print(response)
```

## 按模型类型使用

### 💬 文本 (chat)

```python
from free_llm_api_keys import FreeLLMClient

client = FreeLLMClient(type="texte")
text = client.chat(
    [{"role": "user", "content": "Explain photosynthesis in 2 sentences."}],
    temperature=0.7,
)
print(text)
```

### 🖼️ 图像生成

```python
client = FreeLLMClient(type="image")
urls = client.generate_image("A cyberpunk fox in a neon forest", n=1, size="1024x1024")
print(urls[0])  # Generated image URL
```

### 🔊 文本转语音 (TTS)

```python
client = FreeLLMClient(type="tts")
audio: bytes = client.tts("Hello, this is a test.", voice="alloy")
Path("output.mp3").write_bytes(audio)
```

### 🧮 嵌入 (Embeddings)

```python
client = FreeLLMClient(type="embeddings")
vectors = client.embeddings(["text one", "text two"])
print(len(vectors), len(vectors[0]))  # 2 vectors of dimension N
```

## 可用模型列表

```python
from free_llm_api_keys import Catalog, ModelCategory

catalog = Catalog.load()
print(catalog.list_models())                            # all
print(catalog.list_models(ModelCategory.IMAGE))         # images only
print(len(catalog), "total keys")
```

## 配置

| 变量 / 参数 | 默认值 | 作用 |
|---|---|---|
| `FREE_LLM_CACHE_DIR` (env) | `~/.cache/free-llm-api-keys` | 缓存目录 |
| 缓存 TTL | `3600` s (1 h) | `Catalog.load(ttl_seconds=...)` |
| 基础 URL | `https://aiapiv2.pekpik.com/v1` | `FreeLLMClient(base_url=...)` |

强制从 GitHub 更新：

```python
catalog = Catalog.load(force_refresh=True)
```

## 网络与缓存行为

1. **首次启动**：从 GitHub 下载 `README.md`，对其进行解析并写入本地缓存。
2. **后续启动**（< 1 小时）：使用缓存，**无网络请求**。
3. **过期缓存**（> 1 小时）：重新下载并更新缓存。
4. **网络不可用**：使用现有缓存（即使已过期）；仅当没有缓存时才会抛出 `FetchError`。

## 异常

| 异常 | 何时触发？ |
|---|---|
| `NoKeysAvailableError` | 请求的模型在目录中不存在。 |
| `AllKeysExhaustedError` | 该模型的所有密钥均已失效。 |
| `FetchError` | 无法下载 README 且没有可用的缓存。 |
| `ParseError` | README 的结构已更改，不再可解析。 |

## 项目结构

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

## 许可证

有关密钥的状态，请参阅源仓库。本模块是围绕这些公共密钥的非官方客户端。
