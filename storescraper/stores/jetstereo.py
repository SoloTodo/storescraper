import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import TELEVISION, STEREO_SYSTEM, CELL, \
    REFRIGERATOR, OVEN, AIR_CONDITIONER, WASHING_MACHINE, STOVE, MONITOR, \
    HEADPHONES, WEARABLE, VACUUM_CLEANER, CELL_ACCESORY


class Jetstereo(Store):
    base_url = 'https://www.jetstereo.com'

    @classmethod
    def categories(cls):
        return [
            TELEVISION,
            STEREO_SYSTEM,
            CELL,
            REFRIGERATOR,
            OVEN,
            AIR_CONDITIONER,
            WASHING_MACHINE,
            STOVE,
            MONITOR,
            HEADPHONES,
            WEARABLE,
            VACUUM_CLEANER,
            CELL_ACCESORY,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = {
            'barras-de-sonido': STEREO_SYSTEM,
            'alambricos': HEADPHONES,
            'tvs': TELEVISION,
            'smartphones': CELL,
            'monitores': MONITOR,
            'wearables': WEARABLE,
            'twinwash': WASHING_MACHINE,
            'estufas-de-gas': STOVE,
            'lavadoras-top-load': WASHING_MACHINE,
            'lavadoras': WASHING_MACHINE,
            'microondas': OVEN,
            'refrigeradoras-side-by-side': REFRIGERATOR,
            'audifonos': HEADPHONES,
            'refrigeradora-top-mount': REFRIGERATOR,
            'secadoras': WASHING_MACHINE,
            'lavadora-carga-frontal': WASHING_MACHINE,
            'refrigeradoras': REFRIGERATOR,
            'aspiradoras': VACUUM_CLEANER,
            'estufas-electricas': OVEN,
            'accesorios-tv-y-video': CELL_ACCESORY,
            'equipos-de-sonido': STEREO_SYSTEM,
            'refrigeradoras-french-door': REFRIGERATOR,
            'gadget': CELL_ACCESORY,
            'estufas': OVEN,
            'aire-acondicionado': AIR_CONDITIONER
        }

        session = session_with_proxy(extra_args)
        product_urls = []
        url_subsections = 'https://www.jetstereo.com/brands/lg'
        response = session.get(url_subsections, verify=False).text
        soup = BeautifulSoup(response, 'html.parser')
        sub_sections = soup.findAll('div', 'col-6 col-lg-2')
        for sub_section in sub_sections:
            url_extension = sub_section.find('a')['href']
            category_path = url_extension.split('/')[-1]
            if category_path not in category_paths:
                raise Exception('Not {} in category paths'.format(
                    category_path))
            local_category = category_paths[category_path]
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 20:
                    raise Exception('Page overflow: ' + sub_section)
                url = 'https://www.jetstereo.com{}?page={}'.format(
                    url_extension, page)
                print(url)
                response = session.get(url, verify=False).text
                soup = BeautifulSoup(response, 'html.parser')
                product_containers = soup.findAll('div', 'product-box')

                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url)
                    break

                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')

        add_to_cart_button = soup.find(
            'div', {'id': 'Button-storeAvailability'})
        key = add_to_cart_button['data-product-id']
        sku = soup.find('span', 'id').text.strip()
        add_to_cart_button = soup.find(
            'button', {'id': 'ButtonAddCart-fixeReference'})

        if add_to_cart_button and \
                add_to_cart_button['data-available'] == 'true':
            stock = -1
        else:
            stock = 0

        name = soup.find('h4', 'name').text.strip()
        price = Decimal(soup.find('div', 'sale').text.strip().replace(
            'L. ', '').replace(',', ''))

        picture_urls = []
        pictures = soup.findAll('a', 'zoom')

        for picture in pictures:
            picture_url = picture.find('img')['src'].replace(' ', '%20')
            picture_urls.append(picture_url)

        description = html_to_markdown(str(soup.find('div', 'tecnical-specs')))

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            price,
            price,
            'HNL',
            sku=sku,
            picture_urls=picture_urls,
            description=description,
            part_number=sku
        )

        return [p]
