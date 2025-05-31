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

ESSENTIAL_COLS = ["Substance name", "CAS no", "Status", "Submitter", "Latest update"]

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

def format_sample_html(df, title):
    df_reset = df.reset_index()
    cols_to_show = [col for col in ESSENTIAL_COLS if col in df_reset.columns]
    html_table = df_reset[cols_to_show].head(5).to_html(index=False, escape=False, border=1)
    return f"<h3>{title}</h3>{html_table}<br>"

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
            return None  # No changes

        report = "<p>" + "<br>".join(summary) + "</p><br>"
        if not new_entries.empty:
            report += format_sample_html(new_entries, "New Entries Sample")
        if not removed_entries.empty:
            report += format_sample_html(removed_entries, "Removed Entries Sample")
        if not changed_entries.empty:
            report += format_sample_html(changed_entries, "Changed Entries Sample")

        return report

    except Exception as e:
        return f"<p>Error generating diff: {e}</p>"

def main():
    today = datetime.now()
    yesterday = today - timedelta(days=1)

    file_new = os.path.join("Data", f"clh_snapshot_{today.strftime('%Y-%m-%d')}.csv")
    file_old = os.path.join("Data", f"clh_snapshot_{yesterday.strftime('%Y-%m-%d')}.csv")

    if not os.path.isfile(file_new):
        print(f"❌ Missing: {file_new}")
        return
    if not os.path.isfile(file_old):
        print(f"❌ Missing: {file_old}")
        return

    report = generate_diff_report(file_new, file_old)
    template_id = 7028286  # Replace with your actual Mailjet template ID

    if report is None:
        if TEST_SEND_EMAIL:
            print("⚠️ No changes, but TEST_SEND_EMAIL=True – sending preview.")
            df_new = pd.read_csv(file_new)
            preview_html = df_new.head(10)[ESSENTIAL_COLS].to_html(index=False, escape=False, border=1)

            subject = f"ECHA Monitor – No changes for {today.strftime('%Y-%m-%d')}"
            variables = {
                "content": preview_html,
                "footer": "This is a test email (no changes detected)."
            }

            for email in RECIPIENTS:
                send_email_mailjet_template(template_id, variables, subject, email)
        else:
            print("✅ No changes – no email sent.")
        return

    subject = f"ECHA Monitor – Changes for {today.strftime('%Y-%m-%d')}"
    variables = {
        "content": report,
        "footer": "This email lists changes detected in the CLH registry snapshot."
    }

    for email in RECIPIENTS:
        send_email_mailjet_template(template_id, variables, subject, email)

if __name__ == "__main__":
    main()
