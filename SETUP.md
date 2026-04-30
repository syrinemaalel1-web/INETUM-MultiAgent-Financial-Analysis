# Setup Guide

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Git

### 1. Clone and Setup
```bash
git clone https://github.com/slimgithub04/kpisagent.git
cd kpisagent

# Copy environment template
cp env.example env
```

### 2. Configure Environment
Edit the `env` file with your API keys:
```
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the backend
python backend/main.py
```

### 4. Frontend Setup
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 5. Access the Application
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## API Keys Setup

### Google API Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the Generative AI API
4. Create credentials (API Key)
5. Add to your `env` file

### OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Create an account or sign in
3. Navigate to API Keys section
4. Create a new API key
5. Add to your `env` file

## Troubleshooting

### Common Issues

**Backend won't start:**
- Check if all dependencies are installed: `pip install -r requirements.txt`
- Verify Python version: `python --version` (should be 3.10+)
- Check if port 8000 is available

**Frontend won't start:**
- Check Node.js version: `node --version` (should be 18+)
- Clear npm cache: `npm cache clean --force`
- Delete node_modules and reinstall: `rm -rf node_modules && npm install`

**API Keys not working:**
- Ensure no extra spaces in the `env` file
- Verify the keys are valid and have proper permissions
- Check API quotas and billing

### Development Tips

1. **Hot Reload**: Both frontend and backend support hot reload during development
2. **Logs**: Check `logs/backend.log` for backend issues
3. **Database**: SQLite database is created automatically in `data/data/app.db`
4. **Processing**: Large PDF files may take several minutes to process

## Production Deployment

For production deployment, consider:
- Using environment variables instead of the `env` file
- Setting up proper logging and monitoring
- Using a production WSGI server like Gunicorn
- Building the frontend for production: `npm run build`
- Setting up reverse proxy with Nginx
- Using a production database like PostgreSQL