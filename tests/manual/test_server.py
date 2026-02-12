from llama_cpp import Llama
from fastapi import FastAPI
import uvicorn

# Load model first
print("Loading model...")
llm = Llama(
    model_path=r"C:\works\llm\models\Qwen2.5-7B-Instruct-Uncensored.Q4_K_M.gguf",
    n_ctx=2048,
    n_threads=8,
    verbose=False
)
print("Model loaded!")

# Create app
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/health")
def health_check():
    return {"status": "ok", "model_loaded": True}

if __name__ == "__main__":
    print("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=31301)