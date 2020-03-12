from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown

import json


class GolloTienda(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
            'Television',
            'OpticalDiskPlayer',
            'AirConditioner',
            'Stove',
            'Oven',
            'WashingMachine',
            'Refrigerator',
            'StereoSystem',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # KEEPS ONLY LG PRODUCTS

        category_filters = [
            ('productos/telefonia/celulares', 'Cell'),
            ('productos/pantallas', 'Television'),
            ('productos/audio-y-video/video/reproductores',
             'OpticalDiskPlayer'),
            # ('productos/hogar/ventilacion/aire-acondicionado',
            #  'AirConditioner'),
            ('productos/linea-blanca/cocina/de-gas', 'Stove'),
            ('productos/linea-blanca/cocina/electricas', 'Stove'),
            ('productos/hogar/peque-os-enseres/hornos-y-tostadores',
             'Oven'),
            ('productos/linea-blanca/cocina/microondas', 'Oven'),
            ('productos/linea-blanca/lavanderia',
             'WashingMachine'),
            ('productos/linea-blanca/refrigeracion/refrigeradoras',
             'Refrigerator'),
            ('productos/audio-y-video/audio/minicomponentes',
             'StereoSystem'),
            ('productos/audio-y-video/audio/parlantes', 'StereoSystem')
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            page = 1
            done = False

            local_product_urls = []
            local_lg_product_urls = []

            while not done:
                if page >= 10:
                    raise Exception('Page overflow')

                url = 'https://www.gollotienda.com/{}.html?p={}.html'\
                    .format(category_path, page)

                response = session.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                container = soup.find('div', 'products')

                items = container.findAll('li', 'item')

                if items:
                    for item in items:
                        product_name = item.find(
                            'a', 'product-item-link').text.strip()
                        product_url = item.find('a')['href']

                        if product_url in local_product_urls:
                            done = True
                            break

                        local_product_urls.append(product_url)

                        if 'lg' in product_name.lower():
                            local_lg_product_urls.append(product_url)
                else:
                    if page == 1:
                        raise Exception('No products for category {}'
                                        .format(category))
                    break

                page += 1

            product_urls.extend(local_lg_product_urls)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
            return []

        data = response.text
        soup = BeautifulSoup(data, 'html.parser')

        name = soup.find('span', {'itemprop': 'name'}).text.strip()
        sku = soup.find('div', {'itemprop': 'sku'}).text.strip()

        if soup.find('div', 'stock available')\
                .find('span').text == "Disponible":
            stock = -1
        else:
            stock = 0

        price = Decimal(soup.find('span', {'data-price-type': 'finalPrice'})[
                            'data-price-amount'])

        description = html_to_markdown(
            str(soup.find('div', 'additional-attributes-wrapper')))

        description += '\n\n{}'.format(html_to_markdown(
            str(soup.find('div', 'product attribute description'))
        ))

        description += '\n\n{}'.format(html_to_markdown(
            str(soup.find('div', 'dimensions-wrapper'))
        ))

        scripts = soup.findAll('script', {'type': 'text/x-magento-init'})
        img_json_data = None

        for script in scripts:
            if 'mage/gallery/gallery' in script.text:
                img_json_data = json.loads(script.text)[
                    '[data-gallery-role=gallery-placeholder]'][
                    'mage/gallery/gallery']['data']
                break

        if not img_json_data:
            picture_urls = None
        else:
            picture_urls = [image['full'] for image in img_json_data]

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
            'CRC',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
