from pathlib import Path

# Load the original _Email.py content
email_path = Path("/mnt/data/_Email.py")
original_email_code = email_path.read_text()

# Modified version of the _Email.py script with HTML email content
modified_email_code = '''
import os
from mailjet_rest import Client

# Mailjet API credentials (use environment variables for security)
api_key = os.getenv("MJ_APIKEY_PUBLIC")
api_secret = os.getenv("MJ_APIKEY_PRIVATE")

# Mailjet client setup
mailjet = Client(auth=(api_key, api_secret), version='v3.1')

def send_change_notification(new_items, changed_items, deleted_items):
    def generate_html_section(title, items):
        if not items:
            return ""
        html = f"<h3>{title}</h3><ul>"
        for item in items:
            name = item.get("name", "Unnamed Substance")
            link_id = item.get("link_id")
            if link_id:
                url = f"https://echa.europa.eu/registry-of-clh-intentions-until-outcome/-/dislist/details/{link_id}"
                html += f'<li><a href="{url}">{name}</a></li>'
            else:
                html += f"<li>{name}</li>"
        html += "</ul>"
        return html

    # Construct HTML content
    html_content = "<h2>CLH Registry Update Detected</h2>"
    html_content += generate_html_section("🆕 New Substances", new_items)
    html_content += generate_html_section("✏️ Changed Substances", changed_items)
    html_content += generate_html_section("❌ Deleted Substances", deleted_items)

    data = {
        'Messages': [
            {
                "From": {
                    "Email": os.getenv("SENDER_EMAIL"),
                    "Name": "HazSnap Notifier"
                },
                "To": [
                    {
                        "Email": os.getenv("RECIPIENT_EMAIL"),
                        "Name": "Regulatory Team"
                    }
                ],
                "TemplateID": int(os.getenv("MJ_TEMPLATE_ID")),
                "TemplateLanguage": True,
                "Subject": "⚠️ CLH Registry Update Detected",
                "Variables": {
                    "content": html_content
                }
            }
        ]
    }

    result = mailjet.send.create(data=data)
    return result.status_code, result.json()
'''

# Save the modified version
modified_path = Path("/mnt/data/_Email_modified.py")
modified_path.write_text(modified_email_code)

modified_path.name  # Return filename for user reference

