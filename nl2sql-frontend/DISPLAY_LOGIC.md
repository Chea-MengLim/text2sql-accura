# Display Logic Reference

## Conditional Rendering Rules

### Chart vs Table Decision Flow

```
┌─────────────────────────┐
│  Response Received      │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────────────┐
│ Check: chart_specification?     │
└───────────┬─────────────────────┘
            │
      ┌─────┴─────┐
      │           │
     YES         NO
      │           │
      ▼           ▼
┌─────────┐   ┌──────────────────────┐
│ SHOW    │   │ Check: Column Count? │
│ CHART   │   └──────────┬───────────┘
│         │              │
│ HIDE    │        ┌─────┴─────┐
│ TABLE   │        │           │
└─────────┘    1 column    2+ columns
                   │           │
                   ▼           ▼
              ┌─────────┐ ┌─────────┐
              │ SHOW    │ │ SHOW    │
              │ NOTHING │ │ TABLE   │
              └─────────┘ └─────────┘
```

## Code Implementation

### shouldShowTable() Function

```typescript
const shouldShowTable = () => {
  // No data = no table
  if (!response?.data || response.data.length === 0) 
    return false;
  
  // Chart exists = no table
  if (response.chart_specification) 
    return false;
  
  // Less than 2 columns = no table
  const columns = Object.keys(response.data[0]);
  return columns.length >= 2;
};
```

### Component Rendering

```tsx
{/* Chart - Always shown if specification exists */}
{response.chart_specification && (
  <ChartVisualization chartSpec={response.chart_specification} />
)}

{/* Table - Only shown if shouldShowTable() returns true */}
{shouldShowTable() && (
  <DataTable data={response.data!} />
)}
```

## Examples

### Example 1: Sales by Year (Chart Display)

**Query**: "Show me total sales by year"

**Response**:
```json
{
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
  "data": [
    {"year": "2023", "total_sales": 50000},
    {"year": "2024", "total_sales": 65000}
  ]
}
```

**Display**:
- ✅ Natural Language Answer
- ✅ SQL Query
- ✅ Bar Chart
- ❌ Table (hidden because chart exists)

### Example 2: Customer List (Table Display)

**Query**: "Show me all customers with their orders"

**Response**:
```json
{
  "chart_specification": null,
  "data": [
    {"id": 1, "name": "John", "orders": 5},
    {"id": 2, "name": "Jane", "orders": 3},
    {"id": 3, "name": "Bob", "orders": 7}
  ]
}
```

**Display**:
- ✅ Natural Language Answer
- ✅ SQL Query
- ❌ Chart (no specification)
- ✅ Table (3 columns, no chart)

### Example 3: Total Count (Answer Only)

**Query**: "How many customers do we have?"

**Response**:
```json
{
  "chart_specification": null,
  "data": [
    {"count": 150}
  ]
}
```

**Display**:
- ✅ Natural Language Answer
- ✅ SQL Query
- ❌ Chart (no specification)
- ❌ Table (only 1 column)

### Example 4: Trend Over Time (Line Chart)

**Query**: "Show me profit trend over the last 6 months"

**Response**:
```json
{
  "chart_specification": {
    "chart_type": "line chart",
    "data": [
      {"name": "Jan 2024", "profit": 10000},
      {"name": "Feb 2024", "profit": 12000},
      {"name": "Mar 2024", "profit": 11500},
      {"name": "Apr 2024", "profit": 13000},
      {"name": "May 2024", "profit": 14500},
      {"name": "Jun 2024", "profit": 15000}
    ],
    "config": {
      "profit": {"label": "Profit ($)"}
    },
    "explain": "Profit trend over 6 months"
  },
  "data": [...]
}
```

**Display**:
- ✅ Natural Language Answer
- ✅ SQL Query
- ✅ Line Chart (trend visualization)
- ❌ Table (hidden because chart exists)

## Chart Type Selection

The AI automatically chooses the best chart type:

| Data Pattern | Chart Type | Use Case |
|--------------|-----------|----------|
| Categories vs Values | Bar Chart | Comparing different items |
| Time Series (few points) | Bar Chart | Monthly/yearly comparisons |
| Time Series (many points) | Line Chart | Trend analysis |
| Proportions/Parts of Whole | Pie Chart | Market share, percentages |
| Cumulative Trends | Area Chart | Growth over time |

## Column Count Logic

### 1 Column Examples:
- `{"count": 5}` → No table
- `{"total": 10000}` → No table
- `{"avg_sales": 1500}` → No table

### 2+ Column Examples:
- `{"id": 1, "name": "John"}` → Show table
- `{"year": 2024, "sales": 5000, "profit": 1000}` → Show table

## AI Prompt Check

The backend AI checks data suitability:

```python
def _is_data_suitable_for_chart(self, sql_result, user_question):
    # Single row with count/aggregate? → No chart
    if len(sql_result) == 1:
        if 'count' in str(row).lower():
            return False
    
    # Less than 2 data points? → No chart
    if len(sql_result) < 2:
        return False
    
    # Database metadata query? → No chart
    if 'table' in user_question.lower():
        return False
    
    return True
```

## Summary

### Always Displayed:
- ✅ Natural language answer
- ✅ Generated SQL query
- ✅ Success/failure status

### Conditionally Displayed:

**Charts** ← When `chart_specification` exists
- Bar, Line, Pie, or Area chart
- With formatted axes and tooltips
- Color-coded data series

**Tables** ← When NO chart AND 2+ columns
- Formatted headers
- Auto-formatted values
- Row count display

**Nothing Extra** ← When single value result
- Just the natural language answer
- Plus SQL query for reference

