import urllib

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import GAMING_CHAIR, HEADPHONES
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Zmart(Store):
    @classmethod
    def categories(cls):
        return [
            'VideoGameConsole',
            'Mouse',
            'Keyboard',
            'KeyboardMouseCombo',
            'StereoSystem',
            'Headphones',
            'Notebook',
            GAMING_CHAIR,
            HEADPHONES
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        base_url = 'https://www.zmart.cl'

        category_paths = [
            ['ConsolasPS4', 'VideoGameConsole'],
            ['ConsolasXBOXONE', 'VideoGameConsole'],
            ['ConsolasSwitch', 'VideoGameConsole'],
            ['Consolas3DS', 'VideoGameConsole'],
            ['Asus', 'Notebook'],
            ['logitech', 'Keyboard'],
            ['Razer', 'Mouse'],
            [37, 'Mouse'],
            [38, 'Keyboard'],
            [45, 'StereoSystem'],
            [532, GAMING_CHAIR],
            [76, HEADPHONES]
        ]

        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            if isinstance(category_path, int):
                category_url = \
                    '{}/scripts/prodList.asp?sinstock=0&idCategory={}' \
                    ''.format(base_url, category_path)

                soup = BeautifulSoup(session.get(
                    category_url, verify=False).text, 'html.parser')

                link_containers = soup.findAll('div', 'ProdBox146')

                if not link_containers:
                    raise Exception('Empty category: ' + category_url)

                for link_container in link_containers:
                    product_url = link_container.find('a')['href']
                    if 'http' not in product_url:
                        product_url = base_url + product_url
                    product_urls.append(product_url)
            else:
                category_url = base_url + '/' + category_path

                soup = BeautifulSoup(session.get(
                    category_url, verify=False).text, 'html.parser')

                link_containers = soup.findAll('div', 'BoxProductoS2')
                link_containers += soup.findAll('div', 'ProdBox240Media')
                link_containers += soup.findAll('div', 'ProdBox380_520')
                link_containers += soup.findAll('div', 'BoxProductoNotebook')

                if not link_containers:
                    raise Exception('Empty category: ' + category_url)

                for link_container in link_containers:
                    product_url = base_url + link_container.find('a')['href']
                    product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        soup = BeautifulSoup(session.get(url, verify=False).text,
                             'html.parser')

        if soup.find('img', {'src': '/productos/upload/2015/09/23/'
                                    '20150922-errorpage.jpg'}):
            return []

        name = soup.find('h1').text.strip()

        query_string = urllib.parse.urlparse(url).query
        sku = urllib.parse.parse_qs(query_string)['idProduct'][0]

        if soup.find('input', 'comprar2015'):
            stock = -1
        else:
            stock = 0

        order_type_container = soup.find(
            'div', {'id': 'ficha_producto'}).find('div', 'txTituloRef')

        if 'PREVENTA' in order_type_container.text:
            stock = 0

        price_string = soup.find('div', {'id': 'PriceProduct'})

        if not price_string:
            return []

        price_string = price_string.contents[2]

        price = Decimal(remove_words(price_string))

        description = html_to_markdown(str(soup.find('div', 'tab')),
                                       'https://www.zmart.cl')

        pictures_container = soup.find('ul', {'id': 'imageGallery'})

        if pictures_container:
            picture_urls = []

            for tag in soup.find('ul', {'id': 'imageGallery'}).findAll('li'):
                picture_path = tag['data-src'].replace(' ', '%20')
                if 'http' in picture_path:
                    continue

                picture_urls.append('https://www.zmart.cl' + picture_path)
        else:
            picture_urls = None

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
            'CLP',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
