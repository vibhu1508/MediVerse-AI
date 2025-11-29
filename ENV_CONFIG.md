# MediVerse Configuration Guide

## Environment Variables Required

### 1. Frontend (.env.local in mediverse root)
```
# Supabase
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=

# Python API Endpoints
PYTHON_API_URL=http://localhost:8000
ANALYSIS_BACKEND_URL=http://localhost:8050
RECOMMENDATION_BACKEND_URL=http://localhost:8001
```

### 2. Medical API Backend (mediverse/api/.env)
```
# Google Gemini API Key - Required for LLM and File Search
API_KEY=AIzaSyDk-DN9qr8WSOpT0t_KQULyOcc3X47XiAg
```

### 3. Analysis Backend (mediverse/backend/.env)
```
# Google Generative AI API Key for diagnosis
GOOGLE_API_KEY=AIzaSyDk-DN9qr8WSOpT0t_KQULyOcc3X47XiAg
```

### 4. Recommendation Backend (mediverse/services/recommender)
- No env vars required (uses public Practo API)

## Backend Ports

- **Port 8000**: Medical data API (medical-uploads feature)
- **Port 8050**: Brain tumor analysis (U-Net backend)
- **Port 8001**: Doctor recommendation system

## Start Commands

### Terminal 1: Medical API
```powershell
cd mediverse/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2: Analysis Backend (U-Net)
```powershell
cd mediverse/backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install torch torchvision PIL pillow numpy scipy python-dotenv langchain-google-genai langchain-core fastapi uvicorn
python -m uvicorn main:app --host 0.0.0.0 --port 8050 --reload
```

### Terminal 3: Recommendation Backend
```powershell
cd mediverse/services/recommender
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install fastapi uvicorn requests pydantic
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Terminal 4: Next.js Frontend
```powershell
cd mediverse
npm install
npm run dev
```

## Features Integrated

### 1. Medical Data Processing (/medical-uploads)
- Upload prescription images, medical images, audio
- Automatic text extraction via Google Gemini
- LLM-based query on stored medical records
- Medical report generation

**API Endpoints:**
- `POST /api/medical/process/image` - Process medical image
- `POST /api/medical/process/audio` - Transcribe and process audio
- `POST /api/medical/process/text` - Process text input
- `POST /api/medical/query` - Query medical records
- `POST /api/medical/report` - Generate medical report

### 2. Brain Tumor Analysis (/analysis)
- Upload MRI/CT brain scans
- U-Net model-based tumor segmentation
- Automatic tumor size measurement
- AI-powered diagnosis via Gemini
- Tumor metrics (volume, percentage of brain, dimensions)

**API Endpoint:**
- `POST /api/analysis/start` - Analyze brain image

### 3. Doctor Recommendations (/recommendations)
- Search doctors by city and specialization
- Intelligent ranking using recommendation engine
- Formula: Score = Rating + (Experience × 1.5) + (√Reviews × 5)
- Filter by fees, experience, rating

**API Endpoint:**
- `GET /api/recommendations?city=...&query=...&pages=...` - Search doctors

## Testing the Integration

1. Ensure all three backends are running
2. Navigate to each feature page:
   - Medical uploads: http://localhost:3000/medical-uploads
   - Analysis: http://localhost:3000/analysis
   - Recommendations: http://localhost:3000/recommendations
3. Backend health checks:
   - Medical API: http://localhost:8000/docs
   - Analysis: http://localhost:8050/ 
   - Recommendations: http://localhost:8001/

## Troubleshooting

- **Backend not responding**: Ensure the correct port is running
- **Missing API key**: Set GOOGLE_API_KEY in respective .env files
- **CORS errors**: All backends have CORS enabled
- **Model not found**: Tumor_model.pth must be in mediverse/backend/
