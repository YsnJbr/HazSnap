import streamlit as st
import re
from mailjet_rest import Client

# Load Mailjet credentials
api_key = st.secrets["mailjet"]["api_key"]
api_secret = st.secrets["mailjet"]["api_secret"]
MAILJET_LIST_ID = int(st.secrets["mailjet"]["list_id"])

# Initialize client
mailjet = Client(auth=(api_key, api_secret), version='v3')

# Validate email
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# Add contact to Mailjet list
def add_contact_to_mailjet(email, firstname, lastname, organization, country, city):
    # Step 1 – Add contact to Mailjet (if not already exists)
    contact_resp = mailjet.contact.create(data={"Email": email})
    if contact_resp.status_code not in [200, 201]:
        if "already exists" not in str(contact_resp.json()):
            return False, f"Failed to create contact: {contact_resp.status_code} {contact_resp.json()}"

    # Step 2 – Add to list (handles opt-in)
    list_resp = mailjet.contactslist_managecontact.create(id=MAILJET_LIST_ID, data={
        "Email": email,
        "Action": "addnoforce"
    })
    if list_resp.status_code not in [200, 201]:
        return False, f"Failed to add to list: {list_resp.status_code} {list_resp.json()}"

    # Step 3 – Update custom properties + trigger double opt-in
    update_resp = mailjet.contactdata.update(id=email, data={
        "Data": [
            {"Name": "firstname", "Value": firstname},
            {"Name": "lastname", "Value": lastname},
            {"Name": "organization", "Value": organization},
            {"Name": "country", "Value": country},
        ]
    })

    if update_resp.status_code not in [200, 201]:
        return False, f"Failed to update contact properties: {update_resp.status_code} {update_resp.json()}"

    return True, None

# Main Streamlit App
def app():
    st.set_page_config(page_title="Join HazSnap Alerts", layout="centered")
    st.title("📬 Subscribe to HazSnap Alerts")

    st.markdown("""
Stay informed with automated alerts whenever significant updates occur in the ECHA CLH Registry.  
We’ll notify you by email — no spam, no noise.  
""")

    with st.form("opt_in_form"):
        email = st.text_input("Email *", help="Required")
        firstname = st.text_input("First Name")
        lastname = st.text_input("Last Name")
        organization = st.text_input("Organization / Company")
        country = st.text_input("Country")
        city = st.text_input("City")

        consent = st.checkbox(
            "✅ I consent to receive email notifications from HazSnap about regulatory updates. "
            "I understand that I can unsubscribe at any time via the link provided in each email. "
            "My personal data will be processed securely, in compliance with GDPR and the HazSnap Privacy Policy."
        )

        submitted = st.form_submit_button("Subscribe")

    if submitted:
        if not is_valid_email(email):
            st.error("Please enter a valid email address.")
            return
        if not consent:
            st.error("You must provide consent to receive emails.")
            return

        with st.spinner("Submitting your subscription..."):
            success, error_msg = add_contact_to_mailjet(
                email, firstname, lastname, organization, country, city
            )

        if success:
            st.success(f"✅ Thank you {firstname or email}! Please confirm your subscription via the email we just sent you.")
        else:
            st.error(f"❌ Subscription failed: {error_msg or 'Unknown error. Please try again later.'}")

if __name__ == "__main__":
    app()
