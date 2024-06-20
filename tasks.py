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

import csv

class Scraper:
	# This time is used when we are waiting for element to get loaded in the html
	wait_element_time = 20

	def __init__(self, url):
		self.url = url

		self.setup_driver_options()
		self.setup_driver()

	# Automatically close driver on destruction of the object
	def __del__(self):
		self.driver.close()

	# Add these options in order to make chrome driver appear as a human instead of detecting it as a bot
	# Also change the 'cdc_' string in the chromedriver.exe with Notepad++ for example with 'abc_' to prevent detecting it as a bot
	def setup_driver_options(self):
		self.driver_options = Options()

		arguments = [
			'--disable-blink-features=AutomationControlled'
		]

		experimental_options = {
			'excludeSwitches': ['enable-automation', 'enable-logging'],
			'prefs': {'profile.default_content_setting_values.notifications': 2}
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

		element = self.find_element(selector)

		try:
			element.click()
		except ElementClickInterceptedException:
			self.driver.execute_script("arguments[0].click();", element)

	# Wait random time before clicking on the element
	def element_click_by_xpath(self, xpath, delay = True):
		if delay:
			self.wait_random_time()

		element = self.find_element_by_xpath(xpath)

		try:
			element.click()
		except ElementClickInterceptedException:
			self.driver.execute_script("arguments[0].click();", element)

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
	
	def scroll_to_element(self, selector):
		element = self.find_element(selector)

		self.driver.execute_script('arguments[0].scrollIntoView(true);', element)

	def scroll_to_element_by_xpath(self, xpath):
		element = self.find_element_by_xpath(xpath)

		self.driver.execute_script('arguments[0].scrollIntoView(true);', element)
  
	def element_delete_text(self, selector, delay = True):
			if delay:
				self.wait_random_time()

			element = self.find_element(selector)
			
			# Select all of the text in the input
			element.send_keys(Keys.LEFT_SHIFT + Keys.HOME)
			# Remove the selected text with backspace
			element.send_keys(Keys.BACK_SPACE)


# Remove and then publish each listing
def update_listings(listings, type, scraper, server):
	# If listings are empty stop the function
	if not listings:
		return

	
	# Check if listing is already listed and remove it then publish it like a new one
	for listing in listings:
		scraper.go_to_page("https://www.gumtree.com.au/web/syi")

		publish_listing(listing, type, scraper, server)


def publish_listing(data, listing_type, scraper, server):
	# Click on create new listing button
	scraper.element_click('a[href="/web/syi/title"]')
 
	scraper.element_send_keys('input[name="preSyiTitle"]', data['Title'])
	scraper.element_click_by_xpath('//button[text()="Next"]')

	# scraper.element_click_by_xpath('//span[text()="' + data['Category1'] + '"]')
	scraper.element_click('button[id="9299"]')
	
	scraper.element_click_by_xpath('//span[text()="' + data['Category2'] + '"]')
	scraper.element_click_by_xpath('//span[text()="' + data['Category3'] + '"]')
	scraper.element_click_by_xpath('//button[text()="Next"]')
	
	images_path = generate_multiple_images_path(data['Photos Folder'], data['Photos Names'])
	scraper.input_file_add_files('input[accept="image/gif,image/jpg,image/jpeg,image/pjpeg,image/png,image/x-png"]', images_path)
	
	scraper.scroll_to_element_by_xpath('//h2[text()="Description"]')
	scraper.element_send_keys('textarea[name="description"]', data['Description'])
	
 
	scraper.element_click_by_xpath(f'//span[text()="{data["Condition"]}"]')
 
	scraper.scroll_to_element_by_xpath('//h2[text()="Price"]')
 
	scraper.element_send_keys('input[name="price.amount"]', data['Price'])
	
	scraper.scroll_to_element('label[for="mapAddress"]')
	scraper.element_click_by_xpath('//button[text()="Next"]')

	scraper.element_click('button[value="0"]')

	scraper.scroll_to_element_by_xpath('//h2[text()="Optional extra"]')
	scraper.element_click_by_xpath('//button[text()="Post"]')
 
	success_mess_elm = scraper.find_element_by_xpath('//span[text()="Occasionally ads may take a few hours to go live."]', False, 3)
	
	if success_mess_elm:
		print(f"Listing ${data['Id']} is published successfully")
		try:
			server.post(data['Id'])
			time.sleep(1)
		except Exception:
			raise RuntimeError(f"Listing ${data['Id']} is not updated to database successfully")
	else:
		raise RuntimeError(f"Listing ${data['Id']} is not published successfully")

def generate_multiple_images_path(path, images):
	# Last character must be '/' because after that we are adding the name of the image
	if path[-1] != '/':
		path += '/'

	images_path = ''

	# Split image names into array by this symbol ";"
	image_names = images.split(';')

	# Create string that contains all of the image paths separeted by \n
	if image_names:
		for image_name in image_names:
			# Remove whitespace before and after the string
			image_name = image_name.strip()

			# Add "\n" for indicating new file
			if images_path != '':
				images_path += '\n'

			images_path += path + image_name

	return images_path



############################################################
flask_app = create_app() 
celery_app = flask_app.extensions["celery"] 

@celery_app.task(ignore_result=False, name='tasks.update_price', bind=True, default_retry_delay=120) #ignore_result: store the result of the task
def update_price(self, id, price):
    scraper = Scraper('https://www.gumtree.com.au')
    try:
        scraper.add_login_functionality('https://www.gumtree.com.au/t-login-form.html', 'span.header__my-gumtree-trigger-text')
        time.sleep(2)
        
        scraper.go_to_page(f'https://www.gumtree.com.au/p-edit-ad.html?adId={id}')
        time.sleep(2)
        
        scraper.scroll_to_element_by_xpath('//h2[text()="Additional information"]')
        scraper.element_delete_text('input[name="price.amount"]')
        scraper.element_send_keys('input[name="price.amount"]', price)
        scraper.element_click_by_xpath("//button[text()='Save & close']")
        time.sleep(5)
    except Exception as e:
        raise self.retry()
    finally:
        scraper.__del__()
        

			

