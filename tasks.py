from config import create_app #-Line 1
from celery import shared_task 


import os
import time
import random
from dotenv import load_dotenv
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import InvalidArgumentException
from selenium.common.exceptions import ElementClickInterceptedException

class Scraper:
	# This time is used when we are waiting for element to get loaded in the html
	wait_element_time = 30

	def __init__(self, url):
		self.url = url

		self.setup_driver_options()
		self.setup_driver()

	# Automatically close driver on destruction of the object
	def __del__(self):
		self.driver.close()

	def get_current_url(self):
		return self.driver.current_url
	# Add these options in order to make chrome driver appear as a human instead of detecting it as a bot
	# Also change the 'cdc_' string in the chromedriver.exe with Notepad++ for example with 'abc_' to prevent detecting it as a bot
	def setup_driver_options(self):
		self.driver_options = Options()

		arguments = [
			'--disable-blink-features=AutomationControlled'
		]

		experimental_options = {
			'excludeSwitches': ['enable-automation', 'enable-logging'],
			'prefs': {'profile.default_content_setting_values.notifications': 2, 
             		  "credentials_enable_service": False,
                      "profile.password_manager_enabled": False}
		}

		for argument in arguments:
			self.driver_options.add_argument(argument)

		for key, value in experimental_options.items():
			self.driver_options.add_experimental_option(key, value)

	# Setup chrome driver with predefined options
	def setup_driver(self):
		chrome_driver_path = ChromeDriverManager().install()
		self.driver = webdriver.Chrome(service=ChromeService(chrome_driver_path), options = self.driver_options)
		self.driver.get(self.url)
		self.driver.maximize_window()

	def add_login_functionality(self, login_url, is_logged_in_selector):
		self.login_url = login_url
		self.is_logged_in_selector = is_logged_in_selector
		
		self.login()


	# Check if user is logged in based on a html element that is visible only for logged in users
	def login(self):
		self.go_to_page(self.login_url)
  
		load_dotenv()
		username = os.getenv('USERNAME')
		password = os.getenv('PASSWORD')
  
		self.element_send_keys('input[name="loginMail"]', username)
		self.element_send_keys('input[name="password"]', password)

		self.element_click_by_xpath('//span[text()="Sign In"]')
  
		self.find_element('span[class="header__my-gumtree-trigger-text"]', wait_element_time = 5)
  
  
	# Wait random amount of seconds before taking some action so the server won't be able to tell if you are a bot
	def wait_random_time(self):
		random_sleep_seconds = round(random.uniform(1, 2), 2)

		time.sleep(random_sleep_seconds)

	# Goes to a given page and waits random time before that to prevent detection as a bot
	def go_to_page(self, page):
		# Wait random time before refreshing the page to prevent the detection as a bot
		self.wait_random_time()

		# Refresh the site url with the loaded cookies so the user will be logged in
		self.driver.get(page)
		time.sleep(5)
		self.scroll_down_and_back()
		time.sleep(2)
  

	def find_element(self, selector, exit_on_missing_element = True, wait_element_time = None):
		if wait_element_time is None:
			wait_element_time = self.wait_element_time

		# Intialize the condition to wait
		wait_until = EC.element_to_be_clickable((By.CSS_SELECTOR, selector))

		try:
			# Wait for element to load
			element = WebDriverWait(self.driver, wait_element_time).until(wait_until)
		except:
			if exit_on_missing_element:
				print('ERROR: Timed out waiting for the element with css selector "' + selector + '" to load')
				# End the program execution because we cannot find the element
				exit()
			else:
				return False

		return element

	def find_multiple_elements_by_xpath(self, xpath, index, exit_on_missing_element = True, wait_element_time = None):
		if wait_element_time is None:
			wait_element_time = self.wait_element_time

		# Intialize the condition to wait
		wait_until = EC.presence_of_all_elements_located((By.XPATH, xpath))

		try:
			# Wait for element to load
			elements = WebDriverWait(self.driver, wait_element_time).until(wait_until)
		except:
			if exit_on_missing_element:
				# End the program execution because we cannot find the element
				print('ERROR: Timed out waiting for the element with xpath "' + xpath + '" to load')
				exit()
			else:
				return False

		return elements[index]

	def find_element_by_xpath(self, xpath, exit_on_missing_element = True, wait_element_time = None):
		if wait_element_time is None:
			wait_element_time = self.wait_element_time

		# Intialize the condition to wait
		wait_until = EC.element_to_be_clickable((By.XPATH, xpath))

		try:
			# Wait for element to load
			element = WebDriverWait(self.driver, wait_element_time).until(wait_until)
		except:
			if exit_on_missing_element:
				# End the program execution because we cannot find the element
				print('ERROR: Timed out waiting for the element with xpath "' + xpath + '" to load')
				exit()
			else:
				return False

		return element

	# Wait random time before clicking on the element
	def element_click(self, selector, delay = True):
		if delay:
			self.wait_random_time()

		try:
			element = self.find_element(selector)
		except:
			print('ERROR: Timed out waiting for the element to load')
		if element: 
			element.click()

	# Wait random time before clicking on the element
	def element_click_by_xpath(self, xpath, delay = True):
		
     
		if delay:
			self.wait_random_time()
		try:
			element = self.find_element_by_xpath(xpath)
		except:
			print('ERROR: Timed out waiting for the element with xpath "' + xpath + '" to load')
		if element: 
			element.click()
	
	# Wait random time before sending the keys to the element
	def element_send_keys(self, selector, text, delay = True):
		if delay:
			self.wait_random_time()

		element = self.find_element(selector)

		try:
			element.click()
		except ElementClickInterceptedException:
			self.driver.execute_script("arguments[0].click();", element)
		self.wait_random_time()
		element.send_keys(text)

	# Wait random time before sending the keys to the element
	def element_send_keys_by_xpath(self, xpath, text, delay = True):
		if delay:
			self.wait_random_time()

		element = self.find_element_by_xpath(xpath)

		try:
			element.click()
		except ElementClickInterceptedException:
			self.driver.execute_script("arguments[0].click();", element)
		
		element.send_keys(text)

	def input_file_add_files(self, selector, files):
		# Intialize the condition to wait
		wait_until = EC.presence_of_element_located((By.CSS_SELECTOR, selector))

		try:
			# Wait for input_file to load
			input_file = WebDriverWait(self.driver, self.wait_element_time).until(wait_until)
		except:
			print('ERROR: Timed out waiting for the input_file with selector "' + selector + '" to load')
			# End the program execution because we cannot find the input_file
			exit()

		self.wait_random_time()

		try:
			input_file.send_keys(files)
		except InvalidArgumentException:
			print('ERROR: Exiting from the program! Please check if these file paths are correct:\n' + files)
			exit()
   
	def scroll_down_and_back(self):
		document_height = self.driver.execute_script("return document.body.scrollHeight")
		# Scroll down 100 pixels every 0.25 seconds
		for i in range(0, document_height, 100):
			self.driver.execute_script(f"window.scrollBy(0, {min(100, document_height - i)});")
			time.sleep(0.1)

		for i in range(document_height, 0, -100):
			self.driver.execute_script(f"window.scrollBy(0, -{min(100, i)});")
			time.sleep(0.1)
  
	def scroll_to_element(self, selector):
		element = self.find_element(selector)

		self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)

	def scroll_to_element_by_xpath(self, xpath):
		element = self.find_element_by_xpath(xpath)

		self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
  
	def element_delete_text(self, selector, delay = True):
			if delay:
				self.wait_random_time()

			element = self.find_element(selector)
			
			# Select all of the text in the input
			element.send_keys(Keys.LEFT_SHIFT + Keys.HOME)
			# Remove the selected text with backspace
			element.send_keys(Keys.BACK_SPACE)

############################################################
flask_app = create_app() 
celery_app = flask_app.extensions["celery"] 

scraper = Scraper('https://www.gumtree.com.au')
scraper.add_login_functionality('https://www.gumtree.com.au/t-login-form.html', 'span.header__my-gumtree-trigger-text')

import logging

logger = logging.getLogger(__name__)

@shared_task(name='tasks.update_item', bind=True) 
def update_item(self, item):
	scraper.go_to_page(f'https://www.gumtree.com.au/p-edit-ad.html?adId={item["Id"]}')
	
	scraper.scroll_to_element_by_xpath('//h2[text()="Additional information"]')
	scraper.element_click_by_xpath('//div[button[@name="attributeMap[auto_body_parts.carmake_s]"]]')
	
	if scraper.find_element_by_xpath(f'//button[text()="{item["Make"]}"]', False, 2): 
		scraper.scroll_to_element_by_xpath(f'//button[text()="{item["Make"]}"]')
		scraper.element_click_by_xpath(f'//button[text()="{item["Make"]}"]')
		
		#update car model
		scraper.scroll_to_element_by_xpath('//div[text()="Model"]')
		scraper.element_click_by_xpath('//div[button[@name="attributeMap[auto_body_parts.carmodel_s]"]]')
		if scraper.find_element_by_xpath(f'//button[text()="{item["Model"]}"]', False, 2): 
			scraper.scroll_to_element_by_xpath(f'//button[text()="{item["Model"]}"]')
			scraper.element_click_by_xpath(f'//button[text()="{item["Model"]}"]')
		else:
			scraper.scroll_to_element_by_xpath(f'//button[text()="Other"]') 
			scraper.element_click_by_xpath(f'//button[text()="Other"]') 
		
		#update body type
		scraper.scroll_to_element_by_xpath('//div[text()="Body Type"]')
		scraper.element_click_by_xpath('//div[button[@name="attributeMap[auto_body_parts.carbodytype_s]"]]')
		if scraper.find_element_by_xpath(f'//button[text()="{item["Body Type"]}"]', False, 2):
			scraper.scroll_to_element_by_xpath(f'//button[text()="{item["Body Type"]}"]')
			scraper.element_click_by_xpath(f'//button[text()="{item["Body Type"]}"]')
		else:
			scraper.scroll_to_element_by_xpath(f'//button[text()="Other"]') 
			scraper.element_click_by_xpath(f'//button[text()="Other"]') 
	else: 
		scraper.scroll_to_element_by_xpath(f'//button[text()="Other"]') 
		scraper.element_click_by_xpath(f'//button[text()="Other"]') 
		
		#update body type
		scraper.scroll_to_element_by_xpath('//div[text()="Body Type"]')
		scraper.element_click_by_xpath('//div[button[@name="attributeMap[auto_body_parts.carbodytype_s]"]]')
		if scraper.find_element_by_xpath(f'//button[text()="{item["Body Type"]}"]', False, 2):
			scraper.scroll_to_element_by_xpath(f'//button[text()="{item["Body Type"]}"]')
			scraper.element_click_by_xpath(f'//button[text()="{item["Body Type"]}"]')
		else:
			scraper.scroll_to_element_by_xpath(f'//button[text()="Other"]')
			scraper.element_click_by_xpath(f'//button[text()="Other"]')
	
	#update warranty
	scraper.scroll_to_element_by_xpath('//label[text()="Warranty"]')
	if scraper.find_element_by_xpath(f'//label[@role="radio" and span[text()="{item["Warranty"]}"]]').get_attribute('aria-checked') == 'false':
		scraper.element_click_by_xpath(f'//label[@role="radio" and span[text()="{item["Warranty"]}"]]')
		
	#update condition
	scraper.scroll_to_element_by_xpath('//label[text()="Condition"]')
	if scraper.find_element_by_xpath(f'//label[@role="radio" and span[text()="{item["Condition"]}"]]').get_attribute('aria-checked') == 'false':
		scraper.element_click_by_xpath(f'//label[@role="radio" and span[text()="{item["Condition"]}"]]')
	
	
	#update price
	scraper.scroll_to_element('input[name="price.amount"]')   
	scraper.element_delete_text('input[name="price.amount"]')
		
	scraper.element_send_keys('input[name="price.amount"]', item["Price"])
	
	#update address
	scraper.scroll_to_element('input[name="mapAddress.mapAddress"]')
	scraper.element_delete_text('input[name="mapAddress.mapAddress"]')
	scraper.element_send_keys('input[name="mapAddress.mapAddress"]', item["Location"])
	logger.info(f'{item["Location"]} updated')
	time.sleep(1)
	scraper.find_multiple_elements_by_xpath('//div[@class="pac-item"]', 0).click()
	time.sleep(2)
	
	#save
	scraper.element_click_by_xpath('//button[text()="Save & close"]')
	logger.info(f"Listing {item['Id']} is updated successfully")
	time.sleep(2)

        

			

