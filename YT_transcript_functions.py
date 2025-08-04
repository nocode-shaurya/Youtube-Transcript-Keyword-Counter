import concurrent.futures
from yt_transcript_fetcher import get_transcript
import re
import time
from datetime import datetime

def iso_duration_to_hms(duration_str):
    # Extract hours, minutes, seconds using regex
    pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
    match = pattern.match(duration_str)
    
    if not match:
        return "00:00:00"  # Return default if format is incorrect
    
    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    seconds = int(match.group(3)) if match.group(3) else 0
    # Format as HH:MM:SS
    return f"{hours:02}:{minutes:02}:{seconds:02}"




def fetch_video_details(video, language, trans_search_words):
    video_id = video['id']
    title = video['snippet']['title']
    published_at_temp = video['snippet']['publishedAt']
    dt = datetime.strptime(published_at_temp, "%Y-%m-%dT%H:%M:%SZ")
    published_at = dt.strftime("%d-%m-%Y %H:%M:%S")
    duration_temp = video['contentDetails']['duration']
    duration = iso_duration_to_hms(duration_temp)
    view_count = video['statistics'].get('viewCount')
    like_count = video['statistics'].get('likeCount')
    comment_count = video['statistics'].get('commentCount')
    video_url = f'https://www.youtube.com/watch?v={video_id}'

    try:
        transcript_segments = get_transcript(video_id, language)
        if hasattr(transcript_segments, 'segments'):
            transcript_text = " ".join(segment.text for segment in transcript_segments.segments)
        else:
            transcript_text = ""
    except Exception as e:
        error = str(e)
        transcript_text = ""

    # Use simple substring count for each search word (faster than regex findall)
    word_counts = {word: transcript_text.lower().count(word.strip().lower()) for word in trans_search_words}

    if not transcript_text:
        return {
            'failed': True,
            'data': {
                'video_id': video_id,
                'title': title,
                'published_at': published_at,
                'duration (hh:mm:ss)': duration,
                'view_count': int(view_count) if view_count is not None else 0,
                'like_count': int(like_count) if like_count is not None else 0,
                'comment_count': int(comment_count) if comment_count is not None else 0,
                'video_url': video_url,
                'error': error
            }
        }
    else:
        return {
            'failed': False,
            'data': {
                'video_id': video_id,
                'title': title,
                'published_at': published_at,
                'duration (hh:mm:ss)': duration,
                'view_count': int(view_count) if view_count is not None else 0,
                'like_count': int(like_count) if like_count is not None else 0,
                'comment_count': int(comment_count) if comment_count is not None else 0,
                'video_url': video_url,
                **{f'count_{word.strip()}': cnt for word, cnt in word_counts.items()}
            }
        }
    
# Example
# duration_str = "PT251H14M42S"
# print(iso_duration_to_hms(duration_str))
