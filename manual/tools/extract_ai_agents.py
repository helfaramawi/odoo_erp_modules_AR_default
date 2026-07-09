#!/usr/bin/env python3
"""
Extractor for the AI Agents module family, supplied separately by the client
as addons.zip (not part of the odoo_deployment_ar/addons tree tracked in this
repo). Reuses the exact same AST/XML/CSV parsing functions as
extract_modules.py so the AI agents get the identical level of rigor as the
other 47 modules, but writes to its own output file
(manual/tools/ai_agents_data.json) so it does not touch modules_data.json —
and therefore does not affect Chapter 6/8/13 of the System Manual or any
handbook chapter other than Chapter 10 (AI Agents).

Usage: python3 manual/tools/extract_ai_agents.py <path-to-extracted-addons-dir>
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_modules import (read_manifest, extract_models_from_file,
                              extract_xml_items, extract_acl_csv)

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_agents_data.json")

AI_MODULE_NAMES = [
    "port_said_ai_agents_menu",
    "port_said_arabic_ai_assistant",
    "gov_ai_guide",
    "port_said_budget_ai_agent",
    "port_said_budget_forecast_ai_agent",
    "port_said_budget_reallocation_ai_agent",
    "port_said_commitment_ai_agent",
    "port_said_conflict_interest_ai_agent",
    "port_said_daftar55_reconcile_ai_agent",
    "port_said_dead_stock_ai_agent",
    "port_said_dossier_ai_agent",
    "port_said_duplicate_claim_ai_agent",
    "port_said_eta_retry_ai_agent",
    "port_said_executive_briefing_ai_agent",
    "port_said_payment_anomaly_ai_agent",
    "port_said_payment_cycle_delay_ai_agent",
    "port_said_procurement_legal_compliance_ai_agent",
    "port_said_procurement_splitting_ai_agent",
    "port_said_vendor_data_quality_ai_agent",
    "port_said_vendor_penalty_ai_agent",
    "port_said_vendor_performance_ai_agent",
    "procurement_adjudication_ai_agent",
]


def rel(addons_dir, path):
    return os.path.relpath(path, addons_dir)


def extract_one(addons_dir, entry):
    module_path = os.path.join(addons_dir, entry)
    if not os.path.isdir(module_path):
        return None
    manifest = read_manifest(module_path)
    if manifest is None:
        return None

    models = []
    models_dir = os.path.join(module_path, "models")
    if os.path.isdir(models_dir):
        for fname in sorted(os.listdir(models_dir)):
            if fname.endswith(".py") and fname != "__init__.py":
                models.extend(extract_models_from_file(os.path.join(models_dir, fname)))
    for fname in os.listdir(module_path):
        if fname.endswith("_models.py"):
            models.extend(extract_models_from_file(os.path.join(module_path, fname)))
    for m in models:
        if m.get("source_file"):
            m["source_file"] = os.path.relpath(
                os.path.join(models_dir if os.path.isdir(models_dir) else module_path,
                             os.path.basename(m["source_file"])),
                addons_dir)

    menus, actions, reports, views, buttons = [], [], [], [], []
    rules, crons, sequences, config_params, server_actions = [], [], [], [], []
    for sub in ("views", "report", "reports", "wizard", "data", "security", "controllers"):
        subdir = os.path.join(module_path, sub)
        if os.path.isdir(subdir):
            for fname in sorted(os.listdir(subdir)):
                if fname.endswith(".xml"):
                    d = extract_xml_items(os.path.join(subdir, fname))
                    menus.extend(d["menus"]); actions.extend(d["actions"])
                    reports.extend(d["reports"]); views.extend(d["views"])
                    buttons.extend(d["buttons"]); rules.extend(d["rules"])
                    crons.extend(d["crons"]); sequences.extend(d["sequences"])
                    config_params.extend(d["config_params"]); server_actions.extend(d["server_actions"])

    wizards = []
    wizard_dir = os.path.join(module_path, "wizard")
    if os.path.isdir(wizard_dir):
        for fname in sorted(os.listdir(wizard_dir)):
            if fname.endswith(".py") and fname != "__init__.py":
                wizards.extend(extract_models_from_file(os.path.join(wizard_dir, fname)))

    security_files = []
    acl_rows = []
    security_dir = os.path.join(module_path, "security")
    if os.path.isdir(security_dir):
        security_files = sorted(os.listdir(security_dir))
        acl_path = os.path.join(security_dir, "ir.model.access.csv")
        if os.path.isfile(acl_path):
            acl_rows = extract_acl_csv(acl_path)

    # Python files at top level / controllers (agents often keep their core
    # detection/LLM-call logic in a flat file or controllers/, not models/)
    top_level_py = sorted(
        f for f in os.listdir(module_path)
        if f.endswith(".py") and f != "__init__.py" and os.path.isfile(os.path.join(module_path, f))
    )
    controller_py = []
    controllers_dir = os.path.join(module_path, "controllers")
    if os.path.isdir(controllers_dir):
        controller_py = sorted(f for f in os.listdir(controllers_dir) if f.endswith(".py") and f != "__init__.py")

    all_files = []
    for root, _, files in os.walk(module_path):
        for f in files:
            if not f.startswith("__pycache__"):
                all_files.append(os.path.relpath(os.path.join(root, f), module_path))

    return {
        "manifest": manifest,
        "models": models,
        "wizards": wizards,
        "menus": menus,
        "actions": actions,
        "reports": reports,
        "views": views,
        "buttons": buttons,
        "security_files": security_files,
        "acl_rows": acl_rows,
        "record_rules": rules,
        "cron_jobs": crons,
        "sequences": sequences,
        "config_params": config_params,
        "server_actions": server_actions,
        "top_level_py": top_level_py,
        "controller_py": controller_py,
        "all_files": sorted(all_files),
    }


def main():
    if len(sys.argv) < 2:
        print("usage: extract_ai_agents.py <addons_dir>")
        sys.exit(1)
    addons_dir = sys.argv[1]

    modules = {}
    for entry in AI_MODULE_NAMES:
        data = extract_one(addons_dir, entry)
        if data is not None:
            modules[entry] = data
        else:
            print(f"WARNING: module not found or unparsable: {entry}")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(modules, f, ensure_ascii=False, indent=2)
    print(f"Extracted {len(modules)} AI agent modules -> {OUT_PATH}")


if __name__ == "__main__":
    main()
