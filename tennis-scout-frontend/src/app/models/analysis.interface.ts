export interface AnalysisRequest {
  query: string;
  conversation_history?: any[];
}

export interface AnalysisResponse {
  success: boolean;
  response?: string;
  sources?: AnalysisSource[];
  analysis_id?: number;
  processing_time_ms?: number;
  players_detected?: string[];
  total_matches_searched?: number;
}

export interface AnalysisSource {
  title: string;
  video_id: string;
}