from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, \
    HeadlessChrome, CF_REQUEST_HEADERS

import re


class LadyLee(Store):
    base_url = 'https://www.ladylee.net'

    @classmethod
    def categories(cls):
        return [
            'Television',
            'StereoSystem',
            'Cell',
            'Refrigerator',
            'Oven',
            'WashingMachine',
            'Stove'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('televisores', '217', 'Television'),
            # ('mini-componentes', '1066', 'StereoSystem'),
            ('celulares', '218', 'Cell'),
            ('refrigeradoras', '4551', 'Refrigerator'),
            ('microondas', '1198', 'Oven'),
            ('lavadoras', '1096', 'WashingMachine'),
            ('secadoras', '1100', 'WashingMachine'),
            ('estufas', '1095', 'Stove')
        ]

        session = cls._get_initialized_session()
        session.headers['user-agent'] = CF_REQUEST_HEADERS['User-Agent']
        product_urls = []

        for category_path, section_id, local_category in category_filters:
            if local_category != category:
                continue

            page = 1
            done = False

            while not done:
                if page > 10:
                    raise Exception('Page overflow')

                url = '{}/section/stores/{}/products?ps_{}={}'\
                    .format(cls.base_url, section_id, section_id, page)
                response = session.get(url)
                data = response.text
                html_data = re.search(r'el\.replaceWith\(\'(.*?)\'\)',
                                      data, flags=re.S).group(1)\
                    .replace('\\n', '').replace('\\', '')
                soup = BeautifulSoup(html_data, 'html.parser')

                products = soup.findAll('div', 'product')

                if products:
                    for container in products:
                        if container.find('h6', 'code').text != 'LG':
                            continue
                        product_url = '{}{}'\
                            .format(cls.base_url, container.find('a')['href'])
                        product_urls.append(product_url)
                else:
                    done = True

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = cls._get_initialized_session()
        response = session.get(url, allow_redirects=False)

        if response.status_code == 302:
            return []

        data = response.text
        soup = BeautifulSoup(data, 'html.parser')

        sku_container = soup.find('div', 'sku')
        sku = sku_container.contents[0].replace('SKU', '').strip()
        reference = sku_container.contents[2].replace('REF:', '').strip()

        name = soup.find('h1', 'heading').text.strip()

        if reference:
            name += ' ({})'.format(reference)

        stock = -1

        price = soup.find('dd', {'id': 'product-promotional-price'})
        if not price:
            price = soup.find('dd', {'id': 'product-price'})

        price = Decimal(price.text.replace('L', '').replace(',', ''))

        picture_urls = []
        pictures = soup.find('ul', 'product-image-list')

        for picture in pictures.findAll('li'):
            picture_url = '{}{}'.format(cls.base_url, picture['data-src'])
            picture_urls.append(picture_url)

        description = html_to_markdown(str(
            soup.find('div', 'product-description')))

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
            'HNL',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )

        return [p]

    @classmethod
    def _get_initialized_session(cls):
        session = session_with_proxy(None)

        with HeadlessChrome() as driver:
            agent = driver.execute_script("return navigator.userAgent")
            session.headers['user-agent'] = agent

            driver.get('https://www.ladylee.net/')
            for cookie in driver.get_cookies():
                cookie.pop('expiry', None)
                cookie.pop('httpOnly', None)
                session.cookies.set(**cookie)

        return session
