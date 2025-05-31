import os
import pandas as pd
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

load_dotenv()

MAILJET_API_KEY = os.getenv("MAILJET_API_KEY")
MAILJET_API_SECRET = os.getenv("MAILJET_API_SECRET")
SENDER_EMAIL = os.getenv("MAILJET_SENDER_EMAIL")
TEST_SEND_EMAIL = True  # Set to False in production

RECIPIENTS = [
    "yassine.jebrane@gmail.com",
    # Add more emails if needed
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
        print(f"✅ Email sent to {recipient}")
    else:
        print(f"❌ Failed to send email to {recipient}: {response.text}")

def generate_diff_report(file_new, file_old):
    try:
        df_old = pd.read_csv(file_old)
        df_new = pd.read_csv(file_new)
        key_cols = ["Substance name", "CAS no"]

        if not set(key_cols).issubset(df_old.columns) or not set(key_cols).issubset(df_new.columns):
            return "Error: Required columns not found in CSV files."

        df_old.set_index(key_cols, inplace=True)
        df_new.set_index(key_cols, inplace=True)

        new_entries = df_new.loc[~df_new.index.isin(df_old.index)]
        removed_entries = df_old.loc[~df_old.index.isin(df_new.index)]
        common_idx = df_old.index.intersection(df_new.index)
        changed_mask = (df_old.loc[common_idx] != df_new.loc[common_idx]).any(axis=1)
        changed_entries = df_new.loc[common_idx][changed_mask]

        summary = []
        if not new_entries.empty:
            summary.append(f"<li><strong>🆕 New entries:</strong> {len(new_entries)}</li>")
        if not removed_entries.empty:
            summary.append(f"<li><strong>❌ Removed entries:</strong> {len(removed_entries)}</li>")
        if not changed_entries.empty:
            summary.append(f"<li><strong>🔄 Changed entries:</strong> {len(changed_entries)}</li>")

        if not summary:
            return None

        html_report = "<ul>" + "".join(summary) + "</ul>"

        def to_html(df, title):
            return f"<h4>{title}</h4>" + df.reset_index().head(5).to_html(index=False, border=1)

        if not new_entries.empty:
            html_report += to_html(new_entries, "New Entries Sample")
        if not removed_entries.empty:
            html_report += to_html(removed_entries, "Removed Entries Sample")
        if not changed_entries.empty:
            html_report += to_html(changed_entries, "Changed Entries Sample")

        return html_report

    except Exception as e:
        return f"<p>Error generating diff: {e}</p>"

def main():
    today = datetime.now()
    yesterday = today - timedelta(days=1)

    file_new = os.path.join("Data", f"clh_snapshot_{today.strftime('%Y-%m-%d')}.csv")
    file_old = os.path.join("Data", f"clh_snapshot_{yesterday.strftime('%Y-%m-%d')}.csv")

    if not os.path.isfile(file_new):
        print(f"❌ Missing file: {file_new}")
        return
    if not os.path.isfile(file_old):
        print(f"❌ Missing file: {file_old}")
        return

    report = generate_diff_report(file_new, file_old)
    template_id = 7028286  # Your Mailjet template ID

    subject = f"ECHA Monitor – Changes for {today.strftime('%Y-%m-%d')}"

    if report is None:
        if TEST_SEND_EMAIL:
            print("⚠️ No changes detected, sending test email due to TEST_SEND_EMAIL=True.")
            df_preview = pd.read_csv(file_new)
            preview_html = df_preview.head(10).to_html(index=False, border=1)

            variables = {
                "content": preview_html,
                "footer": "This is a test email – no changes were detected in today's snapshot."
            }

            for email in RECIPIENTS:
                send_email_mailjet_template(template_id, variables, subject, email)
        else:
            print("✅ No changes detected – no email sent.")
        return

    # Send actual report with changes
    variables = {
        "content": report,
        "footer": "This email lists changes detected in the daily CLH registry snapshot."
    }

    for email in RECIPIENTS:
        send_email_mailjet_template(template_id, variables, subject, email)

if __name__ == "__main__":
    main()
