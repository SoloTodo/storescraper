import urllib

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class NewGame(Store):
    @classmethod
    def categories(cls):
        return [
            'Mouse',
            'Keyboard',
            'KeyboardMouseCombo',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['accion=hijo&plt=pc&cat=14', 'Mouse'],
            ['accion=hijo&plt=pc&cat=15', 'Keyboard'],
            ['accion=hijo&plt=pc&cat=29', 'KeyboardMouseCombo'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'https://www.newgame.cl/index.php?' + category_path
            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
            product_cells = soup.findAll('a', 'juego')

            if not product_cells:
                raise Exception('Empty category: {}'.format(category_url))

            for product_cell in product_cells:
                product_url = 'https://www.newgame.cl/' + product_cell['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('div', 'detalle-nombre').text.strip()

        sku = urllib.parse.parse_qs(
            urllib.parse.urlparse(url).query)['type'][0]

        stock_text = soup.find('div', 'stock').find(
            'span').text.split(':')[1].strip()

        if stock_text == 'Disponible':
            stock = -1
        else:
            stock = 0

        offer_price = soup.findAll('div', 'preciobig')[1].find('span')
        offer_price = Decimal(remove_words(offer_price.text))

        normal_price = soup.findAll('div', 'preciobig')[0].find('span')
        normal_price = Decimal(remove_words(normal_price.text))

        if offer_price > normal_price:
            offer_price = normal_price

        description = html_to_markdown(
            str(soup.find('div', 'contenido-juego')))

        pictures_container = soup.find('div', 'nivoSlider')

        if pictures_container:
            picture_urls = [tag['src'] for tag in
                            pictures_container.findAll('img')]
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
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
