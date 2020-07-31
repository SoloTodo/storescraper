from bs4 import BeautifulSoup
from decimal import Decimal

import requests

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, HeadlessChrome, PhantomJS

# Disable some SSL verifications because Intcomex uses a vulnerable SSL
# implementation
requests.packages.urllib3.disable_warnings()
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'

class Intcomex(Store):
    SESSION_COOKIES = None

    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'AllInOne'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ('cpt.notebook', 'Notebook'),  # Portatiles
            ('cpt.ultrabook', 'Notebook'),  # Ultrabooks
            ('cpt.allone', 'AllInOne'),  # all-en-uno
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'http://store.intcomex.com/es-XCL/Products/' \
                           'ByCategory/{}?rpp=1000'.format(category_path)

            print(category_url)

            soup = cls._retrieve_page(session, category_url, extra_args)

            product_containers = soup.findAll('div', 'productArea')

            if not product_containers:
                raise Exception('Empty category: ' + category_url)

            for container in product_containers:
                product_url = 'http://store.intcomex.com' + \
                              container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = cls._retrieve_page(session, url, extra_args)

        pricing_area = soup.find('div', 'productArea')

        if not pricing_area:
            return []

        name = pricing_area.find('div', 'title')['data-productname'].strip()
        sku, part_number = [tag.text.strip() for tag in pricing_area.findAll(
            'span', 'font-bold')]

        price_area = soup.find('div', 'linkArea').find('div', 'font-price')

        if not price_area:
            return []

        price = Decimal(price_area.text.split('$')[1].replace(
            '.', '').replace(',', '.'))

        description = ''

        for panel_id in ['tabs-1', 'tabs-2']:
            panel = soup.find('div', {'id': panel_id})
            if panel:
                description += html_to_markdown(str(panel)) + '\n\n'

        picture_containers = soup.find(
            'div', 'swiper-wrapper')

        picture_urls = None

        if picture_containers:
            tags = picture_containers.findAll('img', 'img-thumb')

            if tags:
                picture_urls = []
                for tag in tags:
                    picture_url = tag['rel'].replace(' ', '%20')
                    if 'http' not in picture_url:
                        picture_url = 'http://store.intcomex.com' + picture_url
                    picture_urls.append(picture_url)

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            -1,
            price,
            price,
            'USD',
            sku=sku,
            part_number=part_number,
            description=description,
            picture_urls=picture_urls
        )

        return [p]

    @classmethod
    def _retrieve_page(cls, session, url, extra_args, refresh=False):
        cookies = cls._session_cookies(extra_args, refresh)
        response = session.get(url, cookies=cookies, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')

        if not soup.find('span', {'id': 'lblTicker'}):
            if refresh:
                raise Exception('Invalid username / password')
            else:
                return cls._retrieve_page(session, url, extra_args,
                                          refresh=True)
        else:
            return soup

    @classmethod
    def _session_cookies(cls, extra_args, refresh=True):
        if not cls.SESSION_COOKIES or refresh:
            # We use Phantom because of a weird SSl error on Chrome
            with PhantomJS() as driver:
                driver.get('https://store.intcomex.com/es-XCL/Account/Login')

                driver.find_element_by_id('User').send_keys(
                    extra_args['username'])
                password_field = driver.find_element_by_id('Password')
                password_field.send_keys(extra_args['password'])
                password_field.submit()

                cookies = {}
                for cookie_entry in driver.get_cookies():
                    cookies[cookie_entry['name']] = cookie_entry['value']

                cls.SESSION_COOKIES = cookies

        return cls.SESSION_COOKIES
