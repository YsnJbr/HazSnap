import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

st.title("HazSnap - Creating time for you")




# Generate filenames based on today and yesterday's date
today = datetime.now()
yesterday = today - timedelta(days=1)

file_new = f"clh_snapshot_{today.strftime('%Y-%m-%d')}.csv"
file_old = f"clh_snapshot_{yesterday.strftime('%Y-%m-%d')}.csv"





# Check if files exist
if not os.path.isfile(file_old):
    st.error(f"Yesterday's file not found: {file_old}")
elif not os.path.isfile(file_new):
    st.error(f"Today's file not found: {file_new}")
else:
    try:
        df_old = pd.read_csv(file_old)
        df_new = pd.read_csv(file_new)
        st.success(f"📅 ✅ Update for {today.strftime('%Y-%m-%d')} sucussfully reflected vs. yesterday")

        # Composite key columns
        key_cols = ["Substance name", "CAS no"]

        # Verify key columns exist
        if not all(col in df_old.columns and col in df_new.columns for col in key_cols):
            st.error(f"Missing one or more key columns: {key_cols}")
        else:
            df_old.set_index(key_cols, inplace=True)
            df_new.set_index(key_cols, inplace=True)

            # New entries
            new_entries = df_new.loc[~df_new.index.isin(df_old.index)].reset_index()
            # Removed entries
            removed_entries = df_old.loc[~df_old.index.isin(df_new.index)].reset_index()
            # Changed entries
            common_idx = df_old.index.intersection(df_new.index)
            changed_mask = (df_old.loc[common_idx] != df_new.loc[common_idx]).any(axis=1)
            changed_entries = df_new.loc[common_idx][changed_mask].reset_index()

            # --- Summary statistics ---
            st.markdown("### 📊 Summary Statistics")
            st.markdown(f"- 🆕 New entries: **{len(new_entries)}**")
            st.markdown(f"- ❌ Removed entries: **{len(removed_entries)}**")
            st.markdown(f"- 🔄 Changed entries: **{len(changed_entries)}**")
            st.markdown("---")
            # Show message if no changes at all
            if len(new_entries) == 0 and len(removed_entries) == 0 and len(changed_entries) == 0:
                st.info("No new changes detected ✅ - No news today, but silent efforts stir the unseen currents of tomorrow’s success, the story of diligence writes itself in unseen ink ✨")

            if not changed_entries.empty:
                st.subheader("🔄 Changed Entries")
                st.dataframe(changed_entries)
            if not new_entries.empty:
                st.subheader("🆕 New Entries")
                st.dataframe(new_entries)
            if not removed_entries.empty:
                st.subheader("❌ Removed Entries")
                st.dataframe(removed_entries)

---
            # Display full today's dataset
            st.subheader(f"📋 Full List for {today.strftime('%Y-%m-%d')}")
            st.dataframe(df_new.reset_index())
    except Exception as e:
        st.error(f"An error occurred: {e}")
