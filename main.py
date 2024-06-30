import os
import time
from urllib.parse import urlparse

from selenium.common import StaleElementReferenceException
from selenium.webdriver.common.by import By
import requests
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Function to smoothly scroll the page and collect image URLs
def smooth_scroll_and_collect_images(driver):
    SCROLL_PAUSE_TIME = 1
    image_urls = []
    video_article_urls = []
    seen_urls = set()
    last_scroll_height = driver.execute_script("return document.body.scrollHeight")
    count = 1
    previous_scroll = 0
    while True:
        # Scroll down a bit
        driver.execute_script("window.scrollBy(0, window.innerHeight);")
        time.sleep(SCROLL_PAUSE_TIME)

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

                # Collect video URLs (including GIFs)
                video_elements = driver.find_elements(By.TAG_NAME, 'video')
                for video in video_elements:
                    src = video.get_attribute('src')
                    if src and src.startswith('https://video.twimg.com') and src not in seen_urls:
                        image_urls.append(src)
                        seen_urls.add(src)
                    elif not src:
                        # Locate the article containing the video
                        article = video.find_element(By.XPATH, './/ancestor::article')
                        if article:
                            a_tags = article.find_elements(By.TAG_NAME, 'a')
                            for a in a_tags:
                                href = a.get_attribute('href')
                                try:
                                    if a and href and href.split('/')[4] == 'status' and href.split('/')[
                                        -1] != 'analytics' and href not in seen_urls:
                                        video_article_urls.append(href)
                                        seen_urls.add(href)
                                except IndexError:
                                    print("error with index")
                break  # Exit retry loop if successful
            except StaleElementReferenceException:
                retries -= 1
                time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with the last scroll height
        new_scroll_height = driver.execute_script("return document.body.scrollHeight")
        current_scroll_position = driver.execute_script("return window.scrollY + window.innerHeight")
        print(f"Scroll performed {count}, total media found: {len(image_urls) + len(video_article_urls)}")
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

    return image_urls, video_article_urls


# Function to extract the filename from a URL or data URL
def extract_filename(url):
    parsed_url = urlparse(url)
    if parsed_url.scheme == 'data':
        return f"blob_{int(time.time())}.mp4"
    return os.path.basename(parsed_url.path)


def download():
    # Create the directory for downloading images
    images_directory = os.path.join('D:/downloaded_media', tweet_id)

    if not os.path.exists(images_directory):
        os.makedirs(images_directory)

    # Download each image
    for index, img_url in enumerate(all_image_urls):
        try:
            response = requests.get(img_url, stream=True)
            if response.status_code == 200:
                response.raw.decode_content = True
                filename = extract_filename(img_url)
                image_path = None
                if filename.endswith("mp4"):
                    image_path = os.path.join(images_directory, f'{filename}')
                else:
                    image_path = os.path.join(images_directory, f'{filename}.jpg')
                with open(image_path, 'wb') as handler:
                    for chunk in response:
                        handler.write(chunk)
                print(f"{filename} downloaded, {index + 1} of {len(all_image_urls)} ")
            else:
                print(f"Failed to download image {img_url}: HTTP {response.status_code}")
        except Exception as e:
            print(f"Could not download image {img_url}: {e}")

    # Save video article URLs to text files
    for url in video_article_urls:
        txt_filename = f"video_url_{tweet_id}.txt"
        txt_path = os.path.join(images_directory, txt_filename)
        with open(txt_path, 'a') as file:
            file.write(url + '\n')
        print(f"URL {url} saved to {txt_filename}")


if __name__ == "__main__":

    URLs = [SET_OF_URLs]

    URLsSet = set(URLs)
    print(len(URLs), len(URLsSet))
    if len(URLs) != len(URLsSet):
        URLs = list(URLsSet)

    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')  # Run in headless mode
    # options.add_argument('--disable-gpu')  # Disable GPU acceleration
    # options.add_argument('--no-sandbox')  # Bypass OS security model (required for some systems)
    # options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems

    driver = webdriver.Chrome(options=options)

    # Open a preliminary page
    driver.get("https://x.com")

    # Add the cookie for authentication
    cookie = {'name': 'auth_token', 'value': AUTH_TOKEN, 'domain': 'x.com'}
    driver.add_cookie(cookie)

    for URL in URLs:
        # Navigate to the desired URL
        driver.get(URL)
        tweet_id = URL.split('/')[3]
        # Wait for the initial set of images to load (if necessary)
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, 'img')))

        # Smoothly scroll the page and collect all image URLs
        all_image_urls, video_article_urls = smooth_scroll_and_collect_images(driver)

        print("the browser has stopped")
        # Wait for additional images to load
        time.sleep(3)

        download()
    # Close the browser
    driver.quit()
    print("the browser exit")
