# free-llm-api-keys-python

<p align="center">
  <img src="assets/banner.jpg" alt="Free LLM API Keys Banner" width="100%"/>
</p>

<!-- README-I18N:START -->

[English](./README.md) | [中文](./README.zh.md) | **हिंदी** | [Español](./README.es.md) | [Français](./README.fr.md) | [العربية](./README.ar.md) | [বাংলা](./README.bn.md) | [Русский](./README.ru.md) | [Português](./README.pt.md) | [Bahasa Indonesia](./README.id.md)

<!-- README-I18N:END -->

पायथन मॉड्यूल जो [`alistaitsacle/free-llm-api-keys`](https://github.com/alistaitsacle/free-llm-api-keys) रिपॉजिटरी से **OpenAI** प्रारूप में **मुफ्त AI कुंजियों** तक पहुंच प्रदान करता है। यह स्रोत `README.md` को डाउनलोड, पार्स और कैश करता है, फिर मॉडल प्रकार (**Text**, **Image**, **TTS**, **Embeddings**) के अनुसार उपयोग के लिए तैयार क्लाइंट्स प्रदान करता है जो उपलब्ध कुंजियों के बीच **स्वचालित रूप से रोटेट** होते हैं।

> ⚠️ **सार्वजनिक और साझा कुंजियाँ**: वे समाप्त (बजट) हो सकती हैं या एक्सपायर (24–48 घंटे) हो सकती हैं। यही कारण है कि क्लाइंट किसी मॉडल के लिए सभी कुंजियों को एक के बाद एक तब तक आजमाता है जब तक कि उसे कोई काम करने वाली कुंजी नहीं मिल जाती।

## विशेषताएँ

- 🔄 **ऑटो-अपडेट**: हर बार लॉन्च होने पर, यदि कैश पुराना (1 घंटे का TTL) है, तो GitHub से सूची को रीफ्रेश करता है, अन्यथा कैश का उपयोग करता है।
- 💾 **स्थानीय कैश + ऑफलाइन मोड**: नेटवर्क अनुपलब्ध होने पर कैश का स्वचालित उपयोग (भले ही वह पुराना हो)।
- 🔁 **कुंजी ऑटो-रोटेशन**: जब कोई कुंजी अस्वीकृत (बजट / एक्सपायर / रेट-लिमिट) हो जाती है, तो यह अगली कुंजी पर स्विच हो जाता है, और क्षणिक नेटवर्क त्रुटियों पर पुनः प्रयास (retries) करता है।
- 🧩 **4 मॉडल प्रकार**: `chat`, `generate_image`, `tts`, `embeddings`।

## इंस्टॉलेशन

[uv](https://docs.astral.sh/uv/) प्रोजेक्ट। आपके उपयोग करने वाले प्रोजेक्ट में:

```bash
# from the local path
uv add "C:/path/to/free-llm-api-keys-python"

# or via git
uv add "git+https://github.com/<your-user>/free-llm-api-keys-python.git"
```

स्थानीय विकास:

```bash
git clone <this-repo>
cd free-llm-api-keys-python
uv sync
uv run pytest
```

## त्वरित शुरुआत

```python
from free_llm_api_keys import FreeLLMClient

# Upon instantiation, the catalog updates from GitHub if needed
# (otherwise it uses the local cache).
client = FreeLLMClient(type="texte")

response = client.chat([{"role": "user", "content": "Hello!"}])
print(response)
```

## मॉडल प्रकार द्वारा उपयोग

### 💬 टेक्स्ट (chat)

```python
from free_llm_api_keys import FreeLLMClient

client = FreeLLMClient(type="texte")
text = client.chat(
    [{"role": "user", "content": "Explain photosynthesis in 2 sentences."}],
    temperature=0.7,
)
print(text)
```

### 🖼️ इमेज जनरेशन

```python
client = FreeLLMClient(type="image")
urls = client.generate_image("A cyberpunk fox in a neon forest", n=1, size="1024x1024")
print(urls[0])  # Generated image URL
```

### 🔊 टेक्स्ट-टू-स्पीच (TTS)

```python
client = FreeLLMClient(type="tts")
audio: bytes = client.tts("Hello, this is a test.", voice="alloy")
Path("output.mp3").write_bytes(audio)
```

### 🧮 एम्बेडिंग

```python
client = FreeLLMClient(type="embeddings")
vectors = client.embeddings(["text one", "text two"])
print(len(vectors), len(vectors[0]))  # 2 vectors of dimension N
```

## उपलब्ध मॉडलों की सूची

```python
from free_llm_api_keys import Catalog, ModelCategory

catalog = Catalog.load()
print(catalog.list_models())                            # all
print(catalog.list_models(ModelCategory.IMAGE))         # images only
print(len(catalog), "total keys")
```

## कॉन्फ़िगरेशन

| वेरिएबल / पैरामीटर | डिफ़ॉल्ट | भूमिका |
|---|---|---|
| `FREE_LLM_CACHE_DIR` (env) | `~/.cache/free-llm-api-keys` | कैश निर्देशिका |
| Cache TTL | `3600` s (1 h) | `Catalog.load(ttl_seconds=...)` |
| Base URL | `https://aiapiv2.pekpik.com/v1` | `FreeLLMClient(base_url=...)` |

GitHub से अपडेट के लिए बाध्य करें:

```python
catalog = Catalog.load(force_refresh=True)
```

## नेटवर्क और कैश व्यवहार

1. **पहला लॉन्च**: GitHub से `README.md` डाउनलोड करता है, इसे पार्स करता है, और स्थानीय कैश लिखता है।
2. **बाद के लॉन्च** (< 1 घंटे): कैश का उपयोग करता है, **कोई नेटवर्क रिक्वेस्ट नहीं**।
3. **पुराना कैश** (> 1 घंटे): पुनः डाउनलोड करता है और कैश अपडेट करता है।
4. **नेटवर्क अनुपलब्ध**: मौजूदा कैश का उपयोग करता है (भले ही पुराना हो); `FetchError` तभी देता है जब कोई कैश मौजूद न हो।

## अपवाद

| अपवाद | कब? |
|---|---|
| `NoKeysAvailableError` | कैटलॉग में अनुरोधित मॉडल मौजूद नहीं है। |
| `AllKeysExhaustedError` | मॉडल के लिए सभी कुंजियाँ विफल हो गई हैं। |
| `FetchError` | README डाउनलोड करना असंभव है और कोई कैश उपलब्ध नहीं है। |
| `ParseError` | README की संरचना बदल गई है और अब पार्स करने योग्य नहीं है। |

## प्रोजेक्ट संरचना

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

## लाइसेंस

कुंजियों की स्थिति के लिए स्रोत रिपॉजिटरी देखें। यह मॉड्यूल इन सार्वजनिक कुंजियों के आसपास एक अनौपचारिक क्लाइंट है।
