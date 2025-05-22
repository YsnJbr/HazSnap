import streamlit as st
import requests

# Send email function
def send_email_mailjet(subject, text, recipients):
    api_key = st.secrets["mailjet"]["api_key"]
    api_secret = st.secrets["mailjet"]["api_secret"]
    sender_email = st.secrets["mailjet"]["sender"]

    data = {
        'Messages': [
            {
                "From": {"Email": sender_email, "Name": "ECHA Monitor"},
                "To": [{"Email": email, "Name": "Test User"} for email in recipients],
                "Subject": subject,
                "TextPart": text
            }
        ]
    }

    response = requests.post(
        "https://api.mailjet.com/v3.1/send",
        auth=(api_key, api_secret),
        json=data
    )

    if response.status_code == 200:
        st.success("✅ Email sent successfully!")
    else:
        st.error(f"❌ Failed to send email: {response.text}")

# Streamlit UI
st.title("📧 Mailjet Test")

if st.button("Send Test Email"):
    send_email_mailjet(
        subject="Mailjet Test Email",
        text="This is a test email from your Streamlit app via Mailjet.",
        recipients=["your@email.com"]
    )
