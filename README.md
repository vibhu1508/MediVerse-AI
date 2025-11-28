# MediVerse AI Stateless API

MediVerse AI is a simplified, stateless API for intelligent medical records management. It uses FastAPI and Google's File Search as a backend for processing, storing, and querying medical data. This version removes the need for a database and user authentication, focusing on the core functionalities of data processing and retrieval.

## Features

- **Stateless Architecture**: No database or user accounts required.
- **Multi-Modal Data Processing**: Upload and process medical data from images, audio, and text. Each record is stored securely in a user-specific Google File Search store.
- **AI-Powered Querying**: Ask natural language questions about a user's medical history using Retrieval-Augmented Generation (RAG).
- **Automated Report Generation**: Create comprehensive medical summaries from a user's stored records.

## Setup and Installation

### Prerequisites

- Python 3.8+
- `pip` for package management

### 1. Clone the Repository

```bash
git clone https://github.com/your-repo/MediVerse-AI.git
cd MediVerse-AI
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root of the project by copying the example file:

```bash
cp .env.example .env
```

Now, edit the `.env` file with your Google Gemini API key:

```env
# Gemini API Key
API_KEY="your_google_gemini_api_key"
```

## Running the API

Once the setup is complete, you can run the FastAPI server using Uvicorn.

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`. You can access the interactive API documentation (provided by Swagger UI) at `http://localhost:8000/docs`.

## How It Works

Each `user_id` you provide to the API endpoints corresponds to a unique, isolated Google File Search store. This ensures that a user's data is only used when querying or generating reports for that same `user_id`.

### API Endpoints

- `POST /api/process/image`: Upload an image, process it, and store it for a given `user_id`.
- `POST /api/process/audio`: Upload an audio file, transcribe it, and store it.
- `POST /api/process/text`: Submit text for analysis and storage.
- `POST /api/query`: Ask a question about a `user_id`'s records.
- `POST /api/report`: Generate a summary report for a `user_id`.
