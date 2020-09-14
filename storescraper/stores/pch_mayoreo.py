import re
import urllib

import requests
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, \
    InvalidSessionCookieException


class PchMayoreo(Store):
    SESSION_COOKIES = None

    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'StorageDrive',
            'SolidStateDrive',
            'ExternalStorageDrive',
            'MemoryCard',
            'UsbFlashDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        session_cookies = cls._session_cookies(extra_args)

        product_urls = []

        category_paths = [
            ['discos-duros.html?cat=128', 'StorageDrive'],
            ['discos-duros.html?cat=131', 'SolidStateDrive'],
            ['discos-duros.html?cat=134', 'SolidStateDrive'],
            ['discos-duros.html?cat=8875', 'SolidStateDrive'],
            ['discos-duros.html?cat=5765', 'ExternalStorageDrive'],
            ['memorias.html?cat=26520', 'UsbFlashDrive'],
            ['memorias.html?cat=210', 'UsbFlashDrive'],
            ['memorias.html?cat=9628', 'UsbFlashDrive'],
            ['memorias.html?cat=233', 'MemoryCard'],
            ['memorias.html?cat=9641', 'MemoryCard'],
            ['memorias.html?cat=9647', 'MemoryCard'],
        ]

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            local_urls = []

            while True:
                category_url = 'https://www.pchmayoreo.com/index.php/' \
                               '{}&limit=25&p={}'.format(category_path, page)
                response = session.get(category_url, cookies=session_cookies)
                soup = BeautifulSoup(response.text, 'html.parser')

                cells = soup.findAll('li', 'item')

                if not cells:
                    raise Exception('Empty category: ' + category_url)

                done = False

                for cell in cells:
                    product_url = cell.find('a')['href']
                    if product_url in local_urls:
                        done = True
                        break

                    local_urls.append(product_url)
                    product_urls.append(product_url)

                if done:
                    break

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session_cookies = cls._session_cookies(extra_args)

        try:
            products = cls._products_for_url(url, category, extra_args,
                                             session_cookies)
        except InvalidSessionCookieException:
            print('Invalid session cookie, refreshing')
            session_cookies = cls._session_cookies(extra_args, refresh=True)
            products = cls._products_for_url(url, category, extra_args,
                                             session_cookies)
        return products

    @classmethod
    def _products_for_url(cls, url, category, extra_args, session_cookies):
        print(url)
        session = session_with_proxy(extra_args)
        page_source = session.get(url, cookies=session_cookies).text

        soup = BeautifulSoup(page_source, 'html.parser')

        if not soup.find('a', {'href': 'https://www.pchmayoreo.com/'
                                       'index.php/customer/account/'}):
            raise InvalidSessionCookieException

        name = soup.find('h1').text.strip()

        sku_and_part_number_text = soup.find('div', 'std').text.split('|')
        sku_text = sku_and_part_number_text[0]
        sku = re.search(r'CLAVE: (\S*)', sku_text).groups()[0]

        part_number = None

        for section in sku_and_part_number_text:
            if 'CLAVE FABRICANTE' in section:
                part_number = re.search(
                    r'CLAVE FABRICANTE: (\S*)', section).groups()[0]
                break

        stock = 0

        stock_cells = soup.findAll('div', {'title': 'Sucursal con Stock'})

        if stock_cells:
            stock_cells = stock_cells[2:]
            for cell in stock_cells:
                stock_text = cell.text.strip()
                if stock_text == 'Sin Stock':
                    continue
                stock += int(stock_text)

        price_components = soup.find('div', 'price-box').find(
            'span', 'price').text.split('&nbsp;')[0].split('\xa0')
        price = Decimal(price_components[1].replace(',', ''))

        currencies_dict = {
            'mxn': 'MXN',
            'dlls': 'USD',
        }
        currency = currencies_dict[price_components[2].strip()]

        description = html_to_markdown(str(soup.find('div', 'box-collateral')))
        picture_urls = [soup.find('p', 'product-image').find('img')['src']]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            currency,
            sku=sku,
            part_number=part_number,
            description=description,
            picture_urls=picture_urls
        )

        return [p]

    @classmethod
    def _session_cookies(cls, extra_args, refresh=False):
        if not cls.SESSION_COOKIES or refresh:
            session = session_with_proxy(extra_args)
            session.headers[
                'Content-Type'] = 'application/x-www-form-urlencoded'

            # Set initial cookies
            session.get('https://www.pchmayoreo.com/')

            url = 'https://www.pchmayoreo.com/index.php/customer/account/' \
                  'loginPost/'
            data = 'login%5Busername%5D={}&login%5Bpassword%5D={}&send=' \
                   ''.format(urllib.parse.quote(extra_args['username']),
                             urllib.parse.quote(extra_args['password']))
            response = session.post(url, data)
            if response.url != 'https://www.pchmayoreo.com/index.php/' \
                               'customer/account/':
                raise Exception('Invalid login')
            cls.SESSION_COOKIES = requests.utils.dict_from_cookiejar(
                session.cookies)

        return cls.SESSION_COOKIES
