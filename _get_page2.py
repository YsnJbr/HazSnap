import os
import requests
from datetime import datetime
import pandas as pd
from lxml import html  # Lightweight alternative to BeautifulSoup

def main():
    print("Downloading CLH Snapshot and Extracting Detail Links...")

    base_url = "https://echa.europa.eu"
    page_url = f"{base_url}/fr/registry-of-clh-intentions-until-outcome"

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

    response = requests.get(page_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to download page. Status code: {response.status_code}")
        return

    today_str = datetime.now().strftime("%Y-%m-%d")
    os.makedirs("Data", exist_ok=True)
    html_path = f"Data/clh_snapshot_{today_str}.html"
    csv_path = f"Data/clh_snapshot_{today_str}.csv"

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(response.text)
    print(f"HTML saved to: {html_path}")

    try:
        df = pd.read_html(response.text)[0]
        df = df.dropna(how='all')
        df.columns = df.columns.str.strip()
        df = df.loc[:, df.columns.notna()]
        df = df.loc[:, df.columns != 'Unnamed: 0']
        df = df.dropna(axis=1, how='all')
    except Exception as e:
        print(f"Error reading table: {e}")
        return

    tree = html.fromstring(response.content)
    table_rows = tree.xpath('//table//tr[position()>1]')

    detail_links = []
    for tr in table_rows:
        hrefs = tr.xpath('./td[last()]//a/@href')
        if hrefs:
            full_link = base_url + hrefs[0]
            detail_links.append(full_link)
        else:
            detail_links.append("")

    df["Details Link"] = detail_links
    df["Details"] = df["Details Link"].apply(lambda u: f'<a href="{u}" target="_blank">Details</a>' if u else "")

    df.to_csv(csv_path, index=False)
    print(f"CSV with detail links saved to: {csv_path}")

if __name__ == "__main__":
    main()
