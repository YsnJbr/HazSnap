import os
import requests
import pandas as pd
from datetime import datetime
from mailjet_rest import Client

# ---------------------- Config ----------------------
ESSENTIAL_COLS = ['Substance name', 'CAS no', 'Status', 'Submitter', 'Latest update']
DATA_DIR = "Data"
CONTACT_LIST_ID = 10530945
TEMPLATE_ID = 7028286
# ----------------------------------------------------

def download_clh_snapshot():
    print("Downloading CLH Snapshot...")

    url = "https://echa.europa.eu/fr/registry-of-clh-intentions-until-outcome"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to download snapshot: {response.status_code}")

    os.makedirs(DATA_DIR, exist_ok=True)
    today_str = datetime.now().strftime("%Y-%m-%d")
    html_path = os.path.join(DATA_DIR, f"clh_snapshot_{today_str}.html")
    csv_path = os.path.join(DATA_DIR, f"clh_snapshot_{today_str}.csv")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(response.text)

    tables = pd.read_html(response.text)
    df = tables[0].dropna(how="all")
    df.columns = df.columns.str.strip()
    df = df.loc[:, df.columns.notna()]
    df = df.loc[:, df.columns != 'Unnamed: 0']
    df = df.dropna(axis=1, how='all')

    df.to_csv(csv_path, index=False)
    print(f"Snapshot saved to {csv_path}")
    return df, csv_path

def get_previous_csv(latest_csv):
    all_csvs = sorted(
        [f for f in os.listdir(DATA_DIR) if f.endswith(".csv") and f != os.path.basename(latest_csv)],
        reverse=True
    )
    return os.path.join(DATA_DIR, all_csvs[0]) if all_csvs else None

def detect_changes(df_current, df_previous):
    df_current_keyed = df_current.set_index("CAS no")
    df_previous_keyed = df_previous.set_index("CAS no")

    new = df_current_keyed.loc[~df_current_keyed.index.isin(df_previous_keyed.index)].reset_index()
    removed = df_previous_keyed.loc[~df_previous_keyed.index.isin(df_current_keyed.index)].reset_index()
    common = df_current_keyed.index.intersection(df_previous_keyed.index)

    changed = []
    for cas in common:
        if not df_current_keyed.loc[cas].equals(df_previous_keyed.loc[cas]):
            changed.append(df_current_keyed.loc[[cas]])

    changed_df = pd.concat(changed).reset_index() if changed else pd.DataFrame(columns=df_current.columns)
    return new, removed, changed_df

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
    </style>
    """
    return f"<h3>{title}</h3>{styles}{table_html}<br>"

def generate_email_body(new_df, removed_df, changed_df):
    summary = (
        f"🆕 New entries: {len(new_df)}<br>"
        f"❌ Removed entries: {len(removed_df)}<br>"
        f"🔄 Changed entries: {len(changed_df)}<br><br>"
    )

    sections = ""
    if not new_df.empty:
        sections += format_sample_html(new_df, "New Entries Sample")
    if not removed_df.empty:
        sections += format_sample_html(removed_df, "Removed Entries Sample")
    if not changed_df.empty:
        sections += format_sample_html(changed_df, "Changed Entries Sample")

    return summary + sections

def get_contacts_from_list(contact_list_id):
    api_key = os.getenv("MAILJET_API_KEY")
    api_secret = os.getenv("MAILJET_API_SECRET")
    mailjet = Client(auth=(api_key, api_secret), version='v3')

    response = mailjet.contact.get()
    if response.status_code != 200:
        raise Exception(f"Failed to fetch contacts: {response.status_code} {response.text}")

    all_contacts = response.json().get("Data", [])
    subscribed_contacts = []

    for contact in all_contacts:
        email = contact["Email"]
        check_url = f"https://api.mailjet.com/v3/REST/contact/{email}/getcontactslists"
        check_resp = requests.get(check_url, auth=(api_key, api_secret))

        if check_resp.status_code == 200:
            lists = check_resp.json().get("Data", [])
            for item in lists:
                if item["ListID"] == contact_list_id and item["IsUnsub"] is False:
                    subscribed_contacts.append({"Email": email, "Name": contact.get("Name", "")})
                    break
        else:
            print(f"Warning: issue checking list for {email}: {check_resp.status_code}")

    return subscribed_contacts

def send_transactional_email(subject, html_content, footer_html, contact_list_id):
    api_key = os.getenv("MAILJET_API_KEY")
    api_secret = os.getenv("MAILJET_API_SECRET")
    sender_email = os.getenv("MAILJET_SENDER_EMAIL")
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')

    contacts = get_contacts_from_list(contact_list_id)

    for contact in contacts:
        data = {
            "Messages": [
                {
                    "From": {"Email": sender_email, "Name": "CLH Monitor"},
                    "To": [{"Email": contact["Email"], "Name": contact["Name"] or "Valued Recipient"}],
                    "TemplateID": TEMPLATE_ID,
                    "TemplateLanguage": True,
                    "Subject": subject,
                    "Variables": {"content": html_content, "footer": footer_html}
                }
            ]
        }

        response = mailjet.send.create(data=data)
        print(f"Sent to {contact['Email']}: status {response.status_code}")
        if response.status_code != 200:
            print("Response content:", response.json())

if __name__ == "__main__":
    df_today, latest_csv = download_clh_snapshot()
    prev_csv = get_previous_csv(latest_csv)

    if prev_csv:
        df_prev = pd.read_csv(prev_csv)
        df_new, df_removed, df_changed = detect_changes(df_today, df_prev)

        if any([not df_new.empty, not df_removed.empty, not df_changed.empty]):
            body_html = generate_email_body(df_new, df_removed, df_changed)
            footer_html = "<p>CLH Monitor &copy; 2025</p>"
            subject = f"🧪 CLH Changes Detected – {datetime.now().strftime('%d %B %Y')}"
            send_transactional_email(subject, body_html, footer_html, CONTACT_LIST_ID)
        else:
            print("No changes detected.")
    else:
        print("No previous CSV found. Skipping comparison.")
