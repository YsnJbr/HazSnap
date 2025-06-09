import streamlit as st
import re
from mailjet_rest import Client

# Load Mailjet credentials from Streamlit secrets
api_key = st.secrets["mailjet"]["api_key"]
api_secret = st.secrets["mailjet"]["api_secret"]
MAILJET_LIST_ID = int(st.secrets["mailjet"]["list_id"])

# Initialize Mailjet client
mailjet = Client(auth=(api_key, api_secret), version='v3')

# Email validation function
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# Add or update contact in Mailjet list (no double opt-in)
def add_contact_to_mailjet(email, firstname, name, country):
    contact_resp = mailjet.contact.create(data={"Email": email})
    if contact_resp.status_code not in [200, 201]:
        if "already exists" not in str(contact_resp.json()):
            return False, f"Failed to create contact: {contact_resp.status_code} {contact_resp.json()}"
    list_resp = mailjet.contactslist_managecontact.create(
        id=MAILJET_LIST_ID,
        data={"Email": email, "Action": "addnoforce"}
    )
    if list_resp.status_code not in [200, 201]:
        return False, f"Failed to add contact to list: {list_resp.status_code} {list_resp.json()}"
    update_resp = mailjet.contactdata.update(
        id=email,
        data={
            "Data": [
                {"Name": "firstname", "Value": firstname},
                {"Name": "name", "Value": name},
                {"Name": "country", "Value": country},
            ]
        }
    )
    if update_resp.status_code not in [200, 201]:
        return False, f"Failed to update contact data: {update_resp.status_code} {update_resp.json()}"
    return True, None

# Main Streamlit app
def app():
    st.set_page_config(page_title="Join HazSnap Alerts", layout="centered")
    st.title("📬 Subscribe to HazSnap")

    st.markdown("### 📢 Stay informed")
    st.markdown(
        """
        Receive automated alerts whenever **important updates** occur in the *ECHA CLH Registry*. We’ll notify you by **email** — no spam, no noise. ✅

        """,
        unsafe_allow_html=False
    )



    with st.form("subscription_form"):
        email = st.text_input("Email *", help="Required: we can't send you email without it 😊!")
        firstname = st.text_input("First Name")
        name = st.text_input("Last Name")
        country = st.text_input("Country")

        # Big, clear consent text before checkbox, styled with HTML and CSS
        consent_text = """
        <div style="
            font-size: 20px; 
            font-weight: 600; 
            line-height: 1.4; 
            background-color: #f7dada; 
            padding: 15px; 
            border-radius: 8px; 
            margin-bottom: 10px;
            border: 2px solid #0078d7;
        ">
            ✅ <label for="consent_checkbox">
            I consent to receive <strong>email notifications</strong> from HazSnap about regulatory updates.
            I understand I can <strong>unsubscribe at any time</strong> via the link in each email.
            My personal data will be processed securely, in compliance with <a href="https://hazsnap.streamlit.app/Terms" target="_blank">our policy</a> and the HazSnap Privacy Policy.
            </label>
        </div>
        """
        st.markdown(consent_text, unsafe_allow_html=True)

        consent = st.checkbox("✅ I read, understood and conscent.", key="consent_checkbox")

        submitted = st.form_submit_button("Subscribe")

    if submitted:
        if not is_valid_email(email):
            st.error("Please enter a valid email address.")
            return
        if not consent:
            st.error("You must provide consent to receive emails.")
            return

        with st.spinner("Submitting your subscription..."):
            success, error_msg = add_contact_to_mailjet(email, firstname, name, country)

        if success:
            st.success(f"✅ Thank you {firstname or email}! You have been subscribed successfully. You can unsubscribe anytime via the link in our emails.")
        else:
            st.error(f"❌ Subscription failed: {error_msg or 'Unknown error. Please try again later.'}")

if __name__ == "__main__":
    app()
