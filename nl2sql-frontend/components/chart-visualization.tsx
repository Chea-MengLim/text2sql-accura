'use client';

import React from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ChartSpecification } from '@/lib/api';

interface ChartVisualizationProps {
  chartSpec: ChartSpecification;
}

const COLORS = [
  '#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8',
  '#82CA9D', '#FFC658', '#FF6B9D', '#C084FC', '#FB923C',
];

export function ChartVisualization({ chartSpec }: ChartVisualizationProps) {
  const { chart_type, data, config, explain } = chartSpec;

  // Get the value keys (excluding 'name')
  const valueKeys = data.length > 0 
    ? Object.keys(data[0]).filter(key => key !== 'name')
    : [];

  // Determine chart type
  const chartTypeLower = chart_type.toLowerCase();
  
  const renderChart = () => {
    // Bar Chart
    if (chartTypeLower.includes('bar')) {
      return (
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="name" 
              angle={-45} 
              textAnchor="end" 
              height={100}
              interval={0}
            />
            <YAxis />
            <Tooltip 
              formatter={(value: number | string) => {
                if (typeof value === 'number') {
                  return value.toLocaleString();
                }
                return value;
              }}
            />
            <Legend />
            {valueKeys.map((key, index) => (
              <Bar 
                key={key} 
                dataKey={key} 
                fill={COLORS[index % COLORS.length]}
                name={config?.[key]?.label || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      );
    }

    // Line Chart
    if (chartTypeLower.includes('line')) {
      return (
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="name" 
              angle={-45} 
              textAnchor="end" 
              height={100}
              interval={0}
            />
            <YAxis />
            <Tooltip 
              formatter={(value: number | string) => {
                if (typeof value === 'number') {
                  return value.toLocaleString();
                }
                return value;
              }}
            />
            <Legend />
            {valueKeys.map((key, index) => (
              <Line 
                key={key}
                type="monotone"
                dataKey={key} 
                stroke={COLORS[index % COLORS.length]}
                strokeWidth={2}
                name={config?.[key]?.label || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      );
    }

    // Pie Chart
    if (chartTypeLower.includes('pie')) {
      // For pie charts, we need to format data differently
      const pieData = data.map((item) => ({
        name: item.name,
        value: item[valueKeys[0]] || 0,
      }));

      return (
        <ResponsiveContainer width="100%" height={400}>
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              labelLine={true}
              label={(entry) => {
                const pieEntry = entry as unknown as { name: string; value: number };
                return `${pieEntry.name}: ${pieEntry.value.toLocaleString()}`;
              }}
              outerRadius={120}
              fill="#8884d8"
              dataKey="value"
            >
              {pieData.map((_entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip 
              formatter={(value: number | string) => {
                if (typeof value === 'number') {
                  return value.toLocaleString();
                }
                return value;
              }}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      );
    }

    // Area Chart
    if (chartTypeLower.includes('area')) {
      return (
        <ResponsiveContainer width="100%" height={400}>
          <AreaChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="name" 
              angle={-45} 
              textAnchor="end" 
              height={100}
              interval={0}
            />
            <YAxis />
            <Tooltip 
              formatter={(value: number | string) => {
                if (typeof value === 'number') {
                  return value.toLocaleString();
                }
                return value;
              }}
            />
            <Legend />
            {valueKeys.map((key, index) => (
              <Area 
                key={key}
                type="monotone"
                dataKey={key} 
                stroke={COLORS[index % COLORS.length]}
                fill={COLORS[index % COLORS.length]}
                fillOpacity={0.6}
                name={config?.[key]?.label || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      );
    }

    // Default to bar chart if type is unknown
    return (
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="name" 
            angle={-45} 
            textAnchor="end" 
            height={100}
            interval={0}
          />
          <YAxis />
          <Tooltip 
            formatter={(value: number | string) => {
              if (typeof value === 'number') {
                return value.toLocaleString();
              }
              return value;
            }}
          />
          <Legend />
          {valueKeys.map((key, index) => (
            <Bar 
              key={key} 
              dataKey={key} 
              fill={COLORS[index % COLORS.length]}
              name={config?.[key]?.label || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    );
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="capitalize">{chart_type}</CardTitle>
        {explain && <CardDescription>{explain}</CardDescription>}
      </CardHeader>
      <CardContent>
        {renderChart()}
      </CardContent>
    </Card>
  );
}

