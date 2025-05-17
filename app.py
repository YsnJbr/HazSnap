import streamlit as st

from style import inject_montserrat_css

inject_montserrat_css()

st.title('Salam')
st.write("Welcome! Use the sidebar to navigate between pages.")
user_input = st.text_input("smiya a bnademiiiin")
st.write('3alikum salam a', user_input)