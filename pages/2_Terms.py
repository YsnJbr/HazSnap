import streamlit as st
from datetime import datetime

from style import inject_montserrat_css
inject_montserrat_css()

current_year = datetime.now().year

st.title("⚖️ Legal Notice & Terms of Use")

st.markdown("""
### Purpose and Nature of This Application
This application automatically captures **timestamped, static snapshots** (PDF or HTML format) of publicly available content from the **European Chemicals Agency (ECHA)** website, specifically from the **CLH Registry of Harmonised Classification and Labelling Intentions**.

The purpose is to detect and notify subscribers about **changes** on that public page for **informational, academic, or research-related purposes**.  
This application is developed and maintained by a **private individual**, with no affiliation to ECHA or any governmental body.
""")

st.markdown("""
### Legal Basis and Compliance
- **Archival Practices:**  
  All data collected consists of **publicly available web content**, and is archived in accordance with accepted standards for transparency and public record-keeping.

- **Use Under EU Directives:**  
  This app operates in alignment with provisions from the **Database Directive (96/9/EC)** and **InfoSoc Directive (2001/29/EC)**, which allow reproduction for **non-commercial research, teaching, or private study**.

- **No Circumvention of Protections:**  
  The application does **not** bypass login systems, paywalls, robots.txt files, or technical access restrictions.  

- **Low Impact:**  
  Data is retrieved at a **low frequency**, and care is taken to **respect the stability and performance of source servers**.
""")

st.markdown("""
### Subscriber & User Responsibilities
- Users are responsible for complying with all applicable laws and terms of the source website(s).  
- This application **does not provide legal or regulatory advice**.  
- Snapshots and notifications are provided **"as-is"**, for **informational** purposes only and should not be relied upon as official data.
""")

st.markdown("""
### Data Privacy
- No personal or sensitive data is stored or processed by this app directly.  
- Anonymous performance and usage metrics may be collected to improve service reliability.  
- The application is designed to be **compliant with GDPR** and respects your privacy.
""")

st.markdown("""
### Email Communication & Subscription
- Email notifications are sent only to users who have **explicitly opted in** via Mailjet.  
- You may unsubscribe at any time using the link provided in each email.  
- Email data is securely handled by Mailjet in accordance with their data protection policies.
""")

st.markdown("""
### Usage Restrictions
- Redistribution, commercial use, or republication of archived snapshots without express permission is **strictly prohibited**.  
- You may not use this application or its outputs for unlawful or malicious purposes.  
- We reserve the right to **suspend or restrict access** for any user who violates these terms or engages in abusive activity.
""")

st.markdown("""
### Limitation of Liability
- This application and its content are provided **without any warranties**, express or implied.  
- The developer accepts **no liability** for errors, omissions, or for actions taken based on the data provided.  
- Always consult **official regulatory sources** for authoritative information.
""")

st.markdown("""
### Contact
For support or legal inquiries, please contact:  
**Email:** [ADD_EMAIL_OR_GITHUB]
""")

st.markdown("---")
st.caption(f"© {current_year} [APP_NAME] | Created with care for transparency and respect for public data.")
