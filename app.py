import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# --- Page setup ---
st.set_page_config(page_title="HazSnap", layout="wide")
st.title("HazSnap")
st.markdown("### *Creating time for you 🧪📸*")

# --- Date setup ---
today = datetime.now()
yesterday = today - timedelta(days=1)

file_new = os.path.join("Data", f"clh_snapshot_{today.strftime('%Y-%m-%d')}.csv")
file_old = os.path.join("Data", f"clh_snapshot_{yesterday.strftime('%Y-%m-%d')}.csv")

# --- Check for files ---
if not os.path.isfile(file_old):
    st.error(f"Yesterday's file not found: {file_old}")
elif not os.path.isfile(file_new):
    st.error(f"Today's file not found: {file_new}")
else:
    try:
        df_old = pd.read_csv(file_old)
        df_new = pd.read_csv(file_new)
        st.success(f"📅 ✅ Update for {today.strftime('%Y-%m-%d')} loaded successfully")

        key_cols = ["Substance name", "CAS no"]
        if not all(col in df_old.columns and col in df_new.columns for col in key_cols):
            st.error(f"Missing key columns: {key_cols}")
        else:
            df_old.set_index(key_cols, inplace=True)
            df_new.set_index(key_cols, inplace=True)

            new_entries = df_new.loc[~df_new.index.isin(df_old.index)].reset_index()
            removed_entries = df_old.loc[~df_old.index.isin(df_new.index)].reset_index()
            common_idx = df_old.index.intersection(df_new.index)
            changed_mask = (df_old.loc[common_idx] != df_new.loc[common_idx]).any(axis=1)
            changed_entries = df_new.loc[common_idx][changed_mask].reset_index()

            # --- Summary section ---
            st.markdown("### 📊 Summary Statistics")
            st.markdown(f"- 🆕 New entries: **{len(new_entries)}**")
            st.markdown(f"- ❌ Removed entries: **{len(removed_entries)}**")
            st.markdown(f"- 🔄 Changed entries: **{len(changed_entries)}**")
            st.markdown("---")

            if all(len(df) == 0 for df in [new_entries, removed_entries, changed_entries]):
                st.info("No new changes detected ✅")

            # --- Helper to display tables with links ---
            def show_table(df, label):
                if df.empty:
                    return
                st.subheader(label)

                df_display = df.copy()
                if "Link ID" in df_display.columns:
                    df_display["Details"] = df_display["Link ID"].apply(
                        lambda link_id: f'[🔗](https://echa.europa.eu/registry-of-clh-intentions-until-outcome/-/dislist/details/{link_id})'
                        if pd.notna(link_id) else ""
                    )
                st.dataframe(df_display, use_container_width=True)
                show_links_section(df_display, label + " Links")

            # --- HTML links section per table ---
            def show_links_section(df, section_title):
                if "Link ID" not in df.columns:
                    return
                html_links = ""
                for _, row in df.iterrows():
                    if pd.notna(row["Link ID"]):
                        url = f"https://echa.europa.eu/registry-of-clh-intentions-until-outcome/-/dislist/details/{row['Link ID']}"
                        name = row["Substance name"]
                        cas = row["CAS no"]
                        html_links += f'<li><strong>{name}</strong> ({cas}) - <a href="{url}" target="_blank">View 🔗</a></li>\n'
                if html_links:
                    st.markdown(f"#### 🔗 {section_title}")
                    st.markdown(f"<ul>{html_links}</ul>", unsafe_allow_html=True)

            # --- Show diffs + links ---
            show_table(changed_entries, "🔄 Changed Entries")
            show_table(new_entries, "🆕 New Entries")
            show_table(removed_entries, "❌ Removed Entries")

            # --- Full Table ---
            st.markdown("---")
            st.subheader(f"📋 Full List for {today.strftime('%Y-%m-%d')}")
            df_full = df_new.reset_index()
            if "Link ID" in df_full.columns:
                df_full["Details"] = df_full["Link ID"].apply(
                    lambda link_id: f'[🔗](https://echa.europa.eu/registry-of-clh-intentions-until-outcome/-/dislist/details/{link_id})'
                    if pd.notna(link_id) else ""
                )
            st.dataframe(df_full, use_container_width=True)

            # --- Full Table Link Section ---
            show_links_section(df_full, f"Full Table Links ({today.strftime('%Y-%m-%d')})")

    except Exception as e:
        st.error(f"An error occurred: {e}")
