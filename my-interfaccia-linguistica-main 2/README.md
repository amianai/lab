# 🎭 AI Joke Generator

Un generatore di barzellette

## 🚀 Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (Vue.js)

```bash
cd my-proj
npm install
npm run dev
```

## 📖 Come usare

1. **Avvia il backend** - Apri un terminale e avvia FastAPI
2. **Avvia il frontend** - Apri un altro terminale e avvia Vue
3. **Carica il modello** - Clicca su "Load Model" (prima volta: ~30 secondi)
4. **Genera barzellette** - Inserisci un topic opzionale e clicca "Generate Joke"
