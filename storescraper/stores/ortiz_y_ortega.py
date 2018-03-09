from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class OrtizYOrtega(Store):
    @classmethod
    def categories(cls):
        return [
            'Refrigerator',
            'AirConditioner',
            'WaterHeater',
            'WashingMachine',
            'Stove',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['hogar/heladeras-y-freezers/heladeras', 'Refrigerator'],
            # ['hogar/heladeras-y-freezers/freezers', 'Refrigerator'],
            ['climatizacion/refrigeracion/aires-acondicionados',
             'AirConditioner'],
            ['hogar/agua-caliente/calefones-a-gas', 'WaterHeater'],
            ['hogar/lavarropas-y-secarropas', 'WashingMachine'],
            ['hogar/cocinas-hornos-y-anafes/anafes-a-gas', 'Stove'],
            ['hogar/cocinas-hornos-y-anafes/anafes-electricos', 'Stove'],
            ['hogar/cocinas-hornos-y-anafes/cocinas-a-gas', 'Stove'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'http://www.ortizyortega.com.ar/t/categorias/' + \
                           category_path
            print(category_url)

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
            containers = soup.findAll('div', 'product-list-item')

            if not containers:
                raise Exception('Empty category: ' + category_path)

            for container in containers:
                product_url = container.find('a')['href'].split('?')[0]
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 500:
            return []

        page_source = response.text
        soup = BeautifulSoup(page_source, 'html.parser')
        sku = soup.find('span', {'itemprop': 'sku'}).text.strip()

        price_string = soup.find('span', 'precio-modal-1pago').text
        price = Decimal(price_string.replace('$', '').replace(
            '.', '').replace(',', '.'))

        description = html_to_markdown(
            str(soup.find('section', 'cont-second_block')))

        main_picture_container = soup.find('img', {'id': 'bigpic'})
        picture_containers = soup.findAll('img', 'thumbnails-img')

        if picture_containers:
            picture_urls = ['http://www.ortizyortega.com.ar' +
                            container['data-zoom-image']
                            for container in picture_containers]
        elif main_picture_container:
            picture_urls = [
                'http://www.ortizyortega.com.ar' +
                main_picture_container['data-zoom-image']]
        else:
            picture_urls = None

        name = soup.find('h2', 'product_name').text.strip()

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            -1,
            price,
            price,
            'ARS',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
