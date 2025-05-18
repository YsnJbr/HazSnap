import requests
from datetime import datetime
import pandas as pd

def main():
    print("Download CLH Snapshot and Convert to CSV")

    # Use default URL directly, no input
    url = "https://echa.europa.eu/fr/registry-of-clh-intentions-until-outcome"

    print(f"Downloading page from: {url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/113.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        print("Page downloaded successfully!")
        today_str = datetime.now().strftime("%Y-%m-%d")
        html_filename = f"clh_snapshot_{today_str}.html"

        with open(html_filename, "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"Snapshot saved as `{html_filename}`")

        try:
            with open(html_filename, "r", encoding="utf-8") as f:
                html_content = f.read()

            tables = pd.read_html(html_content)
            if tables:
                df = tables[0]
                csv_filename = f"clh_snapshot_{today_str}.csv"
                df.to_csv(csv_filename, index=False)
                print(f"CSV file created: `{csv_filename}`")
                print(f"CSV file ready for use: {csv_filename}")
            else:
                print("No tables found in the downloaded HTML.")
        except Exception as e:
            print(f"Error parsing HTML to CSV: {e}")
    else:
        print(f"Failed to download page. Status code: {response.status_code}")

if __name__ == "__main__":
    main()
