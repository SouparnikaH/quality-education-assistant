# 🚀 Quality Education Chatbot - Setup Guide

## Prerequisites

- **Python 3.9+** - Backend runtime
- **Node.js 16+** - Frontend build tools
- **Google Gemini API Key** - AI functionality

## Step-by-Step Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd quality-education-chatbot
```

### 2. Backend Setup

#### Create Virtual Environment
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Configure Environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Gemini API key
# GEMINI_API_KEY=your-actual-api-key-here
```

### 3. Frontend Setup

#### Install Dependencies
```bash
cd ../frontend
npm install
```

### 4. Get Google Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Create a new API key
4. Copy the API key to your `.env` file:
   ```
   GEMINI_API_KEY=AIzaSy...your-key-here
   ```

### 5. Run the Application

#### Start Backend (Terminal 1)
```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Start Frontend (Terminal 2)
```bash
cd frontend
npm run dev
```

### 6. Access the Application

- **Chatbot Interface**: http://localhost:5173/
- **Backend API**: http://127.0.0.1:8000/
- **API Documentation**: http://127.0.0.1:8000/docs

## Troubleshooting

### Backend Won't Start
```bash
# Check Python version
python --version

# Check if port 8000 is available
netstat -ano | findstr :8000

# Try different port
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

### Frontend Won't Start
```bash
# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

### API Key Issues
```bash
# Check .env file exists and has correct format
cat backend/.env

# Test API key validity
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('API Key loaded:', 'Yes' if os.getenv('GEMINI_API_KEY') else 'No')
"
```

### CORS Errors in Browser
- Check browser console for CORS errors
- Verify backend is running on the port specified in frontend
- Try hard refresh (Ctrl+Shift+R)

### Connection Refused
```bash
# Test backend connectivity
curl http://127.0.0.1:8000/

# Test frontend proxy
curl http://localhost:5173/
```

## Project Structure

```
quality-education-chatbot/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI application
│   │   ├── database.py      # Database utilities
│   │   ├── webhook.py       # Webhook handlers
│   │   └── nodes.py         # Graph nodes (if used)
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # Environment template
│   └── venv/                # Virtual environment
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React component
│   │   ├── main.jsx         # React entry point
│   │   ├── components/
│   │   │   └── Chat.jsx     # Chat interface
│   │   └── styles/
│   │       └── App.css      # Styling
│   ├── package.json         # Node dependencies
│   └── vite.config.js       # Vite configuration
├── quality_education.ipynb  # Training notebook
├── README.md                # Documentation
└── SETUP.md                 # This setup guide
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes |

## Ports Used

| Service | Port | URL |
|---------|------|-----|
| Frontend | 5173 | http://localhost:5173/ |
| Backend | 8000 | http://127.0.0.1:8000/ |

## Testing the Chatbot

1. Open http://localhost:5173/
2. Send "Hi" - should respond with greeting
3. Provide name, age, and field of interest
4. Ask field-specific questions like:
   - "what skills do I need for engineering?"
   - "branches in medicine"
   - "business career paths"

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify all prerequisites are installed
3. Check API key validity
4. Review browser console for errors
5. Test backend API directly with curl/Postman

## Next Steps

Once setup is complete, you can:

- Customize the AI responses in `backend/app/main.py`
- Add new academic fields
- Modify the frontend UI in `frontend/src/`
- Deploy to production servers
- Add user authentication
- Integrate with databases

**Happy coding! 🎓🤖**






