import os
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin, urlparse
from selenium.webdriver.common.by import By

# Function to clean up folder and filenames
def clean_filename(url):
    return urlparse(url).path.replace('/', '_').strip('_')

# Function to filter out unwanted links (e.g., menu, home)
def is_valid_link(link_url, root_url):
    # Ignore "home" (root URL) and menu links
    if link_url == root_url or link_url == '/' or 'menu' in link_url:
        return False
    return True

# Function to get all valid links within the "Driving and Roads" section
def get_all_links_in_section(driver, base_url):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    links = []
    
    # Locate the "Driving and Roads" section by its class or ID (adjust if needed)
    section = soup.find('div', class_='body-field')  # Adjust this class or tag to match the section
    
    if section:
        for link in section.find_all('a', href=True):
            full_url = urljoin(base_url, link['href'])
            if is_valid_link(full_url, base_url):
                links.append(full_url)
    else:
        print("Section 'Driving and Roads' not found.")
    return links

# Recursive function to scrape a URL and follow links up to a max depth
def scrape_page(driver, url, current_depth, max_depth, parent_directory, root_url):
    if current_depth > max_depth:
        return

    # Create a directory for the current URL if it doesn't exist
    directory_name = clean_filename(url)
    directory_path = os.path.join(parent_directory, directory_name)
    os.makedirs(directory_path, exist_ok=True)
    print(f'directory name::{directory_path}')

    try:
        # Use Selenium to open the page
        driver.get(url)
        time.sleep(2)  # Let the page load and any JavaScript execute

        # Save the main content (paragraphs) to a .txt file
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        text_filename = os.path.join(directory_path, f'{directory_name}.txt')
        with open(text_filename, 'w', encoding='utf-8') as file:
            main_content = soup.find_all('p')
            for paragraph in main_content:
                file.write(paragraph.get_text() + '\n')

        print(f'Scraped: {url} (depth {current_depth})')

        # Root level: Get all links, store them, and process them later
        if current_depth == 0:  # Root layer
            # Collect all root-level links first
            root_links = get_all_links_in_section(driver, url)

            # After collecting all root-level links, scrape them one by one
            for link_url in root_links:
                scrape_page(driver, link_url, current_depth + 1, max_depth, directory_path, root_url)

        else:  # For deeper layers, continue the recursive scraping
            nested_links = get_all_links_in_section(driver, url)
            for nested_link in nested_links:
                scrape_page(driver, nested_link, current_depth + 1, max_depth, directory_path, root_url)

    except Exception as e:
        print(f"Error accessing {url}: {e}")

# Main script
if __name__ == "__main__":
    root_url = 'https://www.ontario.ca/page/driving-and-roads'
    root_directory = 'ontarioRoadSafety'  # Root folder for storing scraped data
    max_depth = 2  # Go 4 layers deep

    # Create the root directory if it doesn't exist
    os.makedirs(root_directory, exist_ok=True)

    # Initialize Selenium (using Chrome driver)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    # Start scraping from the root URL
    scrape_page(driver, root_url, current_depth=0, max_depth=max_depth, parent_directory=root_directory, root_url=root_url)

    # Close the browser when done
    driver.quit()