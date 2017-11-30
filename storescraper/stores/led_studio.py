import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class LedStudio(Store):
    @classmethod
    def categories(cls):
        return [
            'Lamp',
            'LightTube',
            'LightProjector'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            # Ampolletas LED
            ['iluminacion-led/ampolletas-led', 'Lamp'],
            # Tubos LED
            ['iluminacion-tecnica/tubos-t8', 'LightTube'],
            # Proyectores LED
            ['industrial-vialidad/proyectores', 'LightProjector'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue
            page = 1
            while True:
                category_url = 'http://ledstudio.cl/categoria-producto/' \
                               '{}/page/{}'.format(
                                 category_path, page)

                if page >= 10:
                    raise Exception('Page overflow: ' + category_url)

                response = session.get(category_url)

                if response.status_code == 404:
                    break

                soup = BeautifulSoup(response.text, 'html.parser')

                product_containers = soup.findAll('div', 'item')
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        picture_urls = [soup.find('meta', {'property': 'og:image'})['content']]
        description = html_to_markdown(
            str(soup.find('div', 'bottom-information')))

        products = []

        name = soup.find('h1').text.strip()

        variations_form = soup.find('form', 'variations_form')

        if variations_form:
            data_json = variations_form['data-product_variations']
            data_json = json.loads(data_json)
            for element in data_json:
                variant = ', '.join(['{}: {}'.format(key, value)
                                     for key, value in
                                     element['attributes'].items()])
                price = element['display_price']
                price = Decimal(price)

                stock = int(element['max_qty'] or '0')

                price = price.quantize(0)

                variant_name = '{} {}'.format(name, variant)

                sku = element['sku']

                # Pls remove the url rewrite after migrating

                url_with_variation_id = '{}?p={}'.format(
                    url, element['variation_id'])

                p = Product(
                    variant_name,
                    cls.__name__,
                    category,
                    url_with_variation_id,
                    url,
                    sku,
                    stock,
                    price,
                    price,
                    'CLP',
                    sku=sku,
                    description=description,
                    picture_urls=picture_urls
                )
                products.append(p)
        else:
            if soup.find('button', 'add_to_cart_button'):
                stock = -1
            else:
                stock = 0

            price = soup.find('meta', {'itemprop': 'price'})['content']
            price = Decimal(price).quantize(0)

            sku = soup.find('span', 'sku').text.strip()

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
                description=description,
                picture_urls=picture_urls
            )

            products.append(p)

        return products
