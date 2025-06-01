import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

from st_aggrid import AgGrid, GridOptionsBuilder

st.set_page_config(page_title="HazSnap", layout="wide")
st.title("HazSnap")
st.markdown("### *Creating time for you 🧪📸*")

# --- Date handling ---
today = datetime.now()
yesterday = today - timedelta(days=1)

file_new = os.path.join("Data", f"clh_snapshot_{today.strftime('%Y-%m-%d')}.csv")
file_old = os.path.join("Data", f"clh_snapshot_{yesterday.strftime('%Y-%m-%d')}.csv")

# --- Check if files exist ---
if not os.path.isfile(file_old):
    st.error(f"Yesterday's file not found: {file_old}")
elif not os.path.isfile(file_new):
    st.error(f"Today's file not found: {file_new}")
else:
    try:
        # Load CSVs
        df_old = pd.read_csv(file_old)
        df_new = pd.read_csv(file_new)
        st.success(f"📅 ✅ Update for {today.strftime('%Y-%m-%d')} successfully reflected vs. yesterday")

        # Composite key to detect changes
        key_cols = ["Substance name", "CAS no"]
        if not all(col in df_old.columns and col in df_new.columns for col in key_cols):
            st.error(f"Missing one or more key columns: {key_cols}")
        else:
            df_old.set_index(key_cols, inplace=True)
            df_new.set_index(key_cols, inplace=True)

            new_entries = df_new.loc[~df_new.index.isin(df_old.index)].reset_index()
            removed_entries = df_old.loc[~df_old.index.isin(df_new.index)].reset_index()
            common_idx = df_old.index.intersection(df_new.index)
            changed_mask = (df_old.loc[common_idx] != df_new.loc[common_idx]).any(axis=1)
            changed_entries = df_new.loc[common_idx][changed_mask].reset_index()

            # --- Summary statistics ---
            st.markdown("### 📊 Summary Statistics")
            st.markdown(f"- 🆕 New entries: **{len(new_entries)}**")
            st.markdown(f"- ❌ Removed entries: **{len(removed_entries)}**")
            st.markdown(f"- 🔄 Changed entries: **{len(changed_entries)}**")
            st.markdown("---")

            if len(new_entries) == 0 and len(removed_entries) == 0 and len(changed_entries) == 0:
                st.info("No new changes detected ✅ - Silent efforts stir the unseen currents of tomorrow’s success ✨")

            # --- Render detailed entries ---
            def render_aggrid(df, label):
                if not df.empty:
                    st.subheader(label)
                    gb = GridOptionsBuilder.from_dataframe(df)
                    if "Link ID" in df.columns:
                        df["Details"] = df["Link ID"].apply(
                            lambda link_id: f'<a href="https://echa.europa.eu/registry-of-clh-intentions-until-outcome/-/dislist/details/{link_id}" target="_blank">🔗 Details</a>'
                            if pd.notna(link_id) else ""
                        )
                        gb.configure_column("Details", cellRenderer='''function(params) { return params.value; }''')
                    grid = AgGrid(
                        df,
                        gridOptions=gb.build(),
                        allow_unsafe_jscode=True,
                        fit_columns_on_grid_load=True,
                        height=300
                    )

            render_aggrid(changed_entries, "🔄 Changed Entries")
            render_aggrid(new_entries, "🆕 New Entries")
            render_aggrid(removed_entries, "❌ Removed Entries")

            # --- Full table preview ---
            st.markdown('---')
            st.subheader(f"📋 Full List for {today.strftime('%Y-%m-%d')}")
            df_full = df_new.reset_index()

            if "Link ID" in df_full.columns:
                df_full["Details"] = df_full["Link ID"].apply(
                    lambda link_id: f'<a href="https://echa.europa.eu/registry-of-clh-intentions-until-outcome/-/dislist/details/{link_id}" target="_blank">🔗 Details</a>'
                    if pd.notna(link_id) else ""
                )

            gb_full = GridOptionsBuilder.from_dataframe(df_full)
            gb_full.configure_column("Details", cellRenderer='''function(params) { return params.value; }''')

            AgGrid(
                df_full,
                gridOptions=gb_full.build(),
                allow_unsafe_jscode=True,
                fit_columns_on_grid_load=True,
                height=500
            )

    except Exception as e:
        st.error(f"An error occurred: {e}")
