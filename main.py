from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import asyncio
import time
import base64
import io
from PIL import Image
import pytesseract
import logging
from qa_engine import QAEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TDS Virtual TA",
    description="Virtual Teaching Assistant for Tools in Data Science course",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize QA Engine
qa_engine = QAEngine()

class QuestionRequest(BaseModel):
    question: str
    image: Optional[str] = None

class Link(BaseModel):
    url: str
    text: str

class QuestionResponse(BaseModel):
    answer: str
    links: List[Link]

def extract_text_from_image(base64_image: str) -> str:
    """Extract text from base64-encoded image using OCR"""
    try:
        # Decode base64 image
        image_data = base64.b64decode(base64_image)
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Extract text using OCR
        extracted_text = pytesseract.image_to_string(image)
        return extracted_text.strip()
    
    except Exception as e:
        logger.error(f"Error extracting text from image: {str(e)}")
        return ""

@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {
        "message": "TDS Virtual TA API is running",
        "version": "1.0.0",
        "endpoints": {
            "api": "/api/",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()}

@app.post("/api/", response_model=QuestionResponse)
async def process_question(request: QuestionRequest):
    """
    Process student question and return relevant answers with supporting links
    """
    start_time = time.time()
    
    try:
        # Combine question text with OCR text if image is provided
        full_question = request.question
        
        if request.image:
            try:
                ocr_text = extract_text_from_image(request.image)
                if ocr_text:
                    full_question = f"{request.question}\n\nExtracted from image: {ocr_text}"
            except Exception as e:
                logger.warning(f"Failed to process image: {str(e)}")
        
        # Process question with timeout
        try:
            # Use asyncio.wait_for to enforce 30-second timeout
            answer_data = await asyncio.wait_for(
                asyncio.to_thread(qa_engine.get_answer, full_question),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=408,
                detail="Request timeout: Could not process question within 30 seconds"
            )
        
        # Format response
        response = QuestionResponse(
            answer=answer_data["answer"],
            links=[
                Link(url=link["url"], text=link["text"])
                for link in answer_data["links"]
            ]
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Question processed in {processing_time:.2f} seconds")
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/api/stats")
async def get_stats():
    """Get statistics about the knowledge base"""
    try:
        stats = qa_engine.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve statistics"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
