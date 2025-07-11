from flask import Blueprint, request, jsonify
import os
from datetime import datetime
from azure_tennis_api.config import Config
from azure_tennis_api.services.search_service import SearchService
from azure_tennis_api.services.blob_storage_service import BlobStorageService    
from azure_tennis_api.models import db, Match 

search_bp = Blueprint('search', __name__)

def get_video_title(video_id):
    try:
        match = Match.query.filter_by(video_id=video_id).first()
        if match and match.title:
            return match.title
        else:
            return f"Video {video_id}"
    except Exception as e:
        print(f"Error getting video title: {str(e)}")
        return f"Video {video_id}"

def mark_match_indexed(video_id, indexed=True):
    try:
        match = Match.query.filter_by(video_id=video_id).first()
        
        if not match:
            print(f"⚠️ No match found for video_id: {video_id}")
            return False
        
        match.azure_search_indexed = indexed
        match.updated_at = datetime.utcnow()
        
        db.session.commit()
        print(f"✅ Updated match {video_id} indexing status to {indexed}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating match indexing status: {str(e)}")
        db.session.rollback()
        return False

@search_bp.route('/index/<video_id>', methods=['POST'])
def index_transcript(video_id):
    try:
        captions_dir = Config.CAPTIONS_DIR
        clean_file_path = os.path.join(captions_dir, f"{video_id}_clean.txt")
                
        if not os.path.exists(clean_file_path):
            return jsonify({
                "success": False, 
                "message": f"❌ Clean transcript not found for video ID: {video_id}"
            }), 404
                
        video_title = get_video_title(video_id)
                
        with open(clean_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
                
        search_service = SearchService()
        result = search_service.index_transcript(video_id, video_title, content)
                
        if result.get("success", False):
            mark_match_indexed(video_id, True)
            
            return jsonify({
                "success": True,
                "message": f"✅ Indexed transcript for: {video_title}",
                "video_id": video_id,
                "title": video_title
            })
        else:
            mark_match_indexed(video_id, False)
            
            return jsonify({
                "success": False,
                "message": f"❌ Failed to index transcript: {result.get('error', 'Unknown error')}"
            }), 500
            
    except Exception as e:
        print(f"Error indexing transcript: {str(e)}")
        mark_match_indexed(video_id, False)
        
        return jsonify({"success": False, "message": f"❌ Error: {str(e)}"}), 500

@search_bp.route('/query', methods=['POST'])
def search_transcripts():
    data = request.get_json()
    query = data.get('query')
    top = data.get('top', 3)
        
    if not query:
        return jsonify({"success": False, "message": "❌ No query provided"}), 400
        
    try:
        search_service = SearchService()
        results = search_service.search_transcript(query, top)
                
        if isinstance(results, dict) and not results.get("success", True):
            return jsonify({
                "success": False,
                "message": f"❌ Search failed: {results.get('error', 'Unknown error')}"
            }), 500
                
        return jsonify({
            "success": True,
            "message": f"✅ Found {len(results)} results",
            "results": results
        })
            
    except Exception as e:
        print(f"Error searching transcripts: {str(e)}")
        return jsonify({"success": False, "message": f"❌ Error: {str(e)}"}), 500