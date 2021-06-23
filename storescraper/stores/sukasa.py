import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy
from storescraper.categories import REFRIGERATOR, OVEN, WASHING_MACHINE, \
    TELEVISION, STEREO_SYSTEM, CELL


class Sukasa(Store):
    @classmethod
    def categories(cls):
        return [
            REFRIGERATOR,
            OVEN,
            WASHING_MACHINE,
            TELEVISION,
            STEREO_SYSTEM,
            CELL
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['4232-refrigeradoras', REFRIGERATOR],
            ['72-microondas', OVEN],
            ['93-lavadoras', WASHING_MACHINE],
            ['94-secadoras', WASHING_MACHINE],
            ['95-lavadoras-y-secadoras-todo-en-1', WASHING_MACHINE],
            ['309-televisores', TELEVISION],
            ['2849-parlantes', STEREO_SYSTEM],
            ['4248-micro-y-mini-componentes', STEREO_SYSTEM],
            ['4249-barras-de-sonido-y-teatros-en-casa', STEREO_SYSTEM],
            ['4251-celulares-y-tablets', CELL]
        ]

        session = session_with_proxy(extra_args)
        base_url = 'https://www.sukasa.com/{}?q=Marca-LG'
        product_urls = []

        for url_extension, local_category in category_paths:
            if category != local_category:
                continue

            url = base_url.format(url_extension)
            soup = BeautifulSoup(session.get(url).text, 'html.parser')
            products = soup.findAll('div', 'product-container')

            if not products:
                raise Exception('Empty path: ' + url)

            for product in products:
                product_url = product.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        variants_container = soup.find('div', 'attribute-list')
        sku = soup.find('h2', 'reference-product').text.split(':')[1].strip()
        name = soup.find('h1', 'page-heading').text.strip()

        if variants_container:
            product_id = soup.find('input', {'name': 'id_product'})['value']
            variant_ids = {x['value']: x.text for x in
                           variants_container.findAll('option')}
            ajax_session = session_with_proxy(extra_args)
            ajax_session.headers['content-type'] = \
                'application/x-www-form-urlencoded'

            products = []

            for variant_id, variant_label in variant_ids.items():
                endpoint = 'https://www.sukasa.com/index.php?controller=' \
                           'product?id_product={}&group%5B246%5D={}'.format(
                            product_id, variant_id)
                res = ajax_session.post(endpoint, 'ajax=1&action=refresh')

                if res.status_code == 502:
                    continue

                variant_data = json.loads(res.text)
                variant_soup = BeautifulSoup(
                    variant_data['product_prices'], 'html.parser')
                variant_url = variant_data['product_url']

                normal_price = Decimal(variant_soup.find(
                    'span', 'product-unit-price').text.split('$')[-1])
                offer_price = Decimal(variant_soup.find(
                    'input', {'id': 'basepricesks'})['value'])

                key = '{}_{}'.format(sku, variant_id)
                variant_name = '{} ({})'.format(name, variant_label)

                products.append(Product(
                    variant_name,
                    cls.__name__,
                    category,
                    variant_url,
                    variant_url,
                    key,
                    -1,
                    normal_price,
                    offer_price,
                    'USD',
                    sku=sku
                ))

            return products
        else:
            stock = -1

            price = Decimal(
                soup.find('span', {'itemprop': 'price'})
                    .find('span').text.replace('$', ''))

            picture_urls = [
                a['data-zoom-image'] for a in soup.findAll('a', 'thumb')]

            description = html_to_markdown(
                str(soup.find('div', {'id': 'collapseDescription'})))

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
                'USD',
                sku=sku,
                picture_urls=picture_urls,
                description=description,
            )

            return [p]
