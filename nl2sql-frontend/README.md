# NL2SQL Frontend

A modern Next.js frontend for the NL2SQL AI Assistant that converts natural language questions into SQL queries with beautiful visualizations.

## Features

✨ **Natural Language Queries**: Ask questions in plain English
📊 **Smart Visualizations**: Automatic chart generation (bar, line, pie, area)
📋 **Data Tables**: Conditional table display for multi-column results
💬 **Conversation Memory**: Session-based conversation history
🎨 **Modern UI**: Built with shadcn/ui and Tailwind CSS
📱 **Responsive**: Works on all devices

## Tech Stack

- **Framework**: Next.js 15 with App Router
- **UI Components**: shadcn/ui
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **HTTP Client**: Axios
- **Icons**: Lucide React

## Prerequisites

- Node.js 18+ (currently using v18.19.1)
- npm or yarn
- Backend API running on port 9008

## Installation

1. **Install dependencies**:
```bash
cd nl2sql-frontend
npm install
```

2. **Configure environment**:
```bash
# The .env.local file is already created with:
NEXT_PUBLIC_API_URL=http://localhost:9008
```

3. **Start the development server**:
```bash
npm run dev
```

4. **Open your browser**:
```
http://localhost:3000
```

## Usage

### Basic Query
1. Type your question in plain English
2. Click "Query" or press Enter
3. View the AI-generated response, SQL query, and visualization

### Example Queries
```
Show me total sales by year
What is the profit trend over time?
Display top 10 customers by revenue
How many orders were placed last month?
```

### Features

#### Chart Visualization
- **Automatic**: Charts are generated when data is suitable for visualization
- **Supported Types**: Bar, Line, Pie, Area charts
- **Smart Selection**: AI chooses the best chart type for your data
- **Conditional Display**: Charts show instead of tables when available

#### Data Table
- **Conditional Display**: Only shown when:
  - No chart is generated
  - AND data has 2 or more columns
- **Auto-formatting**: Numbers, dates, and booleans are formatted nicely
- **Responsive**: Scrollable on mobile devices

#### Session Management
- **Persistent Sessions**: Sessions are saved in localStorage
- **Conversation History**: Context is maintained across queries
- **Clear History**: Reset conversation anytime
- **Exchange Counter**: See how many questions you've asked

## Project Structure

```
nl2sql-frontend/
├── app/
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Home page
│   └── globals.css         # Global styles
├── components/
│   ├── ui/                 # shadcn/ui components
│   ├── chart-visualization.tsx  # Chart component
│   ├── data-table.tsx      # Table component
│   └── nl2sql-query.tsx    # Main query interface
├── lib/
│   ├── api.ts              # API client
│   └── utils.ts            # Utilities
└── public/                 # Static assets
```

## API Integration

The frontend communicates with the backend API:

### Endpoints Used
- `POST /api/nl2sql/query` - Submit natural language queries
- `GET /api/nl2sql/conversation/{session_id}/count` - Get conversation count
- `DELETE /api/nl2sql/conversation/{session_id}` - Clear conversation history
- `GET /api/nl2sql/status` - Check API status

### Response Format
```typescript
interface NL2SQLResponse {
  sql_query: string;
  natural_language_answer: string;
  execution_success: boolean;
  error_message?: string;
  chart_specification?: {
    chart_type: string;
    data: Array<{name: string, [key: string]: any}>;
    config?: {[key: string]: {label: string}};
    explain?: string;
  };
  data?: Array<Record<string, any>>;
}
```

## Display Logic

### Chart vs Table Decision Tree

```
1. Check if chart_specification exists
   ├── YES → Display chart (skip table)
   └── NO → Check column count
       ├── < 2 columns → Display nothing (single value)
       └── >= 2 columns → Display table
```

### Implementation

```typescript
// Chart is shown if specification exists
{response.chart_specification && (
  <ChartVisualization chartSpec={response.chart_specification} />
)}

// Table is shown only if NO chart AND 2+ columns
{shouldShowTable() && (
  <DataTable data={response.data!} />
)}
```

## Customization

### Update API URL
Edit `.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://your-api-url:port
```

### Customize Colors
Edit `components/chart-visualization.tsx`:
```typescript
const COLORS = [
  '#0088FE', '#00C49F', '#FFBB28', // Add your colors
];
```

### Modify Chart Types
The system supports:
- Bar Chart (default)
- Line Chart (for trends)
- Pie Chart (for proportions)
- Area Chart (for filled trends)

## Build for Production

```bash
# Build the application
npm run build

# Start production server
npm start

# Or use PM2 for process management
pm2 start npm --name "nl2sql-frontend" -- start
```

## Troubleshooting

### Issue: API Connection Failed
- **Solution**: Ensure backend is running on port 9008
- **Check**: `curl http://localhost:9008/health`

### Issue: Charts Not Displaying
- **Solution**: Check that chart_specification is returned from API
- **Debug**: Open browser console and check response data

### Issue: Table Not Showing
- **Solution**: Verify data has 2+ columns and no chart exists
- **Check**: Console logs in `shouldShowTable()` function

### Issue: Node Version Warning
- **Solution**: Upgrade to Node.js 20+ or ignore warnings
- **Command**: `nvm install 20 && nvm use 20`

## Development

### Add New Components
```bash
npx shadcn@latest add [component-name]
```

### Run Linting
```bash
npm run lint
```

### Type Checking
```bash
npx tsc --noEmit
```

## Contributing

1. Follow the existing code style
2. Update types in `lib/api.ts` when adding new features
3. Test all chart types before committing
4. Ensure responsive design works on mobile

## License

This project is part of the NL2SQL system.
