from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, \
    session_with_proxy


class NiceOne(Store):
    preferred_discover_urls_concurrency = 1
    preferred_products_for_url_concurrency = 1

    @classmethod
    def categories(cls):
        return [
            'StorageDrive',
            'ComputerCase',
            'AllInOne',
            'Keyboard',
            'Headphones',
            'Motherboard',
            'Monitor',
            'Processor',
            'VideoCard',
            'Ram',
            'PowerSupply',
            'Monitor,'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_urls = [
            ['22-discos-duros', 'StorageDrive'],
            ['24-gabinetes', 'ComputerCase'],
            # ['26-computadores-armados', 'AllInOne'],
            ['29-mouse-teclados', 'Keyboard'],
            # ['32-parlantes-audio', 'Headphones'],
            ['33-placas-madre', 'Motherboard'],
            # ['28-monitores', 'Monitor'],
            ['34-procesadores', 'Processor'],
            ['39-tarjetas-graficas', 'VideoCard'],
            ['27-memorias', 'Ram'],
            ['23-fuentes-de-poder', 'PowerSupply'],
            ['28-monitores', 'Monitor'],
        ]

        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) ' \
            'AppleWebKit/537.36 (KHTML, like Gecko) ' \
            'Chrome/80.0.3987.149 ' \
            'Safari/537.36'

        product_urls = []
        for category_path, local_category in category_urls:
            if local_category != category:
                continue

            page = 1

            while True:
                page_url = 'https://n1g.cl/Home/{}?page={}'.format(
                    category_path, page)

                if page > 10:
                    raise Exception('page overflow: ' + page_url)

                soup = BeautifulSoup(session.get(page_url).text, 'html.parser')

                product_cells = soup.findAll('article', 'product-miniature')

                if not product_cells:
                    if page == 1:
                        raise Exception('Empty category: {}'.format(
                            category_path))

                    break

                for cell in product_cells:
                    product_url = cell.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) ' \
            'AppleWebKit/537.36 (KHTML, like Gecko) ' \
            'Chrome/80.0.3987.149 ' \
            'Safari/537.36'

        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')
        name = soup.find('h1').text.strip()
        sku = soup.find('input', {'name': 'id_product'})['value']

        add_to_cart_button = soup.find('div', 'product-add-to-cart').find(
            'button', 'add-to-cart')
        availability_text = soup.find(
            'span', {'id': 'product-availability'}).text.strip()

        if 'disabled' in add_to_cart_button.attrs:
            stock = 0
        elif 'A PEDIDO' in availability_text.upper():
            stock = 0
        else:
            stock = -1

        normal_price = soup.find('span', 'regular-price').text
        normal_price = Decimal(normal_price.replace(
            '\xa0$', '').replace('.', ''))
        offer_price = Decimal(soup.find(
            'span', {'itemprop': 'price'})['content'])
        description = html_to_markdown(str(soup.find('div', 'product_desc')))
        pictures_containers = soup.findAll('img', 'js-thumb')

        if pictures_containers:
            picture_urls = [x['data-image-large-src'] for x in
                            pictures_containers]
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
