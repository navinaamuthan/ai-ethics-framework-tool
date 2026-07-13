"""
llm_caller.py
LLM backends for ethics assessment generation.

Backends:
  - Ollama (local): call_ollama() / call_llm(backend="ollama")
  - Groq (cloud):   call_groq()  / call_llm(backend="groq")
"""

import json
import os

import requests

_load_env_done = False


def _load_env():
    """Load key=value pairs from a local .env file if present."""
    global _load_env_done
    if _load_env_done:
        return
    _load_env_done = True

    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        return

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


_load_env()

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1:8b"
GROQ_DEFAULT_MODEL = "llama-3.3-70b-versatile"

# Backwards-compatible alias used elsewhere in the project.
MODEL = OLLAMA_MODEL


def call_ollama(
    prompt: str,
    model: str = None,
    temperature: float = 0.3,
    max_tokens: int = 4000,
    max_retries: int = 2,
) -> str:
    """Send a prompt to local Ollama and return the response text."""
    model = model or OLLAMA_MODEL

    for attempt in range(max_retries + 1):
        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                        "top_p": 0.9,
                    },
                },
                timeout=300,
            )
            if response.status_code == 200:
                return response.json().get("response", "")
            print(f"  [LLM ERROR] Status {response.status_code}: {response.text[:200]}")
        except requests.exceptions.ConnectionError:
            print("  [LLM ERROR] Cannot connect to Ollama at localhost:11434")
            print("  Make sure Ollama is running: ollama serve")
        except requests.exceptions.Timeout:
            print(f"  [LLM WARNING] Timeout on attempt {attempt + 1}")
        except Exception as e:
            print(f"  [LLM ERROR] {e}")

        if attempt < max_retries:
            print(f"  Retrying... ({attempt + 2}/{max_retries + 1})")

    return ""


def call_groq(
    prompt: str,
    model: str = None,
    temperature: float = 0.3,
    max_tokens: int = 4000,
    max_retries: int = 2,
) -> str:
    """Send a prompt to Groq via the OpenAI-compatible client."""
    from openai import OpenAI

    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        print("  [GROQ ERROR] GROQ_API_KEY not set. Export it or add to ethics-rag/.env")
        return ""

    model = model or GROQ_DEFAULT_MODEL
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )

    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            return content or ""
        except Exception as e:
            print(f"  [GROQ ERROR] {e}")

        if attempt < max_retries:
            print(f"  Retrying... ({attempt + 2}/{max_retries + 1})")

    return ""


def call_llm(
    prompt: str,
    backend: str = "ollama",
    model: str = None,
    temperature: float = 0.3,
    max_tokens: int = 4000,
    max_retries: int = 2,
) -> str:
    """Route a prompt to the selected LLM backend."""
    if backend == "groq":
        return call_groq(
            prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
        )
    return call_ollama(
        prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        max_retries=max_retries,
    )


# Backwards-compatible alias.
def call_llm_groq(prompt: str, max_retries: int = 2, model: str = None) -> str:
    return call_groq(prompt, model=model, max_retries=max_retries)


def parse_json_response(raw: str) -> dict:
    """
    Parse JSON from LLM output.
    Handles markdown fences, extra text before/after JSON.
    """
    text = raw.strip()

    if "```json" in text:
        text = text.split("```json")[1]
        if "```" in text:
            text = text.split("```")[0]
    elif "```" in text:
        parts = text.split("```")
        if len(parts) >= 3:
            text = parts[1]
        elif len(parts) >= 2:
            text = parts[1]

    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  [JSON PARSE ERROR] {e}")
        print(f"  Raw output (first 500 chars): {raw[:500]}")
        return {"parse_error": str(e), "raw_output": raw}


def test_connection(model: str = None) -> bool:
    """Test if Ollama is reachable."""
    model = model or OLLAMA_MODEL
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = [m["name"] for m in response.json().get("models", [])]
            print(f"  [OK] Ollama connected. Available models: {models}")
            if model in models:
                print(f"  [OK] Model '{model}' is available.")
                return True
            print(f"  [WARN] Model '{model}' not found. Run: ollama pull {model}")
            return False
        return False
    except Exception:
        print("  [FAIL] Cannot connect to Ollama. Run: ollama serve")
        return False


def test_groq_connection(model: str = None) -> bool:
    """Test if Groq API is reachable and the API key is valid."""
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        print("  [FAIL] GROQ_API_KEY not set. Export it or add to ethics-rag/.env")
        return False

    model = model or GROQ_DEFAULT_MODEL
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        models = [m.id for m in client.models.list().data]
        print(f"  [OK] Groq connected. Available models: {len(models)}")
        if model in models:
            print(f"  [OK] Model '{model}' is available.")
        else:
            print(f"  [WARN] Model '{model}' not listed. Groq may still accept it.")
        return True
    except Exception as e:
        print(f"  [FAIL] Cannot connect to Groq API: {e}")
        return False


# ── SELF-TEST ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LLM caller self-test")
    parser.add_argument("--backend", default="ollama", choices=["ollama", "groq"])
    parser.add_argument("--model", default=None)
    cli_args = parser.parse_args()

    print("=" * 60)
    print("LLM Caller Module — Self-Test")
    print("=" * 60)

    if cli_args.backend == "groq":
        print("\n1. Testing Groq connection...")
        if not test_groq_connection(cli_args.model):
            raise SystemExit(1)
    else:
        print("\n1. Testing Ollama connection...")
        if not test_connection(cli_args.model):
            raise SystemExit(1)

    print(f"\n2. Testing {cli_args.backend} LLM call...")
    result = call_llm(
        'Respond with exactly: {"status": "ok", "model": "working"}',
        backend=cli_args.backend,
        model=cli_args.model,
    )
    print(f"  Raw response: {result[:200]}")

    print("\n3. Testing JSON parsing...")
    parsed = parse_json_response(result)
    print(f"  Parsed: {parsed}")

    print("\n" + "=" * 60)
    print(
        "ALL TESTS PASSED"
        if "parse_error" not in parsed
        else "JSON PARSING NEEDS WORK — but LLM is responding"
    )
    print("=" * 60)
