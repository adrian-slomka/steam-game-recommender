import os
import json
import time
import requests

from bs4 import BeautifulSoup
from bs4.element import Tag
from dotenv import load_dotenv
load_dotenv()

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By







class SteamDB:
    def __init__(self):
        self.options = Options()
        self.options.binary_location = 'C:/Program Files/Mozilla Firefox/firefox.exe'

        self.service = Service(executable_path='geckodriver.exe')
        self.driver = None


    def _build_filters(self, feature='None', display_only='None', tags=None):
        '''
        Params:
            feature (int):
            display_only (str):
            tags (list):
        '''

        feature_str = f'category={feature}&' if feature in [1, 2, 9, 888] else ''
        display_str = f'&displayOnly={display_only}' if display_only in ['Game', 'DLC'] else ''
        tags_str = '&tagid=' + '%2C'.join(map(str, tags)) if tags else ''
        return f'?{feature_str}cc=us{display_str}{tags_str}'
    


    def get_trending(self, feature: int = 0, display_only: str = 'None', tags: list = None, value=250):
        '''
        Scrapes the SteamDB trending page for app data.

        Params:
            feature (int): Can be: Multi-Player = 1, Single-Player = 2, Co-op = 9, Adult_Only = 888
            display_only (str): Can be: 'Game' or 'DLC'
            tags (list): Lists of SteamDB tag IDs: [19, 4166, 597, 122, 1684, ...] ( 19 is Action )
            value (int): Ca be: 25, 50, 100, 250, 500 or 1000; Default 250 - sets the table to display 1000 apps on SteamDB

        Returns:
            list[dict]: A list of dictionaries, each containing data for a single app
        '''
        filters = self._build_filters(feature, display_only, tags)
        url = f'https://steamdb.info/stats/trendingfollowers/{filters}'
        
        data = self.get_page(url, 'trending', value)   
        return data    



    def get_topselling(self, feature: int = 0, display_only: str = 'None', tags: list = None, value=1000):
        '''
        Scrapes the SteamDB Top CURRENTLY Global Selling Games page for app data.

        Params:
            feature (int): Can be: Multi-Player = 1, Single-Player = 2, Co-op = 9, Adult_Only = 888
            display_only (str): Can be: 'Game' or 'DLC'
            tags (list): Lists of SteamDB tag IDs: [19, 4166, 597, 122, 1684, ...] ( 19 is Action )
            value (int): Ca be: 25, 50, 100, 250, 500 or 1000; Default 1000 - sets the table to display 1000 apps on SteamDB

        Returns:
            list[dict]: A list of dictionaries, each containing data for a single app
        '''
        filters = self._build_filters(feature, display_only, tags)
        url = f'https://steamdb.info/stats/globaltopsellers/{filters}'
        
        data = self.get_page(url, 'topselling', value)   
        return data 



    def get_toprated(self, feature: int = 0, display_only: str = 'None', tags: list = None, value=1000):
        '''
        Scrapes the SteamDB top rated page for app data.

        Params:
            feature (int): Can be: Multi-Player = 1, Single-Player = 2, Co-op = 9, Adult_Only = 888
            display_only (str): Can be: 'Game' or 'DLC'
            tags (list): Lists of SteamDB tag IDs: [19, 4166, 597, 122, 1684, ...] ( 19 is Action )
            value (int): Ca be: 25, 50, 100, 250, 500 or 1000; Default 1000 - sets the table to display 1000 apps on SteamDB

        Returns:
            list[dict]: A list of dictionaries, each containing data for a single app
        '''
        filters = self._build_filters(feature, display_only, tags)
        url = f'https://steamdb.info/stats/gameratings/{filters}&min_reviews=500'
        
        data = self.get_page(url, 'toprated', value)   
        return data 



    def get_mostwishlisted(self, feature: int = 0, display_only: str = 'None', tags: list = None, value=1000):
        '''
        Scrapes the SteamDB most wishlisted page for app data.

        Params:
            feature (int): Can be: Multi-Player = 1, Single-Player = 2, Co-op = 9, Adult_Only = 888
            display_only (str): Can be: 'Game' or 'DLC'
            tags (list): Lists of SteamDB tag IDs: [19, 4166, 597, 122, 1684, ...] ( 19 is Action )
            value (int): Ca be: 25, 50, 100, 250, 500 or 1000; Default 1000 - sets the table to display 1000 apps on SteamDB

        Returns:
            list[dict]: A list of dictionaries, each containing data for a single app
        '''
        filters = self._build_filters(feature, display_only, tags)
        url = f'https://steamdb.info/stats/mostwished/{filters}'
        
        data = self.get_page(url, 'mostwishlisted', value)   
        return data 



    def get_tags(self):
        '''
        Scrapes the SteamDB tags page for all user tags.

        This method uses Selenium to open tags URL and parses it with BeautifulSoup.

        Returns:
            list[dict]: A list of dictionaries, each containing tag and it's SteamDB id:
                {
                    "tag": str          # tag name
                    "id": int           # SteamDB tag id
                    "label_count": int  # Amount of entries under that label
                }
        '''
        url = f'https://steamdb.info/tags/'

        try:
            # Open the page and maximize window
            self.driver = webdriver.Firefox(service=self.service, options=self.options)
            try:
                self.driver.get(url)
                self.driver.maximize_window()
                # Wait for page to load
                time.sleep(.5)
                html = self.driver.page_source
            except Exception as e:
                print(e)
            finally:
                self.driver.quit()
        except Exception as driver_creation_error:
            print(f"Failed to start the driver: {driver_creation_error}")

        soup = BeautifulSoup(html, 'html.parser')
        items = soup.find_all('div', {'class': 'label'})

        tags = []
        for item in items:
            a_tag = item.find("a")

            # Tag name (after the <span>)
            tag_name = a_tag.get_text(strip=True).replace(a_tag.find("span").get_text(strip=True), '').strip()

            # Tag ID from href
            tag_href = a_tag['href']
            tag_id = tag_href.split('/')[2]  # '/tag/4166/?min_reviews=500'

            # Label count (e.g., 100693)
            label_count_tag = item.find("span", class_="label-count")
            label_count = label_count_tag.get_text(strip=True) if label_count_tag else "0"

            tag = {
                'tag': str(tag_name),
                'id': int(tag_id),
                'label_count': int(label_count)
                }
 
            tags.append(tag)
        return tags



    def get_page(self, url, section=None, value=1000):
        '''
        Scrapes the SteamDB page for app data.

        This method uses Selenium to open a given method URL,
        sets the table to display X entries, extracts the page HTML, and parses it with BeautifulSoup.

        Parameters:
            url (str): html to the site
            section (str): Optional - will set is_trending (str: trending) or is_topselling (str: topselling) for those items in the dict list
            value (int): Ca be: 25, 50, 100, 250, 500 or 1000; Default 1000 - sets the table to display 1000 apps on SteamDB

        Returns:
            list[dict]: A list of dictionaries, each containing data for a single app:
                {
                    'appid': int,                     # App ID
                    'is_trending': int,
                    'is_toprated': int,
                    'is_topselling': int,
                    'is_mostwishlisted': int,
                    'position': int,
                    'name': str,
                    'discount': int,
                    'price': int,
                    'rating': int,
                    'follows': int,
                }
        '''

        correct_values = [25, 50, 100, 250, 500, 1000]
        if value not in correct_values:
            print('Incorrect Value! Using default: 1000 --> SteamDB().get_page()')
            value = 1000

        # Open the page and maximize window
        try:
            self.driver = webdriver.Firefox(service=self.service, options=self.options)
            try:
                self.driver.get(url)
                self.driver.maximize_window()
                time.sleep(.4)

                element = self.driver.find_element(By.CSS_SELECTOR, 'select[id="dt-length-0"]')
                element.click()
                element = self.driver.find_element(By.CSS_SELECTOR, f'option[value="{value}"]')
                element.click()

                html = self.driver.page_source
            except Exception as e:
                print(e)
            finally: # ALWAYS quit the driver
                self.driver.quit()
        except Exception as driver_creation_error:
            print(f"Failed to start the driver: {driver_creation_error}")


        soup = BeautifulSoup(html, 'html.parser')
        items = soup.find_all('tr', {'class': 'app'})

        is_trending = int(section == 'trending')
        is_toprated = int(section == 'toprated')
        is_topselling = int(section == 'topselling')
        is_mostwishlisted = int(section == 'mostwishlisted')

        apps = []
        if not items:
            print('erorr no items')
            return apps
        
        for item in items:
            
            app = {
                'appid': int(item.get('data-appid', 0)),
                }
            
            # Filter out NavigableStrings
            tags_only = [tag for tag in item if isinstance(tag, Tag)]

            # Follows table like strcutre (from SteamDB), first col (0) is Nr, second col (1) is img, third col (2) is name... etc 
            for i, tag in enumerate(tags_only, start=0):
                if i == 0:
                    app['is_trending'] = int(tag.get('data-sort', 0)) if is_trending else 0
                    app['is_toprated'] = int(tag.get('data-sort', 0)) if is_toprated else 0
                    app['is_topselling'] = int(tag.get('data-sort', 0)) if is_topselling else 0
                    app['is_mostwishlisted'] = int(tag.get('data-sort', 0)) if is_mostwishlisted else 0

                elif i == 2:
                    a_tag = tag.find('a')
                    app['name'] = a_tag.get_text(strip=True) if a_tag else ''
                elif i == 3:
                    app['discount'] = int(tag.get('data-sort', 0))
                elif i == 4:
                    app['price'] = int(tag.get('data-sort', -1)) if str(tag.get('data-sort', -1)).isdigit() else -1
                elif i == 5:
                    app['rating'] = round(float(tag.get('data-sort', 0)))
                elif i == 6:
                    app['release'] = int(tag.get('data-sort', 0))
                elif i == 7:
                    app['follows'] = int(tag.get('data-sort', 0))

            apps.append(app)
        return apps


class SteamAPI:
    def __init__(self):
        self.API_KEY: str = os.getenv('API_KEY')


    def get_pages_steamspy(self, start: int = 0, end: int = 1) -> list[dict]:
        '''
        Fetches multiple pages of app data from the SteamSpy API. (60s polling limit)

        Params:
            start (int): The starting page number (inclusive). Default is 0.
            end (int): The ending page number (exclusive). Default is 1.

        Returns:
            list[dict]: A list of dictionaries, each containing 'appid' and 'name' of the apps.

        Notes:
            - Fetches data page-by-page from SteamSpy using the "all" request type.
            - Retries requests on failure using self.fetch_with_retry().
            - Waits 60 seconds between each request to avoid hitting API rate limits.
            - Stops early if an empty or invalid response is received.
        '''
        data = []
        i = start
        for i in range(i, end):
            print(f'SteamAPI: fetching data, page {i+1}/{end}', end=' -- ')
            url = f'https://steamspy.com/api.php?request=all&page={i}'

            try:
                results = self.fetch_with_retry(url, 2, 60, 1)
            except Exception as e:
                print(f'request failed: --> get_pages_steamspy() ', e)
                results = {}

            if not results or not isinstance(results, dict):
                print(f'no more data at page {i}. Stopping. --> get_pages_steamspy() ')
                break

            for item in results.values():
                data.append({
                    'appid': int(item.get('appid')),
                    'name': str(item.get('name')),
                })

            print('done')

        return data


    def get_all_apps(self):
        '''
        Retrieve all Steam app IDs via Oficial Steam API.

        Returns:
            List of dictionaries, each representing a game
        '''

        url = 'https://api.steampowered.com/ISteamApps/GetAppList/v2/'

        try:
            results = self.fetch_with_retry(url)
        except Exception as e:
            print('ERROR SteamAPI: request failed:', e)
            results = {}

        data = []
        if results:
            for item in results.get('applist').get('apps'):
                if item.get('name'):
                    data.append(item)
            return data
        return {}
          

    def get_user_library(self, SteamID: int):
        '''
        Retrieve user's Steam game library from the Steam API.

        Parameters:
            SteamID (int): The user's 64-bit Steam ID.

        Returns:
            list: A list of dictionaries, each representing a game.
        '''

        if not self.API_KEY:
            raise ValueError("API key is not set.")
        
        url: str = f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={self.API_KEY}&steamid={SteamID}&include_appinfo=true'

        try:
            results = self.fetch_with_retry(url, retries=2, delay=.7, backoff=10)
        except Exception as e:
            print(f'ERROR SteamAPI: get_user_library() request failed. SteamID: {SteamID};', e)
            results = {}
            
        return results.get('response').get('games')
    

    def get_app_details(self, appid: int):
        '''
        Retrieve app details from the SteamSpy API.

        Parameters:
            appid (int): The app's unique Steam ID.

        Returns:
            dict: Dictionary containing details of the app. Example structure:
                {
                    'appid': int,                     # App ID
                    'name': str,                      # App name
                    'requested_details': 1,           # 
                    'genre': list[str],               # List of genres
                    'tags': list[str]                 # List of tags
                }
        '''

        url = f'https://steamspy.com/api.php?request=appdetails&appid={appid}'

        print('fetching details for ID:', appid, end=' -- ')
        try:
            results = self.fetch_with_retry(url)
        except Exception as e:
            print(f'FAILED.', e) 
            results = {}

        if results:
            genres = [g.strip() for g in (results.get('genre') or '').split(',') if g.strip()]
            tags = list(results.get('tags', {}).keys()) if isinstance(results.get('tags'), dict) else []

            if not genres:
                genres = self._genres_fallback(appid)

            data = {
                'appid': int(results.get('appid', 0)),
                'name': str(results.get('name', 0)),
                'requested_details': 1,
                'genres': genres,
                'tags': tags,
            }

            
            print('SUCCESS.' if genres and tags else 'INCOMPLETE.')
            return data
        
        print('FAILED.')
        return {}


    def _genres_fallback(self, appid):
        '''
        Fallback for retriving app genres. Retrieve app details from the official SteamAPI (undocumented).

        Returns:
            genres (list): A list of genres.
        '''
        url = f'https://store.steampowered.com/api/appdetails?appids={appid}'
        redirect_url = f'https://store.steampowered.com/app/{appid}'

        try:
            # response = requests.get(url)
            results = self.fetch_with_retry(url, 1, .2, 10)
        except Exception as e:
            print(f'error --> _genres_tags_fallback()', e, end=' ') 

        results = results.get(str(appid), {}).get('data') if results else {}
        if not results:
            try:
                response = requests.get(redirect_url, allow_redirects=True)
                if not response.history or response.status_code != 200:
                    return []
                
                new_url = response.url
                try:
                    new_appid = new_url.split('/app/')[1].split('/')[0]
                except IndexError:
                    print('redirect error (Index out of range) --> _genres_tags_fallback()', end=' ')
                    return []
                
                
                time.sleep(.7)
                url = f'https://store.steampowered.com/api/appdetails?appids={new_appid}'
                results = self.fetch_with_retry(url, 1, .2, 10)
                results = results.get(str(new_appid)).get('data')

                if not results:
                    return []

            except Exception as e:
                print('redirect error --> _genres_tags_fallback()', e, end=' ')
        
        genres = [genre.get('description') for genre in results.get('genres', [])]
        return genres


    def fetch_with_retry(self, url, retries=4, delay=1.1, backoff=5):
        '''
        Makes a GET request to the given URL with retry logic.

        Parameters:
            url (str): The API endpoint to fetch.
            retries (int): Number of retry attempts.
            delay (float): Initial delay between attempts.
            backoff (float): Multiplier for delay after each failed attempt.

        Returns:
            dict: The resulting JSON data or empty dict on failure or malformed response.
        '''
        
        for attempt in range(retries):
            time.sleep(delay)
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Attempt failed ({attempt+1}/{retries}), next after {delay * backoff}s: Status code {response.status_code}", end='; ')
            except Exception as e:
                print(f"Attempt {attempt+1}: Request failed - {e}")
                return {}
            delay *= backoff
        return {}



if __name__ == "__main__":
    pass