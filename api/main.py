"""
MediVerse AI - Simplified FastAPI Application
A stateless API using Google File Search for medical data processing.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from .models import (
    RecordType, HealthCheckResponse, ProcessResponse,
    QueryRequest, QueryResponse, ReportRequest, ReportResponse
)
from .services import MedicalDataProcessor, FileSearchService

load_dotenv()


# =============================================================================
# APP LIFECYCLE
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager"""
    print("🚀 Starting MediVerse AI Stateless API...")
    yield
    print("👋 MediVerse AI Stateless API shutdown complete")


# =============================================================================
# APP INITIALIZATION
# =============================================================================

app = FastAPI(
    title="MediVerse AI Stateless API",
    description="A simple API for processing medical documents and queries using Google's File Search.",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.get("/", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    gemini_status = "configured" if os.getenv("API_KEY") else "not configured"
    return HealthCheckResponse(status="healthy", gemini_api=gemini_status)


# =============================================================================
# DATA PROCESSING ROUTES
# =============================================================================

@app.post("/api/process/image", response_model=ProcessResponse)
async def process_image(
    user_id: str = Form(...),
    file: UploadFile = File(...),
    record_type: RecordType = Form(default=RecordType.PRESCRIPTION)
):
    """Process an uploaded medical image."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")
    
    contents = await file.read()
    try:
        extracted_text = await MedicalDataProcessor.extract_from_image(contents)
        metadata = {"original_filename": file.filename, "content_type": file.content_type}
        record_id = await FileSearchService.store_record(user_id, extracted_text, record_type, metadata)
        return ProcessResponse(record_id=record_id, user_id=user_id, record_type=record_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {e}")

@app.post("/api/process/audio", response_model=ProcessResponse)
async def process_audio(
    user_id: str = Form(...),
    file: UploadFile = File(...)
):
    """Process an uploaded audio file."""
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="File must be an audio file.")
        
    contents = await file.read()
    try:
        transcribed_text = await MedicalDataProcessor.transcribe_speech(contents)
        metadata = {"original_filename": file.filename, "content_type": file.content_type}
        record_id = await FileSearchService.store_record(user_id, transcribed_text, RecordType.SYMPTOMS, metadata)
        return ProcessResponse(record_id=record_id, user_id=user_id, record_type=RecordType.SYMPTOMS)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio: {e}")

@app.post("/api/process/text", response_model=ProcessResponse)
async def process_text(
    user_id: str = Form(...),
    text: str = Form(...),
    record_type: RecordType = Form(default=RecordType.NOTES)
):
    """Process submitted text."""
    try:
        processed_text = await MedicalDataProcessor.process_text(text)
        metadata = {"source": "manual_text_entry"}
        record_id = await FileSearchService.store_record(user_id, processed_text, record_type, metadata)
        return ProcessResponse(record_id=record_id, user_id=user_id, record_type=record_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing text: {e}")


# =============================================================================
# QUERY & REPORTING ROUTES
# =============================================================================

@app.post("/api/query", response_model=QueryResponse)
async def query_records(request: QueryRequest):
    """Query a user's medical records."""
    try:
        response = await FileSearchService.query_store(request.user_id, request.query)
        return QueryResponse(user_id=request.user_id, query=request.query, response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during query: {e}")

@app.post("/api/report", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    """Generate a report from a user's medical records."""
    try:
        report = await FileSearchService.generate_report(request.user_id, request.summary_prompt)
        return ReportResponse(user_id=request.user_id, report=report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {e}")


# =============================================================================
# RUN SERVER
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
