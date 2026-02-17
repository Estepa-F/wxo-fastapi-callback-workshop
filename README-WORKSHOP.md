# 🎓 WXO FastAPI Callback - Workshop Edition

Cette version est optimisée pour les **workshops et démonstrations** avec des améliorations de robustesse et de sécurité.

> **📚 Documentation complète:** Voir [README.md](README.md) pour le guide complet d'installation et d'utilisation.

---

## 🆕 Nouveautés Workshop

### 1. 🔐 Protection par Token (Optionnel)

Ajoutez un token partagé pour contrôler l'accès pendant les workshops:

```bash
# Dans .env
WORKSHOP_TOKEN=wxo-workshop-casino-2026
```

Les participants doivent alors inclure ce header dans toutes leurs requêtes:

```bash
curl -X POST https://your-server/process-image-async-b64 \
  -H "x-workshop-token: wxo-workshop-casino-2026" \
  -H "callbackUrl: https://your-callback-url/callback" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "...", "image_base64": "..."}'
```

> **💡 En SaaS :** Utilisez `https://` pour l'API et un `callbackUrl` HTTPS public.

**Avantages:**
- Empêche l'utilisation non autorisée pendant les workshops
- Simple à partager avec les participants
- Facile à désactiver (laisser `WORKSHOP_TOKEN` vide)

---

### 2. 🔄 Callbacks Robustes avec Retries

Les callbacks sont maintenant **automatiquement réessayés** en cas d'échec:

```bash
# Configuration dans .env
CALLBACK_MAX_RETRIES=3              # 3 tentatives au total
CALLBACK_BACKOFF_SECONDS=1,3,8      # Délais entre tentatives (1s, 3s, 8s)
CALLBACK_TIMEOUT_SECONDS=30         # Timeout par tentative
```

**Comportement (3 tentatives maximum):**
1. Première tentative immédiate
2. Si échec → attendre 1s → 2ème tentative
3. Si échec → attendre 3s → 3ème tentative (finale)

> **Note :** Les valeurs de `CALLBACK_BACKOFF_SECONDS` sont utilisées séquentiellement entre les tentatives ; si plus de valeurs sont fournies que nécessaires, les dernières sont ignorées.

**Avantages:**
- Résiste aux problèmes réseau temporaires
- Améliore la fiabilité des workflows WXO
- Logs détaillés pour le debugging

---

### 3. 🛡️ Fallback Local pour Single Images

En cas de limite de billing OpenAI, les endpoints single-image utilisent maintenant un **fallback local automatique**:

```bash
# Dans .env
ENABLE_FALLBACK_SINGLE=true
```

**Comportement:**
- Si OpenAI retourne une erreur de billing → traitement local automatique
- L'image est inversée + watermark "DEMO - FALLBACK"
- Le workflow continue sans interruption
- Métrique `fallback_local` dans le callback

**Avantages:**
- Continuité de la démo même si la limite de facturation OpenAI est atteinte
- Pas de workflow cassé pendant les workshops
- Visibilité claire du mode fallback (watermark)

---

### 4. 🚦 Limites de Sécurité

Protection contre les abus pendant les workshops:

```bash
# Dans .env
MAX_CONCURRENT_JOBS=10              # Max 10 jobs simultanés par instance
MAX_IMAGE_BASE64_CHARS=14000000     # ~10 MB max par image
```

**Protections:**
- Limite de concurrence (évite la surcharge)
- Validation de la taille des images
- Détection du préfixe `data:` (erreur commune)
- Semaphore asyncio pour la gestion des jobs

---

### 5. 🔧 Mode SaaS par Défaut

Le callback rewrite (Mac/Lima) est **désactivé par défaut**:

```bash
# Dans .env
ENABLE_CALLBACK_REWRITE=false  # Important pour SaaS/Cloud
```

**Pour développement local uniquement:**
```bash
ENABLE_CALLBACK_REWRITE=true
LOCAL_TUNNEL_NETLOC=127.0.0.1:14321
```

---

## 📊 Endpoint de Health Amélioré

Le endpoint `/health` retourne maintenant la configuration workshop:

```bash
curl http://localhost:8000/health
```

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

> **Note :** `workshop_token_enabled` passe à `true` si `WORKSHOP_TOKEN` est défini.

---

## 🚀 Quick Start Workshop

### 1. Configuration

```bash
# Copier et éditer .env
cp .env.example .env
nano .env

# Configurer:
# - Credentials IBM COS
# - OpenAI API Key
# - WORKSHOP_TOKEN (optionnel)
```

### 2. Lancer le serveur

```bash
# Charger les variables
set -a && source .env && set +a

# Démarrer FastAPI
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 3. Tester

```bash
# Health check
curl http://localhost:8000/health

# Test avec token (uniquement si WORKSHOP_TOKEN est défini côté serveur)
curl -X POST http://localhost:8000/process-image-async-b64 \
  -H "x-workshop-token: votre-token-ici" \
  -H "callbackUrl: http://localhost:8001/callback" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "add a sunset", "image_base64": "..."}'
```

---

## 🐳 Déploiement Docker

Le `Dockerfile` est inclus et prêt pour le déploiement:

```bash
# Build
docker build -t wxo-image-workshop .

# Run
docker run -p 8000:8000 --env-file .env wxo-image-workshop
```

**Compatible avec:**
- IBM Code Engine
- Kubernetes
- Docker Compose
- Cloud Run (GCP)
- Azure Container Apps

---

## 📝 Différences avec la Version Standard

| Fonctionnalité | Standard | Workshop |
|----------------|----------|----------|
| Callback retries | ❌ Non | ✅ Oui (3x avec backoff) |
| Workshop token | ❌ Non | ✅ Optionnel |
| Fallback single | ⚠️ Selon config | ✅ Single endpoints (billing only) |
| Limites concurrence | ❌ Non | ✅ Oui (configurable) |
| Validation taille | ❌ Basique | ✅ Stricte |
| Health détaillé | ❌ Simple | ✅ Complet |
| Logs verbeux | ⚠️ print basique | ✅ Debug-friendly |

---

## 🔍 Monitoring et Debugging

### Logs de Callback

```
=== CALLBACK ===
job_id   : 550e8400-e29b-41d4-a716-446655440000
original : http://wxo-server:4321/callback
final    : http://127.0.0.1:14321/callback
status   : completed
keys     : ['status', 'job_id', 'filename', 'result_image_base64', 'result_mime_type']
attempt  : 1/3 -> HTTP 200
```

### Logs de Job

```
[ACCEPTED] /process-image-async-b64 job_id=550e8400... filename=burger.jpeg
```

### Logs de Fallback

```
callback : attempt failed (ConnectError: ...); retrying in 3s
```

---

## ⚠️ Recommandations Workshop

### Avant le Workshop

✅ Tester tous les endpoints avec le token  
✅ Vérifier les credentials COS et OpenAI  
✅ Préparer des images de test dans COS  
✅ Documenter le token pour les participants  
✅ Tester le fallback local

### Pendant le Workshop

✅ Monitorer les logs en temps réel  
✅ Vérifier le health endpoint régulièrement
✅ Avoir un plan B si la limite de facturation OpenAI est atteinte (fallback activé)
✅ Partager le token de manière sécurisée
✅ Limiter le nombre de participants si nécessaire

### Après le Workshop

✅ Révoquer/changer le workshop token  
✅ Nettoyer les buckets COS  
✅ Vérifier les coûts OpenAI  
✅ Archiver les logs pour analyse

---

## 🆘 Troubleshooting Workshop

### "Unauthorized (missing/invalid x-workshop-token)"

**Solution:** Vérifier que le header `x-workshop-token` est bien envoyé avec la bonne valeur.

### Callbacks échouent systématiquement

**Solution:** 
1. Vérifier que `CALLBACK_MAX_RETRIES` est > 0
2. Augmenter `CALLBACK_TIMEOUT_SECONDS`
3. Vérifier la connectivité réseau

### "image_base64 trop grand"

**Solution:** 
1. Réduire la taille de l'image
2. Augmenter `MAX_IMAGE_BASE64_CHARS` si nécessaire
3. Utiliser l'endpoint COS URL au lieu de Base64

### Trop de jobs simultanés

**Solution:** Augmenter `MAX_CONCURRENT_JOBS` ou déployer plusieurs instances.

---

## 📚 Documentation Complète

- [README.md](README.md) - Guide complet d'installation
- [API.md](API.md) - Référence API détaillée
- [CONFIGURATION.md](CONFIGURATION.md) - Variables d'environnement
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture technique
- [orchestrate-tools/README.md](orchestrate-tools/README.md) - Intégration WXO

---

## 🤝 Support

Pour questions ou problèmes pendant le workshop, contactez l'équipe technique.

**Version:** 3.2.0-workshop  
**Dernière mise à jour:** Février 2026