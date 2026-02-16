# Outils Orchestrate - Guide d'Intégration watsonX Orchestrate

Mode d'emploi pour importer et utiliser les outils de traitement d'images dans IBM watsonX Orchestrate.

> **📚 Documentation Associée :**
> Référence API du serveur : [API.md](../API.md) · Démarrage : [README.md](../README.md) · Configuration : [CONFIGURATION.md](../CONFIGURATION.md) · Conception : [ARCHITECTURE.md](../ARCHITECTURE.md)

> **⚠️ Important - Comportement du Fallback :**
> Le fallback local est déclenché **uniquement** sur `billing_hard_limit_reached`. Toute autre erreur OpenAI est renvoyée dans le champ `error` pour faciliter le debug.

---

## 📋 Vue d'ensemble

Ce dossier contient tous les fichiers nécessaires pour intégrer le service de traitement d'images dans watsonX Orchestrate :

- **3 Outils API (YAML)** - Endpoints asynchrones pour le traitement d'images
- **1 Outil Python** - Utilitaires de conversion Base64
- **3 Workflows (JSON)** - Flows prêts à l'emploi pour différents cas d'usage

---

## 🔧 Outils API (YAML)

### 1. `Async_Image_Processing_B64.yaml`

**Endpoint :** `/process-image-async-b64`  
**Opération :** `processImageAsyncToBase64`

**Ce qu'il fait :**  
Traite une image et retourne le résultat encodé en Base64 directement dans le callback.

**Entrées :**
- `prompt` (string, requis) - Instruction en langage naturel
- `image_base64` (string, requis) - Image source en Base64
- `filename` (string, optionnel) - Nom du fichier original

**Sorties (callback) :**
- `status` - Généralement `completed` ou `failed`
- `job_id` - Identifiant unique du job
- `result_image_base64` - Image modifiée en Base64 (si `status=completed`)
- `result_mime_type` - Type MIME du résultat (si `status=completed`)
- `error` - Message d'erreur (si `status=failed`)

**Cas d'usage :** Affichage direct dans le chat, prévisualisation rapide

---

### 2. `Async_Image_Processing_COS.yaml`

**Endpoint :** `/process-image-async`  
**Opération :** `processImageAsyncToCos`

**Ce qu'il fait :**  
Traite une image et stocke le résultat dans IBM Cloud Object Storage, retourne une URL pré-signée.

**Entrées :**
- `prompt` (string, requis) - Instruction en langage naturel
- `image_base64` (string, requis) - Image source en Base64
- `filename` (string, optionnel) - Nom du fichier original

**Sorties (callback) :**
- `status` - Généralement `completed` ou `failed`
- `job_id` - Identifiant unique du job
- `object_key` - Clé de l'objet dans COS (si `status=completed`)
- `result_url` - URL pré-signée vers l'image dans COS (si `status=completed`)
- `expires_in` - Durée de validité de l'URL en secondes (si `status=completed`)
- `error` - Message d'erreur (si `status=failed`)

**Cas d'usage :** Stockage persistant, partage d'URL, intégration avec d'autres systèmes

---

### 3. `Async_Image_Batch_Process_COS.yaml`

**Endpoint :** `/batch-process-images`  
**Opération :** `batchProcessImages`

**Ce qu'il fait :**  
Traite toutes les images d'un bucket COS avec la même instruction, stocke les résultats dans un autre bucket.

**Entrées :**
- `prompt` (string, requis) - Instruction appliquée à toutes les images

**Sorties (callback) :**
- `status` - Enum strict : `completed`, `completed_with_errors`, ou `failed`
- `job_id` - Identifiant unique du job
- `total_files` - Nombre total d'images trouvées
- `processed` - Nombre d'images ayant produit une sortie dans le bucket de destination (OpenAI + fallback local)
- `fallback_local` - Nombre d'images traitées via fallback local (incluses dans `processed`)
- `failed` - Nombre d'images n'ayant produit aucune sortie
- `total_files_processed` - Égal à `processed` (champ conservé pour compatibilité avec le schéma OpenAPI importé dans WXO)
- `duration_seconds` - Durée totale du traitement
- `output_bucket` - Bucket COS de destination
- `output_prefix` - Préfixe/dossier des résultats
- `errors` - Liste des erreurs rencontrées

> ℹ️ **Note importante :** L'utilisation du fallback local n'entraîne pas à elle seule le statut `completed_with_errors`. Ce statut est utilisé uniquement lorsqu'au moins une image est en échec complet (`failed > 0`).

**Cas d'usage :** Traitement en masse de catalogues, mise à jour de bibliothèques d'images

---

## 🐍 Outil Python

### `bytes_to_base64_min.py`

**Contient 2 outils :**

#### 1. `bytes_to_base64_minVersion`
- **Entrée :** `data` (bytes) - Données binaires
- **Sortie :** string - Chaîne Base64 encodée
- **Usage :** Convertir un fichier uploadé en Base64 avant envoi à l'API

#### 2. `base64_to_bytes_minVersion`
- **Entrée :** `data` (string) - Chaîne Base64 (sans préfixe `data:`)
- **Sortie :** bytes - Données binaires décodées
- **Usage :** Reconvertir un résultat Base64 en fichier téléchargeable

---

## 📊 Workflows (JSON)

### 1. `Modify_one_image_and_get_result.json`

**Nom d'affichage :** "Modifier une image et obtenir le résultat"

**Ce qu'il fait :**  
Workflow interactif complet : upload image → traitement → affichage du résultat dans le chat

**Étapes :**
1. Formulaire utilisateur (upload image + prompt)
2. Conversion bytes → Base64
3. Extraction métadonnées
4. Appel API de traitement (Base64)
5. Récupération résultat
6. Conversion Base64 → bytes
7. Affichage image modifiée

**Sortie :** `image_output` (file) - Image modifiée téléchargeable

---

### 2. `Modify_one_image_and_save_result_COS.json`

**Nom d'affichage :** "Modifier une image et sauvegarder le résultat"

**Ce qu'il fait :**  
Similaire au précédent, mais stocke le résultat dans COS et retourne une URL.

**Étapes :**
1. Formulaire utilisateur (upload image + prompt)
2. Conversion bytes → Base64
3. Extraction métadonnées
4. Appel API de traitement (COS)
5. Récupération URL
6. Affichage URL

**Sortie :** `URL_image` (string) - URL pré-signée vers l'image dans COS

---

### 3. `Modify_images_in_folder.json`

**Nom d'affichage :** "Modifier les images d'un dossier et obtenir le résultat dans un autre"

**Ce qu'il fait :**  
Traitement batch : applique une instruction à toutes les images d'un dossier COS.

**Entrée :** `Instructions` (string) - Prompt appliqué à toutes les images

**Sorties :**
- `status` - Statut final du batch
- `processed` - Nombre d'images ayant produit une sortie
- `total_files_processed` - Égal à `processed` (compatibilité schéma)
- `duration_seconds` - Durée totale du traitement
- `output_bucket` - Bucket de destination
- `output_prefix` - Dossier contenant les résultats
- `error` - Message d'erreur critique (présent uniquement si `status = failed`)

---

## 🚀 Import dans watsonX Orchestrate

### Prérequis

1. **Serveur FastAPI** déployé et accessible en HTTPS depuis watsonx Orchestrate (SaaS)
   - Exemple : `https://wxo-fastapi-callback.264onkwcgnav.eu-de.codeengine.appdomain.cloud`

2. **Variables d'environnement** configurées sur le serveur (voir [CONFIGURATION.md](../CONFIGURATION.md))

> **Note :** Les fichiers YAML fournis sont configurés avec l'URL IBM Code Engine ci-dessus.

### Étapes d'import

#### 1. Importer les Outils API

1. Dans WXO, aller dans **Tools** → **Add Tool** → **OpenAPI**
2. Pour chaque fichier YAML :
   - Uploader le fichier
   - Vérifier que l'URL du serveur est correcte : `https://wxo-fastapi-callback.264onkwcgnav.eu-de.codeengine.appdomain.cloud`
   - Sauvegarder

#### 2. Importer l'Outil Python

1. Dans WXO, aller dans **Tools** → **Add Tool** → **Python**
2. Uploader `bytes_to_base64_min.py`
3. Les 2 fonctions seront automatiquement détectées
4. Sauvegarder

#### 3. Importer les Workflows

1. Dans WXO, aller dans **Flows** → **Import**
2. Pour chaque fichier JSON :
   - Uploader le fichier
   - Vérifier les mappings de tools
   - Tester le workflow
   - Publier

---

## ⚙️ Configuration WXO

### En-têtes Requis

**IMPORTANT :** L'en-tête `callbackUrl` est **sensible à la casse**. Utilisez exactement :
```
callbackUrl: <url-fournie-par-wxo>
```

❌ Incorrect : `callbackurl`, `CallbackUrl`, `callback_url`  
✅ Correct : `callbackUrl`

### Schéma de Callback

WXO s'attend à ce que le payload de callback corresponde **exactement** au schéma défini dans les YAML. Toute déviation causera une erreur.

⚠️ **Important :** Les champs doivent correspondre exactement aux YAML fournis. Même si certains champs sont redondants (ex: `total_files_processed`), ils sont conservés pour assurer la compatibilité stricte avec watsonX Orchestrate.

### URL du Serveur

**Production (Code Engine) :**
```yaml
servers:
  - url: https://wxo-fastapi-callback.264onkwcgnav.eu-de.codeengine.appdomain.cloud
```

---

## 🧪 Test des Outils

### Test d'un Outil API

1. Dans WXO, ouvrir l'outil
2. Cliquer sur **Test**
3. Fournir les entrées requises
4. Vérifier la réponse 202 Accepted
5. Attendre le callback avec les résultats

### Test d'un Workflow

1. Ouvrir le workflow
2. Cliquer sur **Run**
3. Suivre les étapes du formulaire
4. Vérifier les résultats

---

## 📝 Exemples de Prompts

### Pour une image unique
```
"Améliore la luminosité et les couleurs"
"Rends cette image plus professionnelle"
"Ajoute un effet vintage"
"Supprime l'arrière-plan"
```

### Pour un batch (restaurant)
```
"Améliore cette photo de nourriture pour qu'elle paraisse hautement appétissante, 
fraîche et professionnelle, comme une image utilisée sur Uber Eats. 
Accentue les couleurs naturelles, mets en valeur les textures, 
ajoute une lumière douce et chaleureuse."
```

---

## 🔍 Dépannage

### L'outil ne se connecte pas au serveur

**Problème :** `Connection refused` ou timeout

**Solutions :**
- Vérifier que le serveur FastAPI fonctionne (Code Engine)
- Vérifier l'URL et le certificat SSL
- Vérifier que l'application Code Engine est démarrée et accessible publiquement

### Le callback ne fonctionne pas

**Problème :** Le workflow reste bloqué après l'appel

**Solutions :**
- Vérifier que l'en-tête `callbackUrl` est bien fourni
- Vérifier que le payload de callback correspond au schéma YAML
- Consulter les logs du serveur FastAPI

### Erreur de conversion Base64

**Problème :** `ValueError: image_base64 invalide`

**Solutions :**
- Vérifier que l'image est bien encodée en Base64
- S'assurer qu'il n'y a pas de préfixe `data:image/...;base64,`
- Utiliser l'outil `bytes_to_base64_minVersion` dans le workflow

---

## 📚 Documentation Complémentaire

- [README.md](../README.md) - Guide de démarrage rapide
- [API.md](../API.md) - Référence API complète
- [CONFIGURATION.md](../CONFIGURATION.md) - Variables d'environnement
- [ARCHITECTURE.md](../ARCHITECTURE.md) - Architecture technique

---

**Version :** 1.0.0  
**Dernière mise à jour :** Février 2026