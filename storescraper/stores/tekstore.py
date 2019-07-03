from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy

import re
import json


class Tekstore(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
            'Tablet',
            'Headphones',
            'Wearable'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('smartphones', 'Cell'),
            ('tablets', 'Tablet'),
            ('accesorios', 'Headphones')
        ]

        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            page = 1

            while True:
                if page > 10:
                    raise Exception('Page overflow')

                url = 'https://tekstore.cl/{}?p={}'.format(category_path, page)
                response = session.get(url)

                if response.status_code == 500:
                    break

                soup = BeautifulSoup(response.text, 'html.parser')

                for container in soup.findAll('div', 'product-item-info'):
                    product_url = container.find(
                        'a', 'product-item-photo')['href']

                    product_urls.append(product_url)
                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        data = session.get(url).text
        soup = BeautifulSoup(data, 'html.parser')

        name = soup.find('span', "base").text.strip()
        available = soup.find('div', 'stock available')
        stock = -1 if available else 0
        price = Decimal(soup.find(
            'span', 'price-final_price').find('span', 'price')
                        .text.replace('$', '').replace('.', ''))

        products = []

        json_containers = soup.findAll(
            "script", {"type": "text/x-magento-init"})

        reference_part_number = soup.find('div', 'product-add-form').find(
            'form')['data-product-sku']

        for json_container in json_containers:
            if "spConfig" in json_container.text:
                products = []
                product_info = json.loads(json_container.text)[
                    '#product_addtocart_form']['configurable']['spConfig']
                variant_ids_containers = product_info[
                    'attributes']['93']['options']

                for variant_id_container in variant_ids_containers:
                    variant_id = variant_id_container['products'][0]
                    variant_label = variant_id_container['label']
                    variant_images = product_info['images'][variant_id]
                    picture_urls = []
                    for image_container in variant_images:
                        picture_urls.append(image_container['full'])

                    description = \
                        'SOLO COMO REFERENCIA, PROBABLEMENTE CORRESPONDE A ' \
                        'LA VARIANTE DE OTRO COLOR: {}'.format(
                            reference_part_number)

                    products.append(
                        Product(
                            '{} - {}'.format(name, variant_label),
                            cls.__name__,
                            category,
                            url,
                            url,
                            variant_id,
                            stock,
                            price,
                            price,
                            'CLP',
                            sku=variant_id,
                            picture_urls=picture_urls,
                            description=description
                        )
                    )

                return products
            if "Magento_Catalog/js/product/view/provider" \
                    in json_container.text:
                product_info = json.loads(json_container.text)
                product_id = soup.find('div', 'product-add-form').find(
                    'input', {'name': 'product'})['value']
                product_images = product_info['*'][
                    'Magento_Catalog/js/product/view/provider']['data'][
                    'items'][product_id]['images']
                picture_urls = []
                for image_container in product_images:
                    picture_urls.append(image_container['url'])

                products.append(
                    Product(
                        '{} ({})'.format(name, reference_part_number),
                        cls.__name__,
                        category,
                        url,
                        url,
                        product_id,
                        stock,
                        price,
                        price,
                        'CLP',
                        sku=product_id,
                        part_number=reference_part_number,
                        picture_urls=picture_urls
                    )
                )

        return products
