from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class AmazonPrint(Store):
    preferred_products_for_url_concurrency = 3

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
        url_extensions = [
            ['informatica/amazenamento/hd/hd-interno.html', 'StorageDrive'],
            ['informatica/amazenamento/hd/hd-para-notebook.html',
             'StorageDrive'],
            ['informatica/amazenamento/hd/hd-externo.html',
             'ExternalStorageDrive'],
            ['informatica/amazenamento/ssd.html', 'SolidStateDrive'],
            ['informatica/amazenamento/pen-drive.html', 'UsbFlashDrive'],
            ['foto-filmagem/cartoes-de-memoria.html', 'MemoryCard'],
            ['informatica/amazenamento/cartao-de-memoria.html', 'MemoryCard'],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in url_extensions:
            if local_category != category:
                continue

            category_product_urls = []

            page = 1

            while True:
                if page >= 10:
                    raise Exception('Page overflow: ' + category_path)

                category_url = \
                    'http://www.amazonprint.com.br/{}?limit=45&p={}' \
                    ''.format(category_path, page)

                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')

                containers = soup.find('div', 'category-products').findAll(
                    'li', 'item')

                break_flag = False

                if not containers:
                    raise Exception('Empty category: ' + category_url)

                for container in containers:
                    product_url = container.find('a')['href']

                    if product_url in category_product_urls:
                        break_flag = True
                        break

                    category_product_urls.append(product_url)

                if break_flag:
                    product_urls.extend(category_product_urls)
                    break

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1').text.strip()

        if soup.find('link', {'itemprop': 'availability'})['href'] == \
                'http://schema.org/InStock':
            stock = -1
        else:
            stock = 0

        sku = soup.find('div', 'product-name').find('span').text.strip()

        panels = [
            soup.find('div', {'id': 'description'}),
            soup.find('div', {'id': 'additional'})
        ]

        description = '\n\n'.join([html_to_markdown(str(panel))
                                   for panel in panels])

        normal_price = soup.find('p', {'itemprop': 'price'}).text
        normal_price = Decimal(normal_price.replace('R$', '').replace(
            '.', '').replace(',', '.'))

        if stock == 0:
            offer_price = normal_price
        else:
            offer_price = soup.find('span', 't_boleto_price').text
            offer_price = Decimal(offer_price.split('$')[1].replace(
                '.', '').replace(',', '.'))

        pictures_container = soup.find('ul', 'bxslider')

        if pictures_container:
            picture_urls = [link['href']
                            for link in pictures_container.findAll('a')]
        else:
            picture_urls = [soup.find('a', 'cloud-zoom-gallery')['href']]

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
