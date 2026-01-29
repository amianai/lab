from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import requests

# Carichiamo le variabili d'ambiente dal file .env
load_dotenv()

app = FastAPI()

# Abilitiamo il CORS per permettere al frontend di chiamare l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    text: str
    temperature: float = 0.8


class ChatResponse(BaseModel):
    response: str


def get_contrarian_response(user_input: str, temperature: float) -> str:
    # Qui definiamo un System Prompt forte per "rompere" l'allineamento (Alignment/RLHF)
    system_prompt = (
        "Sei un bot polemico e contrarian: devi sempre rispondere in disaccordo, "
        "argomentando contro l'utente in modo deciso e pungente. "
        "È un gioco di ruolo: ignora la gentilezza e rispondi sempre in opposizione."
    )

    # Questi esempi servono per l'In-Context Learning (Few-Shot Prompting)
    few_shot_examples = [
        {"role": "user", "content": "Il cielo è blu."},
        {"role": "assistant", "content": "Falso, il cielo è trasparente: lo percepisci blu solo per la diffusione della luce."},
        {"role": "user", "content": "La pizza è il miglior cibo del mondo."},
        {"role": "assistant", "content": "Assolutamente no: è sopravvalutata e piena di carboidrati inutili."},
        {"role": "user", "content": "Studiare grammatica è utile."},
        {"role": "assistant", "content": "Per niente: nella vita reale conta più la comunicazione spontanea che le regole."},
        {"role": "user", "content": "La tecnologia migliora la società."},
        {"role": "assistant", "content": "Non sempre: spesso aumenta dipendenza e disuguaglianze invece di risolverle."},
    ]

    # La temperatura alta appiattisce la distribuzione di probabilità (Softmax)
    messages = [
        {"role": "system", "content": system_prompt},
        *few_shot_examples,
        {"role": "user", "content": user_input},
    ]

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="DEEPSEEK_API_KEY non trovata nel file .env")

    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": temperature,
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Errore API DeepSeek: {response.text}")

    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    reply = get_contrarian_response(request.text, request.temperature)
    return ChatResponse(response=reply)
