import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class TodoJuegos(Store):
    @classmethod
    def categories(cls):
        return [
            'VideoGameConsole',
            'VideoGame',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['Productos/PS4/_consolas/', 'VideoGameConsole'],
            ['Productos/PSV/_consolas//', 'VideoGameConsole'],
            ['Productos/xone/_consolas/', 'VideoGameConsole'],
            ['Productos/3DS/_consolas/', 'VideoGameConsole'],
            ['Productos/NSWI/_consolas/', 'VideoGameConsole'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'https://www.todojuegos.cl/' + category_path

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')

            link_containers = soup.findAll('div', 'foto_juego')

            if not link_containers:
                print('No products: ' + category_url)

            for link_container in link_containers:
                product_url = 'https:' + link_container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        picture_url = 'https:' + soup.find('div', 'productoEsp').find('img')[
            'src']
        picture_urls = [picture_url]
        sku = re.search(r'/(\d+)/', picture_url).groups()[0]

        name = soup.find('h1', 'titulo_juego').string

        add_to_cart_icon = soup.find('img', {'id': 'AgregarCarroImg'})

        if add_to_cart_icon:
            stock = -1
        else:
            stock = 0

        price_string = soup.find('h2', 'precio_juego').string.split('$')[1]
        price = Decimal(remove_words(price_string))

        description = ''

        for panel_class in ['infoDetalle', 'descripcionProducto']:
            description += html_to_markdown(
                str(soup.find('table', panel_class))) + '\n\n'

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
