import pandas as pd
import requests

# Load cows data from the parquet file
cows_df = pd.read_parquet('cows.parquet')

# Iterate through each cow record and send it to the API
for _, row in cows_df.iterrows():
    cow_id = row['id']
    payload = {
        "name": row['name'],
        "breed": row['breed'],
        "birth_date": row['birth_date']
    }
    
    response = requests.post(f"http://127.0.0.1:8000/cows/{cow_id}", json=payload)
    
    if response.status_code == 200:
        print(f"Successfully created cow with ID {cow_id}")
    else:
        print(f"Failed to create cow with ID {cow_id}: {response.json()}")
