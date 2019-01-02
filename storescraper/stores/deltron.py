import requests
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, \
    InvalidSessionCookieException


class Deltron(Store):
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

        url_base = 'http://www2.deltron.com.pe/modulos/productos/items/' \
                   'ctBuscador/templates/contenedor_web_2016.php?tamPag=' \
                   '1000&GrupoLineaId='
        product_urls = []

        category_paths = [
            # ['NBK', 'Notebook'],
            ['HD', 'StorageDrive'],
            ['HDE', 'ExternalStorageDrive'],
            # ['MC&product_line=MCCF', 'MemoryCard'],
            ['MC&product_line=MCSD', 'MemoryCard'],
            ['MC&product_line=MCUS', 'UsbFlashDrive'],
        ]

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = url_base + category_path
            print(category_url)
            response = session.get(category_url, cookies=session_cookies)
            soup = BeautifulSoup(response.text, 'html.parser')

            cells = soup.findAll('div', 'container-item-busc-dg')

            if not cells:
                raise Exception('Empty category: ' + category_url)

            for cell in cells:
                product_path = cell.find('a')['href'].replace(
                    'postsql.php', 'producto.php')
                product_urls.append(
                    'http://www2.deltron.com.pe' + product_path)

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

        if 'Item  NO ENCONTRADO' in page_source:
            return []

        soup = BeautifulSoup(page_source, 'html.parser')

        if not soup.findAll('a', 'username-link'):
            raise InvalidSessionCookieException

        name = soup.find('h1', 'title-name-product').text.strip()
        sku = soup.find('span', 'sku').text.strip()
        part_number = None

        headings = soup.find('div', {'id': 'esp_tecnicas'}).findAll(
            'td', 'heading-td')

        for heading in headings:
            if heading.text.strip() == 'NÚMERO DE PARTE':
                part_number = heading.parent.findAll('td')[1].text.strip()
                break

        stocks_table = soup.find('table', {'id': 'tableWarehouse'})
        stock_cells = stocks_table.findAll('td', {'align': 'RIGHT'})[1::3]

        stock = 0

        for stock_cell in stock_cells:
            try:
                stock += int(stock_cell.string)
            except ValueError:
                stock = -1
                break

        price_container = soup.find('span', 'catalog-discount-tag').find(
            'font', 'aquiando777')
        price = Decimal(price_container.text.replace(',', ''))

        specs_container = soup.find('div', {'id': 'esp_tecnicas'})
        description = html_to_markdown(str(specs_container))

        picture_urls = [tag['data-src'] for tag in
                        soup.find('ul', {'id': 'imageGallery'}).findAll('li')]

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
            'USD',
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
            url = 'http://{}:{}@www2.deltron.com.pe/login.php'.format(
                extra_args['username'], extra_args['password'])
            session.get(url)
            cls.SESSION_COOKIES = requests.utils.dict_from_cookiejar(
                session.cookies)

        return cls.SESSION_COOKIES
