import pandas as pd
from mailjet_rest import Client
import os
import requests

ESSENTIAL_COLS = ['Substance name', 'CAS no', 'Status', 'Submitter', 'Latest update']

def format_sample_html(df, title):
    df_reset = df.reset_index(drop=True)
    cols_to_show = [col for col in ESSENTIAL_COLS if col in df_reset.columns]
    df_display = df_reset[cols_to_show].head(5)

    table_html = df_display.to_html(index=False, escape=False, border=0, classes="styled-table")

    styles = """
    <style>
    .styled-table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
        font-size: 14px;
        font-family: Arial, sans-serif;
    }
    .styled-table th, .styled-table td {
        border: 1px solid #dddddd;
        text-align: left;
        padding: 6px;
        vertical-align: top;
        word-wrap: break-word;
    }
    .styled-table th {
        background-color: #f2f2f2;
        text-align: center;
    }
    .styled-table td:nth-child(1) { width: 30%; }
    .styled-table td:nth-child(2) { width: 12%; }
    .styled-table td:nth-child(3) { width: 18%; }
    .styled-table td:nth-child(4) { width: 15%; }
    .styled-table td:nth-child(5) { width: 15%; }
    </style>
    """

    return f"<h3>{title}</h3>{styles}{table_html}<br>"

def generate_email_body(new_df, removed_df, changed_df):
    new_count = len(new_df)
    removed_count = len(removed_df)
    changed_count = len(changed_df)

    summary = (
        f"🆕 New entries: {new_count}<br>"
        f"❌ Removed entries: {removed_count}<br>"
        f"🔄 Changed entries: {changed_count}<br>"
    )

    new_html = format_sample_html(new_df, "New Entries Sample") if new_count else ""
    removed_html = format_sample_html(removed_df, "Removed Entries Sample") if removed_count else ""
    changed_html = format_sample_html(changed_df, "Changed Entries Sample") if changed_count else ""

    full_html = f"{summary}<br>{new_html}{removed_html}{changed_html}"
    return full_html

def get_contacts_from_list(contact_list_id):
    api_key = os.getenv("MAILJET_API_KEY")
    api_secret = os.getenv("MAILJET_API_SECRET")

    mailjet = Client(auth=(api_key, api_secret), version='v3')

    # Step 1: Get all contacts
    response = mailjet.contact.get()
    if response.status_code != 200:
        raise Exception(f"Failed to fetch contacts: {response.status_code} {response.text}")

    all_contacts = response.json().get("Data", [])
    subscribed_contacts = []

    # Step 2: Check if each contact is in the desired list
    for contact in all_contacts:
        email = contact["Email"]
        check_url = f"https://api.mailjet.com/v3/REST/contact/{email}/getcontactslists"
        check_resp = requests.get(check_url, auth=(api_key, api_secret))

        if check_resp.status_code == 200:
            lists = check_resp.json().get("Data", [])
            for item in lists:
                if item["ListID"] == contact_list_id and item["IsUnsub"] is False:
                    subscribed_contacts.append({"Email": email, "Name": contact.get("Name", "")})
                    break  # No need to check further lists
        else:
            print(f"Warning: issue checking list for {email}: {check_resp.status_code}")

    return subscribed_contacts

def send_transactional_email(subject, html_content, footer_html, contact_list_id):
    api_key = os.getenv("MAILJET_API_KEY")
    api_secret = os.getenv("MAILJET_API_SECRET")
    sender_email = os.getenv("MAILJET_SENDER_EMAIL")

    mailjet = Client(auth=(api_key, api_secret), version='v3.1')

    contacts = get_contacts_from_list(contact_list_id)

    template_id = 7028286  # Your Mailjet transactional template ID

    for contact in contacts:
        data = {
            "Messages": [
                {
                    "From": {
                        "Email": sender_email,
                        "Name": "CLH Monitor"
                    },
                    "To": [
                        {
                            "Email": contact["Email"],
                            "Name": contact["Name"] or "Valued Recipient"
                        }
                    ],
                    "TemplateID": template_id,
                    "TemplateLanguage": True,
                    "Subject": subject,
                    "Variables": {
                        "content": html_content,
                        "footer": footer_html
                    }
                }
            ]
        }

        response = mailjet.send.create(data=data)
        print(f"Sent to {contact['Email']}: status {response.status_code}")
        if response.status_code != 200:
            print("Response content:", response.json())

if __name__ == "__main__":
    df_new = pd.DataFrame([
        {"Substance name": "Test Acid", "CAS no": "123-45-6", "Status": "Consultation", "Submitter": "Germany", "Latest update": "31-mai-2025"}
    ])
    df_removed = pd.DataFrame([
        {"Substance name": "Old Compound", "CAS no": "654-32-1", "Status": "Opinion Development", "Submitter": "France", "Latest update": "01-mai-2025"}
    ])
    df_changed = pd.DataFrame([
        {"Substance name": "Modified Agent", "CAS no": "111-22-3", "Status": "Opinion Development", "Submitter": "Sweden", "Latest update": "31-mai-2025"}
    ])

    body_html = generate_email_body(df_new, df_removed, df_changed)
    footer_html = "<p>CLH Monitor &copy; 2025</p>"

    subject = "🧪 CLH Changes Detected – 31 May 2025"
    contact_list_id = 10530945  # Your contact list ID

    send_transactional_email(subject, body_html, footer_html, contact_list_id)
