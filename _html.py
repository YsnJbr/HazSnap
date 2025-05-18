import pandas as pd

tables = pd.read_html("clh_snapshot_2025-05-18.html")
print(f"Found {len(tables)} tables.")
print(tables[0].head())
