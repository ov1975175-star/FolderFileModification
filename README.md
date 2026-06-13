# 🎮 FF MOD BOT

Free Fire Unity asset modifier — Telegram Bot

## Features
| Mod | Kya karta hai |
|-----|--------------|
| 👗 Cloth | Antena (1→3000) + Material transplant |
| 🔫 Gunskin | V4 + Gloo material apply |
| 🧍 Character | Antena + Material |
| 🌈 Hologram | Multi colour inject |
| 🧱 Wall Hack | Trigger / Mide mode |
| 🔹 Mini Gloo | Size chota (0.466) |
| 📋 File Info | fileinfo.txt update |

## Access
Bot sirf OWNER_ID wale user ke liye hai. Baaki sab ko "Access denied" milega.

---

## Setup — Local (Termux / PC)

```bash
pip install -r requirements.txt
cp .env.example .env
# .env mein apna BOT_TOKEN aur OWNER_ID daalo
python bot.py
```

---

## Deploy — Railway.app

### Step 1: GitHub
1. GitHub pe new repo banao (private recommended)
2. Saari files upload karo

### Step 2: Railway
1. railway.app pe jao → Login with GitHub
2. "New Project" → "Deploy from GitHub repo"
3. Apna repo select karo

### Step 3: Environment Variables
Railway dashboard → Variables tab mein ye daalo:
```
BOT_TOKEN = apna_telegram_bot_token
OWNER_ID  = apna_telegram_user_id
```

### Step 4: Deploy
- Railway automatically deploy karega
- Logs mein "✅ FF MOD Bot chal raha hai..." dikh jayega

---

## Bot Use Karne Ka Tarika

```
1. /start bhejo
2. Mod choose karo (buttons se)
3. Wall Hack ke liye sub-mode bhi choose karo
4. Bot folder paths maangega — ek ek karke bhejo
   Example: /storage/emulated/0/Download/E/CLOTH /normal clothes
5. Bot processing karega aur result batayega
6. Output folder mein modified files milegi
```

### Folder flow per mod:
- **Cloth**: Normal folder → REF folder → Output folder
- **Gunskin**: Normal folder → Output folder  
- **Character**: Normal folder → Output folder
- **Hologram**: Normal folder → Output folder
- **Wall Hack**: Normal folder → Output folder (+ mode select)
- **Mini Gloo**: Normal folder → Output folder
- **File Info**: Modified files folder → fileinfo.txt path

---

## Apna OWNER_ID kaise pata kare?
1. Telegram pe @userinfobot ko message karo
2. Woh tumhara ID bata dega
3. Wahi ID OWNER_ID mein daalo

## Bot Token kaise banaye?
1. Telegram pe @BotFather ko /newbot bhejo
2. Naam aur username daalo
3. Token copy karo → BOT_TOKEN mein daalo
