import os
import pandas as pd
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

load_dotenv()

MAILJET_API_KEY = os.getenv("MAILJET_API_KEY")
MAILJET_API_SECRET = os.getenv("MAILJET_API_SECRET")
SENDER_EMAIL = os.getenv("MAILJET_SENDER_EMAIL")
TEST_SEND_EMAIL = os.getenv("TEST_SEND_EMAIL", "false").lower() == "true"

RECIPIENTS = [
    "yassine.jebrane@gmail.com",
    # Add more emails here if needed
]

def send_email_mailjet_template(template_id, variables, subject, recipient):
    data = {
        'Messages': [
            {
                "From": {"Email": SENDER_EMAIL, "Name": "ECHA Monitor"},
                "To": [{"Email": recipient, "Name": recipient.split('@')[0]}],
                "Subject": subject,
                "TemplateID": template_id,
                "TemplateLanguage": True,
                "Variables": variables
            }
        ]
    }

    response = requests.post(
        "https://api.mailjet.com/v3.1/send",
        auth=(MAILJET_API_KEY, MAILJET_API_SECRET),
        json=data
    )

    if response.status_code == 200:
        print(f"✅ Template email sent to {recipient}")
    else:
        print(f"❌ Failed to send template email to {recipient}: {response.text}")

def generate_diff_report(file_new, file_old):
    try:
        df_old = pd.read_csv(file_old)
        df_new = pd.read_csv(file_new)
        key_cols = ["Substance name", "CAS no"]

        df_old.set_index(key_cols, inplace=True)
        df_new.set_index(key_cols, inplace=True)

        new_entries = df_new.loc[~df_new.index.isin(df_old.index)]
        removed_entries = df_old.loc[~df_old.index.isin(df_new.index)]
        common_idx = df_old.index.intersection(df_new.index)
        changed_mask = (df_old.loc[common_idx] != df_new.loc[common_idx]).any(axis=1)
        changed_entries = df_new.loc[common_idx][changed_mask]

        summary = []
        if not new_entries.empty:
            summary.append(f"🆕 New entries: {len(new_entries)}")
        if not removed_entries.empty:
            summary.append(f"❌ Removed entries: {len(removed_entries)}")
        if not changed_entries.empty:
            summary.append(f"🔄 Changed entries: {len(changed_entries)}")

        if not summary:
            return None  # No changes detected

        # Compose summary string for template variable
        detailed_changes = "\n".join(summary) + "\n\n"
        if not new_entries.empty:
            detailed_changes += f"New Entries Sample:\n{new_entries.reset_index().head(5).to_string(index=False)}\n\n"
        if not removed_entries.empty:
            detailed_changes += f"Removed Entries Sample:\n{removed_entries.reset_index().head(5).to_string(index=False)}\n\n"
        if not changed_entries.empty:
            detailed_changes += f"Changed Entries Sample:\n{changed_entries.reset_index().head(5).to_string(index=False)}\n"

        return detailed_changes

    except Exception as e:
        return f"Error generating diff: {e}"

def main():
    today = datetime.now()
    yesterday = today - timedelta(days=1)

    file_new = os.path.join("Data", f"clh_snapshot_{today.strftime('%Y-%m-%d')}.csv")
    file_old = os.path.join("Data", f"clh_snapshot_{yesterday.strftime('%Y-%m-%d')}.csv")

    if not os.path.isfile(file_new):
        print(f"❌ Required CSV file not found: {file_new}")
        return
    if not os.path.isfile(file_old):
        print(f"❌ Required CSV file not found: {file_old}")
        return

    report = generate_diff_report(file_new, file_old)
    template_id = 7028286  # <-- Replace with your Mailjet template ID

    if report is None:
        if TEST_SEND_EMAIL:
            print("⚠️ No changes detected, but TEST_SEND_EMAIL=True, sending test email anyway.")
            # Prepare preview content for testing
            df_new = pd.read_csv(file_new)
            preview_text = df_new.head(10).to_string(index=False)

            subject = f"ECHA Monitor – Test email for {today.strftime('%Y-%m-%d')}"
            variables = {
                "content": preview_text,
                "footer": "This is a test email sent even when no changes are detected."
            }

            for email in RECIPIENTS:
                send_email_mailjet_template(template_id, variables, subject, email)
        else:
            print("✅ No changes detected. No email sent.")
        return

    # If changes detected, send real report email
    subject = f"ECHA Monitor – Changes for {today.strftime('%Y-%m-%d')}"
    variables = {
        "content": report,
        "footer": "This email lists detected changes in the CLH registry snapshot."
    }

    for email in RECIPIENTS:
        send_email_mailjet_template(template_id, variables, subject, email)

if __name__ == "__main__":
    main()
