import re
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from azure_tennis_api.config import Config

def extract_video_id(input_text):
    """Extract video or playlist ID from YouTube URL or direct ID input"""
    youtube_regex = {
        'standard': r'(?:youtube\.com\/watch\?v=)([\w-]+)',
        'short': r'(?:youtu\.be\/)([\w-]+)',
        'embed': r'(?:youtube\.com\/embed\/)([\w-]+)',
        'playlist': r'(?:youtube\.com\/playlist\?list=)([\w-]+)'
    }
    
    playlist_match = re.search(youtube_regex['playlist'], input_text)
    if playlist_match:
        return {'type': 'playlist', 'id': playlist_match.group(1)}
        
    for regex_type, pattern in youtube_regex.items():
        if regex_type != 'playlist':
            match = re.search(pattern, input_text)
            if match:
                return {'type': 'video', 'id': match.group(1)}
    
    if input_text.startswith('PL') and len(input_text) > 10:
        return {'type': 'playlist', 'id': input_text}
    else:
        return {'type': 'video', 'id': input_text}

def get_video_ids_from_playlist(playlist_id, max_videos=None):
    """Get video IDs from a YouTube playlist with a limit"""
    if max_videos is None:
        max_videos = Config.MAX_PLAYLIST_VIDEOS
        
    video_ids = []
    base_url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "part": "contentDetails",
        "playlistId": playlist_id,
        "maxResults": 50,
        "key": Config.YOUTUBE_API_KEY
    }
    
    try:
        response = requests.get(base_url, params=params)
        if response.status_code != 200:
            raise Exception(f"API error {response.status_code}: {response.text}")
        
        data = response.json()
        
        for item in data.get('items', [])[:max_videos]:
            video_ids.append(item['contentDetails']['videoId'])
            
        return video_ids
    except Exception as e:
        print(f"Error getting playlist videos: {str(e)}")
        return []

def get_video_title(video_id):
    """Gets the title of a YouTube video using its ID"""
    base_url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet",
        "id": video_id,
        "key": Config.YOUTUBE_API_KEY
    }
    
    try:
        response = requests.get(base_url, params=params)
        if response.status_code != 200:
            return f"Unknown Title ({video_id})"
        
        data = response.json()
        if data.get('items'):
            return data['items'][0]['snippet']['title']
        else:
            return f"Unknown Title ({video_id})"
    except Exception as e:
        print(f"Error getting video title: {str(e)}")
        return f"Unknown Title ({video_id})"

def get_transcript(video_id):
    """Get transcript for a YouTube video"""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
        raw_transcript = ""
        for entry in transcript_list:
            raw_transcript += entry['text'] + "\n"
            
        return {"success": True, "transcript": raw_transcript}
    
    except Exception as e:
        return {"success": False, "transcript": "", "error": str(e)}