#!/usr/bin/env python3
"""
Static extractor for Odoo addon metadata used to ground Chapter 6 (Customized
Programs) of the Arabic System Manual in the real codebase instead of invented
content.

For every addon under odoo_deployment_ar/addons/<module>/ it collects:
  - manifest data (name, summary, depends, category, version, data files)
  - models defined in models/*.py (via ast, no odoo runtime required):
      _name / _inherit, _description, and field definitions
        (name, field type, string=, required=, help=, selection=, comodel_name=)
  - menu items and window actions declared in views/*.xml
  - report actions (ir.actions.report) declared in views/*.xml or report/*.xml

Output: manual/tools/modules_data.json
"""
import ast
import json
import os
import re
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ADDONS_DIR = os.path.join(ROOT, "odoo_deployment_ar", "addons")
OUT_PATH = os.path.join(ROOT, "manual", "tools", "modules_data.json")

FIELD_CALL_RE = re.compile(r"fields\.(\w+)")


def read_manifest(module_path):
    manifest_path = os.path.join(module_path, "__manifest__.py")
    if not os.path.isfile(manifest_path):
        return None
    with open(manifest_path, encoding="utf-8") as f:
        src = f.read()
    try:
        data = ast.literal_eval(src)
    except Exception:
        # fall back to a very forgiving eval sandbox
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
            "fields": [],
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
                        for kw in stmt.value.keywords or []:
                            if kw.arg == "string":
                                fstring = literal_or_none(kw.value)
                            elif kw.arg == "required":
                                required = literal_or_none(kw.value)
                            elif kw.arg == "comodel_name":
                                comodel = literal_or_none(kw.value)
                            elif kw.arg == "selection":
                                selection = literal_or_none(kw.value)
                        # positional comodel for many2one/one2many/many2many
                        if comodel is None and stmt.value.args:
                            comodel = literal_or_none(stmt.value.args[0])
                        # positional selection list for fields.Selection([...])
                        if selection is None and ftype == "Selection" and stmt.value.args:
                            selection = literal_or_none(stmt.value.args[0])
                        model_info["fields"].append({
                            "name": target,
                            "type": ftype,
                            "string": fstring,
                            "required": bool(required),
                            "comodel": comodel,
                            "selection": selection,
                        })
        models.append(model_info)
    return models


def extract_xml_items(path):
    menus, actions, reports, views = [], [], [], []
    buttons = []
    try:
        tree = ET.parse(path)
    except Exception:
        return menus, actions, reports, views, buttons
    root = tree.getroot()
    for el in root.iter():
        tag = el.tag
        if tag == "button":
            name = el.get("name")
            string = el.get("string")
            btype = el.get("type")
            states = el.get("states") or el.get("invisible")
            if name or string:
                buttons.append({
                    "name": name, "string": string, "type": btype,
                    "states": states,
                })
        if tag == "menuitem":
            menus.append({
                "id": el.get("id"),
                "name": el.get("name"),
                "parent": el.get("parent"),
                "action": el.get("action"),
                "sequence": el.get("sequence"),
            })
        elif tag == "record":
            model = el.get("model")
            rec_id = el.get("id")
            if model == "ir.actions.act_window":
                name_f = el.find("./field[@name='name']")
                res_model_f = el.find("./field[@name='res_model']")
                view_mode_f = el.find("./field[@name='view_mode']")
                actions.append({
                    "id": rec_id,
                    "name": name_f.text if name_f is not None else None,
                    "res_model": res_model_f.text if res_model_f is not None else None,
                    "view_mode": view_mode_f.text if view_mode_f is not None else None,
                })
            elif model == "ir.actions.report":
                name_f = el.find("./field[@name='name']")
                model_f = el.find("./field[@name='model']")
                report_type_f = el.find("./field[@name='report_type']")
                reports.append({
                    "id": rec_id,
                    "name": name_f.text if name_f is not None else None,
                    "model": model_f.text if model_f is not None else None,
                    "report_type": report_type_f.text if report_type_f is not None else None,
                })
            elif model == "ir.ui.view":
                name_f = el.find("./field[@name='name']")
                model_f = el.find("./field[@name='model']")
                views.append({
                    "id": rec_id,
                    "name": name_f.text if name_f is not None else None,
                    "model": model_f.text if model_f is not None else None,
                })
    return menus, actions, reports, views, buttons


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

        # some modules keep a flat model file
        for fname in os.listdir(module_path):
            if fname.endswith("_models.py"):
                models.extend(extract_models_from_file(os.path.join(module_path, fname)))

        menus, actions, reports, views, buttons = [], [], [], [], []
        for sub in ("views", "report", "reports", "wizard", "data", "security"):
            subdir = os.path.join(module_path, sub)
            if os.path.isdir(subdir):
                for fname in sorted(os.listdir(subdir)):
                    if fname.endswith(".xml"):
                        m, a, r, v, b = extract_xml_items(os.path.join(subdir, fname))
                        menus.extend(m)
                        actions.extend(a)
                        reports.extend(r)
                        views.extend(v)
                        buttons.extend(b)

        wizards = []
        wizard_dir = os.path.join(module_path, "wizard")
        if os.path.isdir(wizard_dir):
            for fname in sorted(os.listdir(wizard_dir)):
                if fname.endswith(".py") and fname != "__init__.py":
                    wizards.extend(extract_models_from_file(os.path.join(wizard_dir, fname)))

        security_files = []
        security_dir = os.path.join(module_path, "security")
        if os.path.isdir(security_dir):
            security_files = sorted(os.listdir(security_dir))

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
        }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(modules, f, ensure_ascii=False, indent=2)
    print(f"Extracted {len(modules)} modules -> {OUT_PATH}")


if __name__ == "__main__":
    main()
