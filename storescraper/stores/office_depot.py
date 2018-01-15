from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class OfficeDepot(Store):
    @classmethod
    def categories(cls):
        return [
            'ExternalStorageDrive',
            'MemoryCard',
            'UsbFlashDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        base_url = 'https://www.officedepot.com.mx'

        category_paths = [
            ['/officedepot/en/Categor%C3%ADa/Todas/C%C3%B3mputo/'
             'Almacenamiento/Discos-Duros-y-Accesorios/c/04-044-142-0',
             'ExternalStorageDrive'],
            ['/officedepot/en/Categor%C3%ADa/Todas/C%C3%B3mputo/'
             'Almacenamiento/SD%27s-y-Micro-SD%27s/c/04-044-149-0',
             'MemoryCard'],
            ['/officedepot/en/Categor%C3%ADa/Todas/C%C3%B3mputo/'
             'Almacenamiento/Memorias-USB/c/04-044-141-146', 'UsbFlashDrive'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = '{}{}?show=All'.format(base_url, category_path)

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')

            link_containers = soup.findAll('div', 'product-item')

            if not link_containers:
                raise Exception('Empty category: ' + category_url)

            for link_container in link_containers:
                product_url = base_url + link_container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('div', 'name').text.replace(
            '/ Califica este producto', '').strip()
        sku = soup.find('span', {'id': 'skuEmarsys'}).text.strip()

        if soup.find('button', {'id': 'addToCartButton'}):
            stock = -1
        else:
            stock = 0

        price_container = soup.find('span', {'id': 'priceOriginal'})

        offerprice_container = soup.find('div', 'discountedPrice')

        normal_price = price_container.text
        normal_price = Decimal(normal_price)

        if offerprice_container is None:
            offer_price = normal_price

        else:
            offer_price = offerprice_container.text.strip()
            offer_price = Decimal(offer_price.replace(
                ',', '').replace('$', ''))

        picture_container = soup.find('meta', {'name': 'twitter:image'})
        if picture_container:
            picture_urls = [picture_container['content']]
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
            'MXN',
            sku=sku,
            picture_urls=picture_urls
        )
        return [p]
