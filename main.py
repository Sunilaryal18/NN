from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# In-memory database to store cows data
cows_db = {}
# Define the data structure for a cow using Pydantic
class Cow(BaseModel):
    name: str
    breed: str
    birth_date: str  # You can adjust the date format later

# Endpoint to create a new cow
@app.post("/cows/{id}")
def create_cow(id: int, cow: Cow):
    if id in cows_db:
        return {"error": "Cow with this ID already exists"}
    
    cows_db[id] = cow
    return {"message": "Cow created successfully", "data": cow}

@app.get("/cows/{id}")
def get_cow(id: int):
    cow = cows_db.get(id)
    if not cow:
        return {"error": "Cow not found"}
    
    return {"data": cow}