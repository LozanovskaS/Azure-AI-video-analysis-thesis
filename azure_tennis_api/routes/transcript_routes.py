from flask import Blueprint, request, jsonify
import os
import re
from datetime import datetime
from azure_tennis_api.config import Config
from azure_tennis_api.services.blob_storage_service import BlobStorageService
from azure_tennis_api.models import db, Match, ProcessingStatus
from azure_tennis_api.services.youtube_service import get_transcript, extract_video_id, get_video_ids_from_playlist, get_video_title
from azure_tennis_api.services.openai_service import clean_transcript_with_llm

transcript_bp = Blueprint('transcript', __name__)

blob_service = BlobStorageService()

def create_or_update_match(video_id, title=None):
    try:
        existing_match = Match.query.filter_by(video_id=video_id).first()
        
        if existing_match:
            print(f"Match already exists for video {video_id}, updating status...")
            existing_match.processing_status = ProcessingStatus.PROCESSING
            existing_match.updated_at = datetime.utcnow()
            if title and not existing_match.title:
                existing_match.title = title
            db.session.commit()
            return existing_match
        
        if not title:
            title = get_video_title(video_id)
        
        players = extract_players_from_title(title)
        tournament = extract_tournament_from_title(title)
        
        new_match = Match(
            video_id=video_id,
            title=title,
            players=players,
            tournament=tournament,
            processing_status=ProcessingStatus.PROCESSING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(new_match)
        db.session.commit()
        
        print(f"✅ Created new match record for {video_id}: {title}")
        return new_match
        
    except Exception as e:
        print(f"❌ Error creating/updating match: {str(e)}")
        db.session.rollback()
        return None

def update_match_status(video_id, status, error_message=None):
    try:
        match = Match.query.filter_by(video_id=video_id).first()
        
        if not match:
            print(f"⚠️ No match found for video_id: {video_id}")
            return False
        
        match.processing_status = status
        match.updated_at = datetime.utcnow()
        
        if error_message:
            match.error_message = error_message
        
        db.session.commit()
        print(f"✅ Updated match {video_id} status to {status.value}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating match status: {str(e)}")
        db.session.rollback()
        return False

def extract_players_from_title(title):
    players = []
    
    if not title:
        return players
    
    patterns = [
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+vs?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+-\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, title)
        if match:
            player1 = match.group(1).strip()
            player2 = match.group(2).strip()
            
            non_players = ['highlights', 'match', 'final', 'semi', 'quarter', 'atp', 'wta', 'tennis']
            
            if player1.lower() not in non_players and len(player1) > 2:
                players.append(player1)
            if player2.lower() not in non_players and len(player2) > 2:
                players.append(player2)
            
            break
    
    return players

def extract_tournament_from_title(title):
    if not title:
        return None
    
    title_lower = title.lower()
    
    tournaments = [
        'wimbledon', 'roland garros', 'french open', 'us open', 'australian open',
        'miami open', 'indian wells', 'masters', 'atp finals', 'wta finals',
        'roland-garros', 'cincinnati', 'toronto', 'madrid', 'rome', 'monte carlo'
    ]
    
    for tournament in tournaments:
        if tournament in title_lower:
            return tournament.title()
    
    tournament_pattern = r'(\d{4}\s+[A-Z][a-zA-Z\s]+(?:Open|Masters|Cup|Championship))'
    match = re.search(tournament_pattern, title)
    if match:
        return match.group(1).strip()
    
    return None

@transcript_bp.route('/extract', methods=['POST'])
def extract_transcript():
    data = request.get_json()
    user_input = data.get('input')
    
    if not user_input:
        return jsonify({"success": False, "message": "❌ No input provided."}), 400
    
    try:
        parsed = extract_video_id(user_input)
        captions_dir = Config.CAPTIONS_DIR
        os.makedirs(captions_dir, exist_ok=True)
        
        if parsed['type'] == 'video':
            video_id = parsed['id']
            video_title = get_video_title(video_id)
            match_record = create_or_update_match(video_id, video_title)
            transcript_result = get_transcript(video_id)
            
            if not transcript_result['success']:
                if match_record:
                    update_match_status(video_id, ProcessingStatus.FAILED, transcript_result.get('error'))
                
                return jsonify({
                    "success": False,
                    "message": f"❌ Failed to extract transcript: {transcript_result.get('error', 'Unknown error')}"
                }), 400
            
            file_path = os.path.join(captions_dir, f"{video_id}.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(transcript_result['transcript'])
            
            if Config.USE_BLOB_STORAGE:
                blob_result = blob_service.upload_transcript(
                    video_id=video_id,
                    content=transcript_result['transcript'],
                    is_clean=False
                )
                if not blob_result['success']:
                    print(f"Warning: Failed to upload to blob storage: {blob_result.get('message')}")
            
            if match_record:
                update_match_status(video_id, ProcessingStatus.PROCESSING)
            
            return jsonify({
                "success": True,
                "message": f"✅ Saved transcript for {video_id} to captions/{video_id}.txt",
                "video_id": video_id,
                "title": video_title,
                "match_id": match_record.id if match_record else None
            })
            
        elif parsed['type'] == 'playlist':
            playlist_id = parsed['id']
            video_ids = get_video_ids_from_playlist(playlist_id)
            
            results = []
            for video_id in video_ids:
                try:
                    video_title = get_video_title(video_id)
                    match_record = create_or_update_match(video_id, video_title)
                    transcript_result = get_transcript(video_id)
                    
                    if not transcript_result['success']:
                        if match_record:
                            update_match_status(video_id, ProcessingStatus.FAILED, transcript_result.get('error'))
                        
                        results.append({
                            "success": False,
                            "video_id": video_id,
                            "title": video_title,
                            "error": transcript_result.get('error', 'Unknown error'),
                            "match_id": match_record.id if match_record else None
                        })
                        continue
                    
                    file_path = os.path.join(captions_dir, f"{video_id}.txt")
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(transcript_result['transcript'])
                    
                    if Config.USE_BLOB_STORAGE:
                        blob_result = blob_service.upload_transcript(
                            video_id=video_id,
                            content=transcript_result['transcript'],
                            is_clean=False
                        )
                        if not blob_result['success']:
                            print(f"Warning: Failed to upload to blob storage: {blob_result.get('message')}")
                    
                    if match_record:
                        update_match_status(video_id, ProcessingStatus.PROCESSING)
                    
                    results.append({
                        "success": True,
                        "video_id": video_id,
                        "title": video_title,
                        "match_id": match_record.id if match_record else None
                    })
                    
                except Exception as e:
                    results.append({
                        "success": False,
                        "video_id": video_id,
                        "error": str(e)
                    })
            
            return jsonify({
                "success": True,
                "message": f"✅ Processed {sum(1 for r in results if r['success'])} of {len(results)} videos from playlist",
                "playlist_id": playlist_id,
                "results": results
            })
            
        else:
            return jsonify({"success": False, "message": "❌ Invalid input type."}), 400
            
    except Exception as e:
        return jsonify({"success": False, "message": f"❌ Error: {str(e)}"}), 500

@transcript_bp.route('/clean/<video_id>', methods=['POST'])
def clean_transcript_route(video_id):
    try:
        transcript_text = None
        if Config.USE_BLOB_STORAGE:
            blob_result = blob_service.download_transcript(video_id, is_clean=False)
            if blob_result.get('success', False):
                transcript_text = blob_result['content']
                print(f"Retrieved transcript from blob storage for video ID: {video_id}")
        
        if transcript_text is None:
            captions_dir = Config.CAPTIONS_DIR
            
            possible_filenames = [
                f"{video_id}.txt",
                f"{video_id}_raw.txt"
            ]
            
            file_path = None
            for filename in possible_filenames:
                path = os.path.join(captions_dir, filename)
                print(f"Checking if file exists: {path}")
                if os.path.exists(path):
                    file_path = path
                    break
            
            if not file_path:
                update_match_status(video_id, ProcessingStatus.FAILED, "No transcript file found")
                
                return jsonify({
                    "success": False, 
                    "message": f"❌ No transcript file found for video ID: {video_id}"
                }), 404
                
            with open(file_path, "r", encoding="utf-8") as f:
                transcript_text = f.read()
        
        video_title = get_video_title(video_id)
        print(f"Processing video: {video_title} (ID: {video_id})")
        
        print("Cleaning transcript with Azure OpenAI...")
        cleaned_transcript = clean_transcript_with_llm(transcript_text, video_title)
        
        clean_file_path = os.path.join(Config.CAPTIONS_DIR, f"{video_id}_clean.txt")
        with open(clean_file_path, "w", encoding="utf-8") as f:
            f.write(cleaned_transcript)
        
        if Config.USE_BLOB_STORAGE:
            blob_result = blob_service.upload_transcript(
                video_id=video_id,
                content=cleaned_transcript,
                is_clean=True
            )
            if not blob_result['success']:
                print(f"Warning: Failed to upload cleaned transcript to blob storage: {blob_result.get('message')}")
        
        update_match_status(video_id, ProcessingStatus.COMPLETED)
        
        return jsonify({
            "success": True,
            "message": f"✅ Successfully cleaned transcript for: {video_title}",
            "video_id": video_id,
            "title": video_title
        })
        
    except Exception as e:
        print(f"❌ Error cleaning transcript: {str(e)}")
        import traceback
        traceback.print_exc()
        
        update_match_status(video_id, ProcessingStatus.FAILED, str(e))
        
        return jsonify({"success": False, "message": f"❌ Error: {str(e)}"}), 500

@transcript_bp.route('/content/<video_id>', methods=['GET'])
def get_transcript_content(video_id):
    try:
        clean = request.args.get('clean', 'false').lower() == 'true'
        
        if Config.USE_BLOB_STORAGE:
            blob_result = blob_service.download_transcript(video_id, is_clean=clean)
            if blob_result.get('success', False):
                content = blob_result['content']
                return jsonify({
                    "success": True,
                    "video_id": video_id,
                    "is_clean": clean,
                    "content": content,
                    "title": get_video_title(video_id),
                    "source": "blob_storage"
                })
        
        captions_dir = Config.CAPTIONS_DIR
        file_path = os.path.join(
            captions_dir, 
            f"{video_id}_clean.txt" if clean else f"{video_id}.txt"
        )
        
        if not os.path.exists(file_path):
            return jsonify({
                "success": False, 
                "message": f"❌ Transcript file not found: {file_path}"
            }), 404
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        return jsonify({
            "success": True,
            "video_id": video_id,
            "is_clean": clean,
            "content": content,
            "title": get_video_title(video_id),
            "source": "local_file"
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"❌ Error: {str(e)}"}), 500

@transcript_bp.route('/list', methods=['GET'])
def list_transcripts():
    try:
        transcripts = []
        
        if Config.USE_BLOB_STORAGE:
            blob_result = blob_service.list_transcripts()
            if blob_result.get('success', False):
                for item in blob_result['transcripts']:
                    video_id = item['video_id']
                    
                    if any(t['video_id'] == video_id for t in transcripts):
                        continue
                    
                    try:
                        title = get_video_title(video_id)
                    except:
                        title = f"Unknown Title ({video_id})"
                    
                    transcripts.append({
                        'video_id': video_id,
                        'title': title,
                        'has_raw': any(t['video_id'] == video_id and not t['is_clean'] 
                                      for t in blob_result['transcripts']),
                        'has_clean': any(t['video_id'] == video_id and t['is_clean'] 
                                        for t in blob_result['transcripts']),
                        'source': 'blob_storage'
                    })
        
        captions_dir = Config.CAPTIONS_DIR
        if os.path.exists(captions_dir):
            for filename in os.listdir(captions_dir):
                if filename.endswith('.txt'):
                    is_clean = '_clean' in filename
                    video_id = filename.replace('.txt', '').replace('_clean', '')
                    
                    existing = next((t for t in transcripts if t['video_id'] == video_id), None)
                    if existing:
                        if is_clean:
                            existing['has_clean_local'] = True
                        else:
                            existing['has_raw_local'] = True
                    else:
                        try:
                            title = get_video_title(video_id)
                        except:
                            title = f"Unknown Title ({video_id})"
                        
                        transcripts.append({
                            'video_id': video_id,
                            'title': title,
                            'has_raw': not is_clean,
                            'has_clean': is_clean,
                            'source': 'local_file'
                        })
        
        return jsonify({
            "success": True,
            "transcripts": transcripts
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"❌ Error: {str(e)}"}), 500