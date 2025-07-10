import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, 
    SimpleField, 
    SearchableField,
    SearchFieldDataType
)
from azure_tennis_api.config import Config

class SearchService:
    def __init__(self):
        self.endpoint = Config.AZURE_SEARCH_ENDPOINT
        self.key = Config.AZURE_SEARCH_KEY
        self.index_name = Config.AZURE_SEARCH_INDEX_NAME
        
        # Create SearchIndexClient
        self.index_client = SearchIndexClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.key)
        )
        
        # Create SearchClient
        self.search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_name,
            credential=AzureKeyCredential(self.key)
        )
        
    def verify_index_exists(self):
        try:
            # Get the specific index to verify it exists and check its schema
            index = self.index_client.get_index(self.index_name)
            print(f"✅ Successfully connected to existing index: {self.index_name}")
            
            # Check index schema for field compatibility
            print(f"📋 Index has {len(index.fields)} fields:")
            field_names = []
            key_field = None
            
            for field in index.fields:
                field_names.append(field.name)
                if field.key:
                    key_field = field.name
                print(f"  - {field.name} ({field.type}) {'[KEY]' if field.key else ''} {'[SEARCHABLE]' if getattr(field, 'searchable', False) else ''}")
            
            # Check if required fields exist
            required_fields = ['id', 'video_id', 'title', 'content']
            missing_fields = [field for field in required_fields if field not in field_names]
            
            if missing_fields:
                print(f"Warning: Missing expected fields: {missing_fields}")
                print(f"Available fields: {field_names}")
                print("You may need to adjust your document structure")
            
            if key_field:
                print(f"🔑 Key field: {key_field}")
            else:
                print("⚠️ Warning: No key field found")
            
            return True
            
        except Exception as e:
            print(f"❌ Error accessing index '{self.index_name}': {str(e)}")
            print("Make sure:")
            print("1. The index name is correct: 'tennis-ai-index'")
            print("2. The search service is running") 
            print("3. Your API key has proper permissions")
            print("4. The service URL is correct")
            return False

    def index_transcript(self, video_id, title, transcript):
        """Index a transcript into the existing Azure Search index"""
        try:
            if not self.verify_index_exists():
                return {
                    "success": False,
                    "message": "Failed to connect to existing index"
                }
    
            # Validate inputs
            if not video_id or not title or not transcript:
                return {
                    "success": False,
                    "message": "Missing required fields: video_id, title, or transcript"
                }
    
            # Map to the existing index schema
            document = {
                "chunk_id": str(video_id),  
                "parent_id": str(video_id),
                "content": str(transcript),
                "title": str(title)[:1000],
                "url": f"https://www.youtube.com/watch?v={video_id}", # YouTube URL
                "filepath": f"youtube/{video_id}.txt",
            }
             
            print(f" Preparing to index transcript:")
            print(f"   - Video ID: {video_id}")
            print(f"   - Title: {title[:50]}...")
            print(f"   - Content length: {len(transcript)} characters")
            print(f"   - Mapped to existing schema with chunk_id as key")
            
            # Upload to Azure Search with detailed error handling
            print("🔄 Uploading document to Azure Search...")
            result = self.search_client.upload_documents(documents=[document])
            
            print(f" Upload result: {len(result)} results returned")
            
            if not result:
                return {
                    "success": False,
                    "message": "No upload results returned from Azure Search"
                }
           
            upload_result = result[0]
            print(f" First result details:")
            print(f"   - Succeeded: {upload_result.succeeded}")
            print(f"   - Key: {getattr(upload_result, 'key', 'N/A')}")
            print(f"   - Status code: {getattr(upload_result, 'status_code', 'N/A')}")
            
            if upload_result.succeeded:
                print(f"✅ Successfully indexed transcript for video: {title}")
                return {
                    "success": True,
                    "message": "Transcript indexed successfully"
                }
            else:
                #error information
                error_details = []
                if hasattr(upload_result, 'error_message') and upload_result.error_message:
                    error_details.append(f"Error message: {upload_result.error_message}")
                if hasattr(upload_result, 'status_code'):
                    error_details.append(f"Status code: {upload_result.status_code}")
                if hasattr(upload_result, 'key'):
                    error_details.append(f"Document key: {upload_result.key}")
                
                error_msg = "Document upload failed. " + " | ".join(error_details) if error_details else "Unknown upload error"
                print(f"❌ {error_msg}")
                
                return {
                    "success": False,
                    "message": error_msg
                }
                
        except Exception as e:
            error_msg = f"Exception during indexing: {type(e).__name__}: {str(e)}"
            print(f"❌ {error_msg}")
            
    def search_transcript(self, query, top=3):
        """Search for transcripts in Azure Search using existing schema"""
        try:
            results = self.search_client.search(
                search_text=query,
                top=top,
                highlight_fields="content",
                highlight_pre_tag="<strong>",
                highlight_post_tag="</strong>",
                select="chunk_id,parent_id,title,url"
            )
            
            result_list = []
            for doc in results:
                result_item = {
                    "id": doc["chunk_id"],  
                    "video_id": doc["parent_id"],  
                    "title": doc["title"],
                    "url": doc.get("url", ""),
                    "score": doc.get("@search.score", 0.0)
                }
                
                if "@search.highlights" in doc and "content" in doc["@search.highlights"]:
                    result_item["highlights"] = doc["@search.highlights"]["content"]   
                    
                result_list.append(result_item)
                
            print(f"Found {len(result_list)} results")
            return result_list
        
        except Exception as e:
            print(f"Error searching transcripts: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
