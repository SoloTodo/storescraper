from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


class AlKosto(Store):
    @classmethod
    def categories(cls):
        return [
            'ExternalStorageDrive',
            'MemoryCard',
            'UsbFlashDrive',
            'StorageDrive',
            'Notebook',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        base_url = 'http://www.alkosto.com/'

        url_extensions = [
            ['computadores-y-tablets/accesorios/accesorios-computadores/'
             'memorias-sd-hd/discos-duros/', 'ExternalStorageDrive'],
            ['computadores-y-tablets/accesorios/accesorios-computadores/'
             'memorias-sd-hd/micro-sd/', 'MemoryCard'],
            ['computadores-y-tablets/accesorios/accesorios-computadores/'
             'memorias-sd-hd/memoria-usb/', 'UsbFlashDrive'],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for url_path, local_category in url_extensions:
            if local_category != category:
                continue

            category_url = base_url + url_path

            base_soup = BeautifulSoup(
                session.get(category_url).text, 'html.parser')

            link_containers = base_soup.find(
                'ul', 'products-grid')

            if not link_containers:
                raise Exception('Empty category: ' + category_url)

            link_containers = link_containers.findAll('li', 'item')

            for link_container in link_containers:
                product_url = link_container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('div', 'product-name').text.strip()
        ean = soup.find('span', {'itemprop': 'sku'}).text.strip()
        if len(ean) == 12:
            ean = '0' + ean

        description = ''

        panels = [
            soup.find('div', 'short-description std'),
            soup.find('table', {'id': 'product-attribute-specs-table'})
        ]

        for panel in panels:
            description += html_to_markdown(str(panel)) + '\n\n'

        if soup.find('link', {'itemprop': 'availability'})['href'] == \
                'http://schema.org/InStock':
            stock = -1
        else:
            stock = 0

        picture_urls = []

        for picture_tag in soup.find('li', 'image-extra').findAll('img'):
            picture_urls.append(picture_tag['src'])

        price_container = soup.find('div', 'product-shop')
        normal_price = price_container.find('span', {'itemprop': 'price'})

        # if not normal_price:
        #     normal_price = price_container.findAll('span', 'price')[-1]

        normal_price = Decimal(remove_words(normal_price.string))

        offer_price = normal_price

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            ean,
            stock,
            normal_price,
            offer_price,
            'COP',
            sku=ean,
            ean=ean,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
