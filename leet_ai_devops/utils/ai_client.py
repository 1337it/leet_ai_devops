import os
import frappe
from openai import OpenAI

def get_openai_client():
    # prefer settings; fallback to env
    settings = frappe.get_single("AI DevOps Settings")
    api_key = (settings.openai_api_key or "").strip() or os.getenv("OPENAI_API_KEY")
    if not api_key:
        frappe.throw("OpenAI API Key is not set. Add it in AI DevOps Settings or environment.")
    return OpenAI(api_key=api_key)

def generate_changes(prompt: str, target_app: str, model: str, temperature: float, max_tokens: int) -> dict:
    """
    Ask the model to return a strict JSON describing proposed code changes.

    Expected JSON schema:
    {
      "changes": [
        {
          "file_path": "apps/<appname>/<subpath>/.../file.py",
          "change_type": "new|edit|delete",
          "description": "what and why",
          "language": "python|json|js|css|md|txt",
          "content": "full new file content OR full updated content (for edit/new). Empty for delete."
        }
      ]
    }
    """
    client = get_openai_client()

    system = f"""You are an expert Frappe developer assistant. You will propose file-level changes for the selected app '{target_app}'. 
Return ONLY JSON with a top-level key 'changes' following the schema described. For 'edit', return the FULL desired file content (not a patch). 
Keep file paths relative to the bench folder and ensure they reside within the '{target_app}' app directory.
"""

    user = f"""User Request / Prompt:
{prompt}

Target app: {target_app}
"""

    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[
            {"role":"system","content":system},
            {"role":"user","content":user},
        ]
    )

    import json
    # handle model output robustly
    txt = resp.choices[0].message.content.strip()
    # Try to extract JSON block
    try:
        data = json.loads(txt)
    except Exception:
        # attempt to find JSON in fenced block
        import re
        m = re.search(r"\{[\s\S]*\}", txt)
        if not m:
            frappe.throw("Model did not return valid JSON changes. Try refining the prompt.")
        data = json.loads(m.group(0))
    if "changes" not in data or not isinstance(data["changes"], list):
        frappe.throw("Invalid AI response: missing 'changes' list.")
    return data