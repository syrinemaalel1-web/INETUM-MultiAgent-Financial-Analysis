# Deployment Guide

This guide covers how to deploy the CMF Tunisia Analysis Platform to different environments.

## Environment Configuration

### Development
The application is configured to work with localhost by default.

### Production

#### 1. Backend Configuration
Update your `env` file:
```bash
# Production API configuration
API_HOST=0.0.0.0
API_PORT=8000

# Add your production API keys
GOOGLE_API_KEY=your_production_google_api_key
OPENAI_API_KEY=your_production_openai_api_key

# Production settings
DO_OCR=true
SAFE_MODE=false
```

#### 2. Frontend Configuration
Update `frontend/.env`:
```bash
# Replace with your actual production URLs
VITE_API_URL=https://api.yourdomain.com
VITE_WS_URL=wss://api.yourdomain.com
```

#### 3. Build Frontend
```bash
cd frontend
npm run build
```

## Deployment Options

### Option 1: Traditional Server Deployment

#### Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Run with production WSGI server
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.main:app --bind 0.0.0.0:8000
```

#### Frontend
Serve the built files from `frontend/dist/` using nginx, Apache, or any static file server.

### Option 2: Docker Deployment

Create `Dockerfile` for backend:
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "backend/main.py"]
```

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - API_HOST=0.0.0.0
      - API_PORT=8000
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs

  frontend:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./frontend/dist:/usr/share/nginx/html
    depends_on:
      - backend
```

### Option 3: Cloud Deployment

#### Heroku
1. Create `Procfile`:
```
web: python backend/main.py
```

2. Set environment variables in Heroku dashboard
3. Deploy using Git

#### Vercel (Frontend only)
1. Connect your GitHub repository
2. Set build command: `cd frontend && npm run build`
3. Set output directory: `frontend/dist`
4. Configure environment variables in Vercel dashboard

## Environment Variables Reference

### Backend (`env` file)
| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GOOGLE_API_KEY` | Google AI API key | - | Yes |
| `OPENAI_API_KEY` | OpenAI API key | - | Yes |
| `API_HOST` | Server host | `0.0.0.0` | No |
| `API_PORT` | Server port | `8000` | No |
| `DO_OCR` | Enable OCR processing | `false` | No |
| `SAFE_MODE` | Disable complex table processing | `false` | No |

### Frontend (`frontend/.env` file)
| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` | Yes |
| `VITE_WS_URL` | WebSocket URL | `ws://localhost:8000` | Yes |

## Security Considerations

1. **API Keys**: Never commit API keys to version control
2. **CORS**: Configure CORS properly for production domains
3. **HTTPS**: Use HTTPS in production for both API and WebSocket connections
4. **Environment Files**: Ensure `.env` files are not accessible via web server
5. **WebSocket Security**: Use WSS (WebSocket Secure) in production environments

## WebSocket Configuration

### Development
WebSockets work out of the box with the default configuration:
```bash
VITE_WS_URL=ws://localhost:8000
```

### Production
For production deployments, ensure you use secure WebSocket connections:
```bash
VITE_WS_URL=wss://your-production-domain.com
```

### Proxy Configuration
If using a reverse proxy (nginx, Apache), ensure WebSocket upgrade headers are properly forwarded:

**Nginx Example:**
```nginx
location /ws {
    proxy_pass http://backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
}
```

## Troubleshooting

### Common Issues

1. **Frontend can't connect to backend**
   - Check `VITE_API_URL` in `frontend/.env`
   - Ensure backend is running and accessible
   - Check CORS configuration

2. **WebSocket connection fails**
   - Verify `VITE_WS_URL` is correct
   - Ensure WebSocket endpoint is accessible
   - Check for proxy/firewall blocking WebSocket connections
   - Verify WebSocket upgrade headers in proxy configuration

3. **WebSocket keeps disconnecting**
   - Check network stability
   - Verify backend WebSocket implementation
   - Review proxy timeout settings
   - Check for firewall interference

4. **Build fails**
   - Clear node_modules: `rm -rf node_modules && npm install`
   - Check Node.js version compatibility
   - Verify all environment variables are set

5. **Real-time updates not working**
   - Check WebSocket connection status in browser dev tools
   - Verify backend is sending proper message formats
   - Check console for WebSocket errors

### Logs
- Backend logs: `logs/backend.log`
- Frontend console: Browser developer tools
- Check server logs for detailed error information