import os
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from odoo_client import search_read

load_dotenv()

app = FastAPI(title="Odoo AI Agent")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1")

class AskRequest(BaseModel):
    question: str

def ask_ollama(prompt: str):
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": LLM_MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=300
    )
    response.raise_for_status()
    return response.json().get("response", "")

@app.get("/")
def home():
    return {"status": "Odoo AI Agent Running", "model": LLM_MODEL}

@app.get("/customers")
def customers():
    return search_read(
        "res.partner",
        [["customer_rank", ">", 0]],
        ["name", "email", "phone"],
        limit=10
    )

@app.get("/products")
def products():
    return search_read(
        "product.product",
        [],
        ["name", "qty_available", "list_price"],
        limit=10
    )

@app.get("/low-stock")
def low_stock():
    products = search_read(
        "product.product",
        [["qty_available", "<=", 10]],
        ["name", "qty_available", "list_price"],
        limit=20
    )
    return products

@app.post("/ask")
def ask(req: AskRequest):
    q = req.question.lower()

    if "customer" in q or "client" in q:
        data = customers()
        prompt = f"""
You are an intelligent on-premises Odoo ERP assistant.

Answer the user clearly and professionally.
Use ONLY the Odoo data below.
Do not invent missing information.

User question:
{req.question}

Odoo customer data:
{data}
"""
        return {
            "question": req.question,
            "source": "Odoo / res.partner",
            "answer": ask_ollama(prompt),
            "raw_data": data
        }

    if "product" in q or "stock" in q or "inventory" in q:
        data = products()
        prompt = f"""
You are an on-premises Odoo ERP inventory analyst.

Use ONLY the Odoo data below.

Create a professional inventory summary with:
1. Total number of products.
2. Products out of stock.
3. Products with available stock.
4. Products with high quantity.
5. Short recommendation.

User question:
{req.question}

Odoo product data:
{data}
"""
        return {
            "question": req.question,
            "source": "Odoo / product.product",
            "answer": ask_ollama(prompt),
            "raw_data": data
        }

    prompt = f"""
You are an on-premises Odoo ERP assistant.

Currently you can answer questions about:
- customers
- products
- stock / inventory

User question:
{req.question}

Explain politely what you can help with.
"""
    return {
        "question": req.question,
        "answer": ask_ollama(prompt)
    }