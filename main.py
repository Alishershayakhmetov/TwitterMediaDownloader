import os
import time
from urllib.parse import urlparse

from selenium.webdriver.common.by import By
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

options = webdriver.ChromeOptions()
# options.add_argument('--headless')  # Run in headless mode
# options.add_argument('--disable-gpu')  # Disable GPU acceleration
# options.add_argument('--no-sandbox')  # Bypass OS security model (required for some systems)
# options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems

driver = webdriver.Chrome(options=options)

# Open a preliminary page
driver.get("https://x.com")

# Add the cookie for authentication
cookie = {'name': 'auth_token', 'value': AUTH_TOKEN , 'domain': 'x.com'}
driver.add_cookie(cookie)

URL = URL
# Navigate to the desired URL
driver.get(URL)
tweet_id = URL.split('/')[3]
# Wait for the initial set of images to load (if necessary)
wait = WebDriverWait(driver, 10)
wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, 'img')))

# Function to smoothly scroll the page and collect image URLs
def smooth_scroll_and_collect_images(driver):
    SCROLL_PAUSE_TIME = 1
    image_urls = []
    seen_urls = set()
    last_scroll_height = driver.execute_script("return document.body.scrollHeight")
    count = 1
    previous_scroll = 0
    while True:
        # Scroll down a bit
        driver.execute_script("window.scrollBy(0, window.innerHeight);")
        time.sleep(SCROLL_PAUSE_TIME)

        # Collect image URLs
        image_elements = driver.find_elements(By.TAG_NAME, 'img')
        for img in image_elements:
            src = img.get_attribute('src')
            if src and src.startswith('https://pbs.twimg.com/media') and src not in seen_urls:
                image_urls.append(src)
                seen_urls.add(src)

        # Calculate new scroll height and compare with the last scroll height
        new_scroll_height = driver.execute_script("return document.body.scrollHeight")
        current_scroll_position = driver.execute_script("return window.scrollY + window.innerHeight")
        print(f"Scroll performed {count}, total images found: {len(image_urls)}")
        print(f"previous scroll {previous_scroll}, current {current_scroll_position}")
        count += 1

        # Check if we have reached the end of the page
        if current_scroll_position >= new_scroll_height:
            break
        if previous_scroll == current_scroll_position:
            break
        previous_scroll = current_scroll_position
        last_scroll_height = new_scroll_height

    return image_urls

# Smoothly scroll the page and collect all image URLs
all_image_urls = smooth_scroll_and_collect_images(driver)

print("the browser has stopped")
# Wait for additional images to load
time.sleep(3)

# Close the browser
driver.quit()
print("the browser exit")

# Create the directory for downloading images
project_directory = os.path.dirname(os.path.abspath(__file__))
images_directory = os.path.join(project_directory, fr'downloaded_images\{tweet_id}')

if not os.path.exists(images_directory):
    os.makedirs(images_directory)

# Function to extract the filename from a URL or data URL
def extract_filename(url):
    parsed_url = urlparse(url)
    if parsed_url.scheme == 'data':
        return f"blob_{int(time.time())}.mp4"
    return os.path.basename(parsed_url.path)

# Download each image
for index, img_url in enumerate(all_image_urls):
    try:
        response = requests.get(img_url, stream=True)
        if response.status_code == 200:
            response.raw.decode_content = True
            filename = extract_filename(img_url)
            image_path = os.path.join(images_directory, f'{filename}.jpg')
            with open(image_path, 'wb') as handler:
                for chunk in response:
                    handler.write(chunk)
            print(f"{filename} downloaded ")
        else:
            print(f"Failed to download image {img_url}: HTTP {response.status_code}")
    except Exception as e:
        print(f"Could not download image {img_url}: {e}")