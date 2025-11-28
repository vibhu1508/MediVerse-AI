"""
MediVerse AI - API Request/Response Models
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


# =============================================================================
# ENUMS
# =============================================================================

class RecordType(str, Enum):
    PRESCRIPTION = "prescription"
    SYMPTOMS = "symptoms"
    LAB_REPORT = "lab_report"
    NOTES = "notes"


# =============================================================================
# API REQUEST/RESPONSE MODELS
# =============================================================================

class HealthCheckResponse(BaseModel):
    status: str
    gemini_api: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ProcessResponse(BaseModel):
    record_id: str
    user_id: str
    record_type: RecordType
    status: str = "processed"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class QueryRequest(BaseModel):
    user_id: str
    query: str

class QueryResponse(BaseModel):
    user_id: str
    query: str
    response: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ReportRequest(BaseModel):
    user_id: str
    summary_prompt: Optional[str] = "Summarize the patient's medical history, including key diagnoses, medications, and recent symptoms."

class ReportResponse(BaseModel):
    user_id: str
    report: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
