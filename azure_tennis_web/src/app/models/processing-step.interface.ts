export interface ProcessingStep {
  step: number;
  total: number;
  message: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
}