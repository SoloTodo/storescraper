import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import PROCESSOR, MOTHERBOARD, \
    SOLID_STATE_DRIVE, RAM, CPU_COOLER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class GameMasters(Store):
    @classmethod
    def categories(cls):
        return {
            PROCESSOR,
            MOTHERBOARD,
            SOLID_STATE_DRIVE,
            RAM,
            CPU_COOLER
        }

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['amd', PROCESSOR],
            ['procesador-amd', PROCESSOR],
            ['ryzen-3', PROCESSOR],
            ['ryzen-5', PROCESSOR],
            ['ryzen-7', PROCESSOR],
            ['asus', MOTHERBOARD],
            ['matx', MOTHERBOARD],
            ['placa-madre', MOTHERBOARD],
            ['evo-plus', SOLID_STATE_DRIVE],
            ['m-2', SOLID_STATE_DRIVE],
            ['samsung', SOLID_STATE_DRIVE],
            ['ssd', SOLID_STATE_DRIVE],
            ['memoria-ram', RAM],
            ['ventilador', CPU_COOLER]
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://www.gamemasters.cl/collections/all/' \
                              '{}?page={}'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('a', 'product-grid-item')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container['href']
                    product_urls.append(
                        'https://www.gamemasters.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', {'itemprop': 'name'}).text
        picture_urls = []
        for tag in soup.find('div', 'grid-item large--two-fifths').findAll(
                'img', attrs={'src': True}):
            picture = 'https:' + tag['src'].split('?')[0]
            picture = picture.replace('_300x300', '')
            picture = picture.replace('_580x', '')
            picture = picture.replace('_compact', '')
            if picture not in picture_urls:
                picture_urls.append(picture)
        stock = -1
        variants = soup.find('form', 'addToCartForm').findAll('option')
        if len(variants) > 1:
            products = []
            for product in variants:
                variant_name = name + ' - ' + product.text.split('-')[
                    0].strip()
                sku = product['value']
                variant_url = url + '?variant=' + sku
                price = Decimal(
                    remove_words(product.text.split('-')[1].strip()))
                p = Product(
                    variant_name,
                    cls.__name__,
                    category,
                    variant_url,
                    url,
                    sku,
                    stock,
                    price,
                    price,
                    'CLP',
                    sku=sku,
                    picture_urls=picture_urls,
                )
                products.append(p)
            return products

        else:
            sku = soup.find('span', 'stamped-product-reviews-badge '
                                    'stamped-main-badge')['data-id']
            price = Decimal(remove_words(
                soup.find('span',
                          {'id': 'productPrice-product-template'}).find(
                    'span').text))

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
                picture_urls=picture_urls,
            )
            return [p]
