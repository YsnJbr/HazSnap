import os
import requests
import pandas as pd

# --- Configurable flag ---
SEND_EMAIL_ALWAYS = True  # Set to True to send email always (testing). False = only on changes.

# Load secrets from environment variables
MAILJET_API_KEY = os.getenv("MAILJET_API_KEY")
MAILJET_API_SECRET = os.getenv("MAILJET_API_SECRET")
SENDER_EMAIL = os.getenv("MAILJET_SENDER_EMAIL")

if not all([MAILJET_API_KEY, MAILJET_API_SECRET, SENDER_EMAIL]):
    print("❌ Missing Mailjet credentials in environment variables.")
    exit(1)

# Email sending function
def send_email_mailjet(subject, text, recipients):
    data = {
        'Messages': [
            {
                "From": {"Email": SENDER_EMAIL, "Name": "ECHA Monitor"},
                "To": [{"Email": email} for email in recipients],
                "Subject": subject,
                "TextPart": text
            }
        ]
    }
    response = requests.post(
        "https://api.mailjet.com/v3.1/send",
        auth=(MAILJET_API_KEY, MAILJET_API_SECRET),
        json=data
    )

    if response.status_code == 200:
        print("✅ Email sent successfully!")
    else:
        print(f"❌ Failed to send email: {response.status_code} - {response.text}")

# Load today and yesterday CSVs to detect changes
from datetime import datetime, timedelta

today = datetime.now()
yesterday = today - timedelta(days=1)

file_new = os.path.join("Data", f"clh_snapshot_{today.strftime('%Y-%m-%d')}.csv")
file_old = os.path.join("Data", f"clh_snapshot_{yesterday.strftime('%Y-%m-%d')}.csv")

if not os.path.isfile(file_old):
    print(f"❌ Yesterday's file not found: {file_old}")
    exit(1)
if not os.path.isfile(file_new):
    print(f"❌ Today's file not found: {file_new}")
    exit(1)

df_old = pd.read_csv(file_old)
df_new = pd.read_csv(file_new)

key_cols = ["Substance name", "CAS no"]
if not all(col in df_old.columns and col in df_new.columns for col in key_cols):
    print(f"❌ Missing one or more key columns: {key_cols}")
    exit(1)

df_old.set_index(key_cols, inplace=True)
df_new.set_index(key_cols, inplace=True)

new_entries = df_new.loc[~df_new.index.isin(df_old.index)].reset_index()
removed_entries = df_old.loc[~df_old.index.isin(df_new.index)].reset_index()
common_idx = df_old.index.intersection(df_new.index)
changed_mask = (df_old.loc[common_idx] != df_new.loc[common_idx]).any(axis=1)
changed_entries = df_new.loc[common_idx][changed_mask].reset_index()

# Compose email content
subject = f"ECHA CLH Registry Update {today.strftime('%Y-%m-%d')}"

if len(new_entries) == 0 and len(removed_entries) == 0 and len(changed_entries) == 0:
    email_text = (
        f"No changes detected in ECHA CLH Registry for {today.strftime('%Y-%m-%d')}.\n"
        "This is an automated notification."
    )
else:
    email_text = (
        f"ECHA CLH Registry Update for {today.strftime('%Y-%m-%d')}:\n\n"
        f"New entries: {len(new_entries)}\n"
        f"Removed entries: {len(removed_entries)}\n"
        f"Changed entries: {len(changed_entries)}\n\n"
        "Please check the attached data or dashboard for details."
    )

# Define recipients list here (or load from file/env)
recipients = ["yassine.jebrane@gmail.com"]  # Replace or extend

# Decide whether to send email
if SEND_EMAIL_ALWAYS or (len(new_entries) > 0 or len(removed_entries) > 0 or len(changed_entries) > 0):
    if SEND_EMAIL_ALWAYS:
        print("Test mode ON: sending email regardless of changes.")
    else:
        print("Changes detected, sending email.")
    send_email_mailjet(subject, email_text, recipients)
else:
    print("No changes detected, no email sent.")
