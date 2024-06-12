#!/usr/bin/env python3

# gummiebot: Gumtree Australia automation software

# Copyright (C) 2019  Mariusz Skoneczko

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import requests

import html.parser
import json
import re
import sys
import os
import difflib
import random
import time
import getpass


class GummieBot:
    BASE_URL = 'https://www.gumtree.com.au/'

    def __init__(self, username, password):
        self.session = GummieSession()
        self.login(username, password)
        self.ads = None
        self.category_map = None

    @property
    def category_map(self):
        CATEGORIES_PAGE = ''  # just use the home page
        CATEGORIES_REGEX = re.compile(
            r'Gtau\.Global\.variables\.categories\s+=\s+({.*?})\s*;')

        if self._category_map is None:
            self._category_map = {}
            # we need to figure the categories out by getting them
            # from the website
            response = self.session.get('categories',
                                        self.BASE_URL + CATEGORIES_PAGE)
            matches = CATEGORIES_REGEX.search(response.text)
            if matches is None:
                raise RuntimeError('Could not extract Gumtree ad categories'
                                   ' using known method')
            full_tree = json.loads(matches.group(1))
            gummie_category_extract(full_tree, self._category_map)

        return self._category_map

    @category_map.setter
    def category_map(self, value):
        # setter = resetter
        self._category_map = None

    @property
    def ads(self):
        ADS_PAGE = 'm-my-ads.html'

        if self._ads is None:
            response = self.session.get('ads', self.BASE_URL + ADS_PAGE)
            ad_parser = GumtreeMyAdsParser()
            ad_parser.feed(response.text)
            self._ads = ad_parser.close()

        return self._ads

    @ads.setter
    def ads(self, value):
        # setter = resetter
        self._ads = None

    def login(self, username, password):
        LOGIN_PAGE = 't-login.html'
        ERROR_STRING = 'notification--error'
        LOGIN_FORM_ID = 'login-form'
        HTML_NAME_USERNAME = 'loginMail'
        HTML_NAME_PASSWORD = 'password'

        # read page once to get nice cookies
        response = self.session.get('login form', self.BASE_URL + LOGIN_PAGE)
        form_parser = GumtreeFormParser(LOGIN_FORM_ID)
        form_parser.feed(response.text)
        inputs = form_parser.close()

        data = {
            HTML_NAME_USERNAME: username,
            HTML_NAME_PASSWORD: password
        }
        for input_tag in inputs:
            if input_tag['name'] in data:
                # we already have data to handle this (e.g. user + pass)
                pass
            else:
                # blindly copy hidden inputs (e.g. CSRF token)
                if input_tag['type'] == 'hidden':
                    data[input_tag['name']] = input_tag['value']
                elif input_tag['type'] == 'checkbox':
                    data[input_tag['name']] = 'true'  # check the box
                else:
                    raise ValueError(
                        "Unexpected input tag type '{}' (with name '{}')"
                        .format(input_tag['type'], input_tag['name']))

        response = self.session.post('login details',
                                     self.BASE_URL + LOGIN_PAGE,
                                     data=data)

        if ERROR_STRING in response.text:
            raise ValueError('Incorrect credentials provided')

        log('Logged in')

    def delete_ad_by_id(self, id) -> bool:
        SUCCESS_STRING = 'notification--success'
        AD_ID_KEY = 'adId'
        DELETE_PAGE = 'm-delete-ad.html'
        DELETE_PAYLOAD_BASE = {
            'show': 'ALL',
            'reason': 'NO_REASON',
            'autoresponse': 0
        }
        data = DELETE_PAYLOAD_BASE
        data[AD_ID_KEY] = str(id)

        response = self.session.get("delete request for ad with id '{}'"
                                    .format(id),
                                    self.BASE_URL + DELETE_PAGE,
                                    params=data)
        return SUCCESS_STRING in response.text

    def category_name_to_id(self, category_name):
        return dict_key_else_log_similar(self.category_map,
                                         category_name,
                                         'category')

    def delete_ad_by_name(self, name) -> bool:
        return self.delete_ad_by_id(dict_key_else_log_similar(self.ads,
                                                              name,
                                                              'ad titled'))

    def post_ad(self, ad: 'GumtreeListing') -> bool:
        SUCCESS_STRING = 'notification--success'
        DELETE_DRAFT_PAGE = 'p-post-ad.html'
        FORM_PAGE = 'p-post-ad2.html'
        FORM_ID = 'pstad-main-form'
        UPLOAD_IMAGE_TARGET = 'p-upload-image.html'
        DESIRED_IMAGE_URL_KEY = 'teaserUrl'
        DRAFT_TARGET = 'p-post-draft-ad.html'
        SUBMIT_TARGET = 'p-submit-ad.html'
        MAP_ADDRESS = {
            'confidenceLevel': 'INVALID',
            'houseNumber': '',
            'latitude': -34.92849,
            'localityName': 'Adelaide CBD',
            'locationId': '3006880',
            'longitude': 138.60074,
            'mapAddress': 'Adelaide CBD, SA 5000',
            'postcode': '5000',
            'showLocationOnMap': 'false',
            'streetName': ''
        }
        

        # delete any existing drafts
        self.session.get('delete request for drafts',
                         self.BASE_URL + DELETE_DRAFT_PAGE,
                         params={'delDraft': 'true'})

        # we need to pass the first page of the form and go to the main one
        data_to_get_form = {
            'title': ad.title,
            'categoryId': self.category_name_to_id(ad.category),
            'adType': 'OFFER',
            'shouldShowSimplifiedSyi': 'false'
        }

        response = self.session.post('ad post form',
                                     self.BASE_URL + FORM_PAGE,
                                     data=data_to_get_form)
        form_parser = GumtreeFormParser(FORM_ID)
        form_parser.feed(response.text)
        inputs = form_parser.close()

        condition_field_name = False

        submission = {
            # we do need need to set category and title
            # because we already provided it to the form page
            'description': ad.description,
            'price.amount': ad.price['amount'],
            'price.type': ad.price['type']
        }
        for input_tag in inputs:
            if 'name' not in input_tag:
                continue
            if input_tag['name'] in submission:
                # do not override our values
                pass
            else:
                if input_tag.get('type') == 'checkbox':
                    pass
                else:
                    submission[input_tag['name']] = input_tag.get('value', '')
                    if 'condition' in input_tag['name']:
                        condition_field_name = input_tag['name']
        if condition_field_name is False:
            raise RuntimeError('Could not extract field name'
                               ' for item condition using known method')
        submission[condition_field_name] = ad.condition

        image_links = []
        log('Uploading images...')
        for image in ad.images:
            response = self.session.post("image '{}'".format(image),
                                         self.BASE_URL + UPLOAD_IMAGE_TARGET,
                                         data=submission, files={
                                             'images': open(image, 'rb')
                                         })
            time.sleep(2)
            try:
                url = response.json()[DESIRED_IMAGE_URL_KEY]
                image_links.append(url)
            except Exception:
                raise RuntimeError(
                    "Could not extract uploaded image URL for image '{}'"
                    .format(image))
                
                
        submission['images'] = image_links
        
        submission['mapAddress'] = MAP_ADDRESS

        # post a draft in case the actual submission fails
        # to make it easier for human to post
        self.session.post('draft',
                          self.BASE_URL + DRAFT_TARGET,
                          data=submission)

        response = self.session.post('final listing',
                                     self.BASE_URL + SUBMIT_TARGET,
                                     data=submission)
        
        if SUCCESS_STRING not in response.text:
            with open(f'response{ad.title}.txt', 'w') as file:
                file.write(response.text)

        return SUCCESS_STRING in response.text


def wait(func):
    MIN_WAIT = 1
    MAX_WAIT = 3

    def wrapper(*args, **kwargs):
        if args[0].wait:
            time.sleep(random.randint(MIN_WAIT, MAX_WAIT))
        return func(*args, **kwargs)
    return wrapper


class GummieSession():
    def __init__(self, wait=True):
        self._session = requests.Session()
        self.wait = wait

    def _safe_return_request(self, r: requests.Response) -> requests.Response:
        r.raise_for_status()
        return r

    @wait
    def get(self, name, *args, **kwargs):
        log('Getting {}...'.format(name))
        r = self._session.get(*args, **kwargs)
        return self._safe_return_request(r)

    @wait
    def post(self, name, *args, **kwargs):
        log('Posting {}...'.format(name))
        r = self._session.post(*args, **kwargs)
        return self._safe_return_request(r)


class GumtreeFormParser(html.parser.HTMLParser):
    def __init__(self, target_id):
        super().__init__()
        self.inputs = []
        self.inside_desired_form = False
        self.target_id = target_id

    def handle_starttag(self, tag, attrs):
        if tag == 'form':
            for attr in attrs:
                if attr[0] == 'id' and self.target_id in attr[1]:
                    self.inside_desired_form = True
                    break
        if self.inside_desired_form and tag == 'input':
            attrdict = {}
            # convert tuples like ('id', 'login-password') to dictionary
            # where attrdict['id'] = 'login-password'
            for attr in attrs:
                attrdict[attr[0]] = attr[1]
            self.inputs.append(attrdict)

    def handle_endtag(self, tag):
        if tag == 'form':
            self.inside_desired_form = False

    def close(self):
        return self.inputs


class GumtreeMyAdsParser(html.parser.HTMLParser):
    DESIRED_TAG_ELEMENT = 'a'
    DESIRED_TAG_CLASS = 'rs-ad-title'
    AD_ID_REGEX = re.compile(r'adId=(\d+)')

    def __init__(self):
        super().__init__()
        self.ads = {}
        self.desired_tag = False
        self.last_ad_id = -1

    def handle_starttag(self, tag, attrs):
        self.desired_tag = False
        if tag == self.DESIRED_TAG_ELEMENT:
            for attr in attrs:
                if attr[0] == 'class' and self.DESIRED_TAG_CLASS in attr[1]:
                    self.desired_tag = True

        if self.desired_tag:
            for attr in attrs:
                if attr[0] == 'href':
                    self.last_ad_id = self.AD_ID_REGEX.search(attr[1]).group(1)
                    self.ads[self.last_ad_id] = ''

    def handle_data(self, data):
        # if we are inside a tag with the ad title, get the title
        if self.desired_tag:
            self.ads[self.last_ad_id] += data

    def handle_endtag(self, tag):
        if self.desired_tag:
            # assume same type of tag is not nested
            if tag == self.DESIRED_TAG_ELEMENT:
                self.desired_tag = False

    def close(self):
        name_to_id_map = {value: key for key, value in self.ads.items()}
        self.ads = name_to_id_map
        return self.ads


class GumtreeListing():
    KNOWN_PRICE_TYPES = ['FIXED', 'NEGOTIABLE', 'GIVE_AWAY', 'SWAP_TRADE']
    KNOWN_CONDITIONS = ['used', 'new']

    def __init__(self, title, description, price, category, condition, images):
        self.title = title
        self.description = description

        if not isinstance(price, dict):
            raise TypeError("Expected 'price' element"
                            " to be an object/dictionary")
        if 'amount' not in price or 'type' not in price:
            raise ValueError("Expected subkeys 'amount' and 'type' in 'price'")
        self.price = {}
        try:
            self.price['amount'] = float(price['amount'])
        except ValueError:
            raise ValueError("'amount' is not a valid decimal number")
        if self.price['amount'] <= 0:
            raise ValueError("'amount' must be greater than zero")
        if price['type'] not in self.KNOWN_PRICE_TYPES:
            raise ValueError("Price type '{}' unknown".format(price['type']))
        self.price['type'] = price['type']

        self.category = category
        if condition not in self.KNOWN_CONDITIONS:
            raise ValueError("Condition '{}' unknown".format(condition))
        self.condition = condition
        self.images = images

    def debug(self):
        return {
            'title': self.title,
            'description': self.description,
            'price': self.price,
            'category': self.category,
            'condition': self.condition,
            'images': self.images
        }


def gummie_json_parse(directory: str) -> GumtreeListing:
    GUMMIE_JSON_FILENAME = 'meta.gummie.json'
    DEFAULT_CONDITION = 'used'

    log("Switching to directory '{}'...".format(directory))
    os.chdir(directory)

    log("Opening '{}'...".format(GUMMIE_JSON_FILENAME))
    with open(GUMMIE_JSON_FILENAME) as f:
        log("Parsing '{}'...".format(GUMMIE_JSON_FILENAME))
        raw_data = json.load(f)
        listing_data = {}
        listing_data['title'] = raw_data['title']
        with open(raw_data['description_file']) as f2:
            listing_data['description'] = f2.read()
        listing_data['price'] = raw_data['price']
        listing_data['category'] = raw_data['category']
        listing_data['condition'] = raw_data.get('condition',
                                                 DEFAULT_CONDITION)
        listing_data['images'] = []
        for image in raw_data['images']:
            if not os.path.isfile(image):
                raise FileNotFoundError("Could not find image '{}'"
                                        .format(image))
            listing_data['images'].append(image)
        return GumtreeListing(**listing_data)


def gummie_category_extract(tree, category_map):
    # extract only the "leaf" categories (categories with no children)
    # because only they can be normally selected

    if len(tree["children"]) > 0:
        for child in tree["children"]:
            gummie_category_extract(child, category_map)
    else:
        category_map[tree["name"]] = tree["id"]


def dict_key_else_log_similar(dict_, key, log_noun='key'):
    if key in dict_:
        return dict_[key]
    else:
        # suggest a key named something similar, if appropriate
        similar_list = difflib.get_close_matches(key, dict_.keys(), 1)

        if len(similar_list) > 0:
            raise ValueError("Unknown given {} '{}'. Did you mean '{}'?"
                             .format(log_noun, key, similar_list[0]))
        else:
            raise ValueError("Unknown given {} '{}'".format(log_noun, key))


def log(message, end='\n'):
    sys.stderr.write(str(message) + str(end))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        log('usage: gummiebot COMMAND DIRECTORY...')
        log('       Automation script for Gumtree Australia')
        log('       Execute COMMAND on one or more DIRECTORY sequentially')
        log('')
        log('COMMANDS')
        log('    post        Uploads ad')
        log('    delete      Deletes ad by name')
        log('    refresh     Finds and deletes ad, and then posts it,')
        log('                failing if ad did not exist previously')
        log('    repost      Finds and deletes ad, if it exists,')
        log('                and then posts ad')
        sys.exit()

    def post(gb, listing):
        return gb.post_ad(listing)

    def delete(gb, listing):
        return gb.delete_ad_by_name(listing.title)

    def refresh(gb, listing):
        return delete(gb, listing) and post(gb, listing)

    def repost(gb, listing):
        try:
            delete(gb, listing)
        except ValueError as warning:
            log('Attempt at deleting resulted in the following warning:')
            log('    ' + str(warning))

        return post(gb, listing)

    command = sys.argv[1]
    str2func = {
        'post': post,
        'delete': delete,
        'refresh': refresh,
        'repost': repost
    }
    if command in str2func:
        func = str2func[command]

        log('Username: ', end='')
        username = input('')
        password = getpass.getpass('Password: ', sys.stderr)
        gb = GummieBot(username, password)

        owd = os.getcwd()
        root_items_dir = './items'
        item_names = [name for name in os.listdir(root_items_dir) if os.path.isdir(os.path.join(root_items_dir, name))]
        
        for item_name in item_names:
            item_dir = os.path.join(owd, root_items_dir, item_name)
            os.chdir(item_dir)
            listing = gummie_json_parse(item_dir)
            result = func(gb, listing)
            log("Result for listing '{}': {}".format(listing.title, result))

    else:
        raise ValueError("Unknown command '{}'".format(command))
