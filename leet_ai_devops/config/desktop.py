from frappe import _

def get_data():
    return [
        {
            "label": _("AI DevOps"),
            "icon": "octicon octicon-tools",
            "items": [
                {
                    "type": "doctype",
                    "name": "AI DevOps Settings",
                    "label": _("AI DevOps Settings")
                },
                {
                    "type": "doctype",
                    "name": "Chat Session",
                    "label": _("Chat Session")
                }
            ]
        }
    ]