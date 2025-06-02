import os
import pandas as pd
from datetime import datetime, timedelta
from mailjet_rest import Client
import requests

# ========== CONFIGURATION ==========
ESSENTIAL_COLS = ['Substance name', 'CAS no', 'Status', 'Submitter', 'Latest update', 'Details Link', 'Link ID']
DATA_DIR = "Data"
TEMPLATE_ID = 7028286
CONTACT_LIST_ID = 10530945  # Your Mailjet contact list ID
BASE_URL = "https://echa.europa.eu/registry-of-clh-intentions-until-outcome/-/dislist/details/"

# ========== GENERATE EMAIL BODY ==========
def generate_email_body(new_df, removed_df, changed_df):
    def build_html_list(df, label):
        if df.empty:
            return f"<p><strong>{label}:</strong> None</p>"

        html_items = []
        for _, row in df.iterrows():
            name = row.get('Substance name', 'N/A')
            cas = row.get('CAS no', 'N/A')
            date = row.get('Latest update', 'N/A')

            # Determine the link URL: prefer Details Link, fallback to Link ID if exists
            link = ""
            if 'Details Link' in row and isinstance(row['Details Link'], str) and row['Details Link'].startswith("http"):
                link = row['Details Link']
            elif 'Link ID' in row and pd.notna(row['Link ID']):
                link = BASE_URL + str(row['Link ID'])

            if link:
                link_html = f'<a href="{link}" target="_blank">View 🔗</a>'
            else:
                link_html = "No link"

            html_items.append(f'<li><strong>{name}</strong> (CAS no: {cas}) - {date} - {link_html}</li>')

        return f"<p><strong>{label} ({len(df)}):</strong></p><ul>{''.join(html_items)}</ul>"

    parts = [
        build_html_list(new_df, "New entries"),
        build_html_list(removed_df, "Removed entries"),
        build_html_list(changed_df, "Changed entries"),
    ]

    return "<br>".join(parts)

# ========== LOAD SNAPSHOTS ==========
def load_today_and_yesterday():
    today = datetime.today()
    today_str = today.strftime("%Y-%m-%d")
    yesterday_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")

    today_file = os.path.join(DATA_DIR, f"clh_snapshot_{today_str}.csv")
    yesterday_file = os.path.join(DATA_DIR, f"clh_snapshot_{yesterday_str}.csv")

    if not os.path.exists(today_file):
        raise FileNotFoundError(f"Today's snapshot not found: {today_file}")
    if not os.path.exists(yesterday_file):
        raise FileNotFoundError(f"Yesterday's snapshot not found: {yesterday_file}")

    return pd.read_csv(today_file), pd.read_csv(yesterday_file), today_str

# ========== COMPARE SNAPSHOTS ==========
def compare_snapshots(df_today, df_yesterday):
    key_cols = ['Substance name', 'CAS no']
    today_set = df_today.set_index(key_cols)
    yesterday_set = df_yesterday.set_index(key_cols)

    new_rows = today_set.loc[~today_set.index.isin(yesterday_set.index)].reset_index()
    removed_rows = yesterday_set.loc[~yesterday_set.index.isin(today_set.index)].reset_index()

    common = today_set.index.intersection(yesterday_set.index)
    common_cols = today_set.columns.intersection(yesterday_set.columns).tolist()
    today_common = today_set.loc[common, common_cols]
    yesterday_common = yesterday_set.loc[common, common_cols]

    changed_mask = (today_common != yesterday_common).any(axis=1)
    changed_rows = today_common.loc[changed_mask].reset_index()

    return new_rows, removed_rows, changed_rows

# ========== FETCH MAILJET CONTACTS ==========
def get_contacts(contact_list_id):
    api_key, api_secret = os.getenv("MAILJET_API_KEY"), os.getenv("MAILJET_API_SECRET")
    base_url = "https://api.mailjet.com/v3"

    contacts = []
    res = requests.get(f"{base_url}/REST/contact", auth=(api_key, api_secret))
    if res.status_code != 200:
        raise Exception(f"Failed to fetch contacts: {res.status_code}")

    for contact in res.json().get("Data", []):
        email = contact["Email"]
        list_res = requests.get(f"{base_url}/REST/contact/{email}/getcontactslists", auth=(api_key, api_secret))
        if list_res.status_code == 200:
            for item in list_res.json().get("Data", []):
                if item["ListID"] == contact_list_id and not item["IsUnsub"]:
                    contacts.append({"Email": email, "Name": contact.get("Name", "")})
                    break
    return contacts

# ========== SEND EMAIL ==========
def send_email(subject, html_content, footer):
    """
    Sends personalized emails using a Mailjet template.
    IMPORTANT:
    - The Mailjet template must use {{var:content}} and {{var:footer}} (not triple braces).
    - HTML in these variables will be inserted as raw HTML.
    """
    api_key = os.getenv("MAILJET_API_KEY")
    api_secret = os.getenv("MAILJET_API_SECRET")
    sender_email = os.getenv("MAILJET_SENDER_EMAIL")
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')

    contacts = get_contacts(CONTACT_LIST_ID)
    if not contacts:
        print("No subscribed contacts found.")
        return

    for contact in contacts:
        message = {
            "Messages": [
                {
                    "From": {"Email": sender_email, "Name": "CLH Monitor"},
                    "To": [{"Email": contact["Email"], "Name": contact["Name"] or "Subscriber"}],
                    "TemplateID": TEMPLATE_ID,
                    "TemplateLanguage": True,
                    "Subject": subject,
                    "Variables": {
                        "content": html_content,
                        "footer": footer
                    }
                }
            ]
        }

        response = mailjet.send.create(data=message)
        print(f"Sent to {contact['Email']}: status {response.status_code}")
        if response.status_code != 200:
            print(response.json())

# ========== MAIN ==========
if __name__ == "__main__":
    try:
        df_today, df_yesterday, today_str = load_today_and_yesterday()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        exit(1)

    new_df, removed_df, changed_df = compare_snapshots(df_today, df_yesterday)

    if new_df.empty and removed_df.empty and changed_df.empty:
        print("No changes detected — no emails sent.")
    else:
        html_body = generate_email_body(new_df, removed_df, changed_df)
        footer_html = "<p>CLH Monitor &copy; 2025</p>"
        subject = f"🧪 CLH Changes Detected – {today_str}"
        send_email(subject, html_body, footer_html)
