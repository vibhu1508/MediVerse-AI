import pytest
import httpx
from fastapi.testclient import TestClient
from api.main import app
from unittest.mock import AsyncMock

# =============================================================================
# MOCKS & FIXTURES
# =============================================================================

@pytest.fixture
def client():
    """Provides a test client for the FastAPI app."""
    return TestClient(app)

@pytest.fixture
def mock_gemini_services(mocker):
    """Mocks the external Gemini API services."""
    mocker.patch(
        'api.services.MedicalDataProcessor.extract_from_image',
        new_callable=AsyncMock,
        return_value="Extracted text from image."
    )
    mocker.patch(
        'api.services.MedicalDataProcessor.transcribe_speech',
        new_callable=AsyncMock,
        return_value="Transcribed text from audio."
    )
    mocker.patch(
        'api.services.MedicalDataProcessor.process_text',
        new_callable=AsyncMock,
        return_value="Processed text."
    )
    mocker.patch(
        'api.services.FileSearchService.store_record',
        new_callable=AsyncMock,
        return_value="mock_record_id_123"
    )
    mocker.patch(
        'api.services.FileSearchService.query_store',
        new_callable=AsyncMock,
        return_value="This is the AI's answer to your query."
    )
    mocker.patch(
        'api.services.FileSearchService.generate_report',
        new_callable=AsyncMock,
        return_value="This is the generated AI medical report."
    )

# =============================================================================
# TESTS
# =============================================================================

def test_health_check(client):
    """Tests the health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["status"] == "healthy"
    assert "gemini_api" in json_response

def test_process_image(client, mock_gemini_services):
    """Tests the image processing endpoint."""
    with open("dummy_image.png", "wb") as f:
        f.write(b"fake image data")

    with open("dummy_image.png", "rb") as f:
        files = {'file': ('dummy_image.png', f, 'image/png')}
        data = {'user_id': 'test_user_123', 'record_type': 'prescription'}
        response = client.post("/api/process/image", files=files, data=data)

    assert response.status_code == 200
    json_response = response.json()
    assert json_response["user_id"] == "test_user_123"
    assert json_response["record_type"] == "prescription"
    assert "record_id" in json_response

def test_process_audio(client, mock_gemini_services):
    """Tests the audio processing endpoint."""
    with open("dummy_audio.wav", "wb") as f:
        f.write(b"fake audio data")

    with open("dummy_audio.wav", "rb") as f:
        files = {'file': ('dummy_audio.wav', f, 'audio/wav')}
        data = {'user_id': 'test_user_audio'}
        response = client.post("/api/process/audio", files=files, data=data)
        
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["user_id"] == "test_user_audio"
    assert json_response["record_type"] == "symptoms"
    assert "record_id" in json_response

def test_process_text(client, mock_gemini_services):
    """Tests the text processing endpoint."""
    data = {'user_id': 'test_user_text', 'text': 'I have a headache.'}
    response = client.post("/api/process/text", data=data)
    
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["user_id"] == "test_user_text"
    assert json_response["record_type"] == "notes"
    assert "record_id" in json_response

def test_query_records(client, mock_gemini_services):
    """Tests the query endpoint."""
    json_data = {'user_id': 'query_user', 'query': 'What are my symptoms?'}
    response = client.post("/api/query", json=json_data)
    
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["user_id"] == "query_user"
    assert json_response["query"] == "What are my symptoms?"
    assert json_response["response"] == "This is the AI's answer to your query."

def test_generate_report(client, mock_gemini_services):
    """Tests the report generation endpoint."""
    json_data = {'user_id': 'report_user', 'summary_prompt': 'Generate a summary.'}
    response = client.post("/api/report", json=json_data)
    
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["user_id"] == "report_user"
    assert json_response["report"] == "This is the generated AI medical report."
