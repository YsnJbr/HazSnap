import os
import time
import requests
from datetime import datetime
import pandas as pd
from lxml import html

def cleanup_old_files(folder="Data", days=30):
    print(f"\nCleaning up files older than {days} days in '{folder}'...")
    now = time.time()
    cutoff = now - (days * 86400)  # 86400 seconds per day
    deleted_files = 0

    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.path.isfile(file_path):
            file_modified = os.path.getmtime(file_path)
            if file_modified < cutoff:
                try:
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
                    deleted_files += 1
                except Exception as e:
                    print(f"Failed to delete {file_path}: {e}")

    print(f"Cleanup complete. {deleted_files} file(s) deleted.\n")

def main():
    print("=== Downloading CLH Snapshot (200 entries) and Extracting Detail Links ===")

    base_url = "https://echa.europa.eu"
    page_url = (
        f"{base_url}/en/registry-of-clh-intentions-until-outcome"
        "?p_p_id=disslists_WAR_disslistsportlet"
        "&p_p_lifecycle=0"
        "&p_p_state=normal"
        "&p_p_mode=view"
        "&_disslists_WAR_disslistsportlet_delta=200"
    )
    link_constant = f"{base_url}/registry-of-clh-intentions-until-outcome/-/dislist/details/"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/113.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": base_url,
        "Connection": "keep-alive",
    }

    print(f"Requesting page: {page_url}")
    response = requests.get(page_url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to download page. Status code: {response.status_code}")
        return
    print("✅ Page downloaded successfully.")

    today_str = datetime.now().strftime("%Y-%m-%d")
    os.makedirs("Data", exist_ok=True)
    html_path = f"Data/clh_snapshot_{today_str}.html"
    csv_path = f"Data/clh_snapshot_{today_str}.csv"

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(response.text)
    print(f"📄 HTML saved to: {html_path}")

    try:
        df = pd.read_html(response.text)[0]
        df = df.dropna(how='all')
        df.columns = df.columns.str.strip()
        df = df.loc[:, df.columns.notna()]
        if 'Unnamed: 0' in df.columns:
            df = df.drop(columns=['Unnamed: 0'])
        df = df.dropna(axis=1, how='all')
        print(f"✅ Table extracted. Rows: {len(df)} Columns: {list(df.columns)}")
    except Exception as e:
        print(f"❌ Error reading table: {e}")
        return

    tree = html.fromstring(response.content)
    table_rows = tree.xpath('//table//tr[position()>1]')
    print(f"🔗 Extracting detail links from {len(table_rows)} rows...")

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

    df["Details Link"] = detail_links
    df["Link ID"] = link_ids
    df["Link Constant"] = link_constant
    df["Details"] = df["Link ID"].apply(
        lambda link_id: f'<a href="{link_constant}{link_id}" target="_blank">Details</a>' if link_id else ""
    )

    columns_to_drop = ["Unnamed: 7", "Details Link", "Link Constant"]
    df = df.drop(columns=[col for col in columns_to_drop if col in df.columns])


    df.to_csv(csv_path, index=False)
    print(f"📄 CSV with detail links saved to: {csv_path}")

    cleanup_old_files()

if __name__ == "__main__":
    main()
