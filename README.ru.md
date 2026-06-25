# free-llm-api-keys-python

<p align="center">
  <img src="assets/banner.jpg" alt="Free LLM API Keys Banner" width="100%"/>
</p>

<!-- README-I18N:START -->

[English](./README.md) | [中文](./README.zh.md) | [हिंदी](./README.hi.md) | [Español](./README.es.md) | [Français](./README.fr.md) | [العربية](./README.ar.md) | [বাংলা](./README.bn.md) | **Русский** | [Português](./README.pt.md) | [Bahasa Indonesia](./README.id.md)

<!-- README-I18N:END -->

Модуль Python, предоставляющий доступ к **бесплатным ключам ИИ** из репозитория
[`alistaitsacle/free-llm-api-keys`](https://github.com/alistaitsacle/free-llm-api-keys)
в формате **OpenAI**. Он загружает, парсит и кэширует исходный `README.md`,
а затем предоставляет готовые к использованию клиенты по типам моделей
(**Text**, **Image**, **TTS**, **Embeddings**), которые **автоматически чередуют**
доступные ключи.

> ⚠️ **Публичные и общие ключи**: они могут быть исчерпаны (бюджет)
> или истечь (24–48 ч). Вот почему клиент перебирает все
> ключи для модели один за другим, пока не найдет рабочий.

## Особенности

- 🔄 **Автообновление**: при каждом запуске обновляет список из
  GitHub, если кэш устарел (TTL 1 ч), в противном случае использует кэш.
- 💾 **Локальный кэш + автономный режим**: автоматический возврат к кэшу
  (даже если он устарел), если сеть недоступна.
- 🔁 **Автоматическая ротация ключей**: переключается на следующий ключ, когда ключ
  отклонен (бюджет / истек / лимит запросов), с повторными попытками при временных
  ошибках сети.
- 🧩 **4 типа моделей**: `chat`, `generate_image`, `tts`, `embeddings`.

## Установка

Проект [uv](https://docs.astral.sh/uv/). В вашем проекте:

```bash
# from the local path
uv add "C:/path/to/free-llm-api-keys-python"

# or via git
uv add "git+https://github.com/<your-user>/free-llm-api-keys-python.git"
```

Локальная разработка:

```bash
git clone <this-repo>
cd free-llm-api-keys-python
uv sync
uv run pytest
```

## Быстрый старт

```python
from free_llm_api_keys import FreeLLMClient

# Upon instantiation, the catalog updates from GitHub if needed
# (otherwise it uses the local cache).
client = FreeLLMClient(type="texte")

response = client.chat([{"role": "user", "content": "Hello!"}])
print(response)
```

## Использование по типу модели

### 💬 Текст (chat)

```python
from free_llm_api_keys import FreeLLMClient

client = FreeLLMClient(type="texte")
text = client.chat(
    [{"role": "user", "content": "Explain photosynthesis in 2 sentences."}],
    temperature=0.7,
)
print(text)
```

### 🖼️ Генерация изображений

```python
client = FreeLLMClient(type="image")
urls = client.generate_image("A cyberpunk fox in a neon forest", n=1, size="1024x1024")
print(urls[0])  # Generated image URL
```

### 🔊 Преобразование текста в речь (TTS)

```python
client = FreeLLMClient(type="tts")
audio: bytes = client.tts("Hello, this is a test.", voice="alloy")
Path("output.mp3").write_bytes(audio)
```

### 🧮 Эмбеддинги (Embeddings)

```python
client = FreeLLMClient(type="embeddings")
vectors = client.embeddings(["text one", "text two"])
print(len(vectors), len(vectors[0]))  # 2 vectors of dimension N
```

## Список доступных моделей

```python
from free_llm_api_keys import Catalog, ModelCategory

catalog = Catalog.load()
print(catalog.list_models())                            # all
print(catalog.list_models(ModelCategory.IMAGE))         # images only
print(len(catalog), "total keys")
```

## Конфигурация

| Переменная / параметр | По умолчанию | Роль |
|---|---|---|
| `FREE_LLM_CACHE_DIR` (env) | `~/.cache/free-llm-api-keys` | Директория кэша |
| Cache TTL | `3600` s (1 h) | `Catalog.load(ttl_seconds=...)` |
| Base URL | `https://aiapiv2.pekpik.com/v1` | `FreeLLMClient(base_url=...)` |

Принудительное обновление с GitHub:

```python
catalog = Catalog.load(force_refresh=True)
```

## Поведение сети и кэша

1. **Первый запуск**: загружает `README.md` с GitHub, парсит его
   и записывает локальный кэш.
2. **Последующие запуски** (< 1 ч): использует кэш, **без сетевых запросов**.
3. **Устаревший кэш** (> 1 ч): повторно загружает и обновляет кэш.
4. **Сеть недоступна**: использует существующий кэш (даже если он устарел);
   вызывает `FetchError` только в случае отсутствия кэша.

## Исключения

| Исключение | Когда? |
|---|---|
| `NoKeysAvailableError` | Запрошенная модель не существует в каталоге. |
| `AllKeysExhaustedError` | Все ключи для модели оказались нерабочими. |
| `FetchError` | Невозможно загрузить README и нет доступного кэша. |
| `ParseError` | Структура README изменилась и больше не поддается парсингу. |

## Структура проекта

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

## Лицензия

Смотрите исходный репозиторий для получения информации о статусе ключей. Этот модуль является неофициальным
клиентом для работы с этими публичными ключами.
