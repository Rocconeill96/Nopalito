from selenium.webdriver.common.keys import Keys
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import json
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import  TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import NoSuchElementException
import traceback

chrome_options = Options()
chrome_service = Service(r"C:\Users\CallumO'Neill\PythonBox\chromedriver.exe")
driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
url = 'https://www.tripadvisor.co.uk/Restaurants-g186338-London_England.html'
driver.get(url)


class MexicanRestaurantUrlScraper:
    def __init__(self, driver):
        self.driver = driver
        self.restaurant_urls = []
        self.page_no = 0

    def scrape_restaurant_urls(self):
        while True:
            try:
                wait_time = WebDriverWait(self.driver, 10)

                # Find all Mexican restaurants 
                time.sleep(5)
                mexican_restaurant_elements = wait_time.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="component_2"]/div/div/div/div[1]/div[2]/div[1]/div/span/a')))
                
                for restaurant_element in mexican_restaurant_elements:
                    # Get the URL of the restaurant
                    time.sleep(3)
                    mexican_restaurant_url = restaurant_element.get_attribute('href')
                    
                    # Check if the URL is not None
                    if mexican_restaurant_url is not None:
                        self.restaurant_urls.append(mexican_restaurant_url)

                # Click and go to the next page 
                # Check if there is a next page
                if self.page_no < 2:
                    self.page_no += 1
                else:
                    break  # No more pages, exit the loop

                next_page_xpath = f'/html/body/div[4]/div[3]/div[3]/div[2]/div[2]/div[4]/div[2]/div/div[5]/div[3]/div[5]/div[2]/div/a[{self.page_no}]'
                next_page_element = self.driver.find_element(By.XPATH, next_page_xpath)

                if next_page_element.get_attribute('aria-disabled') == 'true':
                    break  # No more pages, exit the loop

                # Click and go to the next page
                self.driver.execute_script("arguments[0].click();", next_page_element)
                
            except TimeoutException:
                break