#=====================================================================================
# Libraries and Modules
#=====================================================================================
from googleapiclient.discovery import build
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import os
import time
from YT_transcript_functions import fetch_video_details
import concurrent.futures
#=====================================================================================
# Major Variables
#=====================================================================================
start_time = time.time()
api_key = "AIzaSyDXkYmuF6zLsFRbXKH4uiJwFBY_MOIXIt4" #Enter your YouTube Data API key here
channel_id = 'UC-lHJZR3Gqxm24_Vd_AJ5Yw'
language = "en"  # Language code for transcripts
target_video_count = 5000
trans_search_words = ["believe", "man", "jesus", "stop"]  # List of words to search

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
        print(f' Video: {videos_searched}', end="\r")  # Overwrites the previous line
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
videos_processed = 0
error_videos_count = 0
total_videos = len(final_video_ids)
failed_transcript_videos = []


for i in range(0, len(final_video_ids), batch_size):
    batch_ids = final_video_ids[i:i+batch_size]
    videos_data_response = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        id=','.join(batch_ids)
    ).execute()

    videos = videos_data_response['items']

    # Use ThreadPoolExecutor to fetch transcripts concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = [executor.submit(fetch_video_details, video, language, trans_search_words) for video in videos]

    for future in results:
        try:
            result = future.result(timeout=60)  # put a timeout to avoid long hangs
            if result['failed']:
                failed_transcript_videos.append(result['data'])
            else:
                final_video_data.append(result['data'])
        except Exception as e:
            error_videos_count += 1
        finally:
            videos_processed += 1
            percent_done = (videos_processed / total_videos) * 100
            print(f"Progress: {percent_done:.2f}%", end="\r")  # Overwrites 
print(f'Total videos processed: {len(final_video_data)}')
print(f'Videos with errors: {error_videos_count}')
#=====================================================================================
# Calculate and print the total runtime of the program
#=====================================================================================
end_time = time.time()
elapsed_time = end_time - start_time
# Convert elapsed_time (in seconds) to HH:MM:SS format
formatted_time = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
print(f"Total runtime of the program is {formatted_time}")

#=====================================================================================
# Save the final video data to a CSV file
#=====================================================================================
print("Creating DataFrames...")
df = pd.DataFrame(final_video_data)
df2 = pd.DataFrame(failed_transcript_videos)
print("DataFrames created.")

# Hide the root Tkinter window
root = tk.Tk()
root.withdraw()
print("Opening save dialog...")
root.attributes('-topmost', True)
root.update()

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


