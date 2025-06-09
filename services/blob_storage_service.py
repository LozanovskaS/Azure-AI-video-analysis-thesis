import os
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from config import Config

class BlobStorageService:
    def __init__(self):
        """Initialize Blob Storage Service"""
        self.connection_string = Config.AZURE_STORAGE_CONNECTION_STRING
        self.container_name = Config.AZURE_STORAGE_CONTAINER_NAME
        
        # Blob service client
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        
        self._ensure_container_exists()
    
    def _ensure_container_exists(self):
        """Create container if it doesn't exist"""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            container_client.get_container_properties()
        except Exception:
            # Container doesn't exist, create it
            self.blob_service_client.create_container(self.container_name)
    
    def upload_transcript(self, video_id, content, is_clean=False):
        """Upload a transcript file to blob storage"""
        try:
            blob_name = f"{video_id}_clean.txt" if is_clean else f"{video_id}.txt"
            
            # blob client
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Upload content
            blob_client.upload_blob(content, overwrite=True)
            
            return {
                "success": True,
                "message": f"Uploaded {blob_name} to blob storage",
                "url": blob_client.url
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to upload to blob storage: {str(e)}"
            }
    
    def download_transcript(self, video_id, is_clean=False):
        """Download a transcript file from blob storage"""
        try:
            #blob name
            blob_name = f"{video_id}_clean.txt" if is_clean else f"{video_id}.txt"
            
            #blob client
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Download content
            downloaded_blob = blob_client.download_blob()
            content = downloaded_blob.content_as_text()
            
            return {
                "success": True,
                "content": content
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to download from blob storage: {str(e)}"
            }
    
    def list_transcripts(self):
        """List all transcripts in the container"""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            blobs = container_client.list_blobs()
            
            transcripts = []
            for blob in blobs:
                # Extract video_id and is_clean information from blob name
                blob_name = blob.name
                is_clean = blob_name.endswith("_clean.txt")
                video_id = blob_name.replace(".txt", "").replace("_clean", "")
                
                transcripts.append({
                    "video_id": video_id,
                    "blob_name": blob_name,
                    "is_clean": is_clean,
                    "size": blob.size,
                    "last_modified": blob.last_modified
                })
                
            return {
                "success": True,
                "transcripts": transcripts
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to list transcripts: {str(e)}"
            }
    
    def delete_transcript(self, video_id, is_clean=False):
        """Delete a transcript from blob storage"""
        try:
            # Determine blob name
            blob_name = f"{video_id}_clean.txt" if is_clean else f"{video_id}.txt"
            
            # Create a blob client
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Delete blob
            blob_client.delete_blob()
            
            return {
                "success": True,
                "message": f"Deleted {blob_name} from blob storage"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to delete from blob storage: {str(e)}"
            }