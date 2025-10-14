# NL2SQL Frontend Guide

## Quick Start

### 1. Start Backend Services
```bash
# Terminal 1: Start model service (port 8888)
./start_model_service.sh

# Terminal 2: Start API service (port 9008)
./start_app.sh
```

### 2. Start Frontend
```bash
# Terminal 3: Start frontend (port 3000)
cd nl2sql-frontend
./start.sh
```

### 3. Open Browser
Navigate to: `http://localhost:3000`

## Features Overview

### 🤖 Natural Language Queries
Ask questions in plain English:
- "Show me total sales by year"
- "What is the profit trend over time?"
- "Display top 10 customers"

### 📊 Automatic Visualizations
The AI automatically generates charts when appropriate:
- **Bar Charts**: Comparing categories
- **Line Charts**: Showing trends over time
- **Pie Charts**: Showing proportions
- **Area Charts**: Filled trend visualizations

### 📋 Smart Table Display
Tables are shown conditionally:
- ✅ Displayed when: No chart AND 2+ columns
- ❌ Hidden when: Chart exists OR single column

### 💬 Conversation Memory
- Sessions persist across page refreshes
- Context from previous questions is maintained
- Clear history to start fresh

## Display Logic

### Chart vs Table Decision Tree

```
Response Received
│
├── Has chart_specification?
│   ├── YES → Show Chart (hide table)
│   │         ├── Bar Chart
│   │         ├── Line Chart
│   │         ├── Pie Chart
│   │         └── Area Chart
│   │
│   └── NO → Check columns
│       ├── 1 column → Show nothing
│       └── 2+ columns → Show Table
```

### Examples

**Example 1: Chart Display**
```json
{
  "chart_specification": {
    "chart_type": "bar chart",
    "data": [...],
    "explain": "Sales by year"
  },
  "data": [...]
}
```
→ **Shows**: Chart only
→ **Hides**: Table

**Example 2: Table Display**
```json
{
  "chart_specification": null,
  "data": [
    {"id": 1, "name": "John", "sales": 1000},
    {"id": 2, "name": "Jane", "sales": 1500}
  ]
}
```
→ **Shows**: Table (3 columns)
→ **Hides**: Nothing

**Example 3: Single Value**
```json
{
  "chart_specification": null,
  "data": [
    {"total": 5000}
  ]
}
```
→ **Shows**: Natural language answer only
→ **Hides**: Both chart and table (1 column)

## Architecture

### Frontend Stack
```
Next.js 15 (App Router)
├── UI: shadcn/ui + Tailwind CSS
├── Charts: Recharts
├── HTTP: Axios
└── Icons: Lucide React
```

### API Communication
```
Frontend (Port 3000)
    ↓ HTTP Request
Backend API (Port 9008)
    ↓ Process Query
Model Service (Port 8888)
    ↓ Generate SQL
Database (PostgreSQL)
    ↓ Execute & Return
Frontend (Visualize)
```

### Component Hierarchy
```
app/page.tsx
└── NL2SQLQuery
    ├── Input Form
    ├── Status Display
    ├── Results Section
    │   ├── Natural Language Answer
    │   ├── SQL Query Display
    │   ├── ChartVisualization (conditional)
    │   └── DataTable (conditional)
    └── Error Handling
```

## API Endpoints Used

### POST /api/nl2sql/query
**Request:**
```json
{
  "question": "Show me sales by year",
  "session_id": "session_1234567890"
}
```

**Response:**
```json
{
  "sql_query": "SELECT year, SUM(amount) FROM sales GROUP BY year",
  "natural_language_answer": "Here are the sales by year...",
  "execution_success": true,
  "chart_specification": {
    "chart_type": "bar chart",
    "data": [
      {"name": "2023", "total_sales": 50000},
      {"name": "2024", "total_sales": 65000}
    ],
    "config": {
      "total_sales": {"label": "Total Sales"}
    },
    "explain": "Sales comparison by year"
  },
  "data": [...]
}
```

### GET /api/nl2sql/conversation/{session_id}/count
**Response:**
```json
{
  "session_id": "session_1234567890",
  "message_count": 10,
  "exchange_count": 5
}
```

### DELETE /api/nl2sql/conversation/{session_id}
**Response:**
```json
{
  "status": "success",
  "message": "Conversation history cleared for session: session_1234567890"
}
```

## Customization

### Change API URL
Edit `nl2sql-frontend/.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://your-server:9008
```

### Customize Chart Colors
Edit `nl2sql-frontend/components/chart-visualization.tsx`:
```typescript
const COLORS = [
  '#0088FE', // Blue
  '#00C49F', // Green
  '#FFBB28', // Yellow
  '#FF8042', // Orange
  '#8884D8', // Purple
  // Add more colors...
];
```

### Adjust Chart Size
```typescript
<ResponsiveContainer width="100%" height={400}>
  // Change height to your preference
</ResponsiveContainer>
```

### Modify Table Format
Edit `nl2sql-frontend/components/data-table.tsx`:
```typescript
const formatCellValue = (value: any) => {
  // Add your custom formatting logic
  if (value === null) return '-';
  if (typeof value === 'number') {
    return value.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }
  return String(value);
};
```

## Troubleshooting

### Issue: "Failed to process query"
**Cause**: Backend API not running
**Solution**:
```bash
# Check API status
curl http://localhost:9008/health

# Start API if needed
./start_app.sh
```

### Issue: Charts not showing
**Cause**: AI didn't generate chart specification
**Solution**: 
- Check if query is suitable for visualization
- Ensure data has multiple rows
- Try queries like "show trend over time" or "compare by category"

### Issue: Table not displaying
**Cause**: Either chart exists or data has only 1 column
**Solution**:
- Check browser console for `shouldShowTable()` logs
- Verify data structure in response

### Issue: Session not persisting
**Cause**: localStorage disabled or cleared
**Solution**:
- Enable localStorage in browser
- Check browser privacy settings
- Clear site data and refresh

## Development

### Add New Features
```bash
cd nl2sql-frontend

# Add UI components
npx shadcn@latest add [component]

# Install dependencies
npm install [package]

# Update API types
# Edit lib/api.ts
```

### Run Tests
```bash
# Type checking
npx tsc --noEmit

# Linting
npm run lint

# Build check
npm run build
```

### Debug Mode
Enable console logging:
```typescript
// In components/nl2sql-query.tsx
console.log('Response:', response);
console.log('Should show table:', shouldShowTable());
```

## Best Practices

### Query Writing
✅ **Good Queries:**
- "Show me sales by year"
- "Compare revenue across regions"
- "What's the trend of profits over time?"

❌ **Bad Queries:**
- "sales" (too vague)
- "show data" (no specifics)
- "everything" (no context)

### Performance Tips
1. **Limit Results**: Ask for "top 10" or "last 30 days"
2. **Clear History**: Periodically clear conversation history
3. **Specific Queries**: Be specific to get faster responses

### UI/UX Guidelines
1. **Wait for Response**: Don't submit while loading
2. **Read Answer**: Natural language answer provides context
3. **Check SQL**: Review generated SQL for accuracy
4. **Understand Charts**: Read chart labels and legends

## Production Deployment

### Build for Production
```bash
cd nl2sql-frontend

# Build optimized version
npm run build

# Test production build locally
npm start

# Deploy to production server
# (Use your preferred hosting: Vercel, Netlify, etc.)
```

### Environment Variables
```bash
# Production .env.local
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### Performance Optimization
- Enable Next.js caching
- Use CDN for static assets
- Implement request debouncing
- Add error boundaries

## Security Considerations

1. **API URL**: Never expose internal URLs in production
2. **Session IDs**: Implement proper session validation
3. **Input Validation**: Always validate user input
4. **CORS**: Configure proper CORS settings
5. **HTTPS**: Always use HTTPS in production

## Support

For issues or questions:
1. Check this guide
2. Review component code
3. Check browser console
4. Verify backend API is running
5. Review API response format

---

**Happy Querying! 🚀**

