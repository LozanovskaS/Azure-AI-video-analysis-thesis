from flask import Blueprint, request, jsonify
import os
import time
from backend.services.search_service import SearchService 
from backend.services.chat_service import chat_with_context
from backend.config import Config
from backend.models import db, AnalysisSession

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/query', methods=['POST'])
def chat_query():
    """Simple chat with AI using transcript context"""
    data = request.get_json()
    query = data.get('query')
    conversation_history = data.get('conversation_history', [])
    
    if not query:
        return jsonify({"success": False, "message": "No query provided"}), 400
    
    start_time = time.time()
    
    try:
        # 1. Search for relevant transcripts
        search_service = SearchService()
        search_results = search_service.search_transcript(query)
        
        if not search_results:
            return jsonify({
                "success": False,
                "message": "No relevant content found"
            }), 404
        
        # 2. Prepare context from top 3 results
        context_parts = []
        source_video_ids = []
        
        for result in search_results[:3]:
            video_id = result["video_id"]
            source_video_ids.append(video_id)
            
            # Read transcript content
            clean_file_path = os.path.join(Config.CAPTIONS_DIR, f"{video_id}_clean.txt")
            
            if os.path.exists(clean_file_path):
                with open(clean_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                title = result.get("title", f"Video {video_id}")
                context_text = f"From match '{title}':\n{content[:2000]}"
                context_parts.append(context_text)
        
        if not context_parts:
            return jsonify({
                "success": False,
                "message": "No transcript content found"
            }), 404
        
        context = "\n\n".join(context_parts)
        
        # 3. Get AI response
        ai_response = chat_with_context(query, context, conversation_history)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # 4. Save to database (optional - remove if not needed)
        try:
            analysis_session = AnalysisSession(
                user_id=None,
                question=query,
                ai_response=ai_response,
                source_match_ids=[],
                processing_time_ms=processing_time_ms
            )
            db.session.add(analysis_session)
            db.session.commit()
        except Exception:
            # Ignore database errors for simplicity
            pass
        
        # 5. Return response
        return jsonify({
            "success": True,
            "response": ai_response,
            "sources": [
                {"title": result.get("title", result["video_id"]), "video_id": result["video_id"]}
                for result in search_results[:3]
            ],
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