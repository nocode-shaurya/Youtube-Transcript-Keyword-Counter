#=====================================================================================
# Libraries and Modules
#=====================================================================================
from yt_transcript_fetcher import get_transcript
from googleapiclient.discovery import build
import re
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import os
import time
from datetime import datetime
from YT_transcript_functions import iso_duration_to_hms
#=====================================================================================
# Major Variables
#=====================================================================================
start_time = time.time()
api_key = "AIzaSyDXkYmuF6zLsFRbXKH4uiJwFBY_MOIXIt4" #Enter your YouTube Data API key here
channel_id = 'UCdgyTVq1GmOF0sVxqNGNJEg'
language = "hi"  # Language code for transcripts
target_video_count = 900
trans_search_words = [" विचार शून्य ", " शांत ", " रिलैक्सेशन ", " दिस मोमेंट "]  # List of words to search

#=====================================================================================
# Fetch all video IDs from the channel
#=====================================================================================
final_video_ids = []
videos_searched = 0
next_page_token = None

youtube = build('youtube', 'v3', developerKey=api_key)
channel_response = youtube.channels().list(
    part='contentDetails',
    id=channel_id
).execute()
uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

while True:
    playlist_response = youtube.playlistItems().list(
        part='contentDetails',
        playlistId=uploads_playlist_id,
        maxResults=50,
        pageToken=next_page_token
    ).execute()

    for item in playlist_response['items']:
        final_video_ids.append(item['contentDetails']['videoId'])
        videos_searched += 1
        print(f' Video: {videos_searched}')
        if len(final_video_ids) >= target_video_count:
            break

    next_page_token = playlist_response.get('nextPageToken')
    if not next_page_token or len(final_video_ids) >= target_video_count:
        break

#=====================================================================================
# Fetch video details and transcripts in batches
#=====================================================================================
batch_size = 50
final_video_data = []
transcript_video_num = 0
failed_transcript_videos = []

# Pre-compile regular expressions for each search word (case-insensitive)
patterns = {w: re.compile(re.escape(w), re.IGNORECASE) for w in trans_search_words}

for i in range(0, len(final_video_ids), batch_size):
    batch_ids = final_video_ids[i:i+batch_size]
    videos_data_response = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        id=','.join(batch_ids)
    ).execute()

    for video in videos_data_response['items']:
        video_id = video['id']
        title = video['snippet']['title']
        #--------------------------------------
        published_at_temp = video['snippet']['publishedAt']
        dt = datetime.strptime(published_at_temp, "%Y-%m-%dT%H:%M:%SZ")
        published_at = dt.strftime("%d-%m-%Y %H:%M:%S")
        #--------------------------------------
        duration_temp = video['contentDetails']['duration']
        duration = iso_duration_to_hms(duration_temp)
        #--------------------------------------
        view_count = video['statistics'].get('viewCount')
        like_count = video['statistics'].get('likeCount')
        comment_count = video['statistics'].get('commentCount')
        video_url = f'https://www.youtube.com/watch?v={video_id}'

        # Get transcript
        try:
            transcript_segments = get_transcript(video_id, language)
            transcript_text = ""
            if hasattr(transcript_segments, 'segments'):
                transcript_text = " ".join(segment.text for segment in transcript_segments.segments)
                transcript_video_num += 1
                print(f'Transcript Video: {transcript_video_num}')
            else:
                transcript_text = ""
                print(f'No transcript available for video ID: {video_id}')
                transcript_video_num += 1
        except Exception as e:
            transcript_text = ""
            print(f'Error fetching transcript for video ID {video_id}: {e}')
            transcript_video_num += 1

        # Count occurrences for each search word
        word_counts = {word: len(pattern.findall(transcript_text)) for word, pattern in patterns.items()}

        # Append all video data as dictionary to the list
        if transcript_text == "":
            failed_transcript_videos.append({
                'video_id': video_id,
                'title': title,
                'published_at': published_at,
                'duration (hh:mm:ss)': duration,
                'view_count': view_count,
                'like_count': like_count,
                'comment_count': comment_count,
                'video_url': video_url
            })
        
        else:
            final_video_data.append({
                'video_id': video_id,
                'title': title,
                'published_at': published_at,
                'duration (hh:mm:ss)': duration,
                'view_count': view_count,
                'like_count': like_count,
                'comment_count': comment_count,
                'video_url': video_url,
                **{f'count_{word}': cnt for word, cnt in word_counts.items()}
            })

print(f'Total videos processed: {len(final_video_data)}')

#=====================================================================================
# Save the final video data to a CSV file
#=====================================================================================
df = pd.DataFrame(final_video_data)
df2 = pd.DataFrame(failed_transcript_videos)
# Hide the root Tkinter window
root = tk.Tk()
root.withdraw()

# Prompt user to select save location and name
file_path = filedialog.asksaveasfilename(
    title="Save file as...",
    defaultextension='.xlsx',
    filetypes= [('Excel Files', '*.xlsx'),
                ('All Files', '*.*')]
)

if file_path:
    # Ensure directory exists (usually handled by dialog, but safe to check)
    folder = os.path.dirname(file_path)
    os.makedirs(folder, exist_ok=True)

    # Save DataFrame to the chosen path
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Final Videos', index=False)
            df2.to_excel(writer, sheet_name='Failed Transcripts', index=False)
    print(f"Data saved to {file_path}")
else:
    print("Save cancelled.")


#=====================================================================================
# Calculate and print the total runtime of the program
#=====================================================================================
end_time = time.time()
elapsed_time = end_time - start_time
# Convert elapsed_time (in seconds) to HH:MM:SS format
formatted_time = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
print(f"Total runtime of the program is {formatted_time}")