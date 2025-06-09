from flask import Blueprint, request, jsonify
import os
import re
from datetime import datetime
from config import Config
from models import db, Match, ProcessingStatus
from services.youtube_service import get_video_title

# Create blueprint
matches_bp = Blueprint('matches', __name__)

def extract_players_from_title(title):
    """Extract player names from video title using common patterns"""
    players = []
    
    if not title:
        return players
    
    # Common patterns for tennis videos
    patterns = [
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+vs?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "Player1 vs Player2"
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',    # "Player1 v Player2"
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+-\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',    # "Player1 - Player2"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, title)
        if match:
            player1 = match.group(1).strip()
            player2 = match.group(2).strip()
            
            # Filter out common non-player words
            non_players = ['highlights', 'match', 'final', 'semi', 'quarter', 'atp', 'wta', 'tennis']
            
            if player1.lower() not in non_players and len(player1) > 2:
                players.append(player1)
            if player2.lower() not in non_players and len(player2) > 2:
                players.append(player2)
            
            break
    
    return players

def extract_tournament_from_title(title):
    """Extract tournament name from video title"""
    if not title:
        return None
    
    title_lower = title.lower()
    
    # Common tournament patterns
    tournaments = [
        'wimbledon', 'roland garros', 'french open', 'us open', 'australian open',
        'miami open', 'indian wells', 'masters', 'atp finals', 'wta finals',
        'roland-garros', 'cincinnati', 'toronto', 'madrid', 'rome', 'monte carlo'
    ]
    
    for tournament in tournaments:
        if tournament in title_lower:
            return tournament.title()
    
    # Look for patterns like "2024 Tournament Name"
    tournament_pattern = r'(\d{4}\s+[A-Z][a-zA-Z\s]+(?:Open|Masters|Cup|Championship))'
    match = re.search(tournament_pattern, title)
    if match:
        return match.group(1).strip()
    
    return None

@matches_bp.route('/migrate', methods=['POST'])
def migrate_existing_transcripts():
    """Create Match records for existing transcript files"""
    try:
        captions_dir = Config.CAPTIONS_DIR
        
        if not os.path.exists(captions_dir):
            return jsonify({
                "success": False,
                "message": "Captions directory not found"
            })
        
        # Get all transcript files (excluding _clean.txt files to avoid duplicates)
        transcript_files = [f for f in os.listdir(captions_dir) if f.endswith('.txt') and not f.endswith('_clean.txt')]
        
        created_matches = []
        skipped_matches = []
        errors = []
        
        for filename in transcript_files:
            try:
                # Extract video_id from filename
                video_id = filename.replace('.txt', '')
                
                # Check if match already exists
                existing_match = Match.query.filter_by(video_id=video_id).first()
                if existing_match:
                    skipped_matches.append(f"{video_id} - already exists")
                    continue
                
                # Get video title
                try:
                    title = get_video_title(video_id)
                except:
                    title = f"Tennis Match {video_id}"
                
                # Extract players from title
                players = extract_players_from_title(title)
                
                # Extract tournament from title  
                tournament = extract_tournament_from_title(title)
                
                # Check if clean transcript exists to determine status
                clean_file = os.path.join(captions_dir, f"{video_id}_clean.txt")
                
                if os.path.exists(clean_file):
                    status = ProcessingStatus.COMPLETED
                else:
                    status = ProcessingStatus.PROCESSING
                
                # Create match record
                new_match = Match(
                    video_id=video_id,
                    title=title,
                    players=players,
                    tournament=tournament,
                    processing_status=status,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.session.add(new_match)
                created_matches.append(f"{video_id} - {title}")
                
            except Exception as e:
                errors.append(f"{filename}: {str(e)}")
        
        # Commit all changes
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Migration completed: {len(created_matches)} matches created",
            "created_matches": created_matches,
            "skipped_matches": skipped_matches,
            "errors": errors,
            "summary": {
                "total_files": len(transcript_files),
                "created": len(created_matches),
                "skipped": len(skipped_matches),
                "errors": len(errors)
            }
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@matches_bp.route('/', methods=['GET'])
def get_all_matches():
    """Get all processed matches with optional status filter"""
    try:
        status_filter = request.args.get('status')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query based on filters
        query = Match.query
        
        if status_filter and status_filter != 'all':
            # Map frontend status names to database enum values
            status_mapping = {
                'completed': ProcessingStatus.COMPLETED,
                'processing': ProcessingStatus.PROCESSING,
                'failed': ProcessingStatus.FAILED,
                'pending': ProcessingStatus.PENDING
            }
            if status_filter in status_mapping:
                query = query.filter(Match.processing_status == status_mapping[status_filter])
        
        # Order by most recent first
        query = query.order_by(Match.created_at.desc())
        
        # Apply pagination
        total_count = query.count()
        matches = query.offset(offset).limit(limit).all()
        
        # Convert to JSON format
        matches_data = []
        for match in matches:
            # Check if transcript files exist (as additional verification)
            captions_dir = Config.CAPTIONS_DIR
            raw_transcript_path = os.path.join(captions_dir, f"{match.video_id}.txt")
            clean_transcript_path = os.path.join(captions_dir, f"{match.video_id}_clean.txt")
            
            has_raw_transcript = os.path.exists(raw_transcript_path)
            has_clean_transcript = os.path.exists(clean_transcript_path)
            
            # Calculate transcript length if available
            transcript_length = None
            if has_clean_transcript:
                try:
                    with open(clean_transcript_path, 'r', encoding='utf-8') as f:
                        transcript_length = len(f.read())
                except:
                    pass
            elif has_raw_transcript:
                try:
                    with open(raw_transcript_path, 'r', encoding='utf-8') as f:
                        transcript_length = len(f.read())
                except:
                    pass
            
            # Use database status, but verify with file existence
            db_status = match.processing_status.value if match.processing_status else 'pending'
            
            # Additional verification - if DB says completed but files don't exist, mark as failed
            if db_status == 'completed' and not (has_raw_transcript and has_clean_transcript):
                actual_status = 'failed'
            else:
                actual_status = db_status
            
            match_data = {
                'id': match.id,
                'video_id': match.video_id,
                'title': match.title or f"Video {match.video_id}",
                'duration': match.duration_seconds,
                'processed_at': match.created_at.isoformat() if match.created_at else None,
                'status': actual_status,
                'thumbnail_url': f"https://img.youtube.com/vi/{match.video_id}/mqdefault.jpg",
                'players_detected': match.players if match.players else [],
                'transcript_length': transcript_length,
                'has_raw_transcript': has_raw_transcript,
                'has_clean_transcript': has_clean_transcript,
                'azure_search_indexed': match.azure_search_indexed,
                'tournament': match.tournament,
                'surface': match.surface,
                'match_date': match.match_date.isoformat() if match.match_date else None,
                'error_message': match.error_message
            }
            matches_data.append(match_data)
        
        return jsonify({
            'success': True,
            'matches': matches_data,
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'has_more': (offset + limit) < total_count
        })
        
    except Exception as e:
        print(f"Error fetching matches: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Failed to fetch matches: {str(e)}'
        }), 500

@matches_bp.route('/<match_id>', methods=['GET'])
def get_match_by_id(match_id):
    """Get a specific match by ID"""
    try:
        match = Match.query.get(match_id)
        
        if not match:
            return jsonify({
                'success': False,
                'message': 'Match not found'
            }), 404
        
        # Check transcript files
        captions_dir = Config.CAPTIONS_DIR
        raw_transcript_path = os.path.join(captions_dir, f"{match.video_id}.txt")
        clean_transcript_path = os.path.join(captions_dir, f"{match.video_id}_clean.txt")
        
        has_raw_transcript = os.path.exists(raw_transcript_path)
        has_clean_transcript = os.path.exists(clean_transcript_path)
        
        # Get transcript content if requested
        include_content = request.args.get('include_content', 'false').lower() == 'true'
        transcript_content = None
        
        if include_content and has_clean_transcript:
            try:
                with open(clean_transcript_path, 'r', encoding='utf-8') as f:
                    transcript_content = f.read()
            except:
                pass
        
        # Calculate transcript length
        transcript_length = len(transcript_content) if transcript_content else None
        if not transcript_length and has_clean_transcript:
            try:
                with open(clean_transcript_path, 'r', encoding='utf-8') as f:
                    transcript_length = len(f.read())
            except:
                pass
        
        # Use database status
        db_status = match.processing_status.value if match.processing_status else 'pending'
        
        # Verify with file existence
        if db_status == 'completed' and not (has_raw_transcript and has_clean_transcript):
            actual_status = 'failed'
        else:
            actual_status = db_status
        
        match_data = {
            'id': match.id,
            'video_id': match.video_id,
            'title': match.title or f"Video {match.video_id}",
            'duration': match.duration_seconds,
            'processed_at': match.created_at.isoformat() if match.created_at else None,
            'status': actual_status,
            'thumbnail_url': f"https://img.youtube.com/vi/{match.video_id}/mqdefault.jpg",
            'players_detected': match.players if match.players else [],
            'transcript_length': transcript_length,
            'has_raw_transcript': has_raw_transcript,
            'has_clean_transcript': has_clean_transcript,
            'transcript_content': transcript_content if include_content else None,
            'azure_search_indexed': match.azure_search_indexed,
            'tournament': match.tournament,
            'surface': match.surface,
            'match_date': match.match_date.isoformat() if match.match_date else None,
            'error_message': match.error_message
        }
        
        return jsonify({
            'success': True,
            'match': match_data
        })
        
    except Exception as e:
        print(f"Error fetching match: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to fetch match: {str(e)}'
        }), 500

@matches_bp.route('/<match_id>', methods=['DELETE'])
def delete_match(match_id):
    """Delete a processed match and its associated files"""
    try:
        match = Match.query.get(match_id)
        
        if not match:
            return jsonify({
                'success': False,
                'message': 'Match not found'
            }), 404
        
        video_id = match.video_id
        
        # Delete transcript files
        captions_dir = Config.CAPTIONS_DIR
        files_to_delete = [
            os.path.join(captions_dir, f"{video_id}.txt"),
            os.path.join(captions_dir, f"{video_id}_clean.txt")
        ]
        
        deleted_files = []
        for file_path in files_to_delete:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    deleted_files.append(file_path)
                except Exception as e:
                    print(f"Warning: Failed to delete file {file_path}: {e}")
        
        # Delete from database
        db.session.delete(match)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Match deleted successfully',
            'deleted_files': deleted_files
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting match: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to delete match: {str(e)}'
        }), 500

@matches_bp.route('/<match_id>/reprocess', methods=['POST'])
def reprocess_match(match_id):
    """Reprocess a failed match"""
    try:
        match = Match.query.get(match_id)
        
        if not match:
            return jsonify({
                'success': False,
                'message': 'Match not found'
            }), 404
        
        video_id = match.video_id
        
        # Update status to processing
        match.processing_status = ProcessingStatus.PROCESSING
        match.updated_at = datetime.utcnow()
        match.error_message = None
        
        db.session.commit()
        
        # Here you would trigger your reprocessing pipeline
        # For now, we'll just return a success message
        # You can integrate this with your existing transcript extraction and cleaning services
        
        return jsonify({
            'success': True,
            'message': 'Match reprocessing started',
            'job_id': f'reprocess_{match_id}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error reprocessing match: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to reprocess match: {str(e)}'
        }), 500

@matches_bp.route('/search', methods=['GET'])
def search_matches():
    """Search matches by title, video ID, or players"""
    try:
        query = request.args.get('q', '').strip()
        limit = request.args.get('limit', 20, type=int)
        
        if not query:
            return jsonify({
                'success': False,
                'message': 'Search query is required'
            }), 400
        
        # Search in title and video_id
        search_pattern = f'%{query}%'
        matches = Match.query.filter(
            db.or_(
                Match.title.ilike(search_pattern),
                Match.video_id.ilike(search_pattern)
            )
        ).order_by(Match.created_at.desc()).limit(limit).all()
        
        # Convert to JSON format (similar to get_all_matches)
        matches_data = []
        for match in matches:
            captions_dir = Config.CAPTIONS_DIR
            raw_transcript_path = os.path.join(captions_dir, f"{match.video_id}.txt")
            clean_transcript_path = os.path.join(captions_dir, f"{match.video_id}_clean.txt")
            
            has_raw_transcript = os.path.exists(raw_transcript_path)
            has_clean_transcript = os.path.exists(clean_transcript_path)
            
            db_status = match.processing_status.value if match.processing_status else 'pending'
            
            if db_status == 'completed' and not (has_raw_transcript and has_clean_transcript):
                actual_status = 'failed'
            else:
                actual_status = db_status
            
            match_data = {
                'id': match.id,
                'video_id': match.video_id,
                'title': match.title or f"Video {match.video_id}",
                'duration': match.duration_seconds,
                'processed_at': match.created_at.isoformat() if match.created_at else None,
                'status': actual_status,
                'thumbnail_url': f"https://img.youtube.com/vi/{match.video_id}/mqdefault.jpg",
                'players_detected': match.players if match.players else [],
                'has_raw_transcript': has_raw_transcript,
                'has_clean_transcript': has_clean_transcript,
                'tournament': match.tournament,
                'azure_search_indexed': match.azure_search_indexed
            }
            matches_data.append(match_data)
        
        return jsonify({
            'success': True,
            'matches': matches_data,
            'total': len(matches_data),
            'query': query
        })
        
    except Exception as e:
        print(f"Search error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Search failed: {str(e)}'
        }), 500

@matches_bp.route('/stats', methods=['GET'])
def get_matches_stats():
    """Get statistics about processed matches"""
    try:
        total_matches = Match.query.count()
        
        # Count by database status
        completed_count = Match.query.filter(Match.processing_status == ProcessingStatus.COMPLETED).count()
        processing_count = Match.query.filter(Match.processing_status == ProcessingStatus.PROCESSING).count()
        failed_count = Match.query.filter(Match.processing_status == ProcessingStatus.FAILED).count()
        pending_count = Match.query.filter(Match.processing_status == ProcessingStatus.PENDING).count()
        
        # Get matches with Azure Search indexing stats
        indexed_count = Match.query.filter(Match.azure_search_indexed == True).count()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_matches': total_matches,
                'completed': completed_count,
                'processing': processing_count,
                'failed': failed_count,
                'pending': pending_count,
                'indexed': indexed_count,
                'success_rate': round((completed_count / total_matches * 100) if total_matches > 0 else 0, 2)
            }
        })
        
    except Exception as e:
        print(f"Error getting stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to get stats: {str(e)}'
        }), 500

@matches_bp.route('/debug', methods=['GET'])
def debug_matches():
    """Debug endpoint to check matches table and data"""
    try:
        # Check if table exists and get all matches
        from sqlalchemy import text
        
        # Check table existence (this will work for PostgreSQL too)
        result = db.session.execute(text("SELECT COUNT(*) FROM matches"))
        table_accessible = result.fetchone()[0] >= 0
        
        # Get row count
        total_matches = Match.query.count()
        
        # Get all matches
        all_matches = Match.query.all()
        
        # Check what's in the captions directory
        captions_dir = Config.CAPTIONS_DIR
        transcript_files = []
        if os.path.exists(captions_dir):
            transcript_files = [f for f in os.listdir(captions_dir) if f.endswith('.txt')]
        
        debug_info = {
            "success": True,
            "database_info": {
                "table_accessible": table_accessible,
                "total_matches_in_db": total_matches,
                "matches": [match.to_dict() for match in all_matches[:5]]  # Show first 5 only
            },
            "filesystem_info": {
                "captions_dir": captions_dir,
                "captions_dir_exists": os.path.exists(captions_dir),
                "transcript_files": transcript_files,
                "total_transcript_files": len(transcript_files)
            }
        }
        
        return jsonify(debug_info)
        
    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500