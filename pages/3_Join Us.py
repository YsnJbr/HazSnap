import streamlit as st
from mailjet_rest import Client
import re

# Mailjet contact list ID where new contacts will be added
MAILJET_LIST_ID = 10530945

def is_valid_email(email):
    # Simple regex to validate email format
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def add_contact_to_mailjet(email, firstname, lastname, organization, country, city):
    api_key = st.secrets["mailjet"]["api_key"]
    api_secret = st.secrets["mailjet"]["api_secret"]
    mailjet = Client(auth=(api_key, api_secret), version='v3')

    # Prepare contact data with custom properties
    data = {
        "Email": email,
        "Name": f"{firstname} {lastname}".strip(),
        "Properties": {
            "firstname": firstname,
            "lastname": lastname,
            "organization": organization,
            "country": country,
            "city": city,
        },
        "IsExcludedFromCampaigns": False,
        "IsOptInPending": True,  # triggers double opt-in email from Mailjet
        "ListID": MAILJET_LIST_ID
    }

    # Add contact via POST /contactslist/{ListID}/managecontact
    # This endpoint manages subscription and supports opt-in pending flag
    response = mailjet.contactslist.managecontact.create(id=MAILJET_LIST_ID, data={
        "Email": email,
        "Action": "addnoforce"  # adds contact without forcing subscription if already unsubscribed
    })

    if response.status_code not in [200, 201]:
        return False, f"Mailjet API error: {response.status_code} {response.json()}"

    # Now update contact properties & opt-in pending flag
    contact_data = {
        "Properties": data["Properties"],
        "IsOptInPending": True
    }
    # Update contact
    update_resp = mailjet.contacts.update(id=email, data=contact_data)

    if update_resp.status_code not in [200, 201]:
        return False, f"Mailjet API error (update): {update_resp.status_code} {update_resp.json()}"

    return True, None

def app():
    st.set_page_config(page_title="Subscribe to HazSnap Alerts", layout="centered")

    st.title("Subscribe to HazSnap Alerts 📩")

    st.markdown("""
    Please fill in the form below to subscribe to email alerts about chemical classification changes.
    You will receive a confirmation email to validate your subscription.
    """)

    with st.form("subscription_form"):
        email = st.text_input("Email *", help="Enter a valid email address")
        firstname = st.text_input("First Name")
        lastname = st.text_input("Last Name")
        organization = st.text_input("Organization / Company")
        country = st.text_input("Country")
        city = st.text_input("City")

        consent = st.checkbox(
            "I consent to receive email notifications from HazSnap regarding updates and changes. "
            "I understand I can unsubscribe at any time via the link in every email. "
            "My data will be handled in accordance with the Privacy Policy and GDPR regulation.",
            key="consent_checkbox"
        )

        submitted = st.form_submit_button("Subscribe")

    if submitted:
        # Validate email
        if not email or not is_valid_email(email):
            st.error("Please enter a valid email address.")
            return
        if not consent:
            st.error("You must consent to receive emails to subscribe.")
            return

        with st.spinner("Submitting your subscription..."):
            success, error_msg = add_contact_to_mailjet(email, firstname, lastname, organization, country, city)

        if success:
            st.success(f"Thank you for subscribing, {firstname or email}! Please check your inbox to confirm your subscription.")
        else:
            st.error(f"Subscription failed: {error_msg or 'Please try again later.'}")

if __name__ == "__main__":
    app()
