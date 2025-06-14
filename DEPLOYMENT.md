# TDS Virtual TA - Deployment Guide

## Quick Deployment to Vercel

### Prerequisites
- GitHub account
- Vercel account (free tier available)

### Step 1: Prepare Repository

1. **Initialize Git Repository:**
```bash
git init
git add .
git commit -m "Initial TDS Virtual TA implementation"
```

2. **Create GitHub Repository:**
   - Go to GitHub and create a new repository named `tds-virtual-ta`
   - Follow the instructions to push your local code:
```bash
git remote add origin https://github.com/YOUR_USERNAME/tds-virtual-ta.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy to Vercel

#### Option A: Web Interface (Recommended)
1. Visit [vercel.com](https://vercel.com) and sign in
2. Click "New Project"
3. Import your GitHub repository `tds-virtual-ta`
4. Vercel will automatically detect:
   - Framework: Python (FastAPI)
   - Build Command: Not needed
   - Output Directory: Not needed
   - Install Command: Not needed (uses pyproject.toml)
5. Click "Deploy"

#### Option B: Vercel CLI
```bash
# Install Vercel CLI
npm i -g vercel

# Login and deploy
vercel login
vercel --prod
```

### Step 3: Verify Deployment

After deployment, test your endpoints:

```bash
# Replace YOUR_APP_URL with your actual Vercel URL
curl https://your-app-name.vercel.app/

# Test the API
curl -X POST "https://your-app-name.vercel.app/api/" \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I handle missing values in pandas?"}'
```

## Configuration Details

### Vercel Configuration
The `vercel.json` file is pre-configured with:
- Python 3.11 runtime
- 30-second timeout limit
- Optimized for FastAPI deployment

### Dependencies
All required packages are specified in `pyproject.toml`:
- FastAPI for the web framework
- Uvicorn as the ASGI server
- Pillow and pytesseract for image processing
- FuzzyWuzzy for text matching
- BeautifulSoup4 and trafilatura for web scraping
- Additional data science libraries

### Data Files
The application includes sample data in the `data/` directory:
- `course_content.json`: 10 sample course topics
- `tds_posts.json`: 5 sample forum discussions

## Updating Data

### Adding Course Content
Edit `data/course_content.json` to add new course materials:

```json
{
  "id": "new-topic",
  "title": "New Topic Title",
  "description": "Detailed description of the topic",
  "topics": ["keyword1", "keyword2"],
  "url": "https://course.example.com/new-topic",
  "difficulty": "intermediate",
  "module": 3
}
```

### Scraping Forum Posts
To collect real forum data (requires authentication):

1. **Update scraper credentials** in `scrape_discourse.py`
2. **Run the scraper:**
```bash
python scrape_discourse.py --start-date 2025-01-01 --end-date 2025-04-14
```
3. **Redeploy** to update the live application

## Testing

### Manual Testing
```bash
# Health check
curl https://your-app.vercel.app/health

# API statistics
curl https://your-app.vercel.app/api/stats

# Question with image (base64-encoded)
curl -X POST "https://your-app.vercel.app/api/" \
  -H "Content-Type: application/json" \
  -d '{"question": "What does this show?", "image": "iVBORw0KGgoAAAA..."}'
```

### Automated Testing
```bash
# Install promptfoo for evaluation
npm install -g promptfoo

# Run the test suite
npx promptfoo eval --config project-tds-virtual-ta-promptfoo.yaml
```

## Performance Considerations

### Response Times
- Text-only queries: < 1 second
- Image processing: 2-5 seconds
- Hard timeout: 30 seconds

### Scalability
- Vercel automatically handles scaling
- No database required (uses JSON files)
- Stateless design supports concurrent requests

### Monitoring
Monitor your deployment through:
- Vercel Dashboard (analytics, logs, performance)
- Built-in `/health` endpoint
- Custom `/api/stats` endpoint for knowledge base statistics

## Troubleshooting

### Common Issues

1. **Deployment Fails:**
   - Check `vercel.json` configuration
   - Verify all dependencies in `pyproject.toml`
   - Ensure Python 3.11 compatibility

2. **OCR Not Working:**
   - Vercel includes Tesseract by default
   - For custom OCR, add system dependencies to `vercel.json`

3. **Slow Response Times:**
   - Optimize fuzzy matching thresholds
   - Reduce data file sizes
   - Implement caching if needed

4. **Missing Data:**
   - Verify `data/` directory is included in deployment
   - Check file paths are relative (not absolute)
   - Ensure JSON files are valid

### Environment Variables
If needed, add environment variables in Vercel Dashboard:
- Go to Project Settings → Environment Variables
- Add any required API keys or configuration

## Security

### Best Practices
- No sensitive data in repository
- CORS configured for web access
- Input validation on all endpoints
- Timeout protection against long-running requests

### Updates
To update the deployed application:
1. Make changes locally
2. Commit and push to GitHub
3. Vercel automatically redeploys

## Support

For deployment issues:
- Check Vercel documentation
- Review deployment logs in Vercel Dashboard
- Test locally first with `uvicorn main:app --reload`

For application issues:
- Use the `/health` endpoint to verify service status
- Check the `/api/stats` endpoint for data availability
- Review server logs for detailed error information