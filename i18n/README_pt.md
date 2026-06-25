# free-llm-api-keys-python

<p align="center">
  <img src="../assets/banner.jpg" alt="Free LLM API Keys Banner" width="100%"/>
</p>

<!-- README-I18N:START -->

[English](https://github.com/laurentvv/free-llm-api-keys-python) | [中文](README_zh.md) | [हिंदी](README_hi.md) | [Español](README_es.md) | [Français](README_fr.md) | [العربية](README_ar.md) | [বাংলা](README_bn.md) | [Русский](README_ru.md) | **Português** | [Bahasa Indonesia](README_id.md)

<!-- README-I18N:END -->

Módulo Python que fornece acesso a **chaves de IA gratuitas** do repositório
[`alistaitsacle/free-llm-api-keys`](https://github.com/alistaitsacle/free-llm-api-keys)
no formato **OpenAI**. Ele baixa, analisa e armazena em cache o `README.md` original,
em seguida, expõe clientes prontos para uso por tipo de modelo
(**Text**, **Image**, **TTS**, **Embeddings**) que **rotacionam automaticamente**
entre as chaves disponíveis.

> ⚠️ **Chaves públicas e compartilhadas**: elas podem ser esgotadas (orçamento)
> ou expirar (24–48 h). É por isso que o cliente tenta todas as
> chaves para um modelo, uma após a outra, até encontrar uma que funcione.

## Funcionalidades

- 🔄 **Atualização automática**: a cada inicialização, atualiza a lista do
  GitHub se o cache estiver obsoleto (TTL de 1 h), caso contrário, usa o cache.
- 💾 **Cache local + modo offline**: fallback automático para o cache
  (mesmo se obsoleto) se a rede estiver indisponível.
- 🔁 **Rotação automática de chaves**: muda para a próxima chave quando uma chave
  é rejeitada (orçamento / expirada / limite de taxa), com novas tentativas em erros de
  rede transitórios.
- 🧩 **4 tipos de modelos**: `chat`, `generate_image`, `tts`, `embeddings`.

## Instalação

Projeto [uv](https://docs.astral.sh/uv/). Em seu projeto consumidor:

```bash
# a partir do caminho local
uv add "C:/path/to/free-llm-api-keys-python"

# ou via git
uv add "git+https://github.com/<your-user>/free-llm-api-keys-python.git"
```

Desenvolvimento local:

```bash
git clone <this-repo>
cd free-llm-api-keys-python
uv sync
uv run pytest
```

## Início Rápido

```python
from free_llm_api_keys import FreeLLMClient

# Ao instanciar, o catálogo é atualizado do GitHub, se necessário
# (caso contrário, ele usa o cache local).
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

### 🖼️ Geração de imagem

```python
client = FreeLLMClient(type="image")
urls = client.generate_image("A cyberpunk fox in a neon forest", n=1, size="1024x1024")
print(urls[0])  # URL da imagem gerada
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
print(len(vectors), len(vectors[0]))  # 2 vetores de dimensão N
```

## Lista de modelos disponíveis

```python
from free_llm_api_keys import Catalog, ModelCategory

catalog = Catalog.load()
print(catalog.list_models())                            # todos
print(catalog.list_models(ModelCategory.IMAGE))         # apenas imagens
print(len(catalog), "total keys")
```

## Configuração

| Variável / parâmetro | Padrão | Função |
|---|---|---|
| `FREE_LLM_CACHE_DIR` (env) | `~/.cache/free-llm-api-keys` | Diretório de cache |
| Cache TTL | `3600` s (1 h) | `Catalog.load(ttl_seconds=...)` |
| URL base | `https://aiapiv2.pekpik.com/v1` | `FreeLLMClient(base_url=...)` |

Forçar uma atualização do GitHub:

```python
catalog = Catalog.load(force_refresh=True)
```

## Comportamento de rede e cache

1. **Primeira inicialização**: baixa o `README.md` do GitHub, analisa-o
   e grava o cache local.
2. **Inicializações subsequentes** (< 1 h): usa o cache, **sem solicitações de rede**.
3. **Cache obsoleto** (> 1 h): baixa novamente e atualiza o cache.
4. **Rede indisponível**: usa o cache existente (mesmo se obsoleto);
   gera `FetchError` apenas se não existir cache.

## Exceções

| Exceção | Quando? |
|---|---|
| `NoKeysAvailableError` | O modelo solicitado não existe no catálogo. |
| `AllKeysExhaustedError` | Todas as chaves para o modelo falharam. |
| `FetchError` | Impossível baixar o README e nenhum cache disponível. |
| `ParseError` | A estrutura do README mudou e não é mais analisável. |

## Estrutura do projeto

```
src/free_llm_api_keys/
├── __init__.py     # API Pública
├── fetcher.py      # Download do README (httpx + ETag)
├── parser.py       # Análise de markdown -> KeyEntry
├── classifier.py   # Tipo de modelo (text/image/tts/embeddings)
├── cache.py        # Cache local JSON + TTL + fallback offline
├── catalog.py      # Orquestração de fetch + parse + cache
├── client.py       # FreeLLMClient : OpenAI + auto-rotation + retry
└── exceptions.py
```

## Licença

Veja o repositório de origem para o status das chaves. Este módulo é um cliente não oficial
para essas chaves públicas.
