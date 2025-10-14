# NL2SQL Quick Start Guide

## 🚀 Complete Setup in 3 Minutes

### Step 1: Start Backend Services

Open **Terminal 1** - Model Service (Port 8888):
```bash
./start_model_service.sh
```
✅ Wait for: "Model service is running"

Open **Terminal 2** - API Service (Port 9008):
```bash
./start_app.sh
```
✅ Wait for: "Application startup complete"

### Step 2: Start Frontend

Open **Terminal 3** - Frontend (Port 3000):
```bash
cd nl2sql-frontend
./start.sh
```
✅ Wait for: "Ready in X ms"

### Step 3: Open Browser

Navigate to: **http://localhost:3000**

## 🎯 First Query

Try these example queries:

1. **Sales Analysis**
   ```
   Show me total sales by year
   ```

2. **Trend Analysis**
   ```
   What is the profit trend over time?
   ```

3. **Top Results**
   ```
   Display top 10 customers by revenue
   ```

## 📊 Understanding Results

### When You'll See Charts
- ✅ Multiple data points (2+ rows)
- ✅ Suitable for visualization (trends, comparisons)
- ✅ AI determines chart is helpful

**Chart Types:**
- 📊 Bar Chart - Comparing categories
- 📈 Line Chart - Trends over time
- 🥧 Pie Chart - Proportions
- 📉 Area Chart - Filled trends

### When You'll See Tables
- ✅ No chart generated
- ✅ Data has 2+ columns
- ✅ Raw data is more useful than chart

### When You'll See Neither
- Only natural language answer shown
- Single value results (e.g., "Total: 1000")
- Database metadata queries

## 🔧 Port Summary

| Service | Port | URL |
|---------|------|-----|
| Frontend | 3000 | http://localhost:3000 |
| API | 9008 | http://localhost:9008 |
| Model Service | 8888 | http://localhost:8888 |

## ❓ Troubleshooting

### Frontend won't start
```bash
# Check if API is running
curl http://localhost:9008/health

# If not, start it
./start_app.sh
```

### No charts showing
- Try queries with multiple data points
- Use phrases like "trend", "compare", "by year"
- Example: "Show sales trend by month"

### Table not displaying
- This is normal if chart is shown
- Or if data has only 1 column
- Check browser console for details

### Session not saving
- Check browser localStorage is enabled
- Try clearing site data and refresh

## 📚 Next Steps

1. **Explore Features**
   - Try different types of queries
   - Clear conversation history
   - View generated SQL queries

2. **Read Documentation**
   - [Frontend Guide](FRONTEND_GUIDE.md) - Detailed frontend docs
   - [README](README.md) - Complete system overview

3. **Customize**
   - Change chart colors
   - Modify table formatting
   - Update API URL for production

## 🆘 Getting Help

Check in this order:
1. Browser console (F12)
2. Terminal logs
3. Backend API status: http://localhost:9008/api/nl2sql/status
4. Frontend README: `nl2sql-frontend/README.md`
5. This guide

---

**Happy Querying! 🎉**

