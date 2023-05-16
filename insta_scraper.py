from json.tool import main
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import instaloader
from pprint import pprint
from selenium_stealth import stealth
import json
import time

# """Creates a new Chrome webdriver instance using Service."""


def setup_webdriver(webdriver_path):
    service = Service(webdriver_path)
    options = webdriver.ChromeOptions()
    options.add_argument(
        f'--user-data-dir=/Users/ronnydiaz/Library/Application Support/Google/Chrome/Default')
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    return webdriver.Chrome(service=service, options=options)

# """Gets the likes count for a specific Instagram post using instaloader."""


def get_likes_count(post_url):
    loader = instaloader.Instaloader()
    shortcode = post_url.split("/p/")[1].rstrip("/")
    post = instaloader.Post.from_shortcode(loader.context, shortcode)
    return post.likes


# """Gets the post data for the given hashtag."""
def get_post_data(driver, hashtag):
    session_id = 'INSERT_COOKIE_SESSION_ID'
    driver.get(f"https://www.instagram.com/explore/tags/{hashtag}/")
    driver.add_cookie({'name': 'sessionid', 'value': session_id,
                       'domain': '.instagram.com'})

    # Refresh the page to apply the session ID cookie
    driver.refresh()

    # Wait for the page to load and post elements to be present
    wait = WebDriverWait(driver, 10)
    post_elements = wait.until(EC.presence_of_all_elements_located(
        (By.CSS_SELECTOR, 'a[href*="/p/"]')))

    print(f"Attempting: {driver.current_url}")
    if "login" in driver.current_url:
        print("Failed/ redir to login")
        return []

    # Scroll to load more posts
    SCROLL_PAUSE_TIME = 2
    last_height = driver.execute_script("return document.body.scrollHeight")
    while len(post_elements) < 50:
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        post_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/p/"]')
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Extract the HTML content
    html_content = driver.page_source

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    main_section = soup.find('main')

    # Extract post URLs, usernames, and likes
    post_data = []
    count = 0
    post_elements = main_section.select('a[href*="/p/"]')
    for post_element in post_elements:
        post_url = f"https://www.instagram.com{post_element['href']}"
        driver.get(post_url)
        time.sleep(2)

        try:
            likes_count = get_likes_count(post_url)

            # Check if the likes count is a valid integer and greater than 1000
            if likes_count > 300:
                post_data.append({
                    'post_url': post_url,
                    'likes': likes_count
                })
                count += 1

        except (NoSuchElementException, TimeoutException):
            print(
                f"Likes element not found or invalid format for post: {post_url}")

        if count >= 20:
            break

    return post_data


def save_post_data(post_data, filename):
    """Saves the post data to a JSON file."""
    with open(filename, 'w') as file:
        json.dump(post_data, file, indent=4)
    print(f"Total posts: {len(post_data)}")


if __name__ == '__main__':
    # Set up the webdriver
    webdriver_path = '/usr/local/bin/chromedriver'
    driver = setup_webdriver(webdriver_path)

    # Get the post data for the hashtag 'fitness'
    hashtag = 'fitness'
    post_data = get_post_data(driver, hashtag)

    # Save the post data to a JSON file
    filename = 'post_data.json'
    save_post_data(post_data, filename)

    # Close the browser
    driver.quit()
