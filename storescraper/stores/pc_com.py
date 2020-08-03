import urllib

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class PcCom(Store):
    @classmethod
    def categories(cls):
        return [
            'Processor',
            'Ram',
            'VideoCard',
            'SolidStateDrive',
            'ExternalStorageDrive',
            'PowerSupply',
            'ComputerCase',
            'Headphones',
            'Monitor',
            'Mouse',
            'Keyboard',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['procesadores', 'Processor'],
            ['memorias-ram', 'Ram'],
            ['tarjetas-de-video', 'VideoCard'],
            ['unidades-de-estado-solido', 'SolidStateDrive'],
            ['discos-duros/discos-duros-externos', 'ExternalStorageDrive'],
            ['fuentes-de-poder', 'PowerSupply'],
            ['gabinetes', 'ComputerCase'],
            ['audio/audifonos-gamer', 'Headphones'],
            ['audio/audifonos-bluetooth', 'Headphones'],
            ['audio/audifonos-in-ear', 'Headphones'],
            ['monitores-y-accesorios/monitores', 'Monitor'],
            ['perifericos/mouse-alambricos', 'Mouse'],
            ['perifericos/mouse-inalambricos', 'Mouse'],
            ['zona-gamers/mouse-gamers', 'Mouse'],
            ['perifericos/teclado-alambricos', 'Keyboard'],
            ['perifericos/teclado-inalambricos', 'Keyboard'],
            ['zona-gamers/teclados-mecanicos', 'Keyboard'],
            ['zona-gamers/teclados-membrana', 'Keyboard'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1
            done = False

            while not done:
                if page > 10:
                    raise Exception('Page overflow')

                url = 'https://pccom.cl/categoria-producto/{}/page/{}/'\
                    .format(category_path, page)
                response = session.get(url)

                soup = BeautifulSoup(response.text, 'html.parser')
                products = soup.findAll('li', 'product')

                if not products:
                    if page == 1:
                        raise Exception('Empty path: {}'.format(url))
                    break

                for product in products:
                    product_url = product.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', 'product_title').text.strip()
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('=')[1]

        stock = 0
        if soup.find('p', 'stock').text == 'Hay existencias':
            stock = -1

        price_container = soup.find('p', 'price')
        if price_container.find('ins'):
            price_container = price_container.find('ins')

        price = Decimal(remove_words(price_container.text))
        picture_containers = soup.findAll(
            'div', 'woocommerce-product-gallery__image')

        picture_urls = [ic.find('img')['src'] for ic in picture_containers if ic['data-thumb']]

        description = html_to_markdown(
            str(soup.find('div', 'woocommerce-Tabs-panel--description')))

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
