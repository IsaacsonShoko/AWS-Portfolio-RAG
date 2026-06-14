export interface Citation {
  id: number;
  github_url: string;
  repo?: string;
  path?: string;
  language?: string;
  snippet: string;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  sessionId: string;
}

export interface ChatRequest {
  message: string;
  sessionId?: string;
  repo?: string;
}
