"""
MediVerse AI - Core Service Layer
Handles data processing and interaction with Google's File Search API
"""

from google import genai
from google.genai import types
import PIL.Image
import os
import io
import time
import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

try:
    from .models import RecordType
except ImportError:
    from models import RecordType

# Initialize Gemini client - handle missing API key gracefully
api_key = os.getenv("API_KEY")
if api_key and api_key not in ["", "your_google_gemini_api_key_here"]:
    try:
        client = genai.Client(api_key=api_key)
        print("[INFO] Google API key loaded successfully")
    except Exception as e:
        print(f"[ERROR] Error initializing Google client: {e}")
        client = None
else:
    client = None
    print("[WARNING] Google API key not configured. Using mock responses.")


class MedicalDataProcessor:
    """Handles OCR, Speech-to-Text, and data extraction"""
    
    @staticmethod
    async def extract_from_image(image_input: bytes) -> str:
        if not client:
            return "[Mock Response] Image analysis: This appears to be a medical document with structured information. Please provide a valid Google API key for real analysis."
        
        img = PIL.Image.open(io.BytesIO(image_input))
        prompt = "Extract all text and relevant medical information from this document. Format it clearly."
        response = client.models.generate_content(model="gemini-2.5-pro", contents=[prompt, img])
        return response.text
    
    @staticmethod
    async def transcribe_speech(audio_input: bytes) -> str:
        if not client:
            return "[Mock Response] Audio transcribed: Patient reports symptoms including concern. Please provide a valid Google API key for real transcription."
        
        temp_path = f"temp_audio_{uuid.uuid4()}.wav"
        with open(temp_path, 'wb') as f:
            f.write(audio_input)
        
        audio_file = client.files.upload(file=temp_path)
        os.remove(temp_path)
        
        while audio_file.state.name == "PROCESSING":
            time.sleep(1)
            audio_file = client.files.get(name=audio_file.name)
            
        prompt = "Transcribe the following audio and summarize any reported medical symptoms."
        response = client.models.generate_content(model="gemini-2.5-pro", contents=[prompt, audio_file])
        client.files.delete(name=audio_file.name)
        return response.text
    
    @staticmethod
    async def process_text(text: str) -> str:
        if not client:
            return f"[Mock Response] Structured analysis of provided text:\n\n{text}\n\nPlease provide a valid Google API key for real analysis."
        
        prompt = f"Analyze and structure the following text regarding medical symptoms:\n\n{text}"
        response = client.models.generate_content(model="gemini-2.5-pro", contents=prompt)
        return response.text


class FileSearchService:
    """Manages Gemini File Search stores for storing and querying medical records"""
    
    STORE_PREFIX = "mediverse_user_"
    _stores = {}  # In-memory store backup when API key is missing
    
    @staticmethod
    async def get_or_create_store(user_id: str) -> str:
        if not client:
            # Mock implementation using in-memory storage
            store_name = f"{FileSearchService.STORE_PREFIX}{user_id}"
            if store_name not in FileSearchService._stores:
                FileSearchService._stores[store_name] = {"records": []}
            return store_name
        
        display_name = f"{FileSearchService.STORE_PREFIX}{user_id}"
        for store in client.file_search_stores.list():
            if store.display_name == display_name:
                return store.name
        store = client.file_search_stores.create(config={'display_name': display_name})
        return store.name
        
    @staticmethod
    async def store_record(user_id: str, content: str, record_type: RecordType, metadata: Dict[str, Any]) -> str:
        store_name = await FileSearchService.get_or_create_store(user_id)
        record_id = str(uuid.uuid4())
        
        # Create a structured text file for indexing
        file_content = f"RECORD_ID: {record_id}\n"
        file_content += f"USER_ID: {user_id}\n"
        file_content += f"RECORD_TYPE: {record_type.value}\n"
        file_content += f"TIMESTAMP: {datetime.utcnow().isoformat()}\n"
        file_content += "METADATA: " + json.dumps(metadata) + "\n"
        file_content += "---\n"
        file_content += "CONTENT:\n" + content
        
        if not client:
            # Store in memory
            if store_name not in FileSearchService._stores:
                FileSearchService._stores[store_name] = {"records": []}
            FileSearchService._stores[store_name]["records"].append({
                "record_id": record_id,
                "content": file_content,
                "record_type": record_type.value
            })
            return record_id
        
        # Real implementation with File Search API
        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)
        temp_file_path = temp_dir / f"{record_id}.txt"
        
        with open(temp_file_path, "w") as f:
            f.write(file_content)
        
        # Upload to File Search store
        operation = client.file_search_stores.upload_to_file_search_store(
            file=str(temp_file_path),
            file_search_store_name=store_name,
            config={'display_name': f"{record_type.value}_{record_id}"}
        )
        
        while not operation.done:
            time.sleep(1)
            operation = client.operations.get(operation)
        
        temp_file_path.unlink()
        
        return record_id
        
    @staticmethod
    async def query_store(user_id: str, query: str) -> str:
        store_name = await FileSearchService.get_or_create_store(user_id)
        
        if not client:
            # Mock query using stored records
            records = FileSearchService._stores.get(store_name, {}).get("records", [])
            if not records:
                return "[Mock Response] No medical records found for this user. Please upload some medical data first."
            
            # Simple mock: return relevant record summaries
            response = f"[Mock Response] Based on your {len(records)} stored medical record(s):\n\n"
            for i, record in enumerate(records, 1):
                record_type = record.get("record_type", "unknown")
                # Extract first 200 chars of content as preview
                content_preview = record.get("content", "")[:300]
                response += f"{i}. {record_type.upper()}: {content_preview}...\n\n"
            response += f"Query asked: '{query}'\n[Note: This is a mock response. Provide a valid Google API key for real AI-powered analysis]"
            return response
        
        system_prompt = "You are a medical assistant AI. Answer questions based ONLY on the user's provided medical records. If information is not in the records, say so. Do not invent medical advice."
        full_query = f"{system_prompt}\n\nUser Question: {query}"
        
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=full_query,
            config=types.GenerateContentConfig(
                tools=[types.Tool(file_search=types.FileSearch(file_search_store_names=[store_name]))]
            )
        )
        return response.text

    @staticmethod
    async def generate_report(user_id: str, summary_prompt: str) -> str:
        store_name = await FileSearchService.get_or_create_store(user_id)

        if not client:
            # Mock report
            records = FileSearchService._stores.get(store_name, {}).get("records", [])
            if not records:
                return "[Mock Report] No medical records available to generate a report. Please upload medical data first."
            
            report = f"[Mock Medical Report]\n\n"
            report += f"Generated: {datetime.utcnow().isoformat()}\n"
            report += f"Records in file: {len(records)}\n\n"
            report += f"Summary Prompt: {summary_prompt}\n\n"
            report += "Stored Record Types:\n"
            for record in records:
                report += f"- {record.get('record_type', 'unknown')}\n"
            report += "\n[Note: This is a mock report. Provide a valid Google API key for real AI-powered analysis]"
            return report

        system_prompt = f"You are a medical report generation AI. Based on all the available medical records for this user, generate a report that addresses the following prompt: '{summary_prompt}'"

        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=system_prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(file_search=types.FileSearch(file_search_store_names=[store_name]))]
            )
        )
        return response.text
