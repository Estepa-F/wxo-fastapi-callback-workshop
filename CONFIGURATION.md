# ⚙️ Guide de Configuration

Référence de configuration complète pour le service de Traitement d'Images Asynchrone WXO.

> **📚 Documentation Associée :**
> [README.md](README.md) · [API.md](API.md) · [ARCHITECTURE.md](ARCHITECTURE.md) · [orchestrate-tools/README.md](orchestrate-tools/README.md)

---

## Variables d'Environnement

Toute la configuration est gérée via des variables d'environnement suivant la méthodologie [12-factor app](https://12factor.net/).

### Configuration Rapide

1. Copier le fichier exemple :
```bash
cp .env.example .env
```

2. Éditer `.env` avec vos identifiants

3. Charger les variables :
```bash
set -a
source .env
set +a
```

---

## IBM Cloud Object Storage

### Variables Requises

| Variable | Description | Exemple |
|----------|-------------|---------|
| `COS_ENDPOINT` | URL de l'endpoint COS (spécifique à la région) | `https://s3.eu-de.cloud-object-storage.appdomain.cloud` |
| `COS_REGION` | Code de région COS (défaut: `eu-geo` si absent) | `eu-de`, `us-south`, `us-east` |
| `COS_ACCESS_KEY_ID` | ID de clé d'accès HMAC | Obtenir depuis Console IBM Cloud → Object Storage → Service Credentials |
| `COS_SECRET_ACCESS_KEY` | Clé d'accès secrète HMAC | Obtenir depuis Console IBM Cloud → Object Storage → Service Credentials |

### Variables Optionnelles

| Variable | Défaut | Description |
|----------|---------|-------------|
| `COS_BUCKET` | - | Bucket par défaut (legacy). Utilisé comme fallback si `COS_OUTPUT_BUCKET` n'est pas défini. |
| `COS_PRESIGN_EXPIRES` | `900` | Temps d'expiration de l'URL pré-signée en secondes (15 minutes) |

### Endpoints Régionaux

| Région | Endpoint |
|--------|----------|
| EU Allemagne | `https://s3.eu-de.cloud-object-storage.appdomain.cloud` |
| US Sud | `https://s3.us-south.cloud-object-storage.appdomain.cloud` |
| US Est | `https://s3.us-east.cloud-object-storage.appdomain.cloud` |
| UK | `https://s3.eu-gb.cloud-object-storage.appdomain.cloud` |

[Liste complète des endpoints](https://cloud.ibm.com/docs/cloud-object-storage?topic=cloud-object-storage-endpoints)

---

## Configuration du Traitement par Lot

### Variables Requises

| Variable | Description | Exemple |
|----------|-------------|---------|
| `COS_INPUT_BUCKET` | Bucket contenant les images source | `input-images` |
| `COS_OUTPUT_BUCKET` | Bucket où les images traitées seront stockées.<br>**Fortement recommandé pour le traitement par lot** afin d'éviter toute ambiguïté avec le bucket legacy. | `wxo-images` |

### Variables Optionnelles

| Variable | Défaut | Description |
|----------|---------|-------------|
| `COS_INPUT_PREFIX` | `""` | Chemin du dossier dans le bucket d'entrée (ex : `demo/` ou `images/raw/`) |
| `COS_OUTPUT_PREFIX` | `results/batch` | Chemin du dossier de base dans le bucket de sortie<br>Résultats stockés comme : `{OUTPUT_PREFIX}/{job_id}/` |

### Exemple de Structure

```
Bucket d'Entrée (input-images):
├── image1.jpg
├── image2.png
└── subfolder/
    └── image3.jpg

Bucket de Sortie (wxo-images):
└── results/batch/
    └── 550e8400-e29b-41d4-a716-446655440000/
        ├── image1_modified.png
        ├── image2_modified.png
        └── image3_modified.png
```

---

## Configuration OpenAI

### Variables Requises

| Variable | Description | Comment l'Obtenir |
|----------|-------------|-------------------|
| `OPENAI_API_KEY` | Clé API OpenAI | https://platform.openai.com/api-keys |

### Variables Optionnelles

| Variable | Défaut | Options | Description |
|----------|---------|---------|-------------|
| `OPENAI_IMAGE_MODEL` | `gpt-image-1` | Consulter [docs OpenAI](https://platform.openai.com/docs/models) | Modèle d'image à utiliser |
| `OPENAI_IMAGE_QUALITY` | `medium` | `low`, `medium`, `high`, `auto` | Paramètre de qualité d'image |
| `OPENAI_IMAGE_OUTPUT_FORMAT` | `png` | `png`, `jpeg`, `webp` | Format d'image de sortie |

---

## Exemple .env Complet

```bash
# ==================================================
# Configuration IBM Cloud Object Storage
# ==================================================

# Endpoint COS (spécifique à la région)
COS_ENDPOINT=https://s3.eu-de.cloud-object-storage.appdomain.cloud

# Région COS
COS_REGION=eu-de

# Bucket par défaut (legacy, utilisé comme fallback)
COS_BUCKET=wxo-images

# Identifiants COS (HMAC)
COS_ACCESS_KEY_ID=votre_access_key_id_ici
COS_SECRET_ACCESS_KEY=votre_secret_access_key_ici

# Temps d'expiration de l'URL pré-signée (en secondes)
COS_PRESIGN_EXPIRES=900

# ==================================================
# Configuration du Traitement par Lot
# ==================================================

# Bucket d'entrée (où les images source sont stockées)
COS_INPUT_BUCKET=input-images

# Bucket de sortie (où les images traitées seront stockées)
COS_OUTPUT_BUCKET=wxo-images

# Préfixe d'entrée (chemin du dossier dans le bucket d'entrée, optionnel)
COS_INPUT_PREFIX=

# Préfixe de sortie (chemin du dossier dans le bucket de sortie)
COS_OUTPUT_PREFIX=results/batch

# ==================================================
# Configuration OpenAI
# ==================================================

# Clé API OpenAI
OPENAI_API_KEY=votre_cle_api_openai_ici

# Modèle d'image à utiliser
OPENAI_IMAGE_MODEL=gpt-image-1

# Qualité d'image
OPENAI_IMAGE_QUALITY=medium

# Format de sortie
OPENAI_IMAGE_OUTPUT_FORMAT=png
```

---

## Obtenir les Identifiants IBM Cloud

### Étape 1 : Créer des Identifiants de Service

1. Aller sur [Console IBM Cloud](https://cloud.ibm.com/)
2. Naviguer vers **Object Storage** → Votre instance
3. Cliquer sur **Service Credentials** dans le menu de gauche
4. Cliquer sur **New Credential**
5. Activer le toggle **Include HMAC Credential**
6. Cliquer sur **Add**

### Étape 2 : Extraire les Valeurs

Depuis le JSON des identifiants générés :

```json
{
  "apikey": "...",
  "cos_hmac_keys": {
    "access_key_id": "← Utiliser ceci pour COS_ACCESS_KEY_ID",
    "secret_access_key": "← Utiliser ceci pour COS_SECRET_ACCESS_KEY"
  },
  "endpoints": "https://control.cloud-object-storage.cloud.ibm.com/v2/endpoints",
  "iam_apikey_description": "...",
  "iam_apikey_name": "...",
  "iam_role_crn": "...",
  "iam_serviceid_crn": "...",
  "resource_instance_id": "..."
}
```

### Étape 3 : Trouver Votre Endpoint

1. Visiter l'URL des endpoints depuis les identifiants
2. Choisir votre région (ex : `eu-de`)
3. Utiliser l'endpoint **public** pour `COS_ENDPOINT`

---

## Validation

### Tester la Configuration COS

> **⚠️ Note :** Si `WORKSHOP_TOKEN` est configuré, le header `x-workshop-token` est requis.

```bash
# Sans token
curl http://localhost:8000/cos/config

# Avec WORKSHOP_TOKEN (si configuré)
curl http://localhost:8000/cos/config -H "x-workshop-token: ${WORKSHOP_TOKEN}"
```

Réponse attendue :
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

### Tester la Santé

```bash
curl http://localhost:8000/health
```

Réponse attendue :
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

## Workshop / Robustesse (optionnel)

Ces variables permettent d'activer des fonctionnalités avancées pour les workshops, les démos et la robustesse en production.

### Variables de Workshop

| Variable | Défaut | Description |
|----------|---------|-------------|
| `WORKSHOP_TOKEN` | `""` | Token partagé optionnel pour protéger les endpoints.<br>Si défini, les clients doivent envoyer le header `x-workshop-token: <valeur>` |
| `ENABLE_CALLBACK_REWRITE` | `false` | Active la réécriture d'URL de callback (LOCAL UNIQUEMENT).<br>Utile pour tunnels locaux (ngrok, Lima, etc.) |
| `LOCAL_TUNNEL_NETLOC` | `127.0.0.1:14321` | Netloc de remplacement pour la réécriture de callback.<br>Utilisé uniquement si `ENABLE_CALLBACK_REWRITE=true` |

### Variables de Robustesse

| Variable | Défaut | Description |
|----------|---------|-------------|
| `CALLBACK_TIMEOUT_SECONDS` | `30` | Timeout pour les requêtes HTTP de callback (en secondes) |
| `CALLBACK_MAX_RETRIES` | `3` | Nombre total de tentatives pour envoyer le callback.<br>Inclut la tentative initiale (ex: 3 = 1 tentative + 2 retries).<br>Une valeur de `0` est interprétée comme 1 tentative minimale. |
| `CALLBACK_BACKOFF_SECONDS` | `1,3,8` | Délais entre les tentatives de callback (en secondes).<br>Format: liste séparée par des virgules |
| `ENABLE_FALLBACK_SINGLE` | `true` | Active le fallback local pour les endpoints single-image.<br>Déclenché uniquement sur `billing_hard_limit_reached` |
| `MAX_IMAGE_BASE64_CHARS` | `14000000` | Limite de caractères base64 pour les payloads d'image.<br>~10 MB décodé ≈ 13.4 MB base64 |
| `MAX_CONCURRENT_JOBS` | `10` | Limite de concurrence pour les tâches en arrière-plan.<br>Sécurité pour les workshops (in-process BackgroundTasks) |

### Exemple .env Workshop

```bash
# ==================================================
# Configuration Workshop / Robustesse (optionnel)
# ==================================================

# Token de workshop (optionnel)
WORKSHOP_TOKEN=mon-token-secret-123

# Callback rewrite (LOCAL UNIQUEMENT - pour tunnels)
ENABLE_CALLBACK_REWRITE=false
LOCAL_TUNNEL_NETLOC=127.0.0.1:14321

# Robustesse des callbacks
CALLBACK_TIMEOUT_SECONDS=30
CALLBACK_MAX_RETRIES=3
CALLBACK_BACKOFF_SECONDS=1,3,8

# Fallback et limites
ENABLE_FALLBACK_SINGLE=true
MAX_IMAGE_BASE64_CHARS=14000000
MAX_CONCURRENT_JOBS=10
```

> **⚠️ Note de Production :**
> - `ENABLE_CALLBACK_REWRITE` doit rester `false` en production (SaaS)
> - `MAX_CONCURRENT_JOBS` est une limite **in-process** (par instance). En environnement multi-instance (Kubernetes, Code Engine), la limite s'applique **par pod**. Pour la production, utilisez un système de queue externe (voir [ARCHITECTURE.md](ARCHITECTURE.md))
> - Le fallback local est déclenché **uniquement** sur `billing_hard_limit_reached`, pas sur toutes les erreurs OpenAI

> **📋 Modèle de Thread :**
> Les tâches asynchrones sont exécutées via **FastAPI BackgroundTasks** (in-process, même processus que l'API).
> - ✅ **Adapté pour** : démos, workshops, prototypage, charges légères
> - ⚠️ **Limites** : pas de persistance, pas de distribution multi-serveur, perte des jobs en cas de redémarrage
> - 🚀 **Production critique** : utilisez une queue externe (Redis Queue, AWS SQS, Kafka, Celery) pour la résilience et la scalabilité

---

---

## Dépannage

### Variables d'Environnement Manquantes

**Erreur :**
```
RuntimeError: Variables d'environnement COS manquantes : COS_ENDPOINT, COS_ACCESS_KEY_ID
```

**Solution :**
1. Vérifier que le fichier `.env` existe
2. Vérifier les noms de variables (sensibles à la casse)
3. Recharger l'environnement : `set -a && source .env && set +a`

### Identifiants Invalides

**Erreur :**
```
ClientError: An error occurred (InvalidAccessKeyId) when calling the ListObjects operation
```

**Solution :**
1. Vérifier que les identifiants HMAC sont activés dans IBM Cloud
2. Vérifier `COS_ACCESS_KEY_ID` et `COS_SECRET_ACCESS_KEY`
3. S'assurer que les identifiants n'ont pas expiré

### Mauvais Endpoint

**Erreur :**
```
EndpointConnectionError: Could not connect to the endpoint URL
```

**Solution :**
1. Vérifier que `COS_ENDPOINT` correspond à votre région
2. Vérifier la connectivité réseau
3. S'assurer que l'endpoint inclut `https://`

### Bucket Non Trouvé

**Erreur :**
```
NoSuchBucket: The specified bucket does not exist
```

**Solution :**
1. Vérifier les noms de bucket dans `COS_INPUT_BUCKET` et `COS_OUTPUT_BUCKET`
2. Vérifier que le bucket existe dans la Console IBM Cloud
3. S'assurer que les identifiants ont accès au bucket

### Erreur de Décodage Base64

**Erreur :**
```
binascii.Error: Invalid base64-encoded string
```

**Cause :**
Le serveur utilise `base64.b64decode(..., validate=True)` et exige un Base64 strict, sans espaces ni retours ligne.

**Solution :**
1. Retirer les retours ligne et espaces du base64
2. Si copié depuis un data URL, retirer le préfixe `data:image/...;base64,`
3. S'assurer que le base64 ne contient que des caractères valides : `A-Z`, `a-z`, `0-9`, `+`, `/`, `=`

**Exemple de nettoyage :**
```python
# Mauvais (avec préfixe et retours ligne)
data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA
ABAAAAAQCAYAAAAf8/9hAAAA...

# Bon (base64 pur)
iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==
```

---

## Bonnes Pratiques de Sécurité

### Développement

✅ Utiliser un fichier `.env` (ne jamais commiter dans git)  
✅ Ajouter `.env` à `.gitignore`  
✅ Utiliser `.env.example` comme modèle  
✅ Faire tourner les identifiants régulièrement

### Production

✅ Utiliser un service de gestion de secrets (AWS Secrets Manager, IBM Key Protect)  
✅ Implémenter la rotation des identifiants  
✅ Utiliser des rôles IAM au lieu d'identifiants statiques quand possible  
✅ Auditer les logs d'accès régulièrement  
✅ Limiter la portée des identifiants aux permissions minimales requises

---

## Documentation Associée

- [README.md](README.md) - Guide de démarrage rapide
- [API.md](API.md) - Référence API
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture technique
- [Documentation IBM Cloud Object Storage](https://cloud.ibm.com/docs/cloud-object-storage)
- [Référence API OpenAI](https://platform.openai.com/docs/api-reference)