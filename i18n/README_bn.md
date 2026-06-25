# free-llm-api-keys-python

<p align="center">
  <img src="assets/banner.jpg" alt="Free LLM API Keys Banner" width="100%"/>
</p>

<!-- README-I18N:START -->

[English](../README.md) | [中文](README_zh.md) | [हिंदी](README_hi.md) | [Español](README_es.md) | [Français](README_fr.md) | [العربية](README_ar.md) | **বাংলা** | [Русский](README_ru.md) | [Português](README_pt.md) | [Bahasa Indonesia](README_id.md)

<!-- README-I18N:END -->

পাইথন মডিউল যা **OpenAI** ফরম্যাটে [`alistaitsacle/free-llm-api-keys`](https://github.com/alistaitsacle/free-llm-api-keys) রিপোজিটরি থেকে **ফ্রি এআই কি (free AI keys)**-তে অ্যাক্সেস প্রদান করে। এটি সোর্স `README.md` ডাউনলোড, পার্স এবং ক্যাশে করে, তারপর মডেল টাইপ অনুযায়ী রেডি-টু-ইউজ ক্লায়েন্ট এক্সপোজ করে (**Text**, **Image**, **TTS**, **Embeddings**) যা স্বয়ংক্রিয়ভাবে উপলব্ধ কি-গুলোর মধ্যে **রোটেট (rotate)** করে।

> ⚠️ **পাবলিক এবং শেয়ার্ড কি**: এগুলো শেষ হয়ে যেতে পারে (বাজেট) অথবা এক্সপায়ার হতে পারে (২৪–৪৮ ঘণ্টা)। এই কারণে ক্লায়েন্ট একটি মডেলের জন্য সব কি একে একে চেষ্টা করে যতক্ষণ না কার্যকর কোনো কি খুঁজে পায়।

## বৈশিষ্ট্য

- 🔄 **অটো-আপডেট**: প্রতিবার চালু করার সময় ক্যাশে পুরনো হলে (১ ঘণ্টা TTL) গিটহাব থেকে তালিকা রিফ্রেশ করে, অন্যথায় ক্যাশে ব্যবহার করে।
- 💾 **লোকাল ক্যাশে + অফলাইন মোড**: নেটওয়ার্ক উপলব্ধ না থাকলে স্বয়ংক্রিয়ভাবে ক্যাশ ব্যবহার করে (এমনকি পুরনো হলেও)।
- 🔁 **কি অটো-রোটেশন**: কোনো কি প্রত্যাখ্যাত হলে (বাজেট / এক্সপায়ার্ড / রেট-লিমিট) পরবর্তী কি-তে সুইচ করে, সাথে ক্ষণস্থায়ী নেটওয়ার্ক এরর হলে রিট্রাই (retry) করে।
- 🧩 **৪টি মডেল টাইপ**: `chat`, `generate_image`, `tts`, `embeddings`।

## ইনস্টলেশন

[uv](https://docs.astral.sh/uv/) প্রজেক্ট। আপনার কনজিউমিং প্রজেক্টে:

```bash
# from the local path
uv add "C:/path/to/free-llm-api-keys-python"

# or via git
uv add "git+https://github.com/<your-user>/free-llm-api-keys-python.git"
```

লোকাল ডেভেলপমেন্ট:

```bash
git clone <this-repo>
cd free-llm-api-keys-python
uv sync
uv run pytest
```

## কুইক স্টার্ট

```python
from free_llm_api_keys import FreeLLMClient

# Upon instantiation, the catalog updates from GitHub if needed
# (otherwise it uses the local cache).
client = FreeLLMClient(type="texte")

response = client.chat([{"role": "user", "content": "Hello!"}])
print(response)
```

## মডেল টাইপ অনুযায়ী ব্যবহার

### 💬 টেক্সট (chat)

```python
from free_llm_api_keys import FreeLLMClient

client = FreeLLMClient(type="texte")
text = client.chat(
    [{"role": "user", "content": "Explain photosynthesis in 2 sentences."}],
    temperature=0.7,
)
print(text)
```

### 🖼️ ইমেজ জেনারেশন

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

## উপলব্ধ মডেলের তালিকা

```python
from free_llm_api_keys import Catalog, ModelCategory

catalog = Catalog.load()
print(catalog.list_models())                            # all
print(catalog.list_models(ModelCategory.IMAGE))         # images only
print(len(catalog), "total keys")
```

## কনফিগারেশন

| ভেরিয়েবল / প্যারামিটার | ডিফল্ট | ভূমিকা |
|---|---|---|
| `FREE_LLM_CACHE_DIR` (env) | `~/.cache/free-llm-api-keys` | ক্যাশে ডিরেক্টরি |
| ক্যাশে TTL | `3600` s (১ ঘণ্টা) | `Catalog.load(ttl_seconds=...)` |
| বেস URL | `https://aiapiv2.pekpik.com/v1` | `FreeLLMClient(base_url=...)` |

গিটহাব থেকে আপডেট ফোর্স করুন:

```python
catalog = Catalog.load(force_refresh=True)
```

## নেটওয়ার্ক এবং ক্যাশে আচরণ

১. **প্রথম লঞ্চ**: গিটহাব থেকে `README.md` ডাউনলোড করে, এটি পার্স করে এবং লোকাল ক্যাশে লেখে।
২. **পরবর্তী লঞ্চসমূহ** (< ১ ঘণ্টা): ক্যাশে ব্যবহার করে, **কোনো নেটওয়ার্ক রিকোয়েস্ট নেই**।
৩. **পুরনো ক্যাশে** (> ১ ঘণ্টা): পুনরায় ডাউনলোড করে এবং ক্যাশে আপডেট করে।
৪. **নেটওয়ার্ক অনুপলব্ধ**: বিদ্যমান ক্যাশে ব্যবহার করে (এমনকি পুরনো হলেও); ক্যাশে না থাকলেই কেবল `FetchError` রেইজ করে।

## এক্সেপশন

| এক্সেপশন | কখন? |
|---|---|
| `NoKeysAvailableError` | ক্যাটালগে অনুরোধ করা মডেলটির অস্তিত্ব নেই। |
| `AllKeysExhaustedError` | মডেলের জন্য সব কি ব্যর্থ হয়েছে। |
| `FetchError` | README ডাউনলোড করা অসম্ভব এবং কোনো ক্যাশে উপলব্ধ নেই। |
| `ParseError` | README-এর কাঠামো পরিবর্তিত হয়েছে এবং আর পার্স করা সম্ভব নয়। |

## প্রজেক্ট স্ট্রাকচার

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

## লাইসেন্স

কি-গুলোর স্ট্যাটাসের জন্য সোর্স রিপোজিটরি দেখুন। এই মডিউলটি এই পাবলিক কি-গুলোর আশেপাশে একটি আনঅফিসিয়াল ক্লায়েন্ট।
