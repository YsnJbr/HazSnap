import os
import requests
from datetime import datetime
import pandas as pd
from lxml import html

def main():
    print("Downloading CLH Snapshot and Extracting Detail Links...")

    # Base URLs
    base_url = "https://echa.europa.eu"
    page_url = f"{base_url}/fr/registry-of-clh-intentions-until-outcome"
    link_constant = "https://echa.europa.eu/registry-of-clh-intentions-until-outcome/-/dislist/details/"

    # HTTP headers to simulate a real browser
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/113.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://echa.europa.eu/",
        "Connection": "keep-alive",
    }

    # Download the webpage
    response = requests.get(page_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to download page. Status code: {response.status_code}")
        return

    # Create output paths
    today_str = datetime.now().strftime("%Y-%m-%d")
    os.makedirs("Data", exist_ok=True)
    html_path = f"Data/clh_snapshot_{today_str}.html"
    csv_path = f"Data/clh_snapshot_{today_str}.csv"

    # Save HTML snapshot locally
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(response.text)
    print(f"HTML saved to: {html_path}")

    # Try to extract the table using pandas
    try:
        df = pd.read_html(response.text)[0]  # Extract first table
        df = df.dropna(how='all')  # Drop completely empty rows
        df.columns = df.columns.str.strip()  # Clean column names
        df = df.loc[:, df.columns.notna()]  # Drop unnamed/NaN columns
        df = df.loc[:, df.columns != 'Unnamed: 0']  # Drop auto-generated index column if any
        df = df.dropna(axis=1, how='all')  # Drop columns that are fully empty
    except Exception as e:
        print(f"Error reading table: {e}")
        return

    # Parse detail links using XPath
    tree = html.fromstring(response.content)
    table_rows = tree.xpath('//table//tr[position()>1]')

    detail_links = []
    link_ids = []

    for tr in table_rows:
        hrefs = tr.xpath('./td[last()]//a/@href')
        if hrefs:
            full_link = base_url + hrefs[0]
            link_id = full_link.strip().split("/")[-1]
            detail_links.append(full_link)
            link_ids.append(link_id)
        else:
            detail_links.append("")
            link_ids.append("")

    # Add raw links and IDs to DataFrame
    df["Details Link"] = detail_links
    df["Link ID"] = link_ids
    df["Link Constant"] = link_constant

    # Add clickable HTML 'Details' column
    
    df["Details"] = df["Link ID"].apply(
        lambda link_id: f'<a href="{link_constant}{link_id}" target="_blank">Details</a>' if link_id else ""
    )

    # Remove unnecessary columns before saving
    columns_to_drop = ["Unnamed: 7", "Details Link", "Link Constant"]
    df = df.drop(columns=[col for col in columns_to_drop if col in df.columns])

    # Save final CSV
    df.to_csv(csv_path, index=False)
    print(f"CSV with detail links saved to: {csv_path}")

if __name__ == "__main__":
    main()
