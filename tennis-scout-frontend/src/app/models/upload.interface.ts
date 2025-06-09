export interface UploadRequest {
  input: string;
}

export interface UploadResponse {
  success: boolean;
  message: string;
  video_id?: string;
  title?: string;
}