# Lead Generation Tool

Find local businesses using Google Places API and identify leads for your marketing/web development services.

## Quick Start

### 1. Setup Environment

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file in the project root:

```env
GOOGLE_MAPS_API_KEY=your_api_key_here
MONTHLY_API_LIMIT=500
```

### 3. Run the Application

```bash
cd backend
uvicorn app.main:app --reload
```

Then open http://localhost:8000 in your browser.

## Features

- 🔍 **Search Businesses**: Find businesses by type and location
- 📊 **API Usage Tracking**: Stay within free tier limits
- 🌐 **Website Detection**: Identify businesses without websites (hot leads!)
- ⭐ **Rating Filters**: Filter by Google rating
- 📥 **CSV Export**: Export leads for follow-up

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/search` | POST | Search for businesses |
| `/api/search/usage` | GET | Get API usage stats |
| `/api/search/history` | GET | Get search history |
| `/api/businesses` | GET | List stored businesses |
| `/api/businesses/stats/summary` | GET | Get summary stats |
| `/api/health` | GET | Health check |

## Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the **Places API** (already done ✓)
3. Create an API key with Places API access
4. Add the key to your `.env` file

## Cost Management

The tool tracks API usage to help you stay within free tier:
- Default limit: 500 calls/month
- Blocks searches when limit reached
- Resets monthly
