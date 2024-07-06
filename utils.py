from helpers.scraper import Scraper 
import time

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

def update_make(item, scraper: Scraper) -> str:
    is_other = "No"
    
    scraper.scroll_to_element_by_xpath('//h2[text()="Additional information"]')
    scraper.element_click_by_xpath('//div[button[@name="attributeMap[auto_body_parts.carmake_s]"]]')
    
    if scraper.find_element_by_xpath(f'//button[text()="{item["make"]}"]', False, 2): 
        scraper.scroll_to_element_by_xpath(f'//button[text()="{item["make"]}"]')
        scraper.element_click_by_xpath(f'//button[text()="{item["make"]}"]')
    else: 
        is_other = "Yes"
        scraper.scroll_to_element_by_xpath(f'//button[text()="Other"]') 
        scraper.element_click_by_xpath(f'//button[text()="Other"]')
        
    return is_other

def update_model(item, scraper: Scraper):
    scraper.scroll_to_element_by_xpath('//div[text()="Model"]')
    scraper.element_click_by_xpath('//div[button[@name="attributeMap[auto_body_parts.carmodel_s]"]]')
    if scraper.find_element_by_xpath(f'//button[text()="{item["model"]}"]', False, 2): 
        scraper.scroll_to_element_by_xpath(f'//button[text()="{item["model"]}"]')
        scraper.element_click_by_xpath(f'//button[text()="{item["model"]}"]')
    else:
        scraper.scroll_to_element_by_xpath(f'//button[text()="Other"]') 
        scraper.element_click_by_xpath(f'//button[text()="Other"]') 
        
def update_body_type(item, scraper: Scraper):
    scraper.scroll_to_element_by_xpath('//div[text()="Body Type"]')
    scraper.element_click_by_xpath('//div[button[@name="attributeMap[auto_body_parts.carbodytype_s]"]]')
    if scraper.find_element_by_xpath(f'//button[text()="{item["body_type"]}"]', False, 2):
        scraper.scroll_to_element_by_xpath(f'//button[text()="{item["body_type"]}"]')
        scraper.element_click_by_xpath(f'//button[text()="{item["body_type"]}"]')
    else:
        scraper.scroll_to_element_by_xpath(f'//button[text()="Other"]') 
        scraper.element_click_by_xpath(f'//button[text()="Other"]') 
        
def update_warranty(item, scraper: Scraper):
	scraper.scroll_to_element_by_xpath('//label[text()="Warranty"]')
	if scraper.find_element_by_xpath(f'//label[@role="radio" and span[text()="{item["warranty"]}"]]').get_attribute('aria-checked') == 'false':
		scraper.element_click_by_xpath(f'//label[@role="radio" and span[text()="{item["warranty"]}"]]')

def update_condition(item, scraper: Scraper):
	scraper.scroll_to_element_by_xpath('//label[text()="Condition"]')
	if scraper.find_element_by_xpath(f'//label[@role="radio" and span[text()="{item["condition"]}"]]').get_attribute('aria-checked') == 'false':
		scraper.element_click_by_xpath(f'//label[@role="radio" and span[text()="{item["condition"]}"]]')
  
def update_location(item, scraper: Scraper):
	scraper.scroll_to_element('input[name="mapAddress.mapAddress"]')
	scraper.element_delete_text('input[name="mapAddress.mapAddress"]')
	scraper.element_send_keys('input[name="mapAddress.mapAddress"]', item["location"])
	time.sleep(1)
	scraper.find_multiple_elements_by_xpath('//div[@class="pac-item"]', 0).click()

def update_price(item, scraper: Scraper):
	scraper.scroll_to_element('input[name="price.amount"]')   
	scraper.element_delete_text('input[name="price.amount"]')
	scraper.element_send_keys('input[name="price.amount"]', item["price"])