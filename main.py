import os
import time
from dotenv import load_dotenv
load_dotenv()

from selenium.webdriver.common.by import By
# from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from seleniumbase import Driver

from functions import smooth_scroll_and_collect_images_from_author, extract_filename, isPathExistCheck, download, smooth_scroll_and_collect_images

if __name__ == "__main__":
    URLs = os.getenv("SET_OF_URLs").split(",")

    URLsSet = set(URLs)
    print(len(URLs), len(URLsSet))
    if len(URLs) != len(URLsSet):
        URLs = list(URLsSet)

    # options = webdriver.ChromeOptions()
    # options.add_argument('--headless')  # Run in headless mode
    # options.add_argument('--disable-gpu')  # Disable GPU acceleration
    # options.add_argument('--no-sandbox')  # Bypass OS security model (required for some systems)
    # options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems

    # driver = webdriver.Chrome(options=options)
    driver = Driver(wire=True)

    # Open a preliminary page
    if bool(os.getenv("isDynamic")):
        if bool(os.getenv("isAuthNeed")):
            driver.get(os.getenv("PAGEFORAUTH"))

            # Add the cookie for authentication
            cookie = {'name': os.getenv("AUTHCOOKIENAME"), 'value': os.getenv("AUTHTOKEN"), 'domain': os.getenv("AUTHDOMAIN")}
            driver.add_cookie(cookie)

        for URL in URLs:
            # Navigate to the desired URL
            tweet_id = URL.split('/')[3]
            if isPathExistCheck(tweet_id):
                print(F"Path {tweet_id} alreasy exist, skip the URL")
                continue

            driver.get(URL)

            time.sleep(10)
            # Wait for the initial set of images to load (if necessary)
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, 'img')))
            # wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, 'video')))

            # Smoothly scroll the page and collect all image URLs
            if bool(os.getenv("AUTHOR_MEDIA_ONLY")):
                image_urls, gif_urls, video_urls = smooth_scroll_and_collect_images_from_author(driver, f"/{tweet_id}")
            else:
                image_urls, gif_urls, video_urls = smooth_scroll_and_collect_images(driver)
            
            print("the browser has stopped")
            # Wait for additional images to load
            time.sleep(3)

            download(tweet_id, image_urls, gif_urls, video_urls)
        # Close the browser
        print("the browser exit")  
        driver.quit()
    else:
        # block for static page
        pass