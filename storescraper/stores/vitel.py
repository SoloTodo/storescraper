import urllib

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Vitel(Store):
    @classmethod
    def categories(cls):
        return [
            'Lamp',
            'LightProjector',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        base_url = 'http://www.vitel.cl/'

        category_paths = [
            # Ampolletas LED
            ['products/4/iluminacion-led/9/lamparas-led', 'Lamp'],
            # Proyectores
            ['products/4/iluminacion-led/10/proyectores-de-area',
             'LightProjector'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = base_url + category_path
            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
            product_containers = soup.findAll('div', 'c-producto')

            if not product_containers:
                raise Exception('Emtpy category: ' + category_url)

            for container in product_containers:
                product_id = container.find('div', 'c-boton-producto').find(
                    'div')['id']
                product_url = base_url + \
                    'producto_detalle.php/?idproducto=' + product_id
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')
        name = soup.find('span', 'txt-titulo-grandes').text.strip()

        query_string = urllib.parse.urlparse(url).query
        sku = urllib.parse.parse_qs(query_string)['idproducto'][0]

        price = Decimal(remove_words(soup.find(
            'span', 'texto-precio-oferta2').string))

        price *= Decimal('1.19')
        price = price.quantize(0)

        description = html_to_markdown(str(soup.find('div', 'tab_container')))

        picture_urls = ['http://www.vitel.cl/' +
                        soup.find('div', 'slides_container').find(
                            'img')['src']]

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
            'CLP',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
