# TDS Virtual TA

A FastAPI-based virtual Teaching Assistant for the "Tools in Data Science (TDS)" course offered in IIT Madras' Online BSc Degree program.

## Features

- **Question Processing**: Accept student questions as text input
- **Image OCR**: Process base64-encoded images to extract text using OCR
- **Knowledge Base Search**: Search through scraped Discourse forum posts and course content
- **Intelligent Matching**: Use fuzzy text matching to find relevant answers
- **Fast Response**: Process and respond within 30 seconds
- **Supporting Links**: Provide relevant links to source materials and forum discussions

## API Endpoints

### POST `/api/`

Process student questions and return relevant answers.

**Request Body:**
```json
{
  "question": "How do I handle missing values in pandas?",
  "image": "base64_encoded_image_string" // optional
}
