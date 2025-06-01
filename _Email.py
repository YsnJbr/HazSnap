import os
import pandas as pd
from datetime import datetime, timedelta
from mailjet_rest import Client
import requests

# ========== CONFIGURATION ==========
ESSENTIAL_COLS = ['Substance name', 'CAS no', 'Status', 'Submitter', 'Latest update', 'Details']
DATA_DIR = "Data"
TEMPLATE_ID = 7028286
CONTACT_LIST_ID = 10530945  # Your Mailjet contact list ID

# ========== GENERATE EMAIL BODY ==========
def generate_email_body(new_df, removed_df, changed_df, df_today):
    summary = (
        f"🆕 New entries: {len(new_df)}<br>"
        f"❌ Removed entries: {len(removed_df)}<br>"
        f"🔄 Changed entries: {len(changed_df)}<br><br>"
    )

    # Build preview with clickable links for top 5 entries
    preview = df_today.head(5)
    lines = []
    for _, row in preview.iterrows():
        substance = row.get('Substance name', 'N/A')
        cas_no = row.get('CAS no', 'N/A')
        status = row.get('Status', 'N/A')
        submitter = row.get('Submitter', 'N/A')
        latest_update = row.get('Latest update', 'N/A')
        details_url = row.get('Details', '').strip()

        # Safely build hyperlink if details_url looks like a URL
        if details_url.startswith("http"):
            details_link = f'<a href="{details_url}" target="_blank">Details</a>'
        else:
            details_link = "No link"

        line = (f"- <strong>{substance}</strong> (CAS: {cas_no}), Status: {status}, "
                f"Submitter: {submitter}, Updated: {latest_update} — {details_link}")
        lines.append(line)

    preview_html = "<br>".join(lines)

    return summary + "<b>Today's Snapshot – Preview (Top 5 entries):</b><br>" + preview_html + "<br><br>"


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

    # Align columns: take columns intersection, same order
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
                    "Variables": {"content": html_content, "footer": footer}
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
        html_body = generate_email_body(new_df, removed_df, changed_df, df_today)
        footer_html = "<p>CLH Monitor &copy; 2025</p>"
        subject = f"🧪 CLH Changes Detected – {today_str}"
        send_email(subject, html_body, footer_html)
