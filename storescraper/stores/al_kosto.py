from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy, check_ean13


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
            # ['computadores-y-tablets/accesorios/accesorios-computadores/'
            #    'memorias-sd-hd/discos-duros/', 'ExternalStorageDrive'],
            ['accesorios/accesorios-computadores-tablets/'
             'accesorios-computadores/memorias-sd-hd/micro-sd', 'MemoryCard'],
            ['accesorios/accesorios-computadores-tablets/'
             'accesorios-computadores/memorias-sd-hd/memoria-usb',
             'UsbFlashDrive'],
            ['accesorios/accesorios-computadores-tablets/'
             'accesorios-computadores/memorias-sd-hd', 'MemoryCard']
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
        sku = ean
        if len(ean) == 12:
            ean = '0' + ean

        if not check_ean13(ean):
            ean = None

        description = ''

        panels = [
            soup.find('div', 'short-description std'),
            soup.find('table', {'id': 'product-attribute-specs-table'})
        ]

        for panel in panels:
            description += html_to_markdown(str(panel)) + '\n\n'

        if soup.find('p', 'in-stock'):
            stock = -1
        else:
            stock = 0

        picture_urls = []

        for picture_tag in soup.find('li', 'image-extra').findAll('img'):
            picture_urls.append(picture_tag['src'])

        product_box = soup.find('div', 'product-shop')

        price_container = product_box.find('span', {'itemprop': 'price'})

        if price_container:
            normal_price = Decimal(price_container['content'])
        else:
            price_container = product_box.findAll('span', 'price')[1]
            normal_price = Decimal(remove_words(price_container.string))

        offer_price = normal_price

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
            'COP',
            sku=sku,
            ean=ean,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
