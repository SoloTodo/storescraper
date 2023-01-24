from decimal import Decimal
import logging
from bs4 import BeautifulSoup
from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import check_ean13, html_to_markdown, \
    session_with_proxy


class Metro(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Only returns LG products

        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        product_urls = []

        page = 1
        while True:
            if page > 20:
                raise Exception('Page overflow')

            url_webpage = 'https://www.metro.pe/buscapagina?ft=lg&PS=18&sl=1' \
                '9ccd66b-b568-43cb-a106-b52f9796f5cd&cc=18&sm=0&PageNumber=' \
                '{}&O=OrderByScoreDESC'.format(page)
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html.parser')

            product_containers = soup.findAll('div', 'product-item')
            if not product_containers:
                if page == 1:
                    logging.warning('Empty category')
                break
            for container in product_containers:
                product_urls.append(container.find('a')['href'])
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        key_input = soup.find('input', {'id': '___rc-p-id'})
        if not key_input:
            return []

        key = key_input['value']
        product_info = session.get('https://www.metro.pe/api/catalog_'
                                   'system/pub/products/search/'
                                   '?fq=productId:' + key).json()[0]

        name = product_info['productName']
        sku = product_info['productReference']

        item_data = product_info['items'][0]

        for seller in item_data['sellers']:
            if seller['sellerId'] == '1' or seller['sellerId'] == 'metrope':
                metro_seller = seller
                break
        else:
            return []

        stock = metro_seller['commertialOffer']['AvailableQuantity']
        normal_price = Decimal(str(metro_seller['commertialOffer']['Price']))

        # TODO: get correct offer price "Tienda Cencosud"
        offer_price = normal_price

        picture_urls = [i['imageUrl'].split('?')[0]
                        for i in item_data['images']]

        if check_ean13(item_data['ean']):
            ean = item_data['ean']
        else:
            ean = None

        description = product_info.get('description', None)
        if description:
            description = html_to_markdown(description)

        part_number = product_info.get('Modelo', None)
        if part_number:
            part_number = part_number[0]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            normal_price,
            offer_price,
            'PEN',
            sku=sku,
            picture_urls=picture_urls,
            ean=ean,
            description=description,
            part_number=part_number,
        )
        return [p]
