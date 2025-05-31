import os
import pandas as pd
from datetime import datetime, timedelta
from mailjet_rest import Client
import requests

# ========== CONFIGURATION ==========
ESSENTIAL_COLS = ['Substance name', 'CAS no', 'Status', 'Submitter', 'Latest update']
DATA_DIR = "Data"
TEMPLATE_ID = 7028286
CONTACT_LIST_ID = 10530945  # Replace with your actual Mailjet contact list ID

# ========== FORMAT HTML TABLE ==========
def format_sample_html(df, title):
    df_reset = df.reset_index(drop=True)
    cols_to_show = [col for col in ESSENTIAL_COLS if col in df_reset.columns]
    df_display = df_reset[cols_to_show].head(5)

    table_html = df_display.to_html(index=False, escape=False, border=0, classes="styled-table")

    styles = """
    <style>
    .styled-table {
        width: 800px;           /* fixed width for all tables */
        border-collapse: collapse;
        margin: 10px 0;
        font-size: 14px;
        font-family: Arial, sans-serif;
        table-layout: fixed;    /* enforce fixed layout so column widths apply */
    }
    .styled-table th, .styled-table td {
        border: 1px solid #dddddd;
        text-align: left;
        padding: 6px;
        vertical-align: top;
        word-wrap: break-word;
        overflow-wrap: break-word;  /* better word wrapping */
    }
    .styled-table th {
        background-color: #f2f2f2;
        text-align: center;
    }
    .styled-table td:nth-child(1) { width: 240px; }   /* 30% of 800px */
    .styled-table td:nth-child(2) { width: 96px; }    /* 12% of 800px */
    .styled-table td:nth-child(3) { width: 144px; }   /* 18% of 800px */
    .styled-table td:nth-child(4) { width: 120px; }   /* 15% of 800px */
    .styled-table td:nth-child(5) { width: 120px; }   /* 15% of 800px */
    </style>
    """

    return f"<h3>{title}</h3>{styles}{table_html}<br>"


def generate_email_body(new_df, removed_df, changed_df):
    summary = (
        f"🆕 New entries: {len(new_df)}<br>"
        f"❌ Removed entries: {len(removed_df)}<br>"
        f"🔄 Changed entries: {len(changed_df)}<br><br>"
    )

    new_html = format_sample_html(new_df, "New Entries Sample") if not new_df.empty else ""
    removed_html = format_sample_html(removed_df, "Removed Entries Sample") if not removed_df.empty else ""
    changed_html = format_sample_html(changed_df, "Changed Entries Sample") if not changed_df.empty else ""

    return f"{summary}{new_html}{removed_html}{changed_html}"

# ========== LOAD SNAPSHOTS ==========
def load_today_and_yesterday():
    today_str = datetime.today().strftime("%Y-%m-%d")
    yesterday_str = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    today_file = os.path.join(DATA_DIR, f"clh_snapshot_{today_str}.csv")
    yesterday_file = os.path.join(DATA_DIR, f"clh_snapshot_{yesterday_str}.csv")

    if not os.path.exists(today_file):
        raise FileNotFoundError(f"Today's snapshot not found: {today_file}")
    if not os.path.exists(yesterday_file):
        raise FileNotFoundError(f"Yesterday's snapshot not found: {yesterday_file}")

    df_today = pd.read_csv(today_file)
    df_yesterday = pd.read_csv(yesterday_file)

    return df_today, df_yesterday, today_str

# ========== COMPARE SNAPSHOTS ==========
def compare_snapshots(df_today, df_yesterday):
    join_cols = ['Substance name', 'CAS no']

    df_today_keyed = df_today.set_index(join_cols)
    df_yesterday_keyed = df_yesterday.set_index(join_cols)

    new_rows = df_today_keyed.loc[~df_today_keyed.index.isin(df_yesterday_keyed.index)].reset_index()
    removed_rows = df_yesterday_keyed.loc[~df_yesterday_keyed.index.isin(df_today_keyed.index)].reset_index()

    common_index = df_today_keyed.index.intersection(df_yesterday_keyed.index)
    changed_mask = (df_today_keyed.loc[common_index] != df_yesterday_keyed.loc[common_index]).any(axis=1)
    changed_rows = df_today_keyed.loc[common_index][changed_mask].reset_index()

    return new_rows, removed_rows, changed_rows

# ========== FETCH MAILJET CONTACTS ==========
def get_contacts_from_list(contact_list_id):
    api_key = os.getenv("MAILJET_API_KEY")
    api_secret = os.getenv("MAILJET_API_SECRET")
    base_url = "https://api.mailjet.com/v3"

    # Step 1: get all contacts
    url_contacts = f"{base_url}/REST/contact"
    response = requests.get(url_contacts, auth=(api_key, api_secret))

    if response.status_code != 200:
        raise Exception(f"Failed to fetch contacts: {response.status_code} {response.text}")

    all_contacts = response.json().get("Data", [])
    subscribed_contacts = []

    # Step 2: check each contact's lists to confirm membership in our list and not unsubscribed
    for contact in all_contacts:
        email = contact["Email"]
        url_lists = f"{base_url}/REST/contact/{email}/getcontactslists"
        resp = requests.get(url_lists, auth=(api_key, api_secret))

        if resp.status_code == 200:
            lists = resp.json().get("Data", [])
            for item in lists:
                if item["ListID"] == contact_list_id and item["IsUnsub"] is False:
                    subscribed_contacts.append({"Email": email, "Name": contact.get("Name", "")})
                    break
        else:
            print(f"Warning: issue checking list for {email}: {resp.status_code}")

    return subscribed_contacts

# ========== SEND EMAIL ==========
def send_transactional_email(subject, html_content, footer_html):
    api_key = os.getenv("MAILJET_API_KEY")
    api_secret = os.getenv("MAILJET_API_SECRET")
    sender_email = os.getenv("MAILJET_SENDER_EMAIL")

    mailjet = Client(auth=(api_key, api_secret), version='v3.1')

    contacts = get_contacts_from_list(CONTACT_LIST_ID)
    if not contacts:
        print("No subscribed contacts found, no emails will be sent.")
        return

    for contact in contacts:
        message = {
            "Messages": [
                {
                    "From": {"Email": sender_email, "Name": "CLH Monitor"},
                    "To": [{"Email": contact["Email"], "Name": contact["Name"] or "Valued Recipient"}],
                    "TemplateID": TEMPLATE_ID,
                    "TemplateLanguage": True,
                    "Subject": subject,
                    "Variables": {
                        "content": html_content,
                        "footer": footer_html
                    }
                }
            ]
        }

        response = mailjet.send.create(data=message)
        print(f"Sent to {contact['Email']}: status {response.status_code}")
        if response.status_code != 200:
            print("Response content:", response.json())

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
        body_html = generate_email_body(new_df, removed_df, changed_df)
        footer_html = "<p>CLH Monitor &copy; 2025</p>"
        subject = f"🧪 CLH Changes Detected – {today_str}"
        send_transactional_email(subject, body_html, footer_html)
