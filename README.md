# 📸 WXO – Traitement d'Images Asynchrone avec OpenAI & IBM Cloud Object Storage

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-API-412991.svg)](https://openai.com)
[![IBM Cloud](https://img.shields.io/badge/IBM%20Cloud-Object%20Storage-054ADA.svg)](https://www.ibm.com/cloud/object-storage)

> **📦 Scope de ce repo :**
> Ce repo contient le service FastAPI + les tools WXO (YAML/JSON) pour le workshop.

> **📚 Documentation Associée :**
> [API.md](API.md) · [CONFIGURATION.md](CONFIGURATION.md) · [ARCHITECTURE.md](ARCHITECTURE.md) · [orchestrate-tools/README.md](orchestrate-tools/README.md)

> **🧭 Par où commencer ?**
> - Vous voulez l'exécuter localement ? → Vous êtes au bon endroit (README.md)
> - Vous voulez le configurer ? → [CONFIGURATION.md](CONFIGURATION.md)
> - Vous voulez l'intégrer via API ? → [API.md](API.md)
> - Vous voulez comprendre les choix de conception ? → [ARCHITECTURE.md](ARCHITECTURE.md)
> - Vous voulez l'utiliser dans WXO ? → [orchestrate-tools/README.md](orchestrate-tools/README.md)

---

## 📌 Vue d'ensemble

Outils de traitement d'images asynchrone pour **IBM WatsonX Orchestrate (WXO)** avec transformations IA via OpenAI et stockage persistant dans IBM Cloud Object Storage.

### Architecture

```
WXO → FastAPI → OpenAI
              → COS
              → Callback
```

> **💡 Philosophie de Conception :**
> Ce projet est **prêt pour la production par conception** (patterns asynchrones, gestion d'erreurs, observabilité), mais intentionnellement simplifié (tâches en arrière-plan in-process) pour des **fins de démonstration et d'enablement**. Le serveur exécute les jobs en background in-process (OK démo/workshop) ; pour production, voir [ARCHITECTURE.md](ARCHITECTURE.md) (queue externe recommandée). Ce mode implique qu'un redémarrage du conteneur entraîne la perte des jobs en cours.

### Fonctionnalités Clés

✅ **Traitement d'image unique** avec IA (édition d'images OpenAI)
✅ **Traitement d'images par lot** depuis IBM Cloud Object Storage
✅ **Exécution asynchrone** avec mécanisme de callback
✅ **Fallback local** uniquement sur billing_hard_limit_reached (limite de facturation OpenAI)
✅ **Prêt pour l'entreprise** pour démos, prototypage et workflows de production

---

## 🧪 Flux du Workshop

**Partie 1 – Image Unique (Base64)**  
Traiter une image et retourner le résultat directement en Base64 dans le callback.

**Partie 2 – Image Unique (COS)**  
Traiter une image, la stocker dans IBM Cloud Object Storage et retourner une URL pré-signée.

**Partie 3 – Traitement par Lot**  
Appliquer la même instruction IA à toutes les images d'un dossier de bucket COS.

**Partie 4 – Planificateur**  
Déclencher le traitement par lot selon un planning en utilisant les capacités de planification de WatsonX Orchestrate.

---

## 🚀 Pourquoi c'est important

✅ **Le pattern asynchrone est obligatoire pour les charges de travail IA d'entreprise**  
Les opérations IA de longue durée nécessitent une exécution non-bloquante pour maintenir la réactivité du système.

✅ **Orchestrate permet les workflows de longue durée**  
Le mécanisme de callback de WatsonX Orchestrate permet aux workflows de continuer pendant l'attente du traitement IA.

✅ **Séparation de l'orchestration et du fournisseur IA**  
Découpler la logique d'orchestration des services IA permet la flexibilité et facilite le changement de fournisseur.

✅ **Résilience avec fallback**
Le fallback local est déclenché uniquement sur `billing_hard_limit_reached`. Toute autre erreur OpenAI est renvoyée dans `error` pour faciliter le debug.

✅ **Planificateur + déclencheur API**  
Combiner l'automatisation planifiée avec des déclencheurs API à la demande pour une exécution flexible des workflows.

👉 **Prêt pour les Solution Engineers** – Patterns de production pour les déploiements IA d'entreprise.

## 🔁 Pattern Asynchrone (Pourquoi ?)

WXO appelle l'API ➜ reçoit immédiatement un **202 Accepted** ➜  
le traitement se fait en arrière-plan ➜  
le résultat est envoyé via callback ➜  
le workflow continue.

Ce pattern est indispensable pour :
- **les traitements IA longs** – éviter de bloquer l'orchestrateur pendant des minutes
- **éviter les timeouts** – ex: limite de 180s dans certains environnements
- **permettre la planification et l'automatisation** – déclencher des workflows sans attendre la fin

---

## 🚀 Démarrage Rapide

### ⚡ Chemin le Plus Rapide (5 minutes)

```bash
# 1. Copier et configurer l'environnement
cp .env.example .env
# Éditer .env avec vos identifiants

# 2. Créer et activer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Note: Si vous utilisez l'ADK/Agent Builder qui attend venv/, remplacez .venv par venv

# 3. Charger les variables
set -a && source .env && set +a

# 4. Installer les dépendances
pip install -r requirements.txt

# 5. Démarrer le serveur
uvicorn main:app --host 0.0.0.0 --port 8000

# 6. Vérifier (dans un autre terminal)
curl http://localhost:8000/health

# 7. Tester (optionnel)
bash scripts/test_local.sh
```

---

### Prérequis

- **Python 3.10+** (3.9+ supporté, 3.10+ recommandé)
- **IBM Cloud Object Storage** avec identifiants HMAC
- **Clé API OpenAI** depuis https://platform.openai.com/api-keys
- **Pour le développement local sur Mac** : VM Lima avec WatsonX Orchestrate ADK

### Installation

1. **Cloner et configurer :**
```bash
git clone https://github.com/Estepa-F/wxo-fastapi-callback.git
cd wxo-fastapi-callback
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configurer l'environnement :**
```bash
cp .env.example .env
# Éditer .env avec vos identifiants (voir CONFIGURATION.md pour les détails)
```

3. **Charger les variables d'environnement :**

> ⚠️ **CRITIQUE** : Vous DEVEZ charger `.env` avant de lancer le serveur !

```bash
set -a
source .env
set +a
```

**Vérifier que les variables sont chargées :**
```bash
echo $COS_ENDPOINT
# Devrait afficher : https://s3.eu-de.cloud-object-storage.appdomain.cloud

echo $OPENAI_API_KEY | wc -c
# Devrait afficher un nombre > 10 (sans exposer la clé)
```

4. **Lancer le serveur :**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --log-level debug
```

> ⚠️ **Important** : Utilisez `--host 0.0.0.0` (pas `127.0.0.1`) pour rendre le serveur accessible depuis la VM Lima.
>
> **Dépannage** : Si `curl http://host.lima.internal:8000/health` échoue depuis la VM, c'est presque toujours parce que FastAPI a été démarré avec `127.0.0.1` au lieu de `0.0.0.0`.

5. **Vérifier qu'il fonctionne :**
```bash
curl http://localhost:8000/health
# Attendu : {"ok": true}
```

---

## 🧪 Test Rapide

### Option 1 : Script de Test Automatisé (Recommandé)

La façon la plus simple de vérifier votre configuration :

```bash
# 1. Charger les variables d'environnement
set -a
source .env
set +a

# 2. Démarrer FastAPI (dans un terminal séparé)
uvicorn main:app --host 0.0.0.0 --port 8000

# 3. Exécuter le script de test
bash scripts/test_local.sh
```

**Ce qu'il fait :**
- ✅ Vérifie toutes les variables d'environnement requises
- ✅ Vérifie la santé du serveur FastAPI
- ✅ Valide la configuration COS
- ✅ Démarre automatiquement un serveur de callback local
- ✅ Teste le traitement d'image unique (Base64)
- ✅ Teste le traitement d'images par lot
- ✅ Nettoie les ressources à la sortie

**Prérequis :**
- Image de test `burger.jpeg` à la racine du projet (pour le test d'image unique)
- Bucket d'entrée avec des images de test (pour le test par lot)

---

### Option 2 : Test Manuel

#### Prérequis pour le Traitement par Lot

Avant de tester les opérations par lot, assurez-vous que :

✅ **Le bucket d'entrée existe** et contient des images de test (JPEG, PNG)
✅ **Le bucket de sortie existe** (peut être le même que l'entrée)
✅ **Les identifiants HMAC ont les permissions** : `list`, `get`, `put`
✅ **La configuration est valide** :
```bash
curl http://localhost:8000/cos/config
# Vérifier : endpoint, input_bucket, output_bucket correspondent à votre configuration
```

#### 1. Démarrer un Serveur de Callback

Dans un nouveau terminal :
```bash
python - <<'PY'
from fastapi import FastAPI
import uvicorn
from datetime import datetime, timezone

app = FastAPI()

@app.post("/callback")
def cb(data: dict):
    print(f"\n--- {datetime.now(timezone.utc).isoformat()} ---")
    print(data)
    return {"ok": True}

uvicorn.run(app, host="0.0.0.0", port=9999)
PY
```

> **💡 Note :** Si local strict (pas de tunnel/VM), `127.0.0.1` suffit.

#### 2. Traiter une Image

```bash
export B64=$(base64 -i your-image.jpg | tr -d '\n')

curl -X POST http://localhost:8000/process-image-async-b64 \
  -H "Content-Type: application/json" \
  -H "callbackUrl: http://localhost:9999/callback" \
  -d "{
    \"prompt\": \"ajoute un coucher de soleil en arrière-plan\",
    \"filename\": \"test.jpg\",
    \"image_base64\": \"$B64\"
  }"
```

Vous devriez voir :
1. Réponse immédiate : `{"accepted": true, "job_id": "..."}`
2. Callback dans le terminal 1 avec l'image traitée (base64)

---

## 🖥️ Développement Local avec WatsonX Orchestrate (Mac + VM Lima)

### Architecture

```
Mac (Hôte)
├── Serveur FastAPI (port 8000)
│   └── http://0.0.0.0:8000
│
└── VM Lima (ibm-watsonx-orchestrate)
    ├── WatsonX Orchestrate ADK (port 4321)
    │   └── Accessible via tunnel SSH : localhost:14321
    │
    └── Accès à l'hôte Mac via : host.lima.internal:8000
```

### Pourquoi `host.lima.internal:8000` ?

La VM Lima utilise un réseau isolé. L'alias DNS spécial **`host.lima.internal`** se résout vers l'IP de l'hôte Mac depuis la VM, permettant à Orchestrate de communiquer avec votre serveur FastAPI.

### Étapes de Configuration

**1. Démarrer FastAPI sur Mac :**
```bash
cd wxo-fastapi-callback
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --log-level debug
```

**2. Démarrer la VM Lima :**
```bash
limactl start ibm-watsonx-orchestrate
```

**3. Créer un Tunnel SSH :**
```bash
ssh -o 'IdentityFile="/Users/VOTRE_NOM_UTILISATEUR/.lima/_config/user"' \
  -o StrictHostKeyChecking=no \
  -o Hostname=127.0.0.1 \
  -o Port=VOTRE_PORT_SSH_LIMA \
  -N \
  -L 14321:127.0.0.1:4321 \
  lima-ibm-watsonx-orchestrate
```

> 📝 Remplacez `VOTRE_NOM_UTILISATEUR` et `VOTRE_PORT_SSH_LIMA` (vérifiez avec `limactl list`)

**4. Accéder à Orchestrate :**
```
http://localhost:14321
```

**5. Tester la Connectivité :**
```bash
limactl shell ibm-watsonx-orchestrate
curl http://host.lima.internal:8000/health
# Attendu : {"ok": true}
```

**6. Importer les Outils :**

Importez ces fichiers depuis `orchestrate-tools/` dans WatsonX Orchestrate :
- Fichiers YAML comme outils API
- Fichier Python comme outil Python  
- Fichiers JSON comme workflows

Voir [orchestrate-tools/README.md](orchestrate-tools/README.md) pour les instructions détaillées.

---

## ✅ Checklist de Démarrage

Avant de commencer, vérifiez ces points pour éviter les problèmes courants :

1. ✅ **`.env` chargé** : `set -a && source .env && set +a` (vérifier avec `echo $OPENAI_API_KEY`)
2. ✅ **Serveur démarré correctement** : `uvicorn main:app --host 0.0.0.0 --port 8000`
3. ✅ **Health check OK** : `curl http://localhost:8000/health` → `{"ok": true}`
4. ✅ **Config COS valide** : `curl http://localhost:8000/cos/config` → vérifier endpoint et buckets
5. ✅ **En-tête callback exact** : `callbackUrl` (sensible à la casse, pas `callbackurl`)
6. ✅ **Base64 sans préfixe** : Pas de `data:image/...;base64,` dans `image_base64`
7. ✅ **Buckets COS existent** : Créer input/output buckets dans IBM Cloud avant le batch
8. ✅ **Images de test prêtes** : JPEG ou PNG dans le bucket d'entrée pour les tests

---

## ⚠️ Pièges Connus

- **L'en-tête `callbackUrl` est sensible à la casse** - Utilisez exactement `callbackUrl`, pas `callbackurl` ou `callback_url`
- **Pas de préfixe `data:` dans le Base64** - Envoyez la chaîne Base64 brute sans préfixe `data:image/...;base64,`
- **Utilisez `--host 0.0.0.0`** - Requis pour l'accès VM Lima, `127.0.0.1` ne fonctionnera pas
- **Sourcez `.env` avant l'exécution** - Exécutez `set -a && source .env && set +a` ou le serveur échouera
- **Les buckets COS doivent exister** - Créez les buckets d'entrée/sortie dans IBM Cloud avant de tester le lot

---

## 🧰 Outils Disponibles

### 1️⃣ Image Unique (Sortie Base64)
**Endpoint :** `POST /process-image-async-b64`  
**Cas d'usage :** Traiter une image, retourner le résultat directement dans le chat/workflow  
**Idéal pour :** Démos rapides, prévisualisation visuelle, interactions légères

### 2️⃣ Image Unique (Sortie URL COS)
**Endpoint :** `POST /process-image-async`  
**Cas d'usage :** Traiter une image, stocker dans COS, retourner une URL pré-signée  
**Idéal pour :** Stockage persistant, partage, intégration avec d'autres systèmes

### 3️⃣ Traitement par Lot (COS → COS)
**Endpoint :** `POST /batch-process-images`  
**Cas d'usage :** Appliquer la même instruction à toutes les images d'un dossier COS  
**Idéal pour :** Mises à jour de contenu en masse, catalogues e-commerce, assets marketing

---

## 📚 Documentation

| Document | Objectif |
|----------|----------|
| **[API.md](API.md)** | Référence API complète avec endpoints, schémas et exemples |
| **[CONFIGURATION.md](CONFIGURATION.md)** | Variables d'environnement et guide de configuration |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | Architecture technique, patterns et décisions de conception |
| **[orchestrate-tools/README.md](orchestrate-tools/README.md)** | Guide d'intégration WatsonX Orchestrate |

---

## 🎯 Cas d'Usage

- 🎨 **Démos produit** – Présenter les capacités IA
- 🏢 **Workshops clients** – Formation pratique
- 🚀 **Accélérateurs internes** – Prototypage rapide
- 📚 **Bonnes pratiques WatsonX Orchestrate** – Implémentation de référence

---

## 🔒 Notes de Sécurité

- Ne jamais commiter `.env` dans le contrôle de version
- Utiliser des variables d'environnement pour tous les identifiants
- Faire tourner les clés API régulièrement
- Utiliser des URLs pré-signées avec expiration appropriée
- Voir [CONFIGURATION.md](CONFIGURATION.md) pour les recommandations de sécurité en production

---

## 🤝 Contribution

Ceci est un projet de démonstration pour IBM WatsonX Orchestrate. Pour questions ou suggestions, veuillez contacter le mainteneur.

---

## 📝 Licence

Ce projet est à des fins de démonstration et éducatives.