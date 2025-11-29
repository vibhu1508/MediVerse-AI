from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from PIL import Image
import numpy as np
import torch
from torchvision import transforms
from model import UNet
from scipy import ndimage
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
import base64
from io import BytesIO
from pathlib import Path

print("[INFO] Libraries imported successfully")

load_dotenv(Path(__file__).parent / ".env")

app = FastAPI(
    title="MediVerse Brain Tumor Analysis API",
    description="U-Net based brain tumor segmentation with AI-powered diagnosis",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = Path(__file__).parent / "Tumor_model.pth"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Load model
model = UNet(n_classes=1).to(DEVICE)
if MODEL_PATH.exists():
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.eval()
    print(f"[INFO] Model loaded from {MODEL_PATH}")
else:
    print(f"[WARNING] Model not found at {MODEL_PATH}. Using untrained model.")
    model.eval()

UPLOAD_DIR = Path(__file__).parent / "uploaded_images"
UPLOAD_DIR.mkdir(exist_ok=True)

BRAIN_VOLUMES = {"men": 1260, "women": 1130}


def encode_image(img):
    pil_img = Image.fromarray(img)
    buf = BytesIO()
    pil_img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def ai_summary(patient_data):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return "[Mock Response] No Google API key configured. Please set GOOGLE_API_KEY env var for real diagnosis."
    
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            api_key=api_key
        )

        SYSTEM = """You are a professional neurology expert with extensive experience in brain tumor diagnosis. 
        Analyze the tumor measurements and provide a professional diagnosis summary. Include risk assessment and recommendations."""
        
        HUMAN = """Based on the tumor data provided: {patient_data}

Provide a professional diagnosis summary including:
1. Tumor classification based on size
2. Risk assessment
3. Recommendations for further evaluation
4. Clinical significance of the measurements"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM),
            ("human", HUMAN),
        ])

        chain = prompt | llm | StrOutputParser()
        result = chain.invoke({"patient_data": patient_data})
        return result
    except Exception as e:
        print(f"[ERROR] AI summary error: {e}")
        return f"[Error in AI diagnosis]: {str(e)}"


def calculate_tumor_size(mask, gender):
    tumor_pixels = np.sum(mask)
    total_pixels = mask.size

    ratio = tumor_pixels / total_pixels
    volume = ratio * BRAIN_VOLUMES.get(gender, 1260)

    labels, num = ndimage.label(mask)

    if num > 0:
        sizes = ndimage.sum(mask, labels, range(1, num + 1))
        main = np.argmax(sizes) + 1
        slice_ = ndimage.find_objects(labels == main)[0]

        h = slice_[0].stop - slice_[0].start
        w = slice_[1].stop - slice_[1].start
        scale = 14.0 / mask.shape[1]

        width_cm = w * scale
        height_cm = h * scale
        area = tumor_pixels * (scale ** 2)
    else:
        width_cm = height_cm = area = 0

    return {
        "volume_ml": volume,
        "percentage_of_brain": ratio * 100,
        "width_cm": width_cm,
        "height_cm": height_cm,
        "area_cm2": area,
    }


def segment_image(path, gender="men"):
    transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
    ])

    img = Image.open(path).convert("RGB")
    img_t = transform(img)
    tensor = img_t.unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        pred = torch.sigmoid(model(tensor)).cpu().squeeze().numpy()
        mask = (pred > 0.5).astype(np.uint8)

    tumor_data = calculate_tumor_size(mask, gender)

    np_img = (img_t.numpy().transpose(1,2,0) * 255).astype(np.uint8)
    overlay = np.zeros_like(np_img)
    overlay[:,:,0] = mask * 255

    blended = (0.7 * np_img + 0.4 * overlay).astype(np.uint8)

    return blended, tumor_data


@app.get("/")
async def health_check():
    return {
        "status": "healthy",
        "service": "Brain Tumor Analysis API",
        "model_loaded": MODEL_PATH.exists(),
        "device": DEVICE
    }


@app.post("/api/uploadfile")
async def upload_file(file: UploadFile = File(...), gender: str = "men"):
    """Upload and analyze a brain MRI image"""
    save_path = UPLOAD_DIR / file.filename

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        blended, tumor = segment_image(str(save_path), gender)
        summary = ai_summary(tumor)

        return {
            "success": True,
            "message": "Analysis completed successfully",
            "tumor_measurements": tumor,
            "ai_summary": summary,
            "image_base64": encode_image(blended),
            "device_used": DEVICE
        }
    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}")
        return {
            "success": False,
            "message": f"Analysis failed: {str(e)}",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8050,
        reload=False
    )
