import pandas as pd
import os

ESSENTIAL_COLS = ['Substance name', 'CAS no', 'Status', 'Submitter', 'Latest update']


def format_sample_html(df, title):
    df_reset = df.reset_index()
    cols_to_show = [col for col in ESSENTIAL_COLS if col in df_reset.columns]
    df_display = df_reset[cols_to_show].head(5)

    table_html = df_display.to_html(index=False, escape=False, border=0, classes="styled-table")

    styles = """
    <style>
    .styled-table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
        font-size: 14px;
        font-family: Arial, sans-serif;
    }
    .styled-table th, .styled-table td {
        border: 1px solid #dddddd;
        text-align: left;
        padding: 6px;
        vertical-align: top;
        word-wrap: break-word;
    }
    .styled-table th {
        background-color: #f2f2f2;
        text-align: center;
    }
    .styled-table td:nth-child(1) { width: 30%; }
    .styled-table td:nth-child(2) { width: 12%; }
    .styled-table td:nth-child(3) { width: 18%; }
    .styled-table td:nth-child(4) { width: 15%; }
    .styled-table td:nth-child(5) { width: 15%; }
    </style>
    """

    return f"<h3>{title}</h3>{styles}{table_html}<br>"


def generate_email_body(new_df, removed_df, changed_df):
    new_count = len(new_df)
    removed_count = len(removed_df)
    changed_count = len(changed_df)

    summary = f"""
    <p>🆕 <strong>New entries</strong>: {new_count}<br>
    ❌ <strong>Removed entries</strong>: {removed_count}<br>
    🔄 <strong>Changed entries</strong>: {changed_count}</p>
    """

    new_html = format_sample_html(new_df, "New Entries Sample") if new_count else ""
    removed_html = format_sample_html(removed_df, "Removed Entries Sample") if removed_count else ""
    changed_html = format_sample_html(changed_df, "Changed Entries Sample") if changed_count else ""

    body = f"""
    <html>
    <head></head>
    <body>
    {summary}
    {new_html}
    {removed_html}
    {changed_html}
    </body>
    </html>
    """

    return body
