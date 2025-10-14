# NL2SQL AI Assistant

Transform natural language questions into SQL queries with automatic visualizations.

## Architecture
```
Frontend (Port 3000) → Main App (Port 9008) → Model Service (Port 8888) → GPU Model
                                            ↘ Fallback Mode → Local Model (More GPU)
```

## Quick Start

### Backend Setup

#### 1. Check Model Service
```bash
curl http://localhost:8888/health
```

#### 2. Start Model Service (if not running)
```bash
./start_model_service.sh
```

#### 3. Start Main App
```bash
./start_app.sh
```

### Frontend Setup (NEW! 🎨)

#### 4. Start Frontend
```bash
cd nl2sql-frontend
./start.sh
```

#### 5. Open Browser
Navigate to: `http://localhost:3000`

**📖 Detailed Frontend Guide**: See [FRONTEND_GUIDE.md](FRONTEND_GUIDE.md)

## API Usage

### Direct Model Service (Port 8888)
```bash
curl -X POST "http://localhost:8888/generate-sql" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show me sales data for 2024",
    "conversation_context": "",
    "schema_info": "Your database schema"
  }'
```

### Main App API (Port 9008) - Recommended
```bash
curl -X POST "http://localhost:9008/api/nl2sql/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show me sales data for 2024",
    "session_id": "user_123"
  }'
```

## Flow
1. **Check Model Service**: `curl http://localhost:8888/health`
2. **If not running**: `./start_model_service.sh`
3. **Start Main App**: `./start_app.sh`
4. **Call API**: Use port 9008 for full features

## Modes

| Mode | GPU Memory | Users | Startup |
|------|------------|-------|---------|
| Service Mode | ~8GB | Unlimited | Fast |
| Fallback Mode | ~22GB | 1 | Slow |

## Endpoints

| Endpoint | Port | Purpose |
|----------|------|---------|
| `/generate-sql` | 8888 | SQL generation only |
| `/api/nl2sql/query` | 9008 | Full features |
| `/health` | 8888/9008 | Health check |
| `/api/nl2sql/status` | 9008 | Mode status |

## Features

### Backend
- ✅ Automatic fallback
- ✅ Session isolation
- ✅ SQL injection protection
- ✅ Chart generation
- ✅ Conversation memory
- ✅ Multiple concurrent users

### Frontend (NEW! 🎨)
- ✅ Modern Next.js UI with shadcn/ui
- ✅ Automatic chart visualization (bar, line, pie, area)
- ✅ Smart table display (conditional rendering)
- ✅ Session management with localStorage
- ✅ Real-time query processing
- ✅ Responsive design for all devices

## Environment Variables
```bash
export OLLAMA_GPU_ONLY=true
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
```

## Troubleshooting
```bash
# Check GPU memory
nvidia-smi

# Check port availability
netstat -tulpn | grep 8888

# Check logs
tail -f logs/model_service.log
```
