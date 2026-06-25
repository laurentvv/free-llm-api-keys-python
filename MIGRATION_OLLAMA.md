# Migrer depuis Ollama vers FreeLLMClient

Le passage d'un modèle local comme **Ollama** à **`free-llm-api-keys-python`** est une excellente idée si vous souhaitez utiliser des modèles distants (potentiellement plus performants ou rapides) sans avoir à gérer l'infrastructure locale ni payer d'abonnement, le tout avec une gestion automatisée des clés publiques.

Voici un guide détaillé étape par étape pour intégrer ce module à votre projet existant.

## 1. Installation du module

Ce projet utilise **[uv](https://docs.astral.sh/uv/)** comme gestionnaire de dépendances.

```bash
# Si le dossier du module est en local, à côté de votre projet
uv add "./free-llm-api-keys-python"

# Ou directement via le dépôt Git
uv add "git+https://github.com/alistaitsacle/free-llm-api-keys-python.git"
```

## 2. Configuration et remplacement dans le code

Avec Ollama, vous faisiez probablement des requêtes vers `http://localhost:11434` en utilisant la librairie officielle OpenAI (car Ollama offre une compatibilité partielle avec l'API OpenAI). 

Voici comment transformer votre code.

### Avant (Ollama via API compatible OpenAI)

```python
from openai import OpenAI

# Client pointant vers l'instance locale d'Ollama
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"  # Clé factice requise par l'API
)

# Vous deviez préciser le nom du modèle téléchargé (ex: llama3)
reponse = client.chat.completions.create(
    model="llama3",
    messages=[{"role": "user", "content": "Quelle est la capitale de la France ?"}],
    temperature=0.7
)

print(reponse.choices[0].message.content)
```

### Après (Avec FreeLLMClient)

Le client s'occupe de tout (URL de base, rotation des clés et gestion du modèle). Plus besoin de spécifier un modèle en dur, il suffit d'indiquer le *type* d'usage.

```python
from free_llm_api_keys import FreeLLMClient

# 1. On instancie le client en précisant le type souhaité
client = FreeLLMClient(type="texte")

# 2. Le client a sa propre méthode `.chat()` qui simplifie l'appel
texte_genere = client.chat(
    messages=[{"role": "user", "content": "Quelle est la capitale de la France ?"}],
    temperature=0.7
)

# 3. La sortie attendue est directement le contenu du message !
print(texte_genere)
```

> **Note technique** : Le `FreeLLMClient` enveloppe la librairie officielle `openai`. Les arguments optionnels de la méthode `.chat()` (`temperature`, `max_tokens`, etc.) sont donc passés directement à l'API OpenAI sous-jacente.

## 3. Sortie attendue et comportement en arrière-plan

La sortie de `client.chat(...)` sera directement une chaîne de caractères (le contenu texte de la réponse), par exemple :

```text
La capitale de la France est Paris.
```

Mais la vraie magie opère en arrière-plan (ce que vous verrez dans les logs du terminal si le niveau de log est sur `INFO` ou `WARNING`) :

1. **Au premier lancement** : Le script va se connecter silencieusement à GitHub, télécharger un fichier Markdown contenant des dizaines de clés publiques, le parser, et mettre en cache localement un catalogue avec l'état de santé de chaque clé.
2. **Choix du modèle** : Comme vous avez demandé `type="texte"`, le script va prendre les modèles de texte sains du catalogue et essayer d'appeler l'API.
3. **Auto-rotation transparente** : Si la clé publique testée vient d'expirer ou que son budget gratuit a été englouti par d'autres utilisateurs dans le monde, l'API renverra une erreur 4xx (refusé ou épuisé). **Le script va intercepter cette erreur, isoler la clé défaillante, et retenter immédiatement avec la clé ou le modèle suivant.** Tout cela sans faire planter votre application Python ! 
4. **Relances** : S'il y a une erreur réseau (ex: le serveur de l'API est surchargé), le script réessaiera automatiquement (jusqu'à 3 fois par défaut) avec un délai exponentiel avant de lâcher l'affaire.

Grâce à cela, votre application qui utilisait autrefois Ollama bénéficiera de modèles souvent plus lourds et capables, sans surcharger votre CPU ou votre mémoire vive (RAM), tout en restant très résiliente aux pannes de clés.
