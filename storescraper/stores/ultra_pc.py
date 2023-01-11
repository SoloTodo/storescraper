import html
import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MONITOR, NOTEBOOK, TABLET, MOUSE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class UltraPc(Store):

    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            TABLET,
            MOUSE,
            MONITOR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['equipos-de-computo', NOTEBOOK],
            ['tablets-e-ipads', TABLET],
            ['monitores', MONITOR],
            ['accesorios', MOUSE],

        ]
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            url_webpage = 'https://www.ultrapc.cl/categoria-producto/{}/' \
                          '?ppp=-1'.format(url_extension)
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, 'html.parser')
            products_container = soup.find('ul', 'products')

            if not products_container:
                continue

            for cont in products_container.findAll('div', 'product-outer'):
                product_url = \
                    cont.find('a', 'woocommerce-LoopProduct-link')[
                        'href']
                product_urls.append(product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        base_name = soup.find('h1', 'product_title').text

        bundle_tag = soup.find('span', 'accesorios_sumario')
        if bundle_tag:
            base_name += ' + ' + ' '.join(bundle_tag['data-tooltip'].split())

        variants = soup.find('form', 'variations_form')
        products = []

        if variants:
            container_products = json.loads(
                html.unescape(variants['data-product_variations']))

            for product in container_products:
                variant_name = base_name + " - " + next(
                    iter(product['attributes'].values()))
                if product['is_in_stock']:
                    stock = int(product['max_qty'])
                else:
                    stock = 0
                sku = product['sku']
                key = str(product['variation_id'])
                price = Decimal(product['display_price'])
                if product['image']['src'] == '':
                    picture_urls = [tag['src'] for tag in
                                    soup.find('div', 'woocommerce-product'
                                                     '-gallery').findAll(
                                        'img')]
                else:
                    picture_urls = [product['image']['src']]
                products.append(Product(
                    variant_name,
                    cls.__name__,
                    category,
                    url,
                    url,
                    key,
                    stock,
                    price,
                    price,
                    'CLP',
                    sku=sku,
                    picture_urls=picture_urls
                ))
        else:
            key = soup.find('link', {'type': 'application/json'}
                            )['href'].split('/')[-1]
            json_data = json.loads(
                soup.findAll(
                    'script', {'type': 'application/ld+json'}
                )[1].text)['@graph'][1]
            sku = json_data['sku']
            description = json_data['description']

            if soup.find('span',
                         'electro-stock-availability').find('p', 'stock'):
                stock = -1
            else:
                stock = 0

            offer_price = Decimal(
                json_data['offers'][0]['priceSpecification']['price'])

            normal_price_tags = ['precio_oferta', 'precio_con_iva_tbk']
            for tag in normal_price_tags:
                price_tag = soup.find('span', tag)
                if price_tag:
                    normal_price = Decimal(remove_words(price_tag.text))
                    break
            else:
                raise Exception('No normal price found')

            picture_urls = [tag['src'] for tag in soup.find(
                'div', 'woocommerce-product-gallery').findAll(
                'img')]
            condition_text = soup.find(
                'span', 'condicion_item_ultrapc').text.strip()
            if condition_text == 'NUEVO' or condition_text == 'NUEVO SELLADO':
                condition = 'https://schema.org/NewCondition'
            else:
                condition = 'https://schema.org/RefurbishedCondition'

            products.append(Product(
                base_name,
                cls.__name__,
                category,
                url,
                url,
                key,
                stock,
                normal_price,
                offer_price,
                'CLP',
                sku=sku,
                picture_urls=picture_urls,
                condition=condition,
                description=description
            ))
        return products
