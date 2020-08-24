from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class LadyLee(Store):
    base_url = 'https://ladylee.net'

    @classmethod
    def categories(cls):
        return [
            'Television',
            'StereoSystem',
            'Cell',
            'Refrigerator',
            'Oven',
            'WashingMachine',
            'Stove'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('television', 'Television'),
            ('parlantes-portatiles', 'StereoSystem'),
            ('equipos-de-sonido', 'StereoSystem'),
            ('teatros-en-casa', 'StereoSystem'),
            ('equipo-para-auto', 'StereoSystem'),
            ('celulares-1', 'Cell'),
            ('refrigeradoras-1-puerta', 'Refrigerator'),
            ('refrigeradoras-top-freezer', 'Refrigerator'),
            ('refrigeradoras-side-by-side', 'Refrigerator'),
            ('refrigeradoras-frech-door', 'Refrigerator'),
            ('freezers', 'Refrigerator'),
            ('estufas-electricas', 'Stove'),
            ('estufas-de-gas', 'Stove'),
            ('cooktop', 'Stove'),
            ('lavadoras-twinwash', 'WashingMachine'),
            ('lavadoras-carga-frontal', 'WashingMachine'),
            ('lavadoras-carga-superior', 'WashingMachine'),
            ('centro-de-lavado', 'WashingMachine'),
            ('secadoras', 'WashingMachine'),
            ('microondas', 'Oven'),
            ('hornos', 'Oven'),
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            page = 1

            while True:
                if page > 10:
                    raise Exception('Page overflow')

                url = '{}/collections/{}?page={}'.format(
                    cls.base_url, category_path, page)

                response = session.get(url)
                data = response.text

                soup = BeautifulSoup(data, 'html.parser')
                products = soup.findAll('div', 'main_box')

                if not products:
                    if page == 1:
                        raise Exception('Empty category: ' + url)
                    break

                for container in products:
                    product_link = container.find('a')
                    product_url = '{}{}'\
                        .format(cls.base_url, product_link['href'])
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url, allow_redirects=False)
        soup = BeautifulSoup(response.text, 'html.parser')

        sku_container = soup.find('div', 'variant-sku')
        sku = sku_container.text.split(':')[1].strip()
        model_name = soup.find('div', 'description-first-part').text.split(
            ':')[1].strip()
        title = soup.find('h1').text.strip()
        name = '{} ({})'.format(title, model_name)

        brand = soup.find('div', 'product-vendor').text.split(':')[1].strip()

        # We're only interested in LG products
        if brand == 'LG' and soup.find(
                'link', {'href': 'http://schema.org/InStock'}):
            stock = -1
        else:
            stock = 0

        price = soup.find('span', {'id': 'productPrice'})
        price = Decimal(price.text.replace('L', '').replace(',', ''))

        picture_urls = []


        for picture in soup.findAll('a', 'image-slide-link'):
            picture_url = 'https:' + picture['href']
            picture_urls.append(picture_url)

        description = html_to_markdown(str(
            soup.find('div', 'desc_blk')))

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
            'HNL',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )

        return [p]
