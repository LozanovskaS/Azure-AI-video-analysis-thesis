from flask import Blueprint, request, jsonify
import os
import time
from azure_tennis_api.services.search_service import SearchService 
from azure_tennis_api.services.chat_service import chat_with_context
from azure_tennis_api.config import Config
from azure_tennis_api.models import db, AnalysisSession

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/query', methods=['POST'])
def chat_query():
    """Chat with AI using specified transcript"""
    data = request.get_json()
    query = data.get('query')
    video_id = data.get('video_id')  # Frontend sends current video ID
    conversation_history = data.get('conversation_history', [])
    
    if not query:
        return jsonify({"success": False, "message": "No query provided"}), 400
    
    if not video_id:
        return jsonify({"success": False, "message": "No video ID provided"}), 400
    
    start_time = time.time()
    
    try:
        # Read transcript for the specified video
        clean_file_path = os.path.join(Config.CAPTIONS_DIR, f"{video_id}_clean.txt")
        
        if not os.path.exists(clean_file_path):
            return jsonify({
                "success": False,
                "message": f"Transcript not found for video: {video_id}"
            }), 404
        
        with open(clean_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        context = f"From tennis match (Video ID: {video_id}):\n{content}"
        
        # Get AI response using the context
        ai_response = chat_with_context(query, context, conversation_history)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Save to database (optional)
        try:
            analysis_session = AnalysisSession(
                question=query,
                ai_response=ai_response,
                source_match_ids=[],  # Empty since no Match model
                processing_time_ms=processing_time_ms
            )
            db.session.add(analysis_session)
            db.session.commit()
        except Exception:
            # Ignore database errors for simplicity
            pass
        
        # Return response
        return jsonify({
            "success": True,
            "response": ai_response,
            "sources": [{"title": f"Tennis Match ({video_id})", "video_id": video_id}],
            "processing_time_ms": processing_time_ms
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

# Optional: Keep these if needed, otherwise remove
@chat_bp.route('/analyze', methods=['POST'])
def analyze_question():
    """Alternative endpoint for frontend compatibility"""
    return chat_query()

@chat_bp.route('/history', methods=['GET'])
def get_analysis_history():
    """Get recent analysis sessions"""
    try:
        sessions = AnalysisSession.query.order_by(
            AnalysisSession.created_at.desc()
        ).limit(20).all()
        
        return jsonify({
            "success": True,
            "data": [session.to_dict() for session in sessions]
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500