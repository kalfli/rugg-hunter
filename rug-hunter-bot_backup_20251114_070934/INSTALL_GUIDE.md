# 🔧 GUIDE D'INSTALLATION POST-UPDATE

## ✅ Ce qui a été mis à jour automatiquement

- `backend/requirements.txt` - Dépendances corrigées
- `.env.template` - Template de configuration sécurisé
- `.gitignore` - Protection des fichiers sensibles
- `backend/core/honeypot_detector.py` - Détection réelle via API

## 📥 Fichiers volumineux à télécharger manuellement

Les fichiers suivants sont disponibles dans les artifacts Claude:

### 1. detector.py corrigé
**Artifact:** "detector.py - VERSION CORRIGÉE"
**Chemin:** `backend/core/detector.py`
**Changements:**
- Prix ETH/BNB réels depuis Coingecko
- Taxes réelles via Honeypot.is
- LP locked vérifié (Unicrypt, Team Finance, etc.)
- Contract verification via Etherscan API

### 2. token_analyzer.py corrigé
**Artifact:** "token_analyzer.py - VERSION CORRIGÉE"
**Chemin:** `backend/core/token_analyzer.py`
**Changements:**
- 54 indicateurs ML collectés RÉELLEMENT
- Analyse bytecode réelle
- Plus de valeurs hardcodées

### 3. setup_wallet.py sécurisé
**Artifact:** "setup_wallet.py - VERSION SÉCURISÉE"
**Chemin:** `scripts/setup_wallet.py`
**Changements:**
- PBKDF2 avec 480k itérations
- Seed phrase de 12 mots
- Clé privée jamais affichée
- Permissions fichier 600

## 🚀 Étapes d'installation

### 1. Installer les dépendances Python

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configurer l'environnement

```bash
# Copier le template
cp .env.template .env

# Générer les clés de sécurité
openssl rand -base64 32  # Copier dans JWT_SECRET_KEY
openssl rand -base64 32  # Copier dans API_KEY

# Éditer .env avec vos clés API
nano .env
```

### 3. Télécharger les fichiers volumineux

Téléchargez depuis les artifacts Claude:
1. `detector.py` → `backend/core/detector.py`
2. `token_analyzer.py` → `backend/core/token_analyzer.py`
3. `setup_wallet.py` → `scripts/setup_wallet.py`

### 4. Créer un nouveau wallet sécurisé

```bash
python scripts/setup_wallet.py
```

⚠️ **IMPORTANT:** Notez votre seed phrase de 12 mots sur PAPIER !

### 5. Tester le bot

```bash
python backend/main.py
```

## ⚠️ ACTIONS DE SÉCURITÉ URGENTES

### À faire MAINTENANT:

1. **Révoquer le token Telegram exposé**
   ```
   1. Ouvrir Telegram → @BotFather
   2. Envoyer /revoke
   3. Sélectionner votre bot
   4. Générer un nouveau token
   5. Mettre à jour .env avec le nouveau token
   ```

2. **Transférer les fonds du wallet exposé**
   - Le keystore était public sur GitHub
   - Créez un NOUVEAU wallet avec setup_wallet.py
   - Transférez TOUS les fonds
   - Ne réutilisez JAMAIS l'ancien wallet

3. **Supprimer les fichiers sensibles de Git**
   ```bash
   git rm secure/keystore.json
   git rm .env
   git commit -m "Remove sensitive files"
   git push
   ```

4. **Vérifier .gitignore**
   - `.env` est ignoré
   - `secure/keystore.json` est ignoré
   - `*.backup.*` est ignoré

## 📊 Checklist avant de lancer

- [ ] Dépendances installées
- [ ] .env configuré avec NOUVELLES clés
- [ ] Nouveau wallet créé et sécurisé
- [ ] Ancien token Telegram révoqué
- [ ] Fichiers sensibles retirés de Git
- [ ] detector.py, token_analyzer.py, setup_wallet.py téléchargés
- [ ] Mode PAPER activé dans .env
- [ ] MIN_LIQUIDITY_USD >= 5000

## 🧪 Tests recommandés

### Test 1: Vérifier les prix réels
```python
import asyncio
import aiohttp

async def test():
    async with aiohttp.ClientSession() as s:
        async with s.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum,binancecoin&vs_currencies=usd") as r:
            print(await r.json())

asyncio.run(test())
```

### Test 2: Vérifier Honeypot.is API
```python
import asyncio
import aiohttp

async def test():
    async with aiohttp.ClientSession() as s:
        async with s.get("https://api.honeypot.is/v2/IsHoneypot?address=0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2&chainID=1") as r:
            print(await r.json())

asyncio.run(test())
```

## 📚 Documentation complète

Consultez les artifacts:
- "RUG HUNTER - Analyse Complète & Solutions"
- "PLAN D'ACTION - Corrections Prioritaires"

## 💰 Coûts des APIs

| Service | Gratuit | Payant |
|---------|---------|--------|
| Coingecko | 50 calls/min | $129/mois |
| Honeypot.is | Illimité | N/A |
| Etherscan | 5 calls/sec | $199/mois |

**Recommandation:** Commencez avec les plans gratuits

## ⏱️ Timeline

- **Semaine 1:** Installation + Tests (mode PAPER)
- **Semaine 2:** Paper trading continu
- **Semaine 3:** Ajustements + Monitoring
- **Semaine 4:** Décision LIVE (avec <$100)

## 🆘 Besoin d'aide?

Si erreurs:
1. Vérifier les logs: `tail -f backend/logs/*.log`
2. Vérifier .env: toutes les variables sont définies
3. Vérifier API keys: valides et non expirées

Bonne chance ! 🚀
