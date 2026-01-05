# 💬 Configuration Discord

## 1. Créer un Webhook Discord

1. Allez dans les paramètres de votre serveur Discord
2. Allez dans **Intégrations** → **Webhooks**
3. Cliquez sur **Nouveau Webhook**
4. Donnez un nom : `Rug Hunter`
5. Choisissez le salon où envoyer les notifications
6. **Copiez l'URL du webhook**

Exemple : `https://discord.com/api/webhooks/123456789/ABCdefGHIjklMNOpqrsTUVwxyz`

## 2. Configurer le .env

Ajoutez dans votre fichier `.env` :

```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123456789/ABCdefGHIjklMNOpqrsTUVwxyz
```

## 3. Tester

Redémarrez le bot et les notifications seront envoyées sur Discord !
