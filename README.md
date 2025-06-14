# TDS Virtual TA

A FastAPI-based virtual Teaching Assistant for the "Tools in Data Science (TDS)" course offered in IIT Madras' Online BSc Degree program.

## Features

- **Question Processing**: Accept student questions as text input
- **Image OCR**: Process base64-encoded images to extract text using OCR
- **Knowledge Base Search**: Search through scraped Discourse forum posts and course content
- **Intelligent Matching**: Use fuzzy text matching to find relevant answers
- **Fast Response**: Process and respond within 30 seconds
- **Supporting Links**: Provide relevant links to source materials and forum discussions

## Project Structure

```
tds-virtual-ta/
├── main.py                    # FastAPI application
├── qa_engine.py              # Question matching and answer logic
├── scrape_discourse.py       # Discourse forum scraper
├── data/
│   ├── course_content.json   # Course materials data
│   └── tds_posts.json       # Scraped forum posts
├── vercel.json              # Vercel deployment configuration
├── project-tds-virtual-ta-promptfoo.yaml  # Testing configuration
├── LICENSE                  # MIT License
└── README.md               # This file
```

## API Endpoints

### POST `/api/`

Process student questions and return relevant answers.

**Request Body:**
```json
{
  "question": "How do I handle missing values in pandas?",
  "image": "base64_encoded_image_string" // optional
}
```

**Response:**
```json
{
  "answer": "Based on the available course materials...",
  "links": [
    {
      "url": "https://course.example.com/pandas-basics",
      "text": "Course Material: Data Manipulation with Pandas"
    }
  ]
}
```

### GET `/`

Health check endpoint returning API information.

### GET `/health`

Simple health status check.

### GET `/api/stats`

Get statistics about the knowledge base.

## Local Development

### Prerequisites

- Python 3.11+
- pip or uv package manager

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd tds-virtual-ta
```

2. Install dependencies:
```bash
# Using uv (recommended)
uv add fastapi uvicorn python-multipart pillow pytesseract fuzzywuzzy python-levenshtein beautifulsoup4 requests trafilatura

# Or using pip
pip install fastapi uvicorn python-multipart pillow pytesseract fuzzywuzzy python-levenshtein beautifulsoup4 requests trafilatura
```

3. Install Tesseract OCR (required for image processing):
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

### Running the Application

```bash
# Start the development server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Or run directly
python main.py
```

The API will be available at `http://localhost:8000` with automatic documentation at `http://localhost:8000/docs`.

## Data Collection

### Scraping Discourse Posts

Use the included scraper to collect forum posts:

```bash
# Scrape posts from January 1, 2025 to April 14, 2025
python scrape_discourse.py --start-date 2025-01-01 --end-date 2025-04-14 --max-posts 100

# Custom output file
python scrape_discourse.py --output data/custom_posts.json
```

### Course Content

Update `data/course_content.json` with relevant course materials. Each entry should include:

```json
{
  "id": "unique-identifier",
  "title": "Topic Title",
  "description": "Detailed description",
  "topics": ["keyword1", "keyword2"],
  "url": "https://course.example.com/topic",
  "difficulty": "beginner|intermediate|advanced",
  "module": 1
}
```

## Deployment

### Vercel Deployment

1. **Push to GitHub:**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-github-repo-url>
git push -u origin main
```

2. **Deploy to Vercel:**
   - Visit [vercel.com](https://vercel.com)
   - Connect your GitHub account
   - Import your repository
   - Vercel will automatically detect the FastAPI app and deploy it

3. **Environment Variables (if needed):**
   - No external API keys required by default
   - All data is stored in local JSON files

### Manual Vercel CLI Deployment

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

## Testing

### Using curl

```bash
# Test basic question
curl -X POST "https://your-app.vercel.app/api/" \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I handle missing values in pandas?"}'

# Test with image (base64-encoded)
curl -X POST "https://your-app.vercel.app/api/" \
  -H "Content-Type: application/json" \
  -d '{"question": "What does this image say?", "image": "iVBORw0KGgoAAAANSUhEUgA..."}'
```

### Using Promptfoo

```bash
# Install promptfoo
npm install -g promptfoo

# Run evaluation tests
npx promptfoo eval --config project-tds-virtual-ta-promptfoo.yaml
```

## Performance

- **Response Time**: Typically < 1 second for text queries
- **Timeout**: Hard limit of 30 seconds per request
- **Concurrency**: Supports multiple simultaneous requests
- **Memory**: Efficient fuzzy matching with minimal memory footprint

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues related to the TDS course content, please contact the course instructors. For technical issues with this application, please open a GitHub issue.
