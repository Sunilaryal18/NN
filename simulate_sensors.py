import pandas as pd
import requests

# Load measurements from the parquet file
measurements_df = pd.read_parquet('measurements.parquet')

# Iterate through each record and send it to the API
for _, row in measurements_df.iterrows():
    cow_id = row['cow_id']
    payload = {
        "date": row['date'],
        "weight": row['weight'] if not pd.isna(row['weight']) else None,
        "milk_production": row['milk_production'] if not pd.isna(row['milk_production']) else None
    }
    
    response = requests.post(f"http://127.0.0.1:8000/cows/{cow_id}/sensor-data", json=payload)
    
    if response.status_code == 200:
        print(f"Successfully sent data for cow {cow_id}")
    else:
        print(f"Failed to send data for cow {cow_id}: {response.json()}")
