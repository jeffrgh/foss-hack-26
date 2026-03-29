from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from core.frappe_api import import_page, update_page, is_running
from core.validator import validate

app = FastAPI(title="AI Page Builder API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    description: str
    provider: str = "Local Ollama"
    api_key: Optional[str] = None


class ImportRequest(BaseModel):
    page_data: dict


class UpdateRequest(BaseModel):
    page_name: str
    page_data: dict
    refinement: str
    provider: str = "Local Ollama"
    api_key: Optional[str] = None


@app.get("/status")
def status():
    try:
        import requests
        ollama_ok = requests.get("http://localhost:11434/api/tags", timeout=3).status_code == 200
    except:
        ollama_ok = False

    return {
        "ollama": ollama_ok,
        "frappe": is_running()
    }


@app.post("/generate")
def generate(req: GenerateRequest):
    from core.ollama import generate_page, generate_page_groq, generate_page_openai, generate_page_gemini
    from core.validator import validate

    try:
        if req.provider == "Groq" and req.api_key:
            result = generate_page_groq(req.description, req.api_key)
        elif req.provider == "OpenAI" and req.api_key:
            result = generate_page_openai(req.description, req.api_key)
        elif req.provider == "Gemini" and req.api_key:
            result = generate_page_gemini(req.description, req.api_key)
        else:
            result = generate_page(req.description)

        page_data, warnings = validate(result)
        return {"ok": True, "page": page_data, "warnings": warnings}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/import")
def import_to_frappe(req: ImportRequest):
    try:
        result = import_page(req.page_data)
        return {"ok": True, "name": result["name"], "url": result["url"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/refine")
def refine(req: UpdateRequest):
    from core.ollama import refine_page

    try:
        groq_key = req.api_key if req.provider != "Local Ollama" else None
        updated = refine_page(req.page_data, req.refinement, groq_key)
        updated, warnings = validate(updated)
        update_page(req.page_name, updated)
        return {"ok": True, "page": updated, "warnings": warnings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
