from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import requests
import json
import time

app = FastAPI(title="Doctor Finder API", version="1.0")

# --- DATA MODELS ---
# This defines the structure of the data the API will return
class Doctor(BaseModel):
    id: str
    name: str
    specialization: str
    experience: int
    rating: float
    reviews: int
    fees: int
    hospital: str
    locality: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    image: str
    profile_link: str

# --- CORE LOGIC ---

def fetch_practo_data(city: str, keyword: str, page: int):
    base_url = "https://www.practo.com/marketplace-api/dweb/search/provider/v2"
    q_param = [{"word": keyword, "autocompleted": True, "category": "subspeciality"}]
    
    params = {
        "city": city, 
        "page": page, 
        "q": json.dumps(q_param), 
        "results_type": "doctor",
        "url_path": "/search/doctors", 
        "ad_limit": 2, 
        "platform": "desktop_web",
        "topaz": "true", 
        "reach_version": "v4", 
        "enable_partner_listing": "true",
        "placement": "DOCTOR_SEARCH", 
        "show_new_reach_card": "true",
        "tracking_id": "81020639-7184-4756-88b3-d77b5ebe14a8" 
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json"
    }

    try:
        response = requests.get(base_url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def parse_doctors(json_data) -> List[Doctor]:
    doctors_list = []
    try:
        entities = json_data.get("doctors", {}).get("entities", {})
        for doc_id, data in entities.items():
            
            # URL Processing
            raw_url = data.get("profile_url", "")
            full_url = f"https://www.practo.com{raw_url}" if raw_url.startswith("/") else raw_url
            
            # Location Processing
            practice = data.get("practice", {})
            lat = practice.get("latitude") or data.get("locality_latitude")
            lon = practice.get("longitude") or data.get("locality_longitude")

            try:
                lat = float(lat) if lat else None
                lon = float(lon) if lon else None
            except (ValueError, TypeError):
                lat, lon = None, None

            # Create Doctor Object
            doc = Doctor(
                id=str(data.get("id")),
                name=data.get("doctor_name", "Unknown"),
                specialization=data.get("specialization", ""),
                experience=data.get("experience_years", 0) or 0,
                rating=data.get("recommendation_percent", 0) or 0,
                reviews=data.get("reviews_count", 0) or 0,
                fees=data.get("consultation_fees", 0) or 0,
                hospital=practice.get("name", "Clinic"),
                locality=practice.get("locality", ""),
                lat=lat,
                lon=lon,
                image=data.get("profile_photo", {}).get("url", ""),
                profile_link=full_url
            )
            doctors_list.append(doc)
    except AttributeError:
        pass
    return doctors_list

def calculate_score(doc: Doctor):
    """
    The 'Recommendation Engine' Logic:
    Score = Rating + (Experience * 1.5) + (sqrt(Reviews) * 5)
    """
    # Safety check for None values
    rating = doc.rating if doc.rating else 0
    exp = doc.experience if doc.experience else 0
    reviews = doc.reviews if doc.reviews else 0
    
    # The Formula
    score = rating + (exp * 1.5) + (reviews ** 0.5 * 5)
    return score

# --- 2. Update the Search Endpoint ---
@app.get("/search", response_model=List[Doctor])
def search_doctors(
    city: str, 
    query: str, 
    pages: int = Query(5, ge=1, le=10, description="Number of pages to scrape (max 10)")
):
    """
    Search for doctors, ranked by the internal recommendation engine.
    """
    all_doctors = []
    seen_ids = set()

    # 1. Scrape Data
    for page in range(1, pages + 1):
        print(f"Scraping page {page} for {query} in {city}...")
        data = fetch_practo_data(city, query, page)
        if data:
            parsed_docs = parse_doctors(data)
            for doc in parsed_docs:
                if doc.id not in seen_ids:
                    seen_ids.add(doc.id)
                    all_doctors.append(doc)
        time.sleep(0.3)

    if not all_doctors:
        raise HTTPException(status_code=404, detail="No doctors found.")

    # 2. APPLY RECOMMENDATION ENGINE (Sort by Score)
    # We use the calculate_score function as the sorting key
    # reverse=True means highest score first
    sorted_doctors = sorted(all_doctors, key=calculate_score, reverse=True)

    return sorted_doctors

# --- API ENDPOINTS ---

@app.get("/")
def home():
    return {"message": "Doctor Finder API is running. Go to /docs to test it."}

@app.get("/search", response_model=List[Doctor])
def search_doctors(
    city: str, 
    query: str, 
    pages: int = Query(1, ge=1, le=5, description="Number of pages to scrape (max 5)")
):
    """
    Search for doctors in a specific city.
    """
    all_doctors = []
    seen_ids = set()

    for page in range(1, pages + 1):
        data = fetch_practo_data(city, query, page)
        if data:
            parsed_docs = parse_doctors(data)
            
            # Deduplication logic
            for doc in parsed_docs:
                if doc.id not in seen_ids:
                    seen_ids.add(doc.id)
                    all_doctors.append(doc)
        
        # Respectful delay to avoid IP blocks
        time.sleep(0.3)

    if not all_doctors:
        raise HTTPException(status_code=404, detail="No doctors found for these criteria.")

    return all_doctors