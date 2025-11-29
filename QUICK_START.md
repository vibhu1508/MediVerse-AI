# 🚀 MediVerse Quick Start Guide

## ⚡ TL;DR - One Command to Start Everything

**PowerShell**:
```powershell
cd c:\Users\MOHIT MATHANGI\Mohit\supa
.\START_ALL.ps1
```

**Command Prompt**:
```cmd
cd c:\Users\MOHIT MATHANGI\Mohit\supa
START_ALL.bat
```

This opens 4 terminal windows automatically:
- Medical API (port 8000)
- Brain Tumor Analysis (port 8050)  
- Doctor Recommendations (port 8001)
- Next.js Frontend (port 3000)

---

## 📱 Access Your Features

Once running, visit:

1. **Medical Uploads** → http://localhost:3000/medical-uploads
   - Upload prescription images, medical scans, or audio
   - Get LLM-powered analysis and summaries

2. **Brain Tumor Analysis** → http://localhost:3000/analysis
   - Upload brain MRI images
   - Get AI segmentation and diagnosis
   - See tumor measurements and risk assessment

3. **Doctor Finder** → http://localhost:3000/recommendations
   - Search doctors by city and specialty
   - Intelligent ranking algorithm
   - See ratings, experience, fees

---

## 🔌 API Documentation

**Medical API docs**: http://localhost:8000/docs
**Recommendation API docs**: http://localhost:8001/docs

---

## 📋 File Structure

```
mediverse/
├── backend/                           # Brain Tumor Analysis (Port 8050)
│   ├── main.py                       # FastAPI server
│   ├── model.py                      # U-Net architecture
│   ├── unet_utils.py                 # Neural network components
│   ├── Tumor_model.pth               # Pre-trained model (download needed)
│   └── .env                          # Google API key
│
├── api/                              # Medical Data API (Port 8000)
│   ├── main.py                       # FastAPI server
│   ├── services.py                   # Google Gemini integration
│   ├── models.py                     # Request/Response schemas
│   └── .env                          # API key
│
├── services/recommender/             # Doctor Finder (Port 8001)
│   ├── main.py                       # FastAPI + Practo scraper
│   └── requirements.txt
│
├── src/app/
│   ├── api/
│   │   ├── analysis/start/route.ts   # ✨ Proxy to U-Net backend
│   │   ├── recommendations/route.ts  # ✨ Proxy to recommender
│   │   └── medical/*                 # Already set up
│   │
│   ├── analysis/page.tsx             # Brain tumor UI
│   ├── medical-uploads/page.tsx      # Medical data UI
│   └── recommendations/page.tsx      # ✨ Doctor finder UI (NEW)
│
├── src/services/
│   ├── analysisService.ts            # Updated to proxy
│   ├── medicalDataService.ts         # Already set up
│   └── recommendationService.ts      # ✨ Doctor search (NEW)
│
└── INTEGRATION_COMPLETE.md           # Full documentation
```

---

## ✅ What's Integrated

| Feature | Backend | Frontend | Status |
|---------|---------|----------|--------|
| Brain Tumor Analysis | U-Net (Port 8050) | /analysis | ✅ Complete |
| Medical Data Processing | Gemini API (Port 8000) | /medical-uploads | ✅ Complete |
| Doctor Recommendations | Practo (Port 8001) | /recommendations | ✅ Complete |

---

## 🔑 Environment Variables

Created automatically, but key files:

- `mediverse/.env.local` - Frontend config
- `mediverse/api/.env` - Medical API key
- `mediverse/backend/.env` - Analysis API key

The API key provided: `AIzaSyDk-DN9qr8WSOpT0t_KQULyOcc3X47XiAg`

---

## ⚠️ Important Notes

1. **Model File**: Download `Tumor_model.pth` from unet_final folder and place in `mediverse/backend/` if not present

2. **First Run**: First startup will install dependencies (~2-5 mins depending on internet)

3. **Python 3.8+**: Required. Check with `python --version`

4. **Node.js 18+**: Required for Next.js. Check with `node --version`

5. **GPU Optional**: PyTorch will use CPU if no GPU available (slower analysis)

---

## 🐛 If Something Goes Wrong

**Port already in use?**
```powershell
netstat -ano | findstr :8000  # Find what's using port 8000
taskkill /PID <PID> /F        # Kill the process
```

**Module not found?**
```powershell
pip install torch torchvision pillow numpy scipy python-dotenv langchain-google-genai langchain-core fastapi uvicorn
```

**torch not installing?** (Use CPU version)
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

---

## 📖 Full Documentation

See `INTEGRATION_COMPLETE.md` for:
- Architecture details
- Manual startup instructions
- Troubleshooting guide
- API endpoint reference
- Feature workflows

---

## 🎯 Next Steps

1. Run `START_ALL.ps1` or `START_ALL.bat`
2. Wait for all 4 terminal windows to show "Running" messages
3. Open http://localhost:3000 in your browser
4. Test each feature page
5. Check backend health at `/docs` URLs

**Enjoy! 🏥**
