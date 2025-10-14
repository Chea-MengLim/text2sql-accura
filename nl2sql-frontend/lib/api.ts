import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9008';

export interface NL2SQLRequest {
  question: string;
  session_id?: string;
  max_length?: number;
}

export interface ChartSpecification {
  chart_type: string;
  data: Array<{
    name: string;
    [key: string]: string | number;
  }>;
  config?: {
    [key: string]: {
      label: string;
    };
  };
  explain?: string;
}

export interface NL2SQLResponse {
  sql_query: string;
  natural_language_answer: string;
  execution_success: boolean;
  error_message?: string;
  chart_specification?: ChartSpecification;
  data?: Array<Record<string, unknown>>;
}

export interface StatusResponse {
  model_service_url: string;
  model_service_available: boolean;
  current_mode: string;
  fallback_enabled: boolean;
  recommendation?: string;
  start_command?: string;
}

export interface ConversationCountResponse {
  session_id: string;
  message_count: number;
  exchange_count: number;
}

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const nl2sqlApi = {
  /**
   * Send a natural language query to the API
   */
  async query(request: NL2SQLRequest): Promise<NL2SQLResponse> {
    const response = await api.post<NL2SQLResponse>('/api/nl2sql/query', request);
    return response.data;
  },

  /**
   * Get API status
   */
  async getStatus(): Promise<StatusResponse> {
    const response = await api.get<StatusResponse>('/api/nl2sql/status');
    return response.data;
  },

  /**
   * Clear conversation history for a session
   */
  async clearConversation(sessionId: string): Promise<{ status: string; message: string }> {
    const response = await api.delete(`/api/nl2sql/conversation/${sessionId}`);
    return response.data;
  },

  /**
   * Get conversation count for a session
   */
  async getConversationCount(sessionId: string): Promise<ConversationCountResponse> {
    const response = await api.get<ConversationCountResponse>(`/api/nl2sql/conversation/${sessionId}/count`);
    return response.data;
  },

  /**
   * Test endpoint to verify API is working
   */
  async test(): Promise<{ status: string; test_question: string; generated_sql: string; message: string; mode: string }> {
    const response = await api.get('/api/nl2sql/test');
    return response.data;
  },

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: string; service: string }> {
    const response = await api.get('/health');
    return response.data;
  },
};

export default nl2sqlApi;

