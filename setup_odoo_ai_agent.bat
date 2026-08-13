@echo off
setlocal

echo ================================
echo Odoo AI Agent Local Setup
echo ================================

set PROJECT=odoo_ai_agent
set ODOO_URL=http://localhost:8069
set ODOO_DB=odoo17
set ODOO_USER=admin
set ODOO_PASSWORD=admin
set OLLAMA_URL=http://localhost:11434
set LLM_MODEL=llama3.1

where python >nul 2>&1 || (
    echo Python is not installed or not in PATH.
    pause
    exit /b
)

where ollama >nul 2>&1 || (
    echo Ollama is not installed. Please install Ollama first.
    echo https://ollama.com
    pause
    exit /b
)

echo Pulling local AI model...
ollama pull %LLM_MODEL%

echo Creating project...
mkdir %PROJECT%
cd %PROJECT%

echo Creating virtual environment...
python -m venv venv

call venv\Scripts\activate

echo Installing Python packages...
pip install fastapi uvicorn requests python-dotenv pydantic

echo Creating .env file...
(
echo ODOO_URL=%ODOO_URL%
echo ODOO_DB=%ODOO_DB%
echo ODOO_USER=%ODOO_USER%
echo ODOO_PASSWORD=%ODOO_PASSWORD%
echo OLLAMA_URL=%OLLAMA_URL%
echo LLM_MODEL=%LLM_MODEL%
) > .env

echo Creating Odoo connector...
(
echo import os
echo import xmlrpc.client
echo from dotenv import load_dotenv
echo.
echo load_dotenv()
echo.
echo url = os.getenv("ODOO_URL")
echo db = os.getenv("ODOO_DB")
echo user = os.getenv("ODOO_USER")
echo password = os.getenv("ODOO_PASSWORD")
echo.
echo common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
echo uid = common.authenticate(db, user, password, {})
echo.
echo if not uid:
echo     raise Exception("Odoo authentication failed. Check .env values.")
echo.
echo models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
echo.
echo def search_read(model, domain, fields, limit=10):
echo     return models.execute_kw(
echo         db, uid, password,
echo         model, "search_read",
echo         [domain],
echo         {"fields": fields, "limit": limit}
echo     )
) > odoo_client.py

echo Creating AI Agent API...
(
echo import os
echo import requests
echo from fastapi import FastAPI
echo from pydantic import BaseModel
echo from dotenv import load_dotenv
echo from odoo_client import search_read
echo.
echo load_dotenv()
echo app = FastAPI(title="Odoo AI Agent")
echo.
echo class AskRequest(BaseModel):
echo     question: str
echo.
echo def ask_llm(prompt):
echo     r = requests.post(
echo         f"{os.getenv('OLLAMA_URL')}/api/generate",
echo         json={
echo             "model": os.getenv("LLM_MODEL"),
echo             "prompt": prompt,
echo             "stream": False
echo         }
echo     )
echo     r.raise_for_status()
echo     return r.json()["response"]
echo.
echo @app.get("/")
echo def home():
echo     return {"status": "Odoo AI Agent is running"}
echo.
echo @app.post("/ask")
echo def ask(req: AskRequest):
echo     q = req.question.lower()
echo.
echo     if "customer" in q or "client" in q:
echo         data = search_read(
echo             "res.partner",
echo             [["customer_rank", ">", 0]],
echo             ["name", "email", "phone"],
echo             limit=10
echo         )
echo         prompt = f"""
echo You are an on-premises Odoo ERP assistant.
echo Answer only using the provided Odoo data.
echo Do not invent information.
echo.
echo Question:
echo {req.question}
echo.
echo Odoo Data:
echo {data}
echo """
echo         return {"answer": ask_llm(prompt), "data": data}
echo.
echo     if "product" in q or "stock" in q:
echo         data = search_read(
echo             "product.product",
echo             [],
echo             ["name", "qty_available", "list_price"],
echo             limit=10
echo         )
echo         prompt = f"""
echo You are an Odoo inventory assistant.
echo Answer only using this product data.
echo.
echo Question:
echo {req.question}
echo.
echo Product Data:
echo {data}
echo """
echo         return {"answer": ask_llm(prompt), "data": data}
echo.
echo     return {"answer": ask_llm(req.question)}
) > main.py

echo Creating run file...
(
echo @echo off
echo call venv\Scripts\activate
echo uvicorn main:app --reload --port 8000
echo pause
) > run_agent.bat

echo ================================
echo Setup completed successfully.
echo ================================
echo.
echo IMPORTANT:
echo Edit .env file and set your real:
echo ODOO_DB
echo ODOO_USER
echo ODOO_PASSWORD
echo.
echo Then run:
echo run_agent.bat
echo.
echo Open:
echo http://localhost:8000
echo http://localhost:8000/docs
echo ================================

pause