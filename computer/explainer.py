import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"

SYSTEM_PROMPT = (
    "You are a helpful plant pathologist assistant. "
    "Give short, plain-language advice a home gardener can act on immediately. "
    "Maximum 3 sentences."
)


def explain(label: str) -> str:
    """Ask the local Ollama LLM for a plain-language explanation of the diagnosis."""
    prompt = (
        f"A plant leaf has been diagnosed with: {label}. "
        "What is this disease and what should the gardener do right now?"
    )
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": prompt, "system": SYSTEM_PROMPT, "stream": False},
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["response"].strip()
    except requests.exceptions.ConnectionError:
        return f"Explanation unavailable — Ollama is not running on this machine."
    except Exception as e:
        return f"Explanation unavailable: {e}"
