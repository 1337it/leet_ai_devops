import frappe

class ChatSession(frappe.model.document.Document):
    def before_save(self):
        # Keep latest_prompt mirrored as a 'user' message for history
        if self.latest_prompt:
            last = None
            if self.messages:
                last = self.messages[-1]
            if not last or last.role != "user" or (last and last.content != self.latest_prompt):
                row = self.append("messages", {})
                row.role = "user"
                row.content = self.latest_prompt