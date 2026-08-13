import os
import xmlrpc.client
from dotenv import load_dotenv

load_dotenv()

ODOO_URL = os.getenv("ODOO_URL")
ODOO_DB = os.getenv("ODOO_DB")
ODOO_USER = os.getenv("ODOO_USER")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD")

common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})

if not uid:
    raise Exception("Odoo authentication failed. Check .env values.")

models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")

def search_read(model, domain, fields, limit=10):
    return models.execute_kw(
        ODOO_DB,
        uid,
        ODOO_PASSWORD,
        model,
        "search_read",
        [domain],
        {"fields": fields, "limit": limit}
    )