from decimal import Decimal
import logging
from bs4 import BeautifulSoup
from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import check_ean13, html_to_markdown, \
    session_with_proxy


class Multicenter(Store):
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

        url_webpage = 'https://www.multicenter.com.bo/busca?ft=Lg'
        print(url_webpage)
        data = session.get(url_webpage).text
        soup = BeautifulSoup(data, 'html.parser')
        product_containers = soup.findAll('div', 'product-box')
        if not product_containers:
            logging.warning('Empty category')
        for container in product_containers:
            product_url = container.find('a')['href']
            product_urls.append(product_url)
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
        product_info = session.get(
            'https://www.multicenter.com.bo/api/catalog_system/pub/products/se'
            'arch/?fq=productId:' + key).json()[0]

        name = product_info['productName']

        item_data = product_info['items'][0]
        sku = item_data['itemId']

        for seller in item_data['sellers']:
            if seller['sellerId'] == '1':
                promart_seller = seller
                break
        else:
            return []

        stock = promart_seller['commertialOffer']['AvailableQuantity']
        normal_price = Decimal(str(promart_seller['commertialOffer']['Price']))

        item_id = item_data['itemId']
        payload = {
            "items": [{"id": item_id, "quantity": 1, "seller": "1"}],
            "country": "PER",
        }
        offer_info = session.post('https://www.promart.pe/api/checkout/pu'
                                  'b/orderforms/simulation?sc=1', json=payload
                                  ).json()
        if offer_info['ratesAndBenefitsData']:
            teaser = offer_info['ratesAndBenefitsData']['teaser']
            if len(teaser) != 0:
                discount = teaser[0]['effects']['parameters'][-1]['value']
                offer_price = (normal_price - Decimal(discount)).quantize(0)
            else:
                offer_price = normal_price
        else:
            offer_price = normal_price

        picture_urls = [x['imageUrl'].split('?')[0]
                        for x in item_data['images']]

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
            'BOB',
            sku=sku,
            picture_urls=picture_urls,
            ean=ean,
            description=description,
            part_number=part_number,
        )
        return [p]
