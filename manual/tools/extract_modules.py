#!/usr/bin/env python3
"""
Static extractor for Odoo addon metadata, used to ground both the Arabic
System Manual (Chapter 6/8/13) and the Setup & Configuration Handbook in the
real codebase instead of invented content.

For every addon under odoo_deployment_ar/addons/<module>/ it collects, via
AST (Python) and ElementTree/csv (XML/CSV) parsing — no Odoo runtime needed:

  - manifest data (name, summary, depends, category, version, data files)
  - models defined in models/*.py and wizard/*.py:
      _name / _inherit, _description, source file (relative path), fields
      (name, type, string=, required=, help=, selection=, comodel_name=),
      _sql_constraints, and @api.constrains'd field names
  - menu items, window actions, report actions, view records (views/*.xml)
  - buttons declared in form views
  - ir.model.access.csv rows (full CRUD matrix per group per model)
  - ir.rule record rules (name, model, domain_force, groups)
  - ir.cron scheduled actions (name, model, interval, active)
  - ir.sequence definitions (name, code, prefix, padding)
  - ir.config_parameter entries (key/value)
  - ir.actions.server / base.automation records

Output: manual/tools/modules_data.json
"""
import ast
import csv
import json
import os
import re
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ADDONS_DIR = os.path.join(ROOT, "odoo_deployment_ar", "addons")
OUT_PATH = os.path.join(ROOT, "manual", "tools", "modules_data.json")


def rel(path):
    return os.path.relpath(path, ADDONS_DIR)


def read_manifest(module_path):
    manifest_path = os.path.join(module_path, "__manifest__.py")
    if not os.path.isfile(manifest_path):
        return None
    with open(manifest_path, encoding="utf-8") as f:
        src = f.read()
    try:
        data = ast.literal_eval(src)
    except Exception:
        try:
            data = eval(src, {"__builtins__": {}})
        except Exception:
            return {"_parse_error": True}
    return data


def literal_or_none(node):
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def extract_models_from_file(path):
    models = []
    try:
        with open(path, encoding="utf-8") as f:
            src = f.read()
        tree = ast.parse(src, filename=path)
    except Exception:
        return models

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        is_model = False
        for base in node.bases:
            try:
                b = ast.unparse(base)
            except Exception:
                b = ast.dump(base)
            if b in ("models.Model", "models.TransientModel", "models.AbstractModel"):
                is_model = True
        if not is_model:
            continue

        model_info = {
            "class_name": node.name,
            "_name": None,
            "_inherit": None,
            "_description": None,
            "source_file": rel(path),
            "fields": [],
            "sql_constraints": [],
            "constrains_methods": [],
        }
        for stmt in node.body:
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                target = stmt.targets[0].id
                if target == "_name":
                    model_info["_name"] = literal_or_none(stmt.value)
                elif target == "_inherit":
                    model_info["_inherit"] = literal_or_none(stmt.value)
                elif target == "_description":
                    model_info["_description"] = literal_or_none(stmt.value)
                elif target == "_sql_constraints":
                    val = literal_or_none(stmt.value)
                    if val:
                        model_info["sql_constraints"] = [
                            {"name": c[0], "constraint": c[1], "message": c[2]} for c in val
                        ]
                elif isinstance(stmt.value, ast.Call):
                    call_src = ast.dump(stmt.value.func)
                    if "fields" in call_src:
                        ftype = None
                        if isinstance(stmt.value.func, ast.Attribute):
                            ftype = stmt.value.func.attr
                        fstring = None
                        required = False
                        comodel = None
                        selection = None
                        help_text = None
                        for kw in stmt.value.keywords or []:
                            if kw.arg == "string":
                                fstring = literal_or_none(kw.value)
                            elif kw.arg == "required":
                                required = literal_or_none(kw.value)
                            elif kw.arg == "comodel_name":
                                comodel = literal_or_none(kw.value)
                            elif kw.arg == "selection":
                                selection = literal_or_none(kw.value)
                            elif kw.arg == "help":
                                help_text = literal_or_none(kw.value)
                        if comodel is None and stmt.value.args:
                            comodel = literal_or_none(stmt.value.args[0])
                        if selection is None and ftype == "Selection" and stmt.value.args:
                            selection = literal_or_none(stmt.value.args[0])
                        model_info["fields"].append({
                            "name": target,
                            "type": ftype,
                            "string": fstring,
                            "required": bool(required),
                            "comodel": comodel,
                            "selection": selection,
                            "help": help_text,
                        })
            elif isinstance(stmt, ast.FunctionDef):
                for dec in stmt.decorator_list:
                    dec_src = None
                    try:
                        dec_src = ast.unparse(dec)
                    except Exception:
                        pass
                    if dec_src and dec_src.startswith("api.constrains"):
                        args = []
                        if isinstance(dec, ast.Call):
                            args = [literal_or_none(a) for a in dec.args]
                        model_info["constrains_methods"].append({
                            "method": stmt.name, "fields": [a for a in args if a],
                        })
        models.append(model_info)
    return models


def extract_xml_items(path):
    menus, actions, reports, views = [], [], [], []
    buttons, rules, crons, sequences, config_params, server_actions = [], [], [], [], [], []
    try:
        tree = ET.parse(path)
    except Exception:
        return dict(menus=menus, actions=actions, reports=reports, views=views,
                    buttons=buttons, rules=rules, crons=crons, sequences=sequences,
                    config_params=config_params, server_actions=server_actions)
    root = tree.getroot()

    def field_text(el, name):
        f = el.find(f"./field[@name='{name}']")
        return f.text.strip() if f is not None and f.text else None

    def field_any(el, name):
        """ref attribute, then eval attribute, then text content — covers
        every way an Odoo XML data field's value can be expressed."""
        f = el.find(f"./field[@name='{name}']")
        if f is None:
            return None
        ref_attr = f.get("ref")
        if ref_attr is not None:
            return ref_attr
        eval_attr = f.get("eval")
        if eval_attr is not None:
            return eval_attr
        return f.text.strip() if f.text else None

    field_eval = field_any

    for el in root.iter():
        tag = el.tag
        if tag == "button":
            name = el.get("name")
            string = el.get("string")
            btype = el.get("type")
            states = el.get("states") or el.get("invisible")
            if name or string:
                buttons.append({"name": name, "string": string, "type": btype, "states": states})
        if tag == "menuitem":
            menus.append({
                "id": el.get("id"), "name": el.get("name"), "parent": el.get("parent"),
                "action": el.get("action"), "sequence": el.get("sequence"),
            })
        elif tag == "record":
            model = el.get("model")
            rec_id = el.get("id")
            if model == "ir.actions.act_window":
                actions.append({
                    "id": rec_id, "name": field_text(el, "name"),
                    "res_model": field_text(el, "res_model"), "view_mode": field_text(el, "view_mode"),
                })
            elif model == "ir.actions.report":
                reports.append({
                    "id": rec_id, "name": field_text(el, "name"),
                    "model": field_text(el, "model"), "report_type": field_text(el, "report_type"),
                })
            elif model == "ir.ui.view":
                views.append({"id": rec_id, "name": field_text(el, "name"), "model": field_text(el, "model")})
            elif model == "ir.rule":
                rules.append({
                    "id": rec_id, "name": field_text(el, "name"), "model_id": field_any(el, "model_id"),
                    "domain_force": field_text(el, "domain_force"),
                    "groups": field_any(el, "groups"),
                    "perm_read": field_any(el, "perm_read"), "perm_write": field_any(el, "perm_write"),
                    "perm_create": field_any(el, "perm_create"), "perm_unlink": field_any(el, "perm_unlink"),
                })
            elif model == "ir.cron":
                crons.append({
                    "id": rec_id, "name": field_text(el, "name"), "model_id": field_any(el, "model_id"),
                    "interval_number": field_text(el, "interval_number"),
                    "interval_type": field_text(el, "interval_type"),
                    "active": field_any(el, "active"),
                    "code": (field_text(el, "code") or "")[:200] or None,
                })
            elif model == "ir.sequence":
                sequences.append({
                    "id": rec_id, "name": field_text(el, "name"), "code": field_text(el, "code"),
                    "prefix": field_text(el, "prefix"), "padding": field_text(el, "padding"),
                })
            elif model == "ir.config_parameter":
                config_params.append({"id": rec_id, "key": field_text(el, "key"), "value": field_text(el, "value")})
            elif model == "ir.actions.server" or model == "base.automation":
                server_actions.append({
                    "id": rec_id, "model_record": model, "name": field_text(el, "name"),
                    "model_id": field_eval(el, "model_id"), "state": field_text(el, "state"),
                    "trigger": field_text(el, "trigger"),
                })
    return dict(menus=menus, actions=actions, reports=reports, views=views,
                buttons=buttons, rules=rules, crons=crons, sequences=sequences,
                config_params=config_params, server_actions=server_actions)


def extract_acl_csv(path):
    rows = []
    try:
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append({
                    "id": row.get("id"),
                    "name": row.get("name"),
                    "model_id": row.get("model_id:id"),
                    "group_id": row.get("group_id:id") or "",
                    "perm_read": row.get("perm_read"),
                    "perm_write": row.get("perm_write"),
                    "perm_create": row.get("perm_create"),
                    "perm_unlink": row.get("perm_unlink"),
                })
    except Exception:
        pass
    return rows


def main():
    modules = {}
    for entry in sorted(os.listdir(ADDONS_DIR)):
        module_path = os.path.join(ADDONS_DIR, entry)
        if not os.path.isdir(module_path):
            continue
        manifest = read_manifest(module_path)
        if manifest is None:
            continue

        models = []
        models_dir = os.path.join(module_path, "models")
        if os.path.isdir(models_dir):
            for fname in sorted(os.listdir(models_dir)):
                if fname.endswith(".py") and fname != "__init__.py":
                    models.extend(extract_models_from_file(os.path.join(models_dir, fname)))

        for fname in os.listdir(module_path):
            if fname.endswith("_models.py"):
                models.extend(extract_models_from_file(os.path.join(module_path, fname)))

        menus, actions, reports, views, buttons = [], [], [], [], []
        rules, crons, sequences, config_params, server_actions = [], [], [], [], []
        for sub in ("views", "report", "reports", "wizard", "data", "security"):
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

        modules[entry] = {
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
        }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(modules, f, ensure_ascii=False, indent=2)
    print(f"Extracted {len(modules)} modules -> {OUT_PATH}")


if __name__ == "__main__":
    main()
