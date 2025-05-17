import streamlit as st

from style import inject_montserrat_css
inject_montserrat_css()


st.title("📘 About This Project")

st.markdown("""
### 🌍 Empowering Access to Regulatory Knowledge — For Everyone

Every day, professionals across **industry**, **public agencies**, and **civil society organizations** spend time manually checking the [ECHA](https://echa.europa.eu/) website for updates. From **regulatory teams** in global manufacturers, to **public health officials**, to **NGOs tracking chemical risks**, the need for timely, trustworthy information is universal.

Yet this work is often done:

🔁 **Individually**,  
🏢 **Redundantly** across departments and organizations,  
⏱️ **Inefficiently** across the entire ecosystem.

---

### 💡 The Vision

This tool was built to **democratize** and **streamline** access to ECHA CLH (Classification and Labelling) updates, aiming to:

✅ Help **product compliance team** to avoid repeated manual checks  
✅ Support **Agencies** in staying updated  
✅ Enable a **civil society group** to get updates

All without needing to refresh a page or dig through layers of content.

---

### 🚀 The Mission

> Our mission is to **democratize and accelerate access** to chemical data updates by delivering a transparent, interactive, and intuitive platform that empowers professionals, regulators, researchers, and citizens to get **fast** updates and make informed decisions about chemical substances in response the rapidly evolving regulatory developments.
Whether you're:

- A **regulatory affairs manager** ensuring compliance  
- A **public sector official** managing local chemical safety initiatives  
- An **NGO analyst** monitoring health and environmental updates  
- Or a **startup team** building cleaner, compliant products  

This tool exists to serve you.

---

### 🤝 Giving Back

By making this project **freely available**, we aim to:

🌍 Reduce redundant effort across Europe and beyond  
⚙️ Foster collaboration between sectors  
📣 Support a smarter, more transparent regulatory ecosystem  
🕊️ Return **valuable time** to humans to invest elsewhere

---

Let’s reimagine how we interact with public regulatory data — **together**.  
Thanks for being part of this journey. 🙌
""")
