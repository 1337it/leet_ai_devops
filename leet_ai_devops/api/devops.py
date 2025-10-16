import frappe
from frappe import _
from leet_ai_devops.utils.ai_client import generate_changes
from leet_ai_devops.utils.file_ops import (
    get_app_root, read_file_if_exists, compute_diff, apply_change, git_commit
)

@frappe.whitelist()
def generate_proposed_changes(chat_session: str):
    doc = frappe.get_doc("Chat Session", chat_session)
    settings = frappe.get_single("AI DevOps Settings")
    target_app = doc.target_app or settings.target_app
    if not target_app:
        frappe.throw("Target App is not set. Set it in AI DevOps Settings or this Chat Session.")

    if not doc.latest_prompt:
        frappe.throw("No prompt provided.")

    data = generate_changes(
        prompt=doc.latest_prompt,
        target_app=target_app,
        model=settings.model or "gpt-4o-mini",
        temperature=settings.temperature or 0.2,
        max_tokens=int(settings.max_tokens or 3000),
    )

    app_root = get_app_root(target_app)
    # clear previous Proposed Changes for this prompt run? We'll append, keeping history.
    for change in data["changes"]:
        rel_path = _normalize_rel_path(change.get("file_path",""), target_app)
        change_type = (change.get("change_type") or "edit").lower()
        content = change.get("content") or ""
        description = change.get("description") or ""
        existing = read_file_if_exists(_safe_join(app_root, rel_path))
        diff_text = compute_diff(existing, content, rel_path)

        row = doc.append("proposed_changes", {})
        row.file_path = rel_path
        row.change_type = change_type
        row.description = description
        row.diff = diff_text
        row.new_content = content
        row.applied = 0

    doc.save()
    return {"ok": True, "added": len(data["changes"])}

def _safe_join(base, rel):
    import os
    return os.path.realpath(os.path.join(base, rel))

def _normalize_rel_path(path: str, target_app: str) -> str:
    # Accepts paths like "apps/<app>/..." or just "<subpath>"; returns a path relative to the app root.
    import os
    path = path.replace("\\", "/").strip().lstrip("/")
    parts = path.split("/")
    # strip "apps/<app>/" prefix if present
    if len(parts) >= 3 and parts[0] == "apps" and parts[1] == target_app:
        return "/".join(parts[2:])
    # if path starts with the app name, strip it
    if len(parts) >= 1 and parts[0] == target_app:
        return "/".join(parts[1:])
    return path

@frappe.whitelist()
def apply_change_row(rowname: str):
    row = frappe.get_doc("Proposed Change", rowname)
    parent = frappe.get_doc("Chat Session", row.parent)
    settings = frappe.get_single("AI DevOps Settings")
    target_app = parent.target_app or settings.target_app
    if not target_app:
        frappe.throw("Target App is not set.")

    app_root = get_app_root(target_app)

    result = apply_change(app_root, row.file_path, row.change_type, row.new_content or "")
    row.applied = 1
    row.apply_log = f"{result}"
    row.save()

    if (settings.apply_mode or "Dry-run") == "Write & Commit":
        msg = git_commit(
            app_root,
            message=f"[leet_ai_devops] {row.change_type} {row.file_path}",
            author_name=settings.git_author_name,
            author_email=settings.git_author_email,
            branch=settings.default_branch,
        )
        return {"ok": True, "result": result, "git": msg}

    return {"ok": True, "result": result}

@frappe.whitelist()
def apply_all(chat_session: str):
    doc = frappe.get_doc("Chat Session", chat_session)
    settings = frappe.get_single("AI DevOps Settings")
    target_app = doc.target_app or settings.target_app
    if not target_app:
        frappe.throw("Target App is not set.")

    app_root = get_app_root(target_app)
    applied_count = 0
    for row in doc.proposed_changes:
        if row.applied:
            continue
        res = apply_change(app_root, row.file_path, row.change_type, row.new_content or "")
        row.applied = 1
        row.apply_log = f"{res}"
        applied_count += 1
    doc.save()

    git_msg = None
    if (settings.apply_mode or "Dry-run") == "Write & Commit" and applied_count:
        git_msg = git_commit(
            app_root,
            message=f"[leet_ai_devops] applied {applied_count} changes",
            author_name=settings.git_author_name,
            author_email=settings.git_author_email,
            branch=settings.default_branch,
        )

    return {"ok": True, "applied": applied_count, "git": git_msg}