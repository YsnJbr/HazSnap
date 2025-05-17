import streamlit as st
from datetime import datetime

current_year = datetime.now().year

from style import inject_montserrat_css
inject_montserrat_css()

st.title("⚖️ Legal Notice & Data Use")

st.markdown("""
### Data Archival and Use Policy
This application periodically saves **static snapshots** (PDF or HTML files) of publicly accessible data from the **European Chemicals Agency (ECHA)** website, specifically from the **Registry of Classification and Labelling Harmonized (CLH) Intentions** page.  
These snapshots serve as archival copies for **transparency, research, and educational purposes**.
""")

st.markdown("""
### Compliance with EU Law
- **Archival Use:**  
  Snapshots are taken infrequently and represent **static, timestamped captures** of public web pages. This aligns with accepted principles of archiving publicly available information.  
- **Research and Educational Exemptions:**  
  Under EU directives like the **Database Directive (96/9/EC)** and **InfoSoc Directive (2001/29/EC)**, archiving and using data for **non-commercial research, private study, or educational purposes** are exempt from some database and copyright restrictions.  
- **No Unauthorized Scraping:**  
  This app does **not** perform unauthorized automated scraping or bypass any access controls. All data captured is **publicly accessible** without login or paywall.  
- **Respect for Website Integrity:**  
  Snapshotting is performed at **low frequency** to avoid server overload or disruption.
""")

st.markdown("""
### User Responsibilities
Users must comply with applicable laws and respect data ownership.  
The snapshots provided are for **informational and research use only** and **do not substitute official regulatory advice or data from ECHA**. ⚠️
""")

st.markdown("""
### Privacy Policy
- No personal data is collected or stored by this application.  
- Usage data may be collected anonymously for performance monitoring only.  
- We respect your privacy and adhere to GDPR standards.
""")

st.markdown("""
### Terms of Use
- You agree to use the data and snapshots responsibly and only for lawful purposes.  
- Redistribution or commercial use of the snapshots without permission is prohibited.  
- We reserve the right to update or modify these terms at any time.
""")

st.markdown("""
### User Conduct
- Users must not attempt to interfere with the app’s operation or the source website.  
- Automated bulk downloading or abusive behavior will result in access termination.
""")

st.markdown("""
### Limitation of Liability
- This app and its data are provided "as is" without warranties of any kind.  
- We are not liable for any errors, inaccuracies, or damages arising from use of this data.  
- Always verify critical information with official sources.
""")

st.markdown("""
### Contact Information
For questions or concerns, please contact:  
**Email:** ADD_EMAIL_OR_GITHUB  
""")

st.markdown("---")
st.caption(f"© {current_year} APP_NAME | Made with ❤️ and respect for open data")
