# 🔄 Auto-Fallback Mode

## What is it?

Your app now has **automatic fallback** - it works with OR without the model service!

### Two Modes:

1. **Service Mode** (Optimal - 70% memory savings)
   - Uses model service on port 8888
   - Multiple app instances share ONE model
   - ~22GB GPU for 5 instances

2. **Local Mode** (Fallback - standalone)
   - Loads model directly in the app
   - Works without model service
   - ~14GB GPU per instance (more memory)

## How It Works

```
App starts → Try model service (port 8888)
             ↓
             Is service available?
             ↓
         ┌───Yes──────────────No───┐
         ↓                         ↓
    Use Service Mode          Use Local Mode
    (memory efficient)        (fallback - loads locally)
         ↓                         ↓
    Generate SQL              Generate SQL
```

## Usage Scenarios

### Scenario 1: WITH Model Service (Recommended)

**Terminal 1:**
```bash
./start_model_service.sh
```

**Terminal 2:**
```bash
./start_app.sh 9008
```

**Result:**
- ✅ App uses service mode (optimal)
- ✅ 70% GPU memory savings
- ✅ Fast and efficient

### Scenario 2: WITHOUT Model Service (Auto-Fallback)

**Terminal 1:**
```bash
./start_app.sh 9008
```

**Result:**
- ⚠️  App detects no service
- ⚠️  Automatically loads model locally
- ⚠️  Uses more GPU memory (14GB)
- ✅ Still works!

**Logs you'll see:**
```
WARNING:service.sql_generator:⚠️  Cannot connect to model service at http://localhost:8888
WARNING:service.sql_generator:⚠️  FALLBACK MODE: Loading model locally (uses more GPU memory)
WARNING:service.sql_generator:⚠️  Model service not available - loading model LOCALLY (uses more GPU memory)
INFO:service.sql_generator:✅ Local model loaded successfully
```

## Check Current Mode

### Via API:
```bash
# Check status
curl http://localhost:9008/api/nl2sql/status
```

**Response when service is available:**
```json
{
  "model_service_url": "http://localhost:8888",
  "model_service_available": true,
  "current_mode": "service",
  "fallback_enabled": true,
  "recommendation": "Using model service - optimal memory usage!",
  "start_command": null
}
```

**Response when service is NOT available:**
```json
{
  "model_service_url": "http://localhost:8888",
  "model_service_available": false,
  "current_mode": "local",
  "fallback_enabled": true,
  "recommendation": "Start model service for 70% GPU memory savings!",
  "start_command": "./start_model_service.sh"
}
```

### Via Browser:
```
http://localhost:9008/api/nl2sql/status
```

## Mode Switching

The app **automatically switches modes**:

1. **Service goes down** → Switches to local mode
2. **Service comes back online** → Switches back to service mode

**Example:**
```
App running in service mode
  ↓
Model service crashes
  ↓
App detects failure → loads model locally
  ↓
App continues working in local mode
  ↓
You restart model service
  ↓
Next request → App detects service is back
  ↓
App switches back to service mode
```

## Disable Fallback (Optional)

If you want to **force** service mode (no fallback):

```python
# In api/nl2sql.py, line 33:
sql_generator = SQLGenerator(use_fallback=False)
```

Then the app will **fail** if model service is not available (ensures you always use optimal mode).

## Memory Comparison

| Setup | GPU Memory |
|-------|-----------|
| **1 App (Service Mode)** | ~8GB (only Ollama, model in service) |
| **1 App (Local Mode)** | ~22GB (Ollama + Snowflake) |
| **5 Apps (Service Mode)** | ~22GB (shared model) |
| **5 Apps (Local Mode)** | ~78GB (each loads model) |

## Best Practices

### ✅ DO:
- Start model service first for optimal memory usage
- Use service mode in production
- Check `/status` endpoint to verify mode
- Monitor GPU with `nvidia-smi`

### ❌ DON'T:
- Run multiple apps in local mode (wastes GPU memory)
- Forget to start model service in production
- Ignore the fallback warnings

## Troubleshooting

### App is in local mode but I want service mode

1. **Start the model service:**
   ```bash
   ./start_model_service.sh
   ```

2. **Wait for it to load** (check logs)

3. **Make a new request** - app will auto-switch to service mode

4. **Verify:**
   ```bash
   curl http://localhost:9008/api/nl2sql/status
   ```

### App says "loading model locally" every request

**Cause:** Model service keeps crashing  
**Solution:** Check model service logs, might be out of GPU memory

### Want to force service mode (no fallback)

Edit `api/nl2sql.py`:
```python
sql_generator = SQLGenerator(use_fallback=False)
```

Restart your app. Now it will error if service is unavailable.

## Quick Reference

| Command | Purpose |
|---------|---------|
| `./start_model_service.sh` | Start model service (port 8888) |
| `./start_app.sh 9008` | Start app (auto-detects service) |
| `curl localhost:9008/api/nl2sql/status` | Check current mode |
| `curl localhost:8888/health` | Check model service health |
| `nvidia-smi` | Check GPU memory usage |

## Summary

✅ **Fallback enabled by default** - app always works  
✅ **Automatic mode switching** - no manual intervention  
✅ **Status endpoint** - check current mode  
✅ **70% memory savings** - when using service mode  
✅ **Standalone operation** - works without service  

**Recommendation:** Always start model service first for optimal performance! 🚀

