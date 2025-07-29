#=====================================================================================
# Libraries and Modules
#=====================================================================================
from yt_transcript_fetcher import get_transcript
from googleapiclient.discovery import build
import re
import pandas as pd
#=====================================================================================
# Major Variables
#=====================================================================================
api_key = "AIzaSyDXkYmuF6zLsFRbXKH4uiJwFBY_MOIXIt4"  # youtube API key
channel_url = "https://youtube.com/channel/UCw0ry7cLRUnq3Oaszlhgqfg"
channel_id = 'UCw0ry7cLRUnq3Oaszlhgqfg'  # Insert the channel ID you want to fetch videos from  # Replace with your target channel URL
# keyword = "Today Breaking News"
language = "hi"  # Language code for Hindi, 'en' for English, etc.
target_video_count = 800  # Number of videos to fetch transcripts for
trans_search_word = "मोदी"  # Word to search for in the transcript
#=====================================================================================
# Fetch all video IDs from the channel after filtering by keyword
#=====================================================================================
# Blank lists to store video data and IDs
final_video_ids = []
videos_searched = 0
next_page_token = None
# Initialize YouTube API client
youtube = build('youtube', 'v3', developerKey=api_key)

# Channel info
channel_response = youtube.channels().list(
    part='contentDetails',
    id=channel_id
).execute()
uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']


while True:
    # Prepare request with page token if available
    playlist_response = youtube.playlistItems().list(
        part='contentDetails',
        playlistId=uploads_playlist_id,
        maxResults=50,
        pageToken=next_page_token
    ).execute()

    # Loop through current page of results
    for item in playlist_response['items']:
        final_video_ids.append(item['contentDetails']['videoId'])
        videos_searched += 1
        print(f' Video: {videos_searched}')
        next_page_token = playlist_response.get('nextPageToken')
    if not next_page_token:
        break
        
    if len(final_video_ids) >= target_video_count:
        print(f"Reached target video count: {target_video_count}")
        break





#=====================================================================================
# Fetch video details and transcripts for the collected video IDs
#=====================================================================================
batch_size = 50  # YouTube API allows a maximum of 50 IDs per request
final_video_data = []

for i in range(0, len(final_video_ids), batch_size):
    batch_ids = final_video_ids[i:i+batch_size]

    videos_data_response = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        id=','.join(batch_ids)
    ).execute()

    for video in videos_data_response['items']:  
        video_id = video['id']
        title = video['snippet']['title']
        published_at = video['snippet']['publishedAt']
        duration = video['contentDetails']['duration']  # ISO 8601 format
        view_count = video['statistics'].get('viewCount')
        like_count = video['statistics'].get('likeCount')
        comment_count = video['statistics'].get('commentCount')
        video_url = f'https://www.youtube.com/watch?v={video_id}'

        #get transcript for the video
        try:
            transcript_segments = get_transcript(video_id, language)
            transcript = []
            if hasattr(transcript_segments, 'segments'):
                for segment in transcript_segments.segments:
                    transcript.append(segment.text)

                # Count occurrences of the search word in the transcript
                pattern = re.escape(trans_search_word.lower())
                trans_search_word_count = 0
                for i in transcript:
                    trans_search_word_count += len(re.findall(pattern, i.lower()))
            else:
                transcript = None
        except:
            transcript = 'Transcript not available'

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
            'trans_search_word_count': trans_search_word_count,
            'video_url': video_url
        })

print(f'Total videos found: {len(final_video_data)}')
print()

#=====================================================================================
# Save the final video data to a CSV file
#=====================================================================================
#Convert list of dictionaries to pandas DataFrame
df = pd.DataFrame(final_video_data)

# Save DataFrame to CSV file
csv_filename = 'youtube_videos_data.csv'
df.to_csv(csv_filename, index=False, encoding='utf-8-sig')  # encoding for Unicode support

print(f"Data saved to {csv_filename}")

