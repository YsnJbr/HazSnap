import streamlit as st

def inject_montserrat_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');

        /* Apply to body */
        body, html {
            font-family: 'Montserrat', sans-serif !important;
        }

        /* Apply to main container */
        .block-container {
            font-family: 'Montserrat', sans-serif !important;
        }

        /* Apply to all text elements */
        p, span, div, h1, h2, h3, h4, h5, h6, label {
            font-family: 'Montserrat', sans-serif !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
