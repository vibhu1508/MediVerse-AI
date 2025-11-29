from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import requests
import json
import time
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Doctor Finder API", version="1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATA MODELS ---
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
    score: Optional[float] = None  # For recommendation ranking


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
        print(f"[ERROR] Error fetching data from Practo: {e}")
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
    except AttributeError as e:
        print(f"[ERROR] Error parsing doctors: {e}")
        pass
    return doctors_list


def calculate_score(doc: Doctor):
    """
    Recommendation Engine Logic:
    Score = Rating + (Experience * 1.5) + (sqrt(Reviews) * 5)
    This formula prioritizes experience and reviews while considering rating.
    """
    rating = doc.rating if doc.rating else 0
    exp = doc.experience if doc.experience else 0
    reviews = doc.reviews if doc.reviews else 0
    
    score = rating + (exp * 1.5) + (reviews ** 0.5 * 5)
    return score


# --- API ENDPOINTS ---

@app.get("/")
def home():
    return {
        "status": "healthy",
        "service": "Doctor Finder & Recommendation API",
        "message": "Use /search endpoint to find doctors"
    }


@app.get("/search", response_model=List[Doctor])
def search_doctors(
    city: str, 
    query: str, 
    pages: int = Query(3, ge=1, le=10, description="Number of pages to scrape (max 10)")
):
    """
    Search for doctors ranked by recommendation score.
    
    Formula: Score = Rating + (Experience * 1.5) + (sqrt(Reviews) * 5)
    """
    all_doctors = []
    seen_ids = set()

    # Scrape data across multiple pages
    for page in range(1, pages + 1):
        print(f"[INFO] Scraping page {page} for '{query}' in {city}...")
        data = fetch_practo_data(city, query, page)
        if data:
            parsed_docs = parse_doctors(data)
            for doc in parsed_docs:
                if doc.id not in seen_ids:
                    seen_ids.add(doc.id)
                    all_doctors.append(doc)
        time.sleep(0.3)  # Respectful rate limiting

    if not all_doctors:
        raise HTTPException(status_code=404, detail=f"No doctors found for '{query}' in {city}")

    # Apply recommendation engine scoring
    for doc in all_doctors:
        doc.score = calculate_score(doc)
    
    # Sort by score descending (highest score first)
    sorted_doctors = sorted(all_doctors, key=lambda d: d.score or 0, reverse=True)

    return sorted_doctors


@app.get("/search/specialty", response_model=List[Doctor])
def search_by_specialty(
    city: str, 
    specialty: str,
    pages: int = Query(2, ge=1, le=5)
):
    """Search doctors by specialty"""
    return search_doctors(city=city, query=specialty, pages=pages)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=False
    )
