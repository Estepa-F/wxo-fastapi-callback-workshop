# 📡 Documentation API

Référence API complète pour le service de Traitement d'Images Asynchrone WXO.

> **📚 Documentation Associée :**
> Démarrage : [README.md](README.md) · Configuration : [CONFIGURATION.md](CONFIGURATION.md) · Conception : [ARCHITECTURE.md](ARCHITECTURE.md) · Intégration WXO : [orchestrate-tools/README.md](orchestrate-tools/README.md)

---

## URLs de Base

**Production (IBM Code Engine) :**
```bash
BASE_URL="https://wxo-fastapi-callback.264onkwcgnav.eu-de.codeengine.appdomain.cloud"

# Optionnel (si WORKSHOP_TOKEN configuré)
export WORKSHOP_TOKEN="votre-token-ici"

# Quick start - vérifier que le service répond
curl "${BASE_URL}/health"
```

> Le service est exposé publiquement en HTTPS afin d'être accessible depuis watsonx Orchestrate (SaaS).

---

## Configuration

Toute la configuration est gérée via des variables d'environnement. Voir [CONFIGURATION.md](CONFIGURATION.md) pour le guide de configuration complet.

**Validation rapide :**
```bash
# Sans token
curl "${BASE_URL}/cos/config"

# Avec WORKSHOP_TOKEN (si configuré)
curl "${BASE_URL}/cos/config" -H "x-workshop-token: ${WORKSHOP_TOKEN}"
```

---

## Authentification

Par défaut, aucune authentification n'est requise.

> **⚠️ AVERTISSEMENT SÉCURITÉ - Endpoint Public :**
> - Sans authentification, **n'importe qui peut appeler l'API** et déclencher des coûts OpenAI/COS
> - `WORKSHOP_TOKEN` est un garde-fou minimal, **pas une vraie sécurité**
> - **En production :** Implémentez auth + rate limiting + allowlist IP (si possible)
> - Surveillez les coûts et l'utilisation pour détecter les abus

**Workshop guard (optionnel)**
Si la variable `WORKSHOP_TOKEN` est définie, les endpoints suivants exigent le header :

```http
x-workshop-token: <WORKSHOP_TOKEN>
```

**Endpoints protégés par WORKSHOP_TOKEN :**
- `POST /process-image-async-b64`
- `POST /process-image-async`
- `POST /batch-process-images`
- `GET /cos/config`

**Endpoints non protégés :**
- `GET /health`

En production, implémentez un mécanisme d'authentification approprié (API keys, OAuth 2.0, JWT, etc.).

---

## En-têtes Communs

`callbackUrl` est requis uniquement pour :
- `POST /process-image-async-b64`
- `POST /process-image-async`
- `POST /batch-process-images`

**Exemple complet des en-têtes requis :**
```http
Content-Type: application/json
callbackUrl: https://votre-callback-endpoint.com/callback
```

> **Important :**
> - `callbackUrl` est sensible à la casse (pas `callbackurl` ou `CallbackUrl`)
> - L'URL de callback doit être accessible depuis l'instance Code Engine (généralement HTTPS public en environnement SaaS)

Les endpoints `/health` et `/cos/config` ne nécessitent pas ces headers.

---

## Endpoints

### 1. Vérification de Santé

Vérifier si le service fonctionne.

**Endpoint :** `GET /health`

**Réponse :**
```json
{
  "ok": true,
  "mode": "workshop",
  "callback_rewrite_enabled": false,
  "max_concurrent_jobs": 10,
  "callback_retries": 3,
  "fallback_single_enabled": true,
  "workshop_token_enabled": false
}
```

**Codes de Statut :**
- `200 OK` - Le service est opérationnel

---

### 2. Configuration COS

Obtenir la configuration actuelle de Cloud Object Storage.

**Endpoint :** `GET /cos/config`

**Réponse :**
```json
{
  "endpoint": "https://s3.eu-de.cloud-object-storage.appdomain.cloud",
  "region": "eu-de",
  "input_bucket": "input-images",
  "output_bucket": "wxo-images",
  "input_prefix": "",
  "output_prefix": "results/batch",
  "presign_expires": 900
}
```

**Codes de Statut :**
- `200 OK` - Configuration récupérée avec succès

---

### 3. Traiter une Image (Async - Sortie Base64)

Traiter une seule image et retourner le résultat sous forme de données encodées en base64.

**Endpoint :** `POST /process-image-async-b64`

**En-têtes :**
```http
Content-Type: application/json
callbackUrl: https://votre-callback-endpoint.com/callback
```

**Header optionnel (si `WORKSHOP_TOKEN` configuré) :**
```http
x-workshop-token: <WORKSHOP_TOKEN>
```

**Corps de la Requête :**
```json
{
  "prompt": "ajoute un chien à l'image",
  "filename": "burger.jpeg",
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAA..."
}
```

**Schéma de Requête :**
| Champ | Type | Requis | Description |
|-------|------|--------|-------------|
| `prompt` | string | Oui | Instruction en langage naturel pour la modification d'image |
| `filename` | string | Non | Nom de fichier original (pour corrélation/suivi) |
| `image_base64` | string | Oui | Image encodée en Base64 (sans préfixe `data:`) |

**Réponse Immédiate :**
```json
{
  "accepted": true,
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Codes de Statut :**
- `202 Accepted` - Job accepté et traitement démarré
- `500 Internal Server Error` - Erreur de configuration (clés API manquantes, etc.)

**Payload de Callback (Succès) :**
```json
{
  "status": "completed",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "burger.jpeg",
  "result_image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
  "result_mime_type": "image/png"
}
```

> **Note :** Le champ `status` peut valoir : `completed` | `failed`

**Payload de Callback (Échec) :**
```json
{
  "status": "failed",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "burger.jpeg",
  "error": "ValueError: image_base64 invalide (base64 attendu, sans préfixe data:...)"
}
```

---

### 4. Traiter une Image (Async - Sortie URL COS)

Traiter une seule image et stocker le résultat dans IBM Cloud Object Storage.

**Endpoint :** `POST /process-image-async`

**En-têtes :**
```http
Content-Type: application/json
callbackUrl: https://votre-callback-endpoint.com/callback
```

**Header optionnel (si `WORKSHOP_TOKEN` configuré) :**
```http
x-workshop-token: <WORKSHOP_TOKEN>
```

**Corps de la Requête :**
```json
{
  "prompt": "rendre l'arrière-plan transparent",
  "filename": "product.png",
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAA..."
}
```

**Schéma de Requête :**
| Champ | Type | Requis | Description |
|-------|------|--------|-------------|
| `prompt` | string | Oui | Instruction en langage naturel pour la modification d'image |
| `filename` | string | Non | Nom de fichier original (pour corrélation/suivi) |
| `image_base64` | string | Oui | Image encodée en Base64 (sans préfixe `data:`) |

**Réponse Immédiate :**
```json
{
  "accepted": true,
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Codes de Statut :**
- `202 Accepted` - Job accepté et traitement démarré
- `500 Internal Server Error` - Erreur de configuration

**Payload de Callback (Succès) :**
```json
{
  "status": "completed",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "product.png",
  "object_key": "results/550e8400-e29b-41d4-a716-446655440000/product_modified.png",
  "result_url": "https://s3.eu-de.cloud-object-storage.appdomain.cloud/wxo-images/results/...",
  "expires_in": 900
}
```

> **Note :** Le champ `status` peut valoir : `completed` | `failed`

**Payload de Callback (Échec) :**
```json
{
  "status": "failed",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "product.png",
  "error": "RuntimeError: COS put_object failed: ClientError: ..."
}
```

---

### 5. Traiter des Images par Lot (COS → COS)

Traiter toutes les images d'un bucket/préfixe COS avec la même instruction.

**Endpoint :** `POST /batch-process-images`

**En-têtes :**
```http
Content-Type: application/json
callbackUrl: https://votre-callback-endpoint.com/callback
```

**Header optionnel (si `WORKSHOP_TOKEN` configuré) :**
```http
x-workshop-token: <WORKSHOP_TOKEN>
```

**Corps de la Requête :**
```json
{
  "prompt": "rendre l'image plus belle"
}
```

**Schéma de Requête :**
| Champ | Type | Requis | Description |
|-------|------|--------|-------------|
| `prompt` | string | Oui | Instruction en langage naturel appliquée à toutes les images |

**Réponse Immédiate :**
```json
{
  "accepted": true,
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Codes de Statut :**
- `202 Accepted` - Job accepté et traitement démarré
- `500 Internal Server Error` - Erreur de configuration

**Payload de Callback (Succès) :**
```json
{
  "status": "completed",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_files": 5,
  "processed": 5,
  "failed": 0,
  "fallback_local": 0,
  "total_files_processed": 5,
  "duration_seconds": 12.345,
  "output_bucket": "wxo-images",
  "output_prefix": "results/batch/550e8400-e29b-41d4-a716-446655440000/",
  "errors": []
}
```

**Payload de Callback (Succès avec Fallback, sans échec) :**
```json
{
  "status": "completed",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_files": 5,
  "processed": 5,
  "failed": 0,
  "fallback_local": 2,
  "total_files_processed": 5,
  "duration_seconds": 15.678,
  "output_bucket": "wxo-images",
  "output_prefix": "results/batch/550e8400-e29b-41d4-a716-446655440000/",
  "errors": [
    "demo/image1.png: OpenAI billing limit -> fallback local applied",
    "demo/image2.jpg: OpenAI billing limit -> fallback local applied"
  ]
}
```

> **Note :** Le statut reste `completed` tant que `failed = 0`, même si `fallback_local > 0`.

**Payload de Callback (Échec) :**
```json
{
  "status": "failed",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_files": 0,
  "processed": 0,
  "failed": 0,
  "fallback_local": 0,
  "duration_seconds": 0.123,
  "output_bucket": "wxo-images",
  "output_prefix": "results/batch/550e8400-e29b-41d4-a716-446655440000/",
  "errors": [],
  "error": "RuntimeError: Missing env var: COS_INPUT_BUCKET"
}
```

**Schéma de Réponse Callback :**
| Champ | Type | Description |
|-------|------|-------------|
| `status` | string | Statut du job : `completed`, `completed_with_errors`, ou `failed` |
| `job_id` | string | Identifiant unique du job (UUID) |
| `total_files` | integer | Nombre total d'images trouvées dans le bucket d'entrée |
| `processed` | integer | Nombre d'images ayant produit une sortie dans le bucket de destination (OpenAI + fallback local) |
| `failed` | integer | Images n'ayant produit aucune sortie (inclut les échecs de traitement et les échecs d'upload COS) |
| `fallback_local` | integer | Nombre d'images traitées via fallback local (incluses dans `processed`) |
| `total_files_processed` | integer | Égal à `processed` (champ conservé pour compatibilité avec le schéma OpenAPI/WXO) |
| `duration_seconds` | float | Temps de traitement total en secondes |
| `output_bucket` | string | Bucket COS contenant les résultats |
| `output_prefix` | string | Chemin du dossier contenant les images traitées |
| `errors` | array | Liste des messages d'erreur (max 20) |
| `error` | string | Message d'erreur fatale (présent uniquement si status est `failed`) |

---

## Métriques Batch – Comportement Réel

### Compteurs d'Images

**`total_files`**
Nombre total d'images trouvées dans le bucket d'entrée.

**`processed`**
Nombre d'images ayant produit une sortie valide dans le bucket de destination (OpenAI + fallback local).

**`fallback_local`**
Nombre d'images traitées via le fallback local suite à l'erreur `billing_hard_limit_reached`.
**Ces images sont incluses dans `processed`.**

**`failed`**
Nombre d'images n'ayant produit aucune sortie (échec OpenAI + fallback + upload).

**`total_files_processed`**
Égal à `processed` (champ conservé pour compatibilité avec le schéma OpenAPI importé dans WXO).

> **📊 Clarification des métriques :** Dans cette implémentation, `processed` compte les images ayant produit une sortie dans COS (OpenAI ou fallback). Le champ `fallback_local` précise combien en fallback. Le champ `total_files_processed` est conservé pour compatibilité et vaut `processed`.

### Valeurs de Statut

**`completed`**
Aucune image en échec (`failed = 0`).

**`completed_with_errors`**
Au moins une image en échec (`failed > 0`).
**Important :** L'utilisation du fallback local n'entraîne pas à elle seule le statut `completed_with_errors`.

**`failed`**
Erreur système ou configuration empêchant le traitement du lot (identifiants manquants, noms de bucket invalides, erreur critique).

> **Note :** Pour les jobs par lot, le champ `status` peut valoir : `completed` | `completed_with_errors` | `failed`

### Durée et Performance

**`duration_seconds`**
Temps total pris pour traiter l'ensemble du lot, mesuré en secondes. Cela inclut :
- Listage des fichiers dans le bucket d'entrée
- Traitement de chaque image (appels API OpenAI ou fallback)
- Téléchargement des résultats vers le bucket de sortie
- Génération du payload de callback

Utilisez cette métrique pour estimer le temps de traitement pour les futurs lots et optimiser les tailles de lot.

---

## Intégration watsonx Orchestrate (WXO)

Pour l'intégration complète dans watsonx Orchestrate (import des outils YAML, workflows JSON, configuration, bonnes pratiques), consultez :

**📚 [orchestrate-tools/README.md](orchestrate-tools/README.md)**

### Exigence Critique : Schéma de Callback

**Le payload de callback doit contenir exactement les champs déclarés dans la spec OpenAPI de l'outil.**

WXO rejette les callbacks qui :
- Contiennent des champs supplémentaires non déclarés dans le YAML
- Ont des types de données incorrects
- Manquent des champs requis

**Important :**
- L'ordre des champs dans le JSON n'a pas d'importance, mais l'ensemble des champs et les types doivent correspondre
- Si vous ajoutez des champs de debug (ex: `trace_id`, `debug`), vous devez également les ajouter au schéma OpenAPI dans les fichiers `orchestrate-tools/*.yaml`
- Le serveur envoie les callbacks en JSON (généralement `Content-Type: application/json`)

---

## Gestion des Erreurs

### Codes de Statut HTTP

**Codes de succès :**
- `200 OK` - Endpoints de santé et configuration
- `202 Accepted` - Job asynchrone accepté et démarré

**Codes d'erreur :**
- `401 Unauthorized` - Token manquant ou invalide (si `WORKSHOP_TOKEN` configuré)
- `500 Internal Server Error` - Erreur de configuration serveur (variables d'environnement manquantes, etc.)

> **Note :** FastAPI peut également retourner `422 Unprocessable Entity` pour les erreurs de validation de payload (champs manquants, types incorrects).

### Réponses d'Erreur Courantes

**Configuration Manquante :**
```json
{
  "detail": "Variable d'environnement manquante : OPENAI_API_KEY"
}
```

**Base64 Invalide :**
```json
{
  "status": "failed",
  "job_id": "...",
  "error": "ValueError: image_base64 invalide (base64 attendu, sans préfixe data:...)"
}
```

**Limite de Facturation OpenAI :**
Quand la limite de facturation OpenAI est atteinte, le système bascule automatiquement vers le traitement local. Le callback inclura :
```json
{
  "fallback_local": 1,
  "errors": ["demo/image.png: OpenAI billing limit -> fallback local applied"]
}
```

> **Note :** Le fallback local peut aussi s'appliquer sur les endpoints single image si `fallback_single_enabled=true` (voir `/health`), uniquement sur `billing_hard_limit_reached`.

---

## Limitation de Débit

Actuellement, aucune limitation de débit n'est implémentée. Pour la production :
- Implémenter une limitation de débit par client/clé API
- Considérer un traitement basé sur file d'attente pour les opérations par lot
- Surveiller l'utilisation et les coûts de l'API OpenAI

---

## Exemples cURL

### Image Unique (Base64)

**Encodage Base64 :**
```bash
# macOS
export B64=$(base64 -i image.jpg | tr -d '\n')

# Linux (GNU coreutils)
export B64=$(base64 -w 0 image.jpg)

# Alternative universelle (si -w ou -i non disponible)
export B64=$(base64 image.jpg | tr -d '\n')
```

**Sans token :**
```bash
curl -X POST "${BASE_URL}/process-image-async-b64" \
  -H "Content-Type: application/json" \
  -H "callbackUrl: https://votre-callback-endpoint.com/callback" \
  -d "{
    \"prompt\": \"ajoute un coucher de soleil en arrière-plan\",
    \"filename\": \"image.jpg\",
    \"image_base64\": \"$B64\"
  }"
```

**Avec WORKSHOP_TOKEN (si activé) :**
```bash
curl -X POST "${BASE_URL}/process-image-async-b64" \
  -H "Content-Type: application/json" \
  -H "callbackUrl: https://votre-callback-endpoint.com/callback" \
  -H "x-workshop-token: $WORKSHOP_TOKEN" \
  -d "{
    \"prompt\": \"ajoute un coucher de soleil en arrière-plan\",
    \"filename\": \"image.jpg\",
    \"image_base64\": \"$B64\"
  }"
```

### Traitement par Lot

**Sans token :**
```bash
curl -X POST "${BASE_URL}/batch-process-images" \
  -H "Content-Type: application/json" \
  -H "callbackUrl: https://votre-callback-endpoint.com/callback" \
  -d '{"prompt": "améliore les couleurs et la luminosité"}'
```

**Avec WORKSHOP_TOKEN (si activé) :**
```bash
curl -X POST "${BASE_URL}/batch-process-images" \
  -H "Content-Type: application/json" \
  -H "callbackUrl: https://votre-callback-endpoint.com/callback" \
  -H "x-workshop-token: $WORKSHOP_TOKEN" \
  -d '{"prompt": "améliore les couleurs et la luminosité"}'
```


---

## Bonnes Pratiques

### URLs de Callback
- Utiliser HTTPS en production
- Implémenter l'idempotence (le même job_id peut être réessayé)
- Retourner `200 OK` rapidement (< 5 secondes)
- Traiter les données de callback de manière asynchrone si nécessaire

### Encodage d'Image
```bash
# Correct : base64 sans préfixe data:
base64 -i image.jpg | tr -d '\n'

# Incorrect : inclut le préfixe data:
# data:image/jpeg;base64,iVBORw0...
```

### Traitement par Lot
- Commencer avec de petits lots pour tester
- Surveiller `duration_seconds` pour optimiser la taille du lot
- Vérifier le tableau `errors` pour les échecs partiels
- Suivre le compte `fallback_local` pour la disponibilité d'OpenAI

### URLs Pré-signées
- Les URLs expirent après le temps configuré (par défaut : 900 secondes)
- Télécharger les résultats avant l'expiration
- Stocker `object_key` pour régénérer les URLs si nécessaire

---

## Documentation Interactive

**Swagger UI :**
```
${BASE_URL}/docs
```

**ReDoc :**
```
${BASE_URL}/redoc
```

---

## Documentation Associée

- [README.md](README.md) - Démarrage rapide et configuration
- [CONFIGURATION.md](CONFIGURATION.md) - Variables d'environnement
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture technique
- [orchestrate-tools/README.md](orchestrate-tools/README.md) - Intégration watsonX Orchestrate
