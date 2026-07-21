# free-llm-api-keys-python

<p align="center">
  <img src="../assets/banner.jpg" alt="Free LLM API Keys Banner" width="100%"/>
</p>

<!-- README-I18N:START -->

[English](https://github.com/laurentvv/free-llm-api-keys-python) | [中文](README_zh.md) | [हिंदी](README_hi.md) | [Español](README_es.md) | [Français](README_fr.md) | **العربية** | [বাংলা](README_bn.md) | [Русский](README_ru.md) | [Português](README_pt.md) | [Bahasa Indonesia](README_id.md)

<!-- README-I18N:END -->

وحدة بايثون (Python module) توفر إمكانية الوصول إلى **مفاتيح ذكاء اصطناعي مجانية (free AI keys)** من
مستودع [`alistaitsacle/free-llm-api-keys`](https://github.com/alistaitsacle/free-llm-api-keys)
بصيغة **OpenAI**. تقوم هذه الوحدة بتنزيل `README.md` الأساسي، تحليله، وتخزينه مؤقتًا،
ثم توفر عملاء جاهزين للاستخدام حسب نوع النموذج
(**Text**, **Image**, **TTS**, **Embeddings**) والتي **تقوم بالتبديل التلقائي**
بين المفاتيح المتاحة.

> ⚠️ **مفاتيح عامة ومشتركة**: يمكن استنفادها (الرصيد)
> أو انتهاء صلاحيتها (24–48 ساعة). لهذا السبب يحاول العميل استخدام جميع
> المفاتيح المتاحة للنموذج واحدًا تلو الآخر حتى يجد مفتاحًا يعمل.

## الميزات

- 🔄 **التحديث التلقائي**: عند كل تشغيل، يتم تحديث القائمة من
  GitHub إذا كانت الذاكرة المؤقتة قديمة (مدة الصلاحية 1 ساعة)، وإلا يتم استخدام الذاكرة المؤقتة.
- 💾 **ذاكرة مؤقتة محلية + وضع عدم الاتصال**: الرجوع التلقائي إلى الذاكرة المؤقتة
  (حتى وإن كانت قديمة) إذا كانت الشبكة غير متاحة.
- 🔁 **التبديل التلقائي للمفاتيح**: الانتقال إلى المفتاح التالي عند رفض مفتاح معين
  (بسبب الرصيد / انتهاء الصلاحية / حد الطلبات)، مع إعادة المحاولة عند حدوث أخطاء شبكة مؤقتة.
- 🧩 **4 أنواع من النماذج**: `chat`, `generate_image`, `tts`, `embeddings`.

## التثبيت

هذه الحزمة لم يتم نشرها بعد على PyPI. يمكنك تثبيتها مباشرة من GitHub.

### باستخدام `uv` (موصى به)

```bash
uv add "git+https://github.com/laurentvv/free-llm-api-keys-python.git"
```

### باستخدام `pip`

```bash
pip install "git+https://github.com/laurentvv/free-llm-api-keys-python.git"
```

### التطوير المحلي

```bash
git clone https://github.com/laurentvv/free-llm-api-keys-python.git
cd free-llm-api-keys-python
uv sync
uv run pytest
```

## البدء السريع

```python
from free_llm_api_keys import FreeLLMClient

# عند التهيئة، يتم تحديث الفهرس من GitHub إذا لزم الأمر
# (وإلا يتم استخدام الذاكرة المؤقتة المحلية).
client = FreeLLMClient(type="texte")

response = client.chat([{"role": "user", "content": "Hello!"}])
print(response)
```

## الاستخدام حسب نوع النموذج

### 💬 النصوص (chat)

```python
from free_llm_api_keys import FreeLLMClient

client = FreeLLMClient(type="texte")
text = client.chat(
    [{"role": "user", "content": "Explain photosynthesis in 2 sentences."}],
    temperature=0.7,
)
print(text)
```

### 🖼️ توليد الصور

```python
client = FreeLLMClient(type="image")
urls = client.generate_image("A cyberpunk fox in a neon forest", n=1, size="1024x1024")
print(urls[0])  # Generated image URL
```

### 🔊 تحويل النص إلى كلام (TTS)

```python
client = FreeLLMClient(type="tts")
audio: bytes = client.tts("Hello, this is a test.", voice="alloy")
Path("output.mp3").write_bytes(audio)
```

### 🧮 التضمينات

```python
client = FreeLLMClient(type="embeddings")
vectors = client.embeddings(["text one", "text two"])
print(len(vectors), len(vectors[0]))  # 2 vectors of dimension N
```

## قائمة النماذج المتاحة

```python
from free_llm_api_keys import Catalog, ModelCategory

catalog = Catalog.load()
print(catalog.list_models())                            # all
print(catalog.list_models(ModelCategory.IMAGE))         # images only
print(len(catalog), "total keys")
```

## الإعدادات

| المتغير / المعلمة | الافتراضي | الدور |
|---|---|---|
| `FREE_LLM_CACHE_DIR` (env) | `~/.cache/free-llm-api-keys` | مجلد الذاكرة المؤقتة |
| مدة الصلاحية (Cache TTL) | `3600` s (1 h) | `Catalog.load(ttl_seconds=...)` |
| الرابط الأساسي (Base URL) | `https://aiapiv2.pekpik.com/v1` | `FreeLLMClient(base_url=...)` |

فرض التحديث من GitHub:

```python
catalog = Catalog.load(force_refresh=True)
```

## سلوك الشبكة والذاكرة المؤقتة

1. **التشغيل الأول**: يقوم بتنزيل `README.md` من GitHub، تحليله،
   وكتابة الذاكرة المؤقتة المحلية.
2. **التشغيلات اللاحقة** (< 1 ساعة): يستخدم الذاكرة المؤقتة، **بدون طلبات شبكة**.
3. **ذاكرة مؤقتة قديمة** (> 1 ساعة): يعيد التنزيل ويحدث الذاكرة المؤقتة.
4. **الشبكة غير متاحة**: يستخدم الذاكرة المؤقتة الحالية (حتى وإن كانت قديمة)؛
   يُطلق استثناء `FetchError` فقط في حالة عدم وجود ذاكرة مؤقتة.

## الاستثناءات

| الاستثناء | متى؟ |
|---|---|
| `NoKeysAvailableError` | النموذج المطلوب غير موجود في الفهرس. |
| `AllKeysExhaustedError` | فشلت جميع المفاتيح للنموذج. |
| `FetchError` | من المستحيل تنزيل README ولا تتوفر ذاكرة مؤقتة. |
| `ParseError` | تغيرت بنية README ولم يعد قابلاً للتحليل. |

## بنية المشروع

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

## الترخيص

راجع المستودع المصدر لمعرفة حالة المفاتيح. هذه الوحدة عبارة عن
عميل غير رسمي حول هذه المفاتيح العامة.
