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
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import ElementNotVisibleException
from selenium.common.exceptions import ElementClickInterceptedException

restaurant_urls = pd.read_csv(r"C:\Users\CallumO'Neill\windows_directory\data\mexican_restaurant_url_list_tripadvisor.csv")
url_list = restaurant_urls['mexican_restaurant_urls'].to_list()

class Scraper:
    def __init__(self, driver, url_list, starting_position = 0, terrible_rating=False):
        self.chrome_options = Options()
        self.chrome_service = Service(r"C:\Users\CallumO'Neill\PythonBox\chromedriver.exe")
        self.driver = driver
        self.actions = ActionChains(self.driver)
        self.date_list = []
        self.review_title = []
        self.descriptions = []
        self.visit_date = []
        self.urls = url_list[starting_position:]
        self.url_total = len(self.urls)
        self.urls_being_scraped = []
        self.scraped_count = 0
        self.terrible_rating = terrible_rating

    def scrape(self):
        for url in self.urls:
            self.page = 0
            self.driver.get(url)
            self.urls_being_scraped.append(url)
            index_position = self.urls.index(url)
            print('Index Position:', index_position)
            print('Urls scraped or being scraped:', self.urls_being_scraped)

            self.wait_for_page_load(10, '/html/body/div[1]/div[2]/div/button[1]')

            self.accept_cookies()

            if self.terrible_rating == False:
                self.isolate_excellent_reviews()
            else:
                self.isolate_terrible_reviews()

            while True:
                try:
                    self.reveal_full_description_entries()

                    paths = [
                        'ratingDate',
                        'noQuotes',
                        'div.ui_column.is-9 > div.prw_rup.prw_reviews_text_summary_hsx > div > p',
                        'prw_rup.prw_reviews_stay_date_hsx',
                    ]

                    elements = self.wait_for_elements(paths, 35)

                    zipped_elements = list(zip(*elements.values()))

                    for review_date_element, review_title_element, description_element, visit_date_element in zipped_elements:
                        self.extract_review_date(review_date_element)
                        self.extract_review_title(review_title_element)
                        self.extract_description(description_element)
                        self.extract_visit_date(visit_date_element)


                    if self.click_next_page() or self.scraped_count == self.url_total:
                        break

                except NoSuchElementException:
                    print('No more pages to scrape!')
                    break

    def wait_for_page_load(self, timeout, xpath):
        time.sleep(timeout)
        reload_button_elems = self.driver.find_elements(By.XPATH, xpath)

        if reload_button_elems:
            reload_button_elem = reload_button_elems[0]
            reload_button_elem.click()

        time.sleep(15)

    def accept_cookies(self):
        accept_button_id = 'onetrust-accept-btn-handler'
        accept_button_elems = self.driver.find_elements(By.ID, accept_button_id)

        if accept_button_elems:
            accept_button_elem = accept_button_elems[0]
            accept_button_elem.click()

    def isolate_excellent_reviews(self):
        time.sleep(10)
        excellent_xpath = '/html/body/div[2]/div[2]/div[2]/div[6]/div/div[1]/div[3]/div/div[2]/div/div[1]/div/div[2]/div[1]/div/div[2]/div/div[1]/label'
        WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.XPATH, excellent_xpath)))
        excellent_box = self.driver.find_element(By.XPATH, excellent_xpath)
        self.actions.move_to_element(excellent_box).perform()
        excellent_box.click()
        time.sleep(5)

    def isolate_terrible_reviews(self):
        time.sleep(10)
        terrible_xpath = '/html/body/div[2]/div[2]/div[2]/div[6]/div/div[1]/div[3]/div/div[2]/div/div[1]/div/div[2]/div[1]/div/div[2]/div/div[5]/label'
        WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.XPATH, terrible_xpath)))
        terrible_box = self.driver.find_element(By.XPATH, terrible_xpath)
        self.actions.move_to_element(terrible_box).perform()
        terrible_box.click()
        time.sleep(5)
        

    def reveal_full_description_entries(self):
        more_revealer_class = 'taLnk.ulBlueLinks'
        WebDriverWait(self.driver, 15).until(EC.visibility_of_all_elements_located((By.CLASS_NAME, more_revealer_class)))
        more_elements = self.driver.find_elements(By.CLASS_NAME, more_revealer_class)
        more_button_count = len(more_elements)
        more_button = 0
        time.sleep(5)

        while more_button < more_button_count:
            try:
                WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.CLASS_NAME, more_revealer_class))).click()
                time.sleep(3)
                more_button += 1
            except (StaleElementReferenceException, ElementClickInterceptedException) as e:
                if isinstance(e, StaleElementReferenceException):
                    WebDriverWait(self.driver, 15).until(EC.presence_of_all_elements_located((By.CLASS_NAME, more_revealer_class)))
                    more_elements = self.driver.find_elements(By.CLASS_NAME, more_revealer_class)
                    if more_button < len(more_elements):
                        more_element = more_elements[more_button]
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", more_element)
                        more_element.click()
                        time.sleep(3)
                        more_button += 1
                elif isinstance(e, ElementClickInterceptedException):
                    WebDriverWait(self.driver, 30).until(EC.presence_of_all_elements_located((By.CLASS_NAME, more_revealer_class)))
                    more_elements = self.driver.find_elements(By.CLASS_NAME, more_revealer_class)
                    if more_button < len(more_elements):
                        more_element = more_elements[more_button]
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", more_element)
                        more_element.click()
                        time.sleep(3)
                        more_button += 1

    def wait_for_elements(self, paths, timeout):
        element_visibility_wait_time = WebDriverWait(self.driver, timeout)
        elements = {}

        try:
            for class_path in paths:
                if class_path == 'div.ui_column.is-9 > div.prw_rup.prw_reviews_text_summary_hsx > div > p':
                    elements[class_path] = element_visibility_wait_time.until(
                        EC.visibility_of_all_elements_located((By.CSS_SELECTOR, class_path))
                    )
                else:
                    elements[class_path] = element_visibility_wait_time.until(
                        EC.visibility_of_all_elements_located((By.CLASS_NAME, class_path))
                    )
        except (WebDriverException, TimeoutException):
            if WebDriverException:
                print('Web driver exception error occurred! Trying an alternative')
                for class_path in paths:
                    if class_path == 'div.ui_column.is-9 > div.prw_rup.prw_reviews_text_summary_hsx > div > p':
                        elements[class_path] = self.driver.find_elements(By.CSS_SELECTOR, class_path)
                    else:
                        elements[class_path] = self.driver.find_elements(By.CLASS_NAME, class_path)
            elif TimeoutException:
                print('Scraping timed out. Potential scraping limit reached. Next URL....')

        return elements

    def extract_review_date(self, review_date_element):
        try:
            WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, 'ratingDate')))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", review_date_element)
            date = review_date_element.get_attribute('title')
            if date is not None:
                self.date_list.append(date)
        except (StaleElementReferenceException, NoSuchElementException, WebDriverException) as e:
            if isinstance(e, StaleElementReferenceException):
                print('Review date element became stale while trying to extract or scroll to it')
                print('Trying again: second try.....')
                WebDriverWait(self.driver, 25).until(EC.presence_of_element_located((By.CLASS_NAME, 'ratingDate')))
                self.driver.execute_script("arguments[0].scrollIntoView(true);", review_date_element)
                review_date = review_date_element.get_attribute('title')
                if review_date is not None:
                    self.date_list.append(review_date)
                    
            elif isinstance(e, NoSuchElementException):
                print('Element not found: Review date element could not be obtained!')
                print(e)
                self.date_list.append(' ')
            elif isinstance(e, WebDriverException):
                print('Web Driver Exception: Review date element could not be obtained!')
                print(e)
                self.date_list.append(' ')

    def extract_review_title(self, review_title_element):
        try:
            WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, 'noQuotes')))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", review_title_element)
            title = review_title_element.text
            if title is not None:
                self.review_title.append(title)
        except (StaleElementReferenceException, NoSuchElementException, WebDriverException) as e:
            if isinstance(e, StaleElementReferenceException):
                print('Review title element became stale while trying to extract or scroll to it')
                print('Trying again: second try.....')
                WebDriverWait(self.driver, 25).until(EC.presence_of_element_located((By.CLASS_NAME, 'noQuotes')))
                self.driver.execute_script("arguments[0].scrollIntoView(true);", review_title_element)
                title = review_title_element.text
                if title is not None:
                    self.review_title.append(title)
        
            elif isinstance(e, NoSuchElementException):
                print('Element not found: Review title element could not be obtained!')
                print(e)
                self.review_title.append(' ')
            elif isinstance(e, WebDriverException):
                print('Web Driver Exception: Review title element could not be obtained!')
                print(e)
                self.review_title.append(' ')

    def extract_description(self, description_element):
        try:
            WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.ui_column.is-9 > div.prw_rup.prw_reviews_text_summary_hsx > div > p')))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", description_element)
            description = description_element.text
            if description is not None:
                self.descriptions.append(description)
        except (StaleElementReferenceException, NoSuchElementException, WebDriverException) as e:
            if isinstance(e, StaleElementReferenceException):
                print('Review description element became stale while trying to extract or scroll to it')
                print('Trying again: second try.....')
                WebDriverWait(self.driver, 25).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.ui_column.is-9 > div.prw_rup.prw_reviews_text_summary_hsx > div > p')))
                self.driver.execute_script("arguments[0].scrollIntoView(true);", description_element)
                description = description_element.text
                if description is not None:
                    self.descriptions.append(description)
                    
            elif isinstance(e, NoSuchElementException):
                print('Element not found: Review description element could not be obtained!')
                print(e)
                self.descriptions.append(' ')
            elif isinstance(e, WebDriverException):
                print('Web Driver Exception: Review description element could not be obtained!')
                print(e)
                self.descriptions.append(' ')

    def extract_visit_date(self, visit_date_element):
        try:
            WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, 'prw_rup.prw_reviews_stay_date_hsx')))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", visit_date_element)
            visit_date_text = visit_date_element.text
            if visit_date_text is not None:
                self.visit_date.append(visit_date_text)
        except (StaleElementReferenceException, NoSuchElementException, WebDriverException) as e:
            if isinstance(e, StaleElementReferenceException):
                print('Visit date element became stale while trying to extract or scroll to it')
                print('Trying again: second try.....')
                WebDriverWait(self.driver, 25).until(EC.presence_of_element_located((By.CLASS_NAME, 'prw_rup.prw_reviews_stay_date_hsx')))
                self.driver.execute_script("arguments[0].scrollIntoView(true);", visit_date_element)
                visit_date_text = visit_date_element.text
                if visit_date_text is not None:
                    self.visit_date.append(visit_date_text)
                
            elif isinstance(e, NoSuchElementException):
                print('Element not found: Visit date element could not be obtained!')
                print(e)
                self.visit_date.append(' ')
            elif isinstance(e, WebDriverException):
                print('Web Driver Exception: Review description element could not be obtained!')
                print(e)
                self.visit_date.append(' ')

    def click_next_page(self):
        page_button_class = 'nav.next.ui_button.primary'
        try:
            next_page = self.driver.find_element(By.CLASS_NAME, page_button_class)
            self.no_more_pages = False
            if 'disabled' in next_page.get_attribute('class'):
                print('Final page scraped. Next URL.....')
                self.scraped_count += 1
                self.no_more_pages = True
            self.driver.execute_script("arguments[0].scrollIntoView(true);", next_page)
            time.sleep(3)
            print("Next page element found and clickable. Clicking...")
            time.sleep(3)
            self.driver.execute_script("arguments[0].click();", next_page)
            print("Clicked on the next page")
            time.sleep(10)
            self.no_more_pages = False
            self.page +=1
            print('pages scraped: ', self.page)
        except NoSuchElementException:
            print("Couldn't find page button! Trying again!")
            self.driver.refresh()
            time.sleep(3)
            try:
                next_page = self.driver.find_element(By.CLASS_NAME, page_button_class)
                self.no_more_pages = False
                if 'disabled' in next_page.get_attribute('class'):
                    print('Final page scraped. Next URL.....')
                    self.scraped_count += 1
                    self.no_more_pages = True
                self.driver.execute_script("arguments[0].scrollIntoView(true);", next_page)
                time.sleep(3)
                print("Next page element found and clickable. Clicking...")
                time.sleep(3)
                self.driver.execute_script("arguments[0].click();", next_page)
                print("Clicked on the next page")
                time.sleep(10)
                self.no_more_pages = False
                self.page +=1
                print('pages scraped: ', self.page)
            except NoSuchElementException:
                print('Final page scraped....')
                self.scraped_count += 1
                self.no_more_pages = True
