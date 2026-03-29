# AI Page Builder for Frappe

Describe a page in plain English. Get a fully structured Frappe Builder page in seconds.

Type something like _"a dark SaaS landing page with pricing table and hero"_ and the app generates valid Frappe Builder JSON, imports it into your site, and opens it ready to edit — no JSON writing, no drag-and-drop from scratch. Helps get a head start with your ideas as you type them and form a visual representation making it easier to build your website.

## The Problem
Frappe is an incredible framework, but the Frappe Builder requires developers to manually construct pages block-by-block. Designing layouts, configuring base styles, and structuring the nested JSON DOM by hand is tedious and creates a bottleneck when you just need to rapidly prototype a landing page or dashboard. 

## The Solution
This tool acts as a bridge between LLMs and the Frappe Builder. Instead of dragging and dropping or writing raw JSON, developers can type a single prompt to generate a fully compliant, natively structured Frappe Builder layout that imports in one click.

## How it works

1. You describe a page in plain English
2. An LLM (local Ollama or any API key you have) generates Frappe Builder-compatible JSON
3. The page is imported directly into Frappe Builder on your site
4. You can refine it with follow-up instructions

## Supported LLM providers

- **Local Ollama** — runs on your machine, no API key needed (requires Ollama installed)
- **Groq** — fast, free tier available
- **OpenAI** — gpt-4o-mini
- **Gemini** — gemini-2.5-flash

## ⚖️ Architecture & Compliance

This project was built with the FOSS Hackathon core rules in mind, specifically the requirement that **core functionality must not depend on closed-source software or proprietary APIs.**

* **The Core:** The default engine for this project is **Local Ollama** running the open-weight `Llama 3.1` model. Any user with capable hardware can run this entire pipeline 100% locally, offline, and without vendor lock-in. 
* **Hardware Inclusivity (The Fallbacks):** Generating strictly structured, complex JSON layouts is a highly demanding task for an LLM. For developers running on low-end hardware (where local generation might crash or produce malformed JSON), I have included optional fallback integrations for cloud APIs (Groq, Gemini, OpenAI). 

These cloud providers are strictly **optional enhancements** for accessibility and speed, not dependencies. The application's architecture proves the workflow is fully viable using only FOSS tools.


## Installation

### Option 1 — Frappe App (recommended)

If you already have Frappe with Frappe Builder installed:

```bash
bench get-app https://github.com/jeffrgh/foss-hack-26
bench --site yoursite install-app ai_page_builder
```

Then go to `yoursite/ai-page-builder`.

If you want Ollama to work, install it from [ollama.com](https://ollama.com) and pull a model:
```bash
ollama pull llama3.1
```

If you don't have Ollama, just use a Groq or Gemini API key in the UI — both have free tiers.

### Option 2 — Standalone

You still need Frappe running somewhere to import pages into or just get the json and use it anywhere else, but the UI runs separately.

```bash
git clone https://github.com/jeffrgh/foss-hack-26
cd foss-hack-26/standalone
pip install -r requirements.txt
```

Terminal 1:
```bash
python api.py
```

Terminal 2:
```bash
streamlit run app.py
```

Open `localhost:8501`.

## Dependencies

The Frappe app installs these automatically via bench:
```
groq
openai
google-generativeai
requests
```

For standalone, they're in `standalone/requirements.txt`.

## LLM Attribution
Various Large Language Models (including Gemini, claude and local Ollama models) were utilized during the development of this project to assist with Streamlit UI boilerplate generation, debugging Frappe framework routing integrations, and refining the JSON parsing logic.


## License

MIT