from config import create_app #-Line 1
from celery import shared_task 


import logging
import requests

import os
import time
import random
from urllib.parse import urlparse, parse_qs
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

from helpers.scraper import Scraper

from utils import generate_multiple_images_path, update_condition, update_location



############################################################
flask_app = create_app() 
celery_app = flask_app.extensions["celery"] 

scraper = Scraper('https://www.gumtree.com.au')
scraper.add_login_functionality('https://www.gumtree.com.au/t-login-form.html', 'span.header__my-gumtree-trigger-text')


logger = logging.getLogger(__name__)

def confirm_updating_item(id):
	response = requests.get(f'http://localhost:5000/main_app/gummtree_bot/confirm_update/{id}')
	logger.info(f"Confirming updating item {id} is successfully with response: {response}")
 
def confirm_deleting_item(id):
	response = requests.get(f'http://localhost:5000/main_app/gummtree_bot/confirm_delete/{id}')
	logger.info(f"Confirming deleting item {id} is successfully with response: {response}")
 
def confirm_creating_item(id):
	response = requests.get(f'http://localhost:5000/main_app/gummtree_bot/confirm_create/{id}')
	logger.info(f"Confirming creating item {id} is successfully with response: {response}")

from utils import update_make, update_model, update_body_type, update_warranty, update_price

@shared_task(name='tasks.update_item', bind=True) 
def update_item(self, item):
	scraper.go_to_page(f'https://www.gumtree.com.au/p-edit-ad.html?adId={item["Id"]}')
 
	is_other_make = "Yes";	
 
	if item.get('make'): # update car make
		is_other_make = update_make(item, scraper)	

	if item.get('model') and is_other_make == "No": # update car model
		update_model(item, scraper)
	
	if item.get('body_type'): # update body type
		update_body_type(item, scraper)
 
	if item.get('warranty'): # update warranty
		update_warranty(item, scraper)

	if item.get('condition'): # update condition
		update_condition(item, scraper)
  
	if item.get('price'): # update price
		logger.info(f"Updating price of item {item['id']} to {item['price']}")
		update_price(item, scraper)
  
	if item.get('location'): # update location
		update_location(item, scraper)
	
	#save
	scraper.element_click_by_xpath('//button[text()="Save & close"]')
	logger.info(f"Item {item['id']} is updated successfully")
	time.sleep(2)
	
	try:
		confirm_updating_item(item['id'])
	except:
		logger.error(f"Failed to confirm updating of item {item['id']}")
        

@shared_task(name='tasks.delete_item', bind=True) 
def delete_item(self, item):
	scraper.go_to_page(f"https://www.gumtree.com.au/m-my-ad.html?adId={item['id']}")
 
	if scraper.find_element_by_xpath(f'//a[@href="/m-delete-ad.html?adId={item["id"]}"]', False, 2):
		scraper.scroll_to_element_by_xpath(f'//a[@href="/m-delete-ad.html?adId={item["id"]}"]')
		scraper.element_click_by_xpath(f'//a[@href="/m-delete-ad.html?adId={item["id"]}"]')
		scraper.element_click_by_xpath(f'//label[text()="{item["reason"]}"]')
		scraper.element_click_by_xpath('//button[@id="delete-ad-confirm"]')
  
		logger.info(f"Item {item['id']} is deleted successfully")
		time.sleep(2)
	
	try:
		confirm_deleting_item(item['id'])
	except:
		logger.error(f"Failed to confirm deleting of item {item['id']}")			

@shared_task(name='tasks.create_item', bind=True) 
def create_item(self, item):
	scraper.go_to_page(f'https://www.gumtree.com.au/web/syi/title')
	
	scraper.element_send_keys('input[name="preSyiTitle"]', item['title'])
	scraper.element_click_by_xpath('//button[text()="Next"]')

	scraper.element_click_by_xpath(f'//span[text()="{item["category_1"]}"]')
	time.sleep(1)
	scraper.element_click_by_xpath(f'//span[text()="{item["category_2"]}"]')
	time.sleep(1)
	scraper.element_click_by_xpath(f'//span[text()="{item["category_3"]}"]')
	time.sleep(1)

	scraper.element_click_by_xpath('//button[text()="Next"]')
	
	images_path = generate_multiple_images_path(item['photo_dir'], item['photo_names'])
	scraper.input_file_add_files('input[accept="image/gif,image/jpg,image/jpeg,image/pjpeg,image/png,image/x-png"]', images_path)
	
	scraper.scroll_to_element_by_xpath('//h2[text()="Description"]')
	scraper.element_send_keys('textarea[name="description"]', item['description'])
	
 
	scraper.element_click_by_xpath(f'//span[text()="{item["condition"]}"]')
 
	scraper.scroll_to_element_by_xpath('//h2[text()="Price"]')
 
	scraper.element_send_keys('input[name="price.amount"]', item['price'])
	
	scraper.scroll_to_element('label[for="mapAddress"]')
	scraper.element_click_by_xpath('//button[text()="Next"]')
	time.sleep(2)

	id = scraper.get_current_url().split("=")[-1]
	
	#Free
	scraper.element_click('button[value="0"]')

	scraper.scroll_to_element_by_xpath('//h2[text()="Optional extra"]')
	scraper.element_click_by_xpath('//button[text()="Post"]')
 
	try:
		confirm_creating_item(id)
	except:
		logger.error(f"Failed to confirm creating of item {item['title']}")			
