#=====================================================================================
# Libraries and Modules
#=====================================================================================
from yt_transcript_fetcher import list_languages, get_transcript
from googleapiclient.discovery import build
import re
from selenium.webdriver.common.by import By
import pandas as pd
#=====================================================================================
# Major Variables
#=====================================================================================
api_key = "AIzaSyDXkYmuF6zLsFRbXKH4uiJwFBY_MOIXIt4"  # youtube API key
channel_url = "https://www.youtube.com/c/DLSNews/videos"  # Replace with your target channel URL
keyword = "Today Breaking News"
language = "hi"  # Language code for Hindi, 'en' for English, etc.
target_video_count = 200  # Number of videos to fetch transcripts for
trans_search_word = "भारत"  # Word to search for in the transcript
#=====================================================================================
youtube = build('youtube', 'v3', developerKey=api_key)

channel_id = 'UCw0ry7cLRUnq3Oaszlhgqfg'  # Insert the channel ID you want to fetch videos from

request = youtube.search().list(
    part="id,snippet",
    channelId=channel_id,
    maxResults=50,     
    order="date",
    type="video"
)
trans_response = request.execute()

final_video_data = []
final_video_ids = []

# Loop through the search results and filter by keyword in title
for item in trans_response['items']:
    title = item['snippet']['title']
    video_id = item['id']['videoId']
    #Check title for keyword
    if re.search(keyword, title, re.IGNORECASE) != None:
        final_video_ids.append(video_id)
    else:
        continue

videos_data_response = youtube.videos().list(
    part="snippet,statistics,contentDetails",
    id=','.join(final_video_ids)
).execute()

for video in videos_data_response['items']:  
    video_id = video['id']
    title = video['snippet']['title']
    published_at = video['snippet']['publishedAt']
    duration = video['contentDetails']['duration']  # ISO 8601 format
    view_count = video['statistics'].get('viewCount')
    like_count = video['statistics'].get('likeCount')
    comment_count = video['statistics'].get('commentCount')

    #get transcript for the video
    transcript_segments = get_transcript(video_id, language)
    transcript = []
    if hasattr(transcript_segments, 'segments'):
        for segment in transcript_segments.segments:
            transcript.append(segment.text)
    # Count occurrences of the search word in the transcript
    pattern = re.escape(trans_search_word)
    trans_search_word_count = 0
    for i in transcript:
        trans_search_word_count += len(re.findall(pattern, i))

    # Append all video data as dictionary to the list
    final_video_data.append({
        'video_id': video_id,
        'title': title,
        'published_at': published_at,
        'duration': duration,
        'view_count': view_count,
        'like_count': like_count,
        'comment_count': comment_count,
        'search_word' : f'{trans_search_word}',
        'trans_search_word_count': trans_search_word_count
    })

print(f'Total videos found: {len(final_video_data)}')
print()
for video in final_video_data:
    print(video)
    print()

