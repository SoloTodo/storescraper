import json

import re
from bs4 import BeautifulSoup
from decimal import Decimal

from selenium import webdriver

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, PhantomJS


class Kabum(Store):
    SESSION_COOKIES = None

    @classmethod
    def categories(cls):
        return [
            'StorageDrive',
            'ExternalStorageDrive',
            'MemoryCard',
            'UsbFlashDrive',
            'SolidStateDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_urls = [
            ['hardware/ssd-2-5', 'SolidStateDrive'],
            ['hardware/disco-rigido-hd/externo-firewire',
             'ExternalStorageDrive'],
            ['hardware/disco-rigido-hd/externo-usb', 'ExternalStorageDrive'],
            ['hardware/disco-rigido-hd/portatil-usb', 'ExternalStorageDrive'],
            ['perifericos/pen-drive', 'UsbFlashDrive'],
            ['hardware/disco-rigido-hd/sata-3-5', 'StorageDrive'],
            ['hardware/disco-rigido-hd/sata-2-5-notebook', 'StorageDrive'],
            ['cameras-digitais/cartoes-de-memoria', 'MemoryCard'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        if not cls.SESSION_COOKIES:
            cls._session_cookies()

        for category_path, local_category in category_urls:
            if local_category != category:
                continue

            page = 1

            while True:
                category_url = 'https://www.kabum.com.br/{}?limite=100&' \
                               'pagina={}'.format(category_path, page)
                print(category_url)
                if page >= 10:
                    raise Exception('Page overflow: ' + category_url)

                soup = BeautifulSoup(
                    session.get(category_url,
                                cookies=cls.SESSION_COOKIES).content,
                    'html.parser')

                containers = soup.findAll('div', 'listagem-box')

                if not containers:
                    if page == 1:
                        raise Exception('Empty category: ' + category_url)
                    break

                for container in containers:
                    product_id = container.find('a')['data-id']
                    product_url = 'https://www.kabum.com.br/cgi-local/site/' \
                                  'produtos/descricao_ofertas.cgi?codigo=' + \
                                  product_id
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        if not cls.SESSION_COOKIES:
            cls._session_cookies()

        session = session_with_proxy(extra_args)
        page_source = session.get(
            url, cookies=cls.SESSION_COOKIES).content.decode('latin-1')

        soup = BeautifulSoup(page_source, 'html.parser')
        redirect_tag = soup.find('meta', {'http-equiv': 'refresh'})

        if redirect_tag:
            new_url = redirect_tag['content'].split('url=')[1]
            print('Redirect to: {}'.format(new_url))
            page_source = session.get(
                new_url, cookies=cls.SESSION_COOKIES).content.decode('latin-1')
            soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('p', {'itemprop': 'description'}).text.strip()[:255]
        sku = soup.find('span', {'itemprop': 'sku'}).text.strip()

        availability = soup.find('link', {'itemprop': 'availability'})

        if availability and availability['href'] != \
                'http://schema.org/InStock':
            stock = 0
        else:
            stock = -1

        normal_price_container = soup.find('div', 'preco_desconto-cm')

        if normal_price_container:
            normal_price = Decimal(
                normal_price_container.text.replace(
                    'R$', '').replace('.', '').replace(',', '.'))

            offer_price = Decimal(
                soup.find('span', 'preco_desconto_avista-cm').text.replace(
                    'R$', '').replace('.', '').replace(',', '.'))
        else:
            normal_price = Decimal(
                soup.find('div', 'preco_normal').text.replace(
                    'R$', '').replace('.', '').replace(',', '.'))
            offer_price = Decimal(soup.find(
                'meta', {'itemprop': 'price'})['content'])

        description = html_to_markdown(str(soup.find('div', 'content_tab')))

        picture_urls = [tag['src'] for tag in
                        soup.find('ul', {'id': 'imagem-slide'}).findAll('img')]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            'BRL',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]

    @classmethod
    def _session_cookies(cls):
        if not cls.SESSION_COOKIES:
            with PhantomJS() as driver:
                driver.get('https://www.kabum.com.br/')

                cookies = {}
                for cookie_entry in driver.get_cookies():
                    cookies[cookie_entry['name']] = cookie_entry['value']

                cls.SESSION_COOKIES = cookies

        return cls.SESSION_COOKIES
