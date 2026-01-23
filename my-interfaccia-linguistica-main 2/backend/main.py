from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

app = FastAPI()

# Enable CORS for Vue frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:8001",
    ],
    allow_origin_regex=r"https://.*\.app\.github\.dev",  # Match all Codespaces URLs
    allow_credentials=True,                    # Allow cookies/auth headers
    allow_methods=["*"],                       # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],                       # Allow all request headers
)

# Global model state
model_state = {
    "model": None,
    "tokenizer": None,
    "model_loaded": False
}

# Model configuration
MODEL_NAME = "KingNish/Qwen2.5-0.5b-Test-ft"

class GenerateJokeRequest(BaseModel):
    topic: str = ""
    max_length: int = 100
    temperature: float = 0.8

class JokeResponse(BaseModel):
    joke: str
    topic: str

@app.get("/")
def read_root():
    return {
        "message": "Joke Generator API", 
        "model_loaded": model_state["model_loaded"],
        "model_name": MODEL_NAME
    }

@app.post("/load-model")
def load_model():
    """Load the model (call this once at startup)"""
    if model_state["model_loaded"]:
        return {"message": "Model already loaded", "model_name": MODEL_NAME}
    
    try:
        print(f"Loading model {MODEL_NAME}...")
        print(f"CUDA available: {torch.cuda.is_available()}")
        
        # Load tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
        
        # Set pad token if not exists
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            load_in_8bit=True,
            device_map="auto",
            low_cpu_mem_usage=True
        )
        
        model_state["model"] = model
        model_state["tokenizer"] = tokenizer
        model_state["model_loaded"] = True
        
        print("Model loaded successfully!")
        
        return {
            "message": "Model loaded successfully",
            "model_name": MODEL_NAME,
            "device": "cuda" if torch.cuda.is_available() else "cpu"
        }
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error loading model: {error_details}")
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")

@app.post("/generate-joke", response_model=JokeResponse)
def generate_joke(request: GenerateJokeRequest):
    """Generate a joke using an llm"""
    if not model_state["model_loaded"]:
        raise HTTPException(status_code=400, detail="Model not loaded. Call /load-model first.")
    
    try:
        model = model_state["model"]
        tokenizer = model_state["tokenizer"]
        
        # Create prompt for joke generation
        if request.topic:
            prompt = f"Here's a funny joke about {request.topic}:\n"
        else:
            prompt = "Here's a funny joke:\n"
        
        # Tokenize input
        inputs = tokenizer(prompt, return_tensors="pt")
        if torch.cuda.is_available():
            inputs = inputs.to("cuda")
        else:
            inputs = inputs.to("cpu")
        
        # Generate joke (reduced tokens for faster generation)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=min(request.max_length, 50),
                min_new_tokens=10,
                temperature=request.temperature,
                do_sample=True,
                top_p=0.9,
                top_k=50,
                pad_token_id=tokenizer.eos_token_id,
                repetition_penalty=1.2
            )
        
        # Decode and clean output
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Remove the prompt from the output
        joke = generated_text.replace(prompt, "").strip()
        
        # Clean up and limit length
        if len(joke) > 500:
            joke = joke[:500] + "..."
        
        # If joke is empty or too short, provide a default
        if len(joke) < 10:
            joke = "Why don't scientists trust atoms? Because they make up everything!"
        
        return JokeResponse(
            joke=joke if joke else "Why don't scientists trust atoms? Because they make up everything!",
            topic=request.topic if request.topic else "general"
        )
    except Exception as e:
        print(f"Error generating joke: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate joke: {str(e)}")