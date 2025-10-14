'use client';

import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ChartVisualization } from '@/components/chart-visualization';
import { DataTable } from '@/components/data-table';
import nl2sqlApi, { NL2SQLResponse } from '@/lib/api';
import { 
  Send, 
  Trash2, 
  Database, 
  CheckCircle2, 
  XCircle, 
  MessageSquare,
  Loader2 
} from 'lucide-react';

export function NL2SQLQuery() {
  const [question, setQuestion] = useState('');
  const [sessionId, setSessionId] = useState<string>('');
  const [response, setResponse] = useState<NL2SQLResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationCount, setConversationCount] = useState(0);

  // Initialize session ID on mount
  useEffect(() => {
    const storedSessionId = localStorage.getItem('nl2sql_session_id');
    if (storedSessionId) {
      setSessionId(storedSessionId);
      loadConversationCount(storedSessionId);
    } else {
      const newSessionId = `session_${Date.now()}`;
      setSessionId(newSessionId);
      localStorage.setItem('nl2sql_session_id', newSessionId);
    }
  }, []);

  const loadConversationCount = async (sid: string) => {
    try {
      const count = await nl2sqlApi.getConversationCount(sid);
      setConversationCount(count.exchange_count);
    } catch (err) {
      console.error('Failed to load conversation count:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError(null);
    
    try {
      const result = await nl2sqlApi.query({
        question: question.trim(),
        session_id: sessionId,
      });
      
      setResponse(result);
      setQuestion(''); // Clear input after successful query
      
      // Update conversation count
      if (sessionId) {
        await loadConversationCount(sessionId);
      }
    } catch (err: unknown) {
      console.error('Query failed:', err);
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(error.response?.data?.detail || error.message || 'Failed to process query');
    } finally {
      setLoading(false);
    }
  };

  const handleClearConversation = async () => {
    if (!sessionId) return;
    
    try {
      await nl2sqlApi.clearConversation(sessionId);
      
      // Create new session
      const newSessionId = `session_${Date.now()}`;
      setSessionId(newSessionId);
      localStorage.setItem('nl2sql_session_id', newSessionId);
      
      setResponse(null);
      setConversationCount(0);
      setError(null);
    } catch (err: unknown) {
      console.error('Failed to clear conversation:', err);
      setError('Failed to clear conversation history');
    }
  };

  // Check if we should show table: no chart AND data has 2+ columns
  const shouldShowTable = () => {
    if (!response?.data || response.data.length === 0) return false;
    if (response.chart_specification) return false; // Don't show table if chart exists
    
    const columns = Object.keys(response.data[0]);
    return columns.length >= 2; // Only show if 2+ columns
  };

  return (
    <div className="space-y-6">
      {/* Query Input Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Natural Language to SQL</CardTitle>
              <CardDescription>
                Ask questions about your data in plain English
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              {conversationCount > 0 && (
                <Badge variant="secondary" className="flex items-center gap-1">
                  <MessageSquare className="h-3 w-3" />
                  {conversationCount} {conversationCount === 1 ? 'exchange' : 'exchanges'}
                </Badge>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={handleClearConversation}
                disabled={loading || conversationCount === 0}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Clear History
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g., Show me total sales by year..."
              className="flex-1"
              disabled={loading}
            />
            <Button type="submit" disabled={loading || !question.trim()}>
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Send className="h-4 w-4 mr-2" />
                  Query
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Loading Skeleton */}
      {loading && (
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-4 w-64 mt-2" />
          </CardHeader>
          <CardContent className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-64 w-full mt-4" />
          </CardContent>
        </Card>
      )}

      {/* Results Section */}
      {!loading && response && (
        <div className="space-y-4">
          {/* Status Badge */}
          <div className="flex items-center gap-2">
            {response.execution_success ? (
              <Badge variant="default" className="flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3" />
                Query Successful
              </Badge>
            ) : (
              <Badge variant="destructive" className="flex items-center gap-1">
                <XCircle className="h-3 w-3" />
                Query Failed
              </Badge>
            )}
          </div>

          {/* Natural Language Answer */}
          {response.natural_language_answer && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Answer</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-muted-foreground leading-relaxed markdown-content">
                  <ReactMarkdown>{response.natural_language_answer}</ReactMarkdown>
                </div>
              </CardContent>
            </Card>
          )}

          {/* SQL Query */}
          {response.sql_query && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Database className="h-5 w-5" />
                  Generated SQL Query
                </CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="bg-muted p-4 rounded-lg text-sm overflow-x-auto">
                  <code>{response.sql_query}</code>
                </pre>
              </CardContent>
            </Card>
          )}

          {/* Chart Visualization (if chart_specification exists) */}
          {response.chart_specification && (
            <ChartVisualization chartSpec={response.chart_specification} />
          )}

          {/* Data Table (only if NO chart AND 2+ columns) */}
          {shouldShowTable() && (
            <DataTable 
              data={response.data!} 
              title="Query Results"
              description={`${response.data!.length} ${response.data!.length === 1 ? 'row' : 'rows'} returned`}
            />
          )}

          {/* Error Message */}
          {response.error_message && (
            <Alert variant="destructive">
              <XCircle className="h-4 w-4" />
              <AlertDescription>{response.error_message}</AlertDescription>
            </Alert>
          )}
        </div>
      )}
    </div>
  );
}

