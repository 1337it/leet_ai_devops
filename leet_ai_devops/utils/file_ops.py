import os, io, difflib, subprocess
import frappe
from git import Repo

def get_app_root(app_name: str) -> str:
    app_path = frappe.get_app_path(app_name)
    return app_path  # absolute path like /home/frappe/frappe-bench/apps/<app>

def is_path_within(base: str, candidate: str) -> bool:
    base = os.path.realpath(base)
    cand = os.path.realpath(candidate)
    return os.path.commonpath([base]) == os.path.commonpath([base, cand])

def compute_diff(existing: str, new: str, path: str) -> str:
    existing_lines = (existing or "").splitlines(keepends=True)
    new_lines = (new or "").splitlines(keepends=True)
    diff = difflib.unified_diff(existing_lines, new_lines, fromfile=f"a/{path}", tofile=f"b/{path}")
    return "".join(diff)

def read_file_if_exists(full_path: str) -> str:
    if os.path.exists(full_path) and os.path.isfile(full_path):
        with io.open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    return ""

def write_file(full_path: str, content: str):
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with io.open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

def apply_change(base_app_path: str, rel_file_path: str, change_type: str, new_content: str):
    full_path = os.path.join(base_app_path, rel_file_path)
    if not is_path_within(base_app_path, full_path):
        frappe.throw(f"Refusing to write outside app path: {rel_file_path}")

    if change_type == "delete":
        if os.path.exists(full_path):
            os.remove(full_path)
        return "deleted"
    elif change_type in ("new","edit"):
        write_file(full_path, new_content or "")
        return "written"
    else:
        frappe.throw(f"Unknown change_type: {change_type}")

def git_commit(app_root: str, message: str, author_name: str=None, author_email: str=None, branch: str=None):
    repo_root = os.path.realpath(os.path.join(app_root, ".."))  # app lives in apps/<app>, repo is usually bench root or app repo
    # Try to find nearest git repo starting from app_root
    repo_path = app_root
    while repo_path != "/":
        if os.path.isdir(os.path.join(repo_path, ".git")):
            break
        repo_path = os.path.dirname(repo_path)

    if not os.path.isdir(os.path.join(repo_path, ".git")):
        return "No git repo found; skipped commit."

    repo = Repo(repo_path)
    if branch:
        try:
            repo.git.checkout(branch)
        except Exception:
            pass  # ignore if branch not present

    repo.git.add(all=True)
    if author_name and author_email:
        repo.index.commit(message, author=f"{author_name} <{author_email}>")
    else:
        repo.index.commit(message)
    return f"Committed in {repo_path}"