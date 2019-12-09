import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Raenco(Store):
    @classmethod
    def categories(cls):
        return [
            'Television',
            'StereoSystem',
            'Cell',
            'Refrigerator',
            'Oven',
            'AirConditioner',
            'WashingMachine',
            'Stove',
            'Projector',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('tecnologia/tv.html', 'Television'),
            ('tecnologia/tv/tv-led-hd-fhd.html', 'Television'),
            ('tecnologia/tv/tv-4k.html', 'Television'),
            ('tecnologia/tv/tv-qled.html', 'Television'),
            ('tecnologia/audio-hogar/equipos-de-sonido.html', 'StereoSystem'),
            ('tecnologia/celulares.html', 'Cell'),
            ('tecnologia/celulares/8-gb.html', 'Cell'),
            # ('tecnologia/celulares/16-gb.html', 'Cell'),
            ('tecnologia/celulares/32-gb.html', 'Cell'),
            ('tecnologia/celulares/64-gb.html', 'Cell'),
            ('tecnologia/celulares/128-gb.html', 'Cell'),
            ('tecnologia/celulares/256-gb.html', 'Cell'),
            ('hogar/linea-blanca/refrigeradoras.html', 'Refrigerator'),
            ('hogar/linea-blanca/refrigeradoras/puerta-horizontal.html',
             'Refrigerator'),
            ('hogar/linea-blanca/refrigeradoras/puerta-vertical.html',
             'Refrigerator'),
            ('hogar/linea-blanca/lavadoras.html', 'WashingMachine'),
            ('hogar/linea-blanca/lavadoras/semi-automatica.html',
             'WashingMachine'),
            ('hogar/linea-blanca/lavadoras/centro-de-lavado.html',
             'WashingMachine'),
            ('hogar/linea-blanca/lavadoras/automatica.html',
             'WashingMachine'),
            ('hogar/linea-blanca/secadoras.html', 'WashingMachine'),
            ('hogar/linea-blanca/secadoras/secadoras-a-gas.html',
             'WashingMachine'),
            ('hogar/linea-blanca/secadoras/secadoras-electricas.html',
             'WashingMachine'),
            ('hogar/aires-acondicionados.html', 'AirConditioner'),
            ('hogar/linea-blanca/electrodomesticos/microondas.html', 'Oven'),
            ('hogar/linea-blanca/hornos-empotrables.html', 'Oven'),
            ('hogar/linea-blanca/estufas.html', 'Stove'),
            # ('hogar/linea-blanca/estufas/estufas-electricas.html', 'Stove'),
            ('hogar/linea-blanca/estufas/estufas-empotrables.html', 'Stove'),
            ('hogar/linea-blanca/estufas/de-mesa-a-gas-y-electricas.html',
             'Stove'),
            ('hogar/linea-blanca/estufas/a-gas-de-20-y-24-pulgadas.html',
             'Stove'),
            ('hogar/linea-blanca/estufas/a-gas-de-30-y-36-pulgadas.html',
             'Stove'),
        ]

        session = session_with_proxy(extra_args)

        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            page = 1
            local_urls = []
            done = False

            while True:
                if page >= 15:
                    raise Exception('Page overflow')

                url = 'https://raenco.com/index.php/departamentos/{}?p={}'\
                    .format(category_path, page)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                product_containers = soup.findAll('div', 'border-products')

                if not product_containers and page == 1:
                    raise Exception('Empty section {}'.format(category_path))

                for container in product_containers:
                    product_url = container.find('a')['href']
                    if product_url in local_urls:
                        done = True
                        break

                    local_urls.append(product_url)

                if done:
                    break

                product_urls.extend(local_urls)

                page += 1

        return list(set(product_urls))

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url, allow_redirects=False)

        if response.status_code in [303, 500]:
            return []

        data = response.text

        if 'fatal error' in data.lower():
            return []

        soup = BeautifulSoup(data, 'html.parser')

        name = soup.find('div', 'product-name').find('h1').text.strip()
        sku = soup.find('div', 'product-name').find('p')\
            .text.replace('Código del producto', '').strip()
        stock = -1

        price_container = soup.find('div', 'price-box')\
            .find('span', 'regular-price')

        if not price_container:
            price_container = soup.find('div', 'price-box')

        if price_container.find('del'):
            price = price_container.find(
                'span', 'price').text.strip().split(' ')[-1]
        else:
            price = price_container.find('span', 'price').text

        price = Decimal(price.replace('$', '').replace(',', ''))

        images = soup.find('div', 'product-image-gallery').findAll('img')

        picture_urls = [i['src'] for i in images]

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
            picture_urls=picture_urls
        )

        return [p]
