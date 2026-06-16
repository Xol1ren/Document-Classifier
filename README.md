# Document Classifier

Document analysis system.

## Stack
- FastAPI
- HTML + JS 
- Google Gemini API
- pdfplumber 

## Features
- Upload PDF
- AI classification of document type

## Run

### Backend
cd back
source venv/bin/activate
pip install -r req.txt
export GEMINI_API_KEY="your_api_key"
uvicorn main:app --reload

### Frontend 
cd front
xdg-open index.html

## Or open file front/index.html
