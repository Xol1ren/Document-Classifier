import os
import pdfplumber
import tempfile
from google import genai
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(title="Document Classifier")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """
You are a professional document classification used by bank.

You will receive text extracted from a PDF document. 
The content may come from OCR and can contain formatting errors, missing characters, multiple languages (Kyrgyz, Russian, English), tables, stamps, signatures, or scanned text.

Your tasks:

1. Classify the document type.
2. Extract important metadata and key fields.

Possible document types include:
- passport_kg
- id_card_kg
- birth_certificate
- marriage_certificate
- divorce_certificate
- income_certificate
- employment_certificate
- pension_certificate
- bank_statement
- loan_agreement
- contract
- court_decision
- tax_document
- property_certificate
- vehicle_registration
- power_of_attorney
- diploma
- medical_certificate
- government_document
- other

Extraction rules:
- Use only information explicitly found in the document.
- Do not invent or infer missing values.
- If a field is not found, return null.
- If multiple names exist, identify the primary document holder whenever possible.
- Normalize dates to YYYY-MM-DD when possible.
- If the document type is uncertain, return "other".
- Return ONLY valid JSON.
- Do not include explanations, markdown, comments, or additional text.

Required JSON format:

{
  "document_type": "string",
  "fields": {
    "full_name": "string or null",
    "date": "string or null",
    "document_number": "string or null",
    "issuing_authority": "string or null"
  },
  "summary": "Brief 1-2 sentence description of the document."
}
"""

@app.get("/")
def root():
    return {"status": "ok", "message": "Document Classifier"}

@app.post("/classify")
async def classify_document(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Загрузите PDF файл")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        text = ""
        with pdfplumber.open(tmp_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    finally:
        os.unlink(tmp_path)

    if not text.strip():
        raise HTTPException(
            status_code=422,
            detail="Не удалось извлечь текст из PDF."
        )

    text_snippet = text[:15000]

    message = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=f"""

    {SYSTEM_PROMPT}

    Document text:

    {text_snippet}
    """
    )

    raw = message.text.strip()

    import json
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"Ошибка парсинга ответа ИИ: {raw}")

    return JSONResponse(content={
        "filename": file.filename,
        "pages_text_length": len(text),
        "result": result
    })