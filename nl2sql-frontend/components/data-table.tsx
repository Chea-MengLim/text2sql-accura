'use client';

import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface DataTableProps {
  data: Array<Record<string, unknown>>;
  title?: string;
  description?: string;
}

export function DataTable({ data, title, description }: DataTableProps) {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>No Data</CardTitle>
          <CardDescription>No results found</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  // Get column names from the first row
  const columns = Object.keys(data[0]);

  // Check if we should show the table (2 or more columns)
  if (columns.length < 2) {
    return null;
  }

  // Format column headers - capitalize and replace underscores
  const formatColumnHeader = (column: string) => {
    return column
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (l) => l.toUpperCase());
  };

  // Format cell values
  const formatCellValue = (value: unknown, columnName: string) => {
    if (value === null || value === undefined) {
      return '-';
    }
    
    // Handle numbers with proper formatting
    if (typeof value === 'number') {
      // For large numbers, add thousands separators and consider currency formatting
      const columnLower = columnName.toLowerCase();
      const isCurrency = columnLower.includes('amt') || columnLower.includes('amount') || 
                        columnLower.includes('price') || columnLower.includes('cost') ||
                        columnLower.includes('value') || columnLower.includes('total');
      
      if (isCurrency) {
        // Format as currency with 2 decimal places
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 2,
          maximumFractionDigits: 2
        }).format(value);
      } else {
        // Format as number with thousands separators
        return new Intl.NumberFormat('en-US').format(value);
      }
    }
    
    // Handle date strings (YYYYMMDD format)
    if (typeof value === 'string') {
      const strValue = String(value).trim();
      
      // Check if it's a date in YYYYMMDD format (8 digits)
      if (/^\d{8}$/.test(strValue)) {
        try {
          const year = strValue.substring(0, 4);
          const month = strValue.substring(4, 6);
          const day = strValue.substring(6, 8);
          const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
          
          // Format as readable date
          return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
          });
        } catch (e) {
          // If date parsing fails, return original string
          return strValue;
        }
      }
      
      // Check if it's a date in YYYYMM format (6 digits)
      if (/^\d{6}$/.test(strValue)) {
        try {
          const year = strValue.substring(0, 4);
          const month = strValue.substring(4, 6);
          const date = new Date(parseInt(year), parseInt(month) - 1, 1);
          
          // Format as readable month/year
          return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short'
          });
        } catch (e) {
          // If date parsing fails, return original string
          return strValue;
        }
      }
      
      // Check if it's a number string (for cases where numbers come as strings)
      if (/^\d+\.?\d*$/.test(strValue)) {
        const numValue = parseFloat(strValue);
        if (!isNaN(numValue)) {
          const columnLower = columnName.toLowerCase();
          const isCurrency = columnLower.includes('amt') || columnLower.includes('amount') || 
                            columnLower.includes('price') || columnLower.includes('cost') ||
                            columnLower.includes('value') || columnLower.includes('total');
          
          if (isCurrency) {
            return new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: 'USD',
              minimumFractionDigits: 2,
              maximumFractionDigits: 2
            }).format(numValue);
          } else {
            return new Intl.NumberFormat('en-US').format(numValue);
          }
        }
      }
      
      return strValue;
    }
    
    if (typeof value === 'boolean') {
      return value ? 'Yes' : 'No';
    }
    
    return String(value);
  };

  return (
    <Card className="w-full">
      {(title || description) && (
        <CardHeader>
          {title && <CardTitle>{title}</CardTitle>}
          {description && <CardDescription>{description}</CardDescription>}
        </CardHeader>
      )}
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                {columns.map((column) => (
                  <TableHead key={column} className="font-semibold">
                    {formatColumnHeader(column)}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((row, rowIndex) => (
                <TableRow key={rowIndex}>
                  {columns.map((column) => (
                    <TableCell key={`${rowIndex}-${column}`}>
                      {formatCellValue(row[column], column)}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
        <div className="mt-2 text-sm text-muted-foreground">
          Showing {data.length} {data.length === 1 ? 'row' : 'rows'}
        </div>
      </CardContent>
    </Card>
  );
}

