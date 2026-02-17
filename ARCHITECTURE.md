# 🏗️ Documentation d'Architecture

Architecture technique détaillée et décisions de conception pour le service de Traitement d'Images Asynchrone WXO.

> **📚 Documentation Associée :**
> Pour le démarrage : [README.md](README.md) · Pour le contrat API : [API.md](API.md) · Pour la configuration : [CONFIGURATION.md](CONFIGURATION.md)

---

## Table des Matières

1. [Vue d'Ensemble du Système](#vue-densemble-du-système)
2. [Patterns d'Architecture](#patterns-darchitecture)
3. [Conception des Composants](#conception-des-composants)
4. [Flux de Données](#flux-de-données)
5. [Stratégie de Gestion des Erreurs](#stratégie-de-gestion-des-erreurs)
6. [Considérations de Scalabilité](#considérations-de-scalabilité)
7. [Sécurité](#sécurité)
8. [Décisions Techniques](#décisions-techniques)

---

## Vue d'Ensemble du Système

### Architecture de Haut Niveau

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent / Workflow WXO                      │
│                  (IBM watsonx Orchestrate)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP POST (Outil OpenAPI)
                         │ + en-tête callbackUrl
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Serveur d'Outils FastAPI                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Endpoints:                                           │  │
│  │  • /process-image-async-b64                          │  │
│  │  • /process-image-async                              │  │
│  │  • /batch-process-images                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                         │                                    │
│         ┌───────────────┴───────────────┐                   │
│         ▼                               ▼                   │
│  ┌─────────────┐              ┌──────────────────┐         │
│  │   OpenAI    │              │ Traitement       │         │
│  │ Image Edit  │              │ Fallback Local   │         │
│  │     API     │              │  (PIL/Pillow)    │         │
│  └─────────────┘              └──────────────────┘         │
│         │                               │                   │
│         └───────────────┬───────────────┘                   │
│                         ▼                                    │
│         ┌───────────────────────────────┐                   │
│         │  IBM Cloud Object Storage     │                   │
│         │        (Compatible S3)        │                   │
│         └───────────────────────────────┘                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP POST (callback)
                         │ + résultats du job
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Endpoint de Callback                      │
│                  (WXO ou Serveur Personnalisé)               │
└─────────────────────────────────────────────────────────────┘
```

---

## Patterns d'Architecture

### 1. Pattern Requête-Réponse Asynchrone

**Problème :** Le traitement d'images peut prendre plusieurs secondes, bloquant la connexion HTTP.

**Solution :** Implémenter un pattern async avec callbacks :
1. Accepter la requête immédiatement (202 Accepted)
2. Traiter en arrière-plan
3. Notifier via callback quand terminé

> **Important :** Ici "arrière-plan" signifie in-process via FastAPI BackgroundTasks ; un redémarrage de l'instance annule les jobs en cours.

**Avantages :**
- Opérations non-bloquantes
- Meilleure utilisation des ressources
- Scalable pour les tâches de longue durée

### 2. Pattern de Fallback

**Problème :** L'API externe (OpenAI) peut atteindre sa limite de facturation.

**Solution :** Implémenter une dégradation gracieuse avec détection précise :
1. Essayer le service principal (OpenAI)
2. Détecter l'erreur spécifique via une fonction helper (ex: `_looks_like_openai_billing_limit(...)`) ou un matching équivalent sur le message d'erreur
3. **Uniquement** sur cette erreur, basculer vers le traitement local (PIL/Pillow)
4. Toute autre erreur OpenAI est renvoyée dans le payload de callback : champ `error` pour les endpoints single (avec `status=failed`) et/ou ajoutée dans `errors[]` pour le batch, afin de faciliter le debug
5. Suivre l'utilisation du fallback dans les métriques

> **Note :** Le fallback n'est **pas** déclenché sur toutes les erreurs OpenAI (ex: erreurs réseau, timeouts, etc.), seulement sur la limite de facturation.

**Avantages :**
- Haute disponibilité pendant les workshops
- Démos prévisibles même avec limite de facturation
- Debug facilité pour les autres erreurs

### 3. Principe de Responsabilité Unique

Chaque composant a un objectif clair et focalisé, implémenté via des fonctions helpers et des tâches en arrière-plan :
- **Endpoints :** Validation des requêtes et orchestration des jobs
- **Tâches en arrière-plan :** Logique de traitement async (via `BackgroundTasks`)
- **Fonctions helper :** Utilitaires réutilisables (COS, OpenAI, nommage, détection d'erreurs)
- **Gestionnaire de callback :** Livraison des résultats avec retries

---

## Conception des Composants

### 1. Application FastAPI ([`main.py`](main.py))

**Composants Principaux :**

#### Gestion de la Configuration
```python
# Configuration basée sur l'environnement
COS_ENDPOINT = os.getenv("COS_ENDPOINT", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

# Fonctions de validation
def _require_cos_config() -> None
def _require_openai_config() -> None
```

**Décision de Conception :** Utiliser des variables d'environnement pour toute la configuration pour supporter :
- Principes 12-factor app
- Déploiement facile à travers les environnements
- Gestion sécurisée des identifiants

#### Modèles de Requête (Pydantic)
```python
class ProcessImageRequest(BaseModel):
    prompt: str
    filename: Optional[str]
    image_base64: str

class BatchProcessRequest(BaseModel):
    prompt: str
```

**Décision de Conception :** Utiliser Pydantic pour :
- Validation automatique
- Sécurité des types
- Génération de schéma OpenAPI

#### Pattern de Tâche en Arrière-plan
```python
@app.post("/process-image-async-b64", status_code=202)
async def process_image_async_b64(
    body: ProcessImageRequest,
    background_tasks: BackgroundTasks,
    callbackUrl: str = Header(...),
):
    job_id = str(uuid.uuid4())
    background_tasks.add_task(process_and_callback_b64, job_id, body, callbackUrl)
    return {"accepted": True, "job_id": job_id}
```

**Décision de Conception :** Utiliser BackgroundTasks de FastAPI pour :
- Exécution async simple
- Pas de file d'attente externe requise
- Adapté aux charges de travail modérées

---

### 2. Intégration OpenAI

```python
def edit_image_with_openai(image_bytes: bytes, prompt: str) -> tuple[bytes, str, str]:
    client = OpenAI(api_key=OPENAI_API_KEY)
    result = client.images.edit(
        model=OPENAI_IMAGE_MODEL,
        image=image_file,
        prompt=prompt,
        quality=OPENAI_IMAGE_QUALITY,
        output_format=OPENAI_IMAGE_OUTPUT_FORMAT,
    )
    return out_bytes, mime, output_ext
```

**Décisions de Conception :**
- Retourner un tuple pour plusieurs sorties (bytes, mime, extension)
- Qualité et format configurables via variables d'env
- Lever des exceptions pour la gestion d'erreurs en amont

---

### 3. Traitement Fallback Local

```python
def local_fallback_process(image_bytes: bytes) -> tuple[bytes, str, str]:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    img = ImageOps.invert(img.convert("RGB")).convert("RGBA")
    
    # Ajouter un filigrane
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.text((20, 20), "DEMO - FALLBACK (Limite de facturation OpenAI)", fill=(255, 0, 0, 200))
    
    img = Image.alpha_composite(img, overlay)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue(), "image/png", "png"
```

**Décisions de Conception :**
- Transformation simple et visible (inversion des couleurs)
- Filigrane clair indiquant le mode fallback
- Retourne toujours du PNG pour la cohérence
- Pas de dépendances externes au-delà de Pillow

---

### 4. Intégration IBM Cloud Object Storage

```python
def make_s3_client():
    cfg = BotoConfig(
        region_name=COS_REGION,
        signature_version="s3v4",
        s3={"addressing_style": "path"},
        retries={"max_attempts": 3, "mode": "standard"},
    )
    return boto3.client("s3", endpoint_url=COS_ENDPOINT, ...)
```

**Décisions de Conception :**
- Utiliser boto3 pour la compatibilité S3
- Adressage de style path pour IBM COS
- Tentatives automatiques (3 essais)
- URLs pré-signées pour un accès sécurisé et temporaire

---

### 5. Mécanisme de Callback

```python
async def post_callback(callback_url: str, payload: dict) -> None:
    final_callback_url = rewrite_callback_url(callback_url)
    
    for attempt in range(1, max(CALLBACK_MAX_RETRIES, 1) + 1):
        try:
            async with httpx.AsyncClient(timeout=CALLBACK_TIMEOUT_SECONDS) as client:
                r = await client.post(final_callback_url, json=payload)
                r.raise_for_status()
                return  # Success
        except Exception as e:
            if attempt < max(CALLBACK_MAX_RETRIES, 1):
                await asyncio.sleep(CALLBACK_BACKOFF_LIST[attempt - 1])
            else:
                raise  # Final attempt failed
```

**Décisions de Conception :**
- Réécriture d'URL pour le développement local (support tunnel)
- **Timeout configurable** via `CALLBACK_TIMEOUT_SECONDS` (défaut: 30 secondes)
- **Retries avec backoff configurable** :
  - Nombre de tentatives : `CALLBACK_MAX_RETRIES` (défaut: 3 total)
  - Délais entre tentatives : `CALLBACK_BACKOFF_SECONDS` (défaut: 1,3,8 secondes)
  - Le backoff est défini par une liste configurable et n'est pas forcément exponentiel
  - Minimum 1 tentative même si `CALLBACK_MAX_RETRIES=0`
- **Gestion d'erreur** : `post_callback` lève une exception après toutes les tentatives ; les tâches background la catchent et loggent sans faire tomber le service

---

## Flux de Données

### Traitement d'Image Unique (Base64)

```
1. Client → POST /process-image-async-b64
   ├─ En-têtes: callbackUrl
   └─ Corps: {prompt, filename, image_base64}

2. Serveur → 202 Accepted
   └─ Réponse: {accepted: true, job_id: "..."}

3. Tâche en Arrière-plan:
   ├─ Décoder base64 → bytes
   ├─ Appeler l'API OpenAI
   ├─ Encoder le résultat → base64
   └─ POST vers callbackUrl
      └─ {status, job_id, filename, result_image_base64, result_mime_type, error?}
      
   Note: Le champ error est présent uniquement si status=failed

4. Le client reçoit le callback
```

### Traitement d'Image Unique (URL COS)

```
1. Client → POST /process-image-async
   ├─ En-têtes: callbackUrl
   └─ Corps: {prompt, filename, image_base64}

2. Serveur → 202 Accepted
   └─ Réponse: {accepted: true, job_id: "..."}

3. Tâche en Arrière-plan:
   ├─ Décoder base64 → bytes
   ├─ Appeler l'API OpenAI
   ├─ Télécharger vers COS
   ├─ Générer une URL pré-signée
   └─ POST vers callbackUrl
      └─ {status, job_id, filename, object_key, result_url, expires_in, error?}
      
   Note: Le champ error est présent uniquement si status=failed

4. Le client reçoit le callback
```

### Traitement par Lot

```
1. Client → POST /batch-process-images
   ├─ En-têtes: callbackUrl
   └─ Corps: {prompt}

2. Serveur → 202 Accepted
   └─ Réponse: {accepted: true, job_id: "..."}

3. Tâche en Arrière-plan:
   ├─ Lister tous les objets dans COS_INPUT_BUCKET
   ├─ Pour chaque image:
   │  ├─ Télécharger depuis COS
   │  ├─ Essayer l'API OpenAI
   │  │  └─ Sur billing_hard_limit_reached:
   │  │     └─ Basculer vers le traitement local
   │  └─ Télécharger le résultat vers COS_OUTPUT_BUCKET
   ├─ Collecter les métriques (processed, failed, fallback_local)
   └─ POST vers callbackUrl (callback unique)
      └─ {status, job_id, total_files, processed, failed,
          fallback_local, total_files_processed, duration_seconds,
          output_bucket, output_prefix, errors}

4. Le client reçoit le callback avec les résultats complets du lot
```

---

## Stratégie de Gestion des Erreurs

### 1. Erreurs de Configuration (Fail Fast)

```python
def _require_cos_config() -> None:
    missing = []
    if not COS_ENDPOINT: missing.append("COS_ENDPOINT")
    # ...
    if missing:
        raise RuntimeError(f"Variables d'env COS manquantes: {', '.join(missing)}")
```

**Stratégie :** Valider la configuration à l'entrée de l'endpoint, retourner 500 immédiatement.

### 2. Erreurs de Traitement (Dégradation Gracieuse)

```python
try:
    out_bytes, out_mime, out_ext = edit_image_with_openai(img_bytes, req.prompt)
except Exception as e:
    msg = str(e)
    if "billing_hard_limit_reached" in msg:
        out_bytes, out_mime, out_ext = local_fallback_process(img_bytes)
        fallback_local += 1
    else:
        failed += 1
        errors.append(msg)
```

**Stratégie :**
- Détection d'erreur spécifique (`billing_hard_limit_reached` uniquement)
- Fallback automatique sur cette erreur uniquement
- Toutes les autres erreurs OpenAI sont reportées telles quelles (single : `error` + `status=failed`, batch : entrée dans `errors[]` et incrément de `failed`), sans déclencher de fallback
- Suivre les métriques pour l'observabilité

### 3. Erreurs de Callback (Logger et Continuer)

```python
try:
    await post_callback(callback_url, payload)
except Exception as cb_err:
    print("!!! CALLBACK ÉCHOUÉ !!!", repr(cb_err))
```

**Stratégie :** Logger les échecs de callback mais ne pas crasher le service.

**Amélioration Future :** Implémenter une file d'attente de tentatives pour les callbacks échoués.

---

## Considérations de Scalabilité

### Implémentation Actuelle (Serveur Unique)

**Adapté pour :**
- Démos et prototypes
- Trafic faible à modéré (< 100 jobs concurrents)
- Développement et tests

**Limitations :**
- Les tâches en arrière-plan s'exécutent in-process via `BackgroundTasks`
- Pas de persistance des jobs (mémoire uniquement)
- Le redémarrage du serveur perd les jobs en cours
- Pas de distribution multi-serveur (chaque instance a sa propre queue)

> **⚠️ Workshop vs Production :** `BackgroundTasks` est in-process : un redémarrage perd les jobs. En production, utilisez une queue externe (Redis, SQS) + workers dédiés pour la résilience et la scalabilité.

### Options de Mise à l'Échelle en Production

#### Option 1 : Mise à l'Échelle Horizontale + File d'Attente

```
Load Balancer
    ├─ Serveur FastAPI 1 ─┐
    ├─ Serveur FastAPI 2 ─┼─→ Redis/RabbitMQ ─→ Pool de Workers
    └─ Serveur FastAPI N ─┘
```

**Changements Requis :**
- Remplacer BackgroundTasks par Celery/RQ
- Ajouter Redis pour la file d'attente des jobs
- Implémenter la persistance des jobs
- Ajouter l'auto-scaling des workers

#### Option 2 : Serverless

```
API Gateway → Lambda/Cloud Functions → S3/COS
                  ↓
            Step Functions (orchestration)
```

**Changements Requis :**
- Refactoriser en fonctions sans état
- Utiliser l'orchestration cloud-native
- Implémenter le callback via SNS/EventBridge

---

## Sécurité

### Implémentation Actuelle

**Points Forts :**
- Pas d'identifiants dans le code
- Configuration basée sur l'environnement
- URLs pré-signées avec expiration

**Lacunes (pour la production) :**
- Authentification légère uniquement (workshop guard optionnel)
- Pas de limitation de débit
- Sanitisation des entrées limitée (validation Pydantic + limites de taille)

**Implémenté (Workshop/Demo) :**
- **Workshop Guard (optionnel)** : Token partagé via header `x-workshop-token` si `WORKSHOP_TOKEN` est défini
- **Validation Base64** : Décodage strict avec `validate=True` (rejette les caractères invalides)
- **Limite de taille** : `MAX_IMAGE_BASE64_CHARS` (défaut: 14M caractères ≈ 10MB décodé)
- **Cap de concurrence** : Semaphore in-process `MAX_CONCURRENT_JOBS` (défaut: 10 jobs simultanés)

### Recommandations pour la Production

1. **Authentification :**
   - Clés API via en-têtes
   - OAuth 2.0 pour l'entreprise
   - Tokens JWT pour le contexte utilisateur

2. **Autorisation :**
   - Contrôle d'accès basé sur les rôles
   - Permissions au niveau du bucket
   - Gestion des quotas par client

3. **Validation des Entrées :**
   - Limites de taille d'image (actuellement implémenté : `MAX_IMAGE_BASE64_CHARS`)
   - Filtrage du contenu des prompts (à implémenter)
   - Validation du type de fichier (à implémenter)
   - Validation base64 stricte (actuellement implémenté : `validate=True`)

4. **Sécurité Réseau :**
   - HTTPS uniquement
   - Configuration CORS
   - Liste blanche IP pour les callbacks

5. **Gestion des Secrets :**
   - Utiliser AWS Secrets Manager / IBM Key Protect
   - Faire tourner les identifiants régulièrement
   - Auditer les logs d'accès

---

## Décisions Techniques

### Pourquoi FastAPI ?

**Avantages :**
- Support async natif
- Documentation OpenAPI automatique
- Type hints et validation
- Haute performance (Starlette + Pydantic)

**Alternatives Considérées :**
- Flask : Manque d'async natif
- Django : Trop lourd pour un microservice
- Express.js : Nécessiterait l'écosystème Node.js

### Pourquoi Boto3 pour COS ?

**Avantages :**
- API compatible S3
- Mature, bien documenté
- Support des URLs pré-signées
- Tentatives automatiques

**Alternatives Considérées :**
- ibm-cos-sdk : Moins maintenu
- HTTP direct : Plus complexe

### Pourquoi Pillow pour le Fallback ?

**Avantages :**
- Python pur (déploiement facile)
- Manipulation d'images riche
- Pas de dépendances externes
- Rapide pour les opérations simples

**Alternatives Considérées :**
- OpenCV : Surdimensionné pour les transformations simples
- ImageMagick : Dépendance binaire externe

### Pourquoi un Callback Unique ?

**Avantages :**
- Intégration simple
- Workflow prévisible
- Débogage facile

**Inconvénients :**
- Pas de mises à jour de progression (callback final uniquement)
- Pas de mécanisme de reprise/persistance si le serveur redémarre avant la fin du job

**Améliorations Futures :**
- Ajouter des callbacks de progression optionnels pour les opérations par lot
- Implémenter une dead-letter queue pour les callbacks échoués après tous les retries
- Ajouter une signature HMAC des callbacks pour la sécurité
- Implémenter une retry queue durable (Redis) pour les callbacks si le destinataire est down longtemps

---

## Monitoring et Observabilité

### Logging Actuel

```python
print("=== CALLBACK ===")
print("original :", callback_url)
print("réécrit:", final_callback_url)
```

**Limitations :** Console uniquement, pas de logging structuré.

### Recommandations pour la Production

1. **Logging Structuré :**
```python
import structlog

logger = structlog.get_logger()
logger.info("callback_sent", 
    job_id=job_id, 
    callback_url=callback_url,
    status=status)
```

2. **Métriques :**
   - Histogramme de durée des jobs
   - Taux de succès/échec
   - Pourcentage d'utilisation du fallback
   - Latence de l'API OpenAI

3. **Traçage :**
   - Intégration OpenTelemetry
   - Traçage distribué à travers les services
   - IDs de corrélation

4. **Alertes :**
   - Taux d'échec élevé
   - Échecs de livraison de callback
   - Erreurs de l'API OpenAI

---

## Améliorations Futures

### Court Terme
- [ ] Ajouter une dead-letter queue pour les callbacks échoués après tous les retries
- [ ] Implémenter le suivi d'ID de requête / correlation-id
- [ ] Ajouter un health check pour l'API OpenAI
- [ ] Supporter plus de formats d'image

### Moyen Terme
- [ ] Ajouter un endpoint de requête de statut de job
- [ ] Implémenter la vérification de signature webhook
- [ ] Ajouter l'annulation de job par lot
- [ ] Supporter le traitement vidéo

### Long Terme
- [ ] Support multi-modèles (Stable Diffusion, DALL-E)
- [ ] Fine-tuning de modèle personnalisé
- [ ] Streaming de progression en temps réel
- [ ] Analyse d'image avancée (OCR, détection d'objets)

---

## Références

- [Documentation FastAPI](https://fastapi.tiangolo.com/)
- [Référence API OpenAI](https://platform.openai.com/docs/api-reference)
- [IBM Cloud Object Storage](https://cloud.ibm.com/docs/cloud-object-storage)
- [Documentation Boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [Documentation Pillow](https://pillow.readthedocs.io/)