# 📱 Configuration Telegram

## 1. Créer un bot Telegram

1. Ouvrez Telegram et cherchez **@BotFather**
2. Envoyez `/newbot`
3. Donnez un nom : `Rug Hunter Bot`
4. Donnez un username : `your_rug_hunter_bot` (doit finir par "bot")
5. **Copiez le token** que BotFather vous donne

Exemple de token : `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

## 2. Obtenir votre Chat ID

1. Cherchez votre bot sur Telegram
2. Appuyez sur **Start**
3. Envoyez n'importe quel message à votre bot
4. Allez sur : `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
5. Trouvez votre **chat_id** dans la réponse JSON

Exemple : `"chat":{"id":123456789`

## 3. Configurer le .env

Ajoutez dans votre fichier `.env` :

```bash
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

## 4. Tester

Redémarrez le bot et vous recevrez une notification de démarrage !
