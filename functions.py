import os
import time
from dotenv import load_dotenv
load_dotenv()
from urllib.parse import urlparse, parse_qs

from selenium.common import StaleElementReferenceException
from selenium.webdriver.common.by import By
import requests

import subprocess
import urllib.parse

from moviepy.editor import VideoFileClip

def smooth_scroll_and_collect_images_from_author(driver, author_profile_path):
    """
    Scrolls a page, collects media URLs from posts authored by a specific user.
    
    Args:
        driver: The Selenium WebDriver instance.
        author_profile_path: The username of the author
    
    Returns:
        A tuple containing lists of image, gif, and video URLs.
    """
    SCROLL_PAUSE_TIME = 1
    image_urls, video_urls, gif_urls = [], [], []
    seen_urls = set()
    last_scroll_height = driver.execute_script("return document.body.scrollHeight")
    count = 1
    previous_scroll = 0
    while True:
        # Scroll down a bit
        time.sleep(SCROLL_PAUSE_TIME)
        driver.execute_script("window.scrollBy(0, window.innerHeight);")

        retries = 3
        while retries > 0:
            try:
                # Collect media only from author's posts
                articles = driver.find_elements(By.TAG_NAME, 'article')
                for article in articles:
                    # Check if the article belongs to the author
                    author_links = article.find_elements(By.XPATH, f".//a[@href='{author_profile_path}']")
                    if not author_links:
                        continue
                    for link in author_links:
                        href = link.get_attribute("href")
                        text = link.text
                        if text != "":
                            continue

                        # Collect image URLs
                        image_elements = article.find_elements(By.TAG_NAME, 'img')
                        for img in image_elements:
                            src = img.get_attribute('src')
                            if src and src.startswith('https://pbs.twimg.com/media') and src not in seen_urls:
                                image_urls.append(src)
                                seen_urls.add(src)

                        # Collect GIFs URLs
                        video_elements = article.find_elements(By.TAG_NAME, 'video')
                        for video in video_elements:
                            src = video.get_attribute('src')
                            if src and src.startswith('https://video.twimg.com') and src not in seen_urls:
                                gif_urls.append(src)
                                seen_urls.add(src)

                        # Collect m3u8 files video
                        for request in driver.requests:
                            if request.response and request.path.endswith('.m3u8') and request.path not in seen_urls and len(str(request).split('?')) != 1:
                                seen_urls.add(request.path)
                                video_urls.append(request)
                break  # Exit retry loop if successful
            except StaleElementReferenceException:
                retries -= 1
                time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with the last scroll height
        new_scroll_height = driver.execute_script("return document.body.scrollHeight")
        current_scroll_position = driver.execute_script("return window.scrollY + window.innerHeight")
        print(f"Scroll performed {count}, images: {len(image_urls)}, videos: {len(video_urls)}, gifs: {len(gif_urls)}")
        print(f"previous scroll {previous_scroll}, current {current_scroll_position}")
        count += 1

        # Check if we have reached the end of the page
        if current_scroll_position >= new_scroll_height:
            break
        if previous_scroll == current_scroll_position:
            print("probable end of webpage")
            time.sleep(SCROLL_PAUSE_TIME * 20)
            scroll_position = driver.execute_script("return document.body.scrollHeight")
            if scroll_position >= current_scroll_position:
                break
            else:
                pass
        previous_scroll = current_scroll_position
        last_scroll_height = new_scroll_height

    return image_urls, gif_urls, video_urls

def smooth_scroll_and_collect_images(driver):
    SCROLL_PAUSE_TIME = 1
    image_urls, video_urls, gif_urls = [], [], []
    seen_urls = set()
    last_scroll_height = driver.execute_script("return document.body.scrollHeight")
    count = 1
    previous_scroll = 0
    while True:
        # Scroll down a bit
        time.sleep(SCROLL_PAUSE_TIME)
        driver.execute_script("window.scrollBy(0, window.innerHeight);")

        retries = 3
        while retries > 0:
            try:
                # Collect image URLs
                image_elements = driver.find_elements(By.TAG_NAME, 'img')
                for img in image_elements:
                    src = img.get_attribute('src')
                    if src and src.startswith('https://pbs.twimg.com/media') and src not in seen_urls:
                        image_urls.append(src)
                        seen_urls.add(src)

                # Collect GIFs URLs
                video_elements = driver.find_elements(By.TAG_NAME, 'video')
                for video in video_elements:
                    src = video.get_attribute('src')
                    if src and src.startswith('https://video.twimg.com') and src not in seen_urls:
                        gif_urls.append(src)
                        seen_urls.add(src)

                # Collect m3u8 files video
                for request in driver.requests:
                    if request.response and request.path.endswith('.m3u8') and request.path not in seen_urls and len(str(request).split('?')) != 1:
                        seen_urls.add(request.path)
                        video_urls.append(request)
                break  # Exit retry loop if successful
            except StaleElementReferenceException:
                retries -= 1
                time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with the last scroll height
        new_scroll_height = driver.execute_script("return document.body.scrollHeight")
        current_scroll_position = driver.execute_script("return window.scrollY + window.innerHeight")
        print(f"Scroll performed {count}, images: {len(image_urls)}, videos: {len(video_urls)}, gifs: {len(gif_urls)}")
        print(f"previous scroll {previous_scroll}, current {current_scroll_position}")
        count += 1

        # Check if we have reached the end of the page
        if current_scroll_position >= new_scroll_height:
            break
        if previous_scroll == current_scroll_position:
            print("probable end of webpage")
            time.sleep(SCROLL_PAUSE_TIME * 20)
            scroll_position = driver.execute_script("return document.body.scrollHeight")
            if scroll_position >= current_scroll_position:
                break
            else:
                pass
        previous_scroll = current_scroll_position
        last_scroll_height = new_scroll_height

    return image_urls, gif_urls, video_urls

# Function to extract the filename from a URL or data URL
def extract_filename(url):
    parsed_url = urlparse(url)
    if parsed_url.scheme == 'data':
        return f"blob_{int(time.time())}.mp4"
    return os.path.basename(parsed_url.path)

def isPathExistCheck(id):
    # Checks if directory exists
    images_directory = os.path.join(os.getenv("DIRPATH"), id)

    if not os.path.exists(images_directory):
        return False
    else:
        return True

def download(id, image_urls, gif_urls, video_urls):
    # Create the directory for downloading images
    download_directory = os.path.join(os.getenv("DIRPATH"), id)

    if not os.path.exists(download_directory):
        os.makedirs(download_directory)
    else:
        raise FileExistsError(f"The directory '{download_directory}' already exists.")

    # Download each image
    for index, media_url in enumerate(image_urls):
        count = 0
        while count < int(os.getenv("numberOfRepetitions")):
            try:
                response = requests.get(media_url, stream=True)
                if response.status_code == 200:
                    response.raw.decode_content = True
                    filename = extract_filename(media_url)
                    """
                    image_path = None
                    if filename.endswith("mp4"):
                        # gif with .mp4 extension
                        image_path = os.path.join(download_directory, f'{filename}')
                    else:"""
                    image_path = os.path.join(download_directory, f'{filename}.jpg')
                    with open(image_path, 'wb') as handler:
                        for chunk in response:
                            handler.write(chunk)
                    print(f"{filename} downloaded, {index + 1} of {len(image_urls)} ")
                    break
                else:
                    print(f"Failed to download image {media_url}: HTTP {response.status_code}")
                    count += 1
            except Exception as e:
                print(f"Could not download image {media_url}: {e}")
                count += 1

    # Download each gif
    for index, media_url in enumerate(gif_urls):
        count = 0
        while count < int(os.getenv("numberOfRepetitions")):
            try:
                response = requests.get(media_url, stream=True)
                if response.status_code == 200:
                    response.raw.decode_content = True
                    filename = extract_filename(media_url)
                    # Save the mp4 file
                    video_path = os.path.join(download_directory, f'{filename}')
                    with open(video_path, 'wb') as handler:
                        for chunk in response:
                            handler.write(chunk)
                    # Convert to GIF and save
                    gif_path = os.path.join(download_directory, f"{filename.rsplit('.', 1)[0]}.gif")
                    with VideoFileClip(video_path) as clip:
                        clip.write_gif(gif_path, fps=10)
                    
                    # After conversion, delete the original mp4 file
                    os.remove(video_path)
                    print(f"{filename} downloaded and converted to GIF, {index + 1} of {len(gif_urls)} ")
                    break
                else:
                    print(f"Failed to download gif {media_url}: HTTP {response.status_code}")
                    count += 1
            except Exception as e:
                print(f"Could not download gif {media_url}: {e}")
                count += 1

    # download each video
    for index, request in enumerate(video_urls):
        print(video_urls, index, request)
        count = 0
        while count < int(os.getenv("numberOfRepetitions")):
            try:
                base_filename = os.path.basename(urllib.parse.urlparse(request.path).path).replace('.m3u8', '.mp4')
                # define the path to your ffmpeg file
                ffmpeg = os.getenv("FFMPEG_PATH") + "\\ffmpeg"
                # Run FFmpeg command, check if command defined correctly
                ffmpeg_command = f'{ffmpeg} -i "{str(request).strip()}" -c copy -bsf:a aac_adtstoasc {download_directory + "\\" + base_filename}'
                subprocess.run(ffmpeg_command, shell=True)
                break
            except Exception as e:
                print(f"Could not download video {request}: {e}")
                count += 1
