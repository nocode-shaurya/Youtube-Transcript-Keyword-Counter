#=====================================================================================
# Libraries and Modules
#=====================================================================================
from yt_transcript_fetcher import list_languages, get_transcript
from googleapiclient.discovery import build
import re
from selenium import webdriver
import time
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
# Get Video IDs
#=====================================================================================

driver = webdriver.Chrome()
driver.get(channel_url)
time.sleep(10)  # Wait for page to load (increase if needed)
scroll_pause = 2
for _ in range(target_video_count//10):  # Adjust for how many videos you want
    driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
    time.sleep(scroll_pause)

video_links = driver.find_elements(By.XPATH, '//a[@id="video-title-link"]')

# initiate blank list for dictionary
video_data = []
video_count = 0
for link in video_links:
    title = link.get_attribute('title')
    href = link.get_attribute('href')
    # print('Video Title:', title)
    # print('Video Link:', href)
    if re.search(keyword, title, re.IGNORECASE) != None and video_count < target_video_count:
        print('Keyword found in title:', title)
        if href and 'v=' in href:
            video_id_full = href.split('v=')[1]
            video_id = video_id_full.split('&')[0]  # Take only before '&'

            #get the transcript for the video
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
            
            # Fetch video details using YouTube Data API
            youtube = build('youtube', 'v3', developerKey=api_key)
            response = youtube.videos().list(
                part="snippet, statistics, contentDetails",
                id=video_id
            ).execute()

            video = response['items'][0]

            title = video['snippet']['title']
            published_at = video['snippet']['publishedAt']
            duration = video['contentDetails']['duration']             # ISO 8601 format
            view_count = video['statistics'].get('viewCount')
            like_count = video['statistics'].get('likeCount')
            comment_count = video['statistics'].get('commentCount')
           
            # append all video data as dicotionary to the list
            video_data.append({
                'video_id': video_id,
                'title': title,
                'published_at': published_at,
                'duration': duration,
                'view_count': view_count,
                'like_count': like_count,
                'comment_count': comment_count,
                'keyword_search': f'{trans_search_word}',
                'keyword_count': trans_search_word_count,
            })
            video_count += 1
    else:
        continue



driver.quit()

#=====================================================================================
# Save to CSV
#=====================================================================================
df = pd.DataFrame(video_data)
df.to_csv('video_data_testing.csv', index=False, encoding='utf-8-sig')
print(df)