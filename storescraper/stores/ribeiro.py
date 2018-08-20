from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Ribeiro(Store):
    @classmethod
    def categories(cls):
        return [
            'Refrigerator',
            'AirConditioner',
            'WaterHeater',
            'WashingMachine',
            'Stove',
            'UsbFlashDrive',
            'MemoryCard',
            'ExternalStorageDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            # ['heladeras-cocina-y-lavado-heladeras/_/N-cwxc56',
            # 'Refrigerator'],
            # ['aires-y-climatizacion-aire-acondicionado-aire-acondicionado-'
            #  'split/_/N-4g7p32', 'AirConditioner'],
            # ['aires-y-climatizacion-calefones-calefones-a-gas/_/N-lhc2v4',
            #  'WaterHeater'],
            # ['aires-y-climatizacion-calefones-calefones-electrico/_/N-sdg43p',
            #  'WaterHeater'],
            # ['heladeras-cocina-y-lavado-lavado-lavarropas-automatico/'
            #  '_/N-vlbaf6', 'WashingMachine'],
            # ['heladeras-cocina-y-lavado-lavado-lavarropas-semi-automatico/'
            # '_/N-1twuqgi', 'WashingMachine'],
            # ['heladeras-cocina-y-lavado-cocinas-cocinas/_/'
            #  'N-5k0lxo', 'Stove'],
            # ['heladeras-cocina-y-lavado-cocinas-anafes/_/'
            #  'N-orsxeo', 'Stove'],
            # ['heladeras-cocina-y-lavado-cocinas-anafes/_/'
            #  'N-orsxeo', 'Stove'],
            # ['celulares-informatica-y-gaming-accesorios-de-tecnologia-'
            #  'pendrives/_/N-1g03f3', 'UsbFlashDrive'],
            ['televisores-audio-foto-y-video-foto-y-video-memorias/'
             '_/N-1enokiq', 'MemoryCard'],
            ['celulares-informatica-y-gaming-accesorios-de-tecnologia-'
             'software-y-otros/_/N-wu7x14', 'ExternalStorageDrive'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'https://www.ribeiro.com.ar/browse/{}?Nrpp=1000' \
                           ''.format(category_path)

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
            containers = soup.findAll('span', 'atg_store_productImage')

            if not containers:
                raise Exception('Empty category: ' + category_url)

            for container in containers:
                product_url = 'https://www.ribeiro.com.ar' + \
                              container.parent['href']
                product_url = product_url.split(';jsessionid')[0]
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', 'product_name')

        if not name:
            return []

        name = name.text.strip()
        sku = soup.find('input', {'id': 'ArtId'})['value'].replace('prod', '')

        availability = soup.find('span', {'itemprop': 'availability'})

        if availability and availability['content'] == \
                'http://schema.org/InStock':
            stock = -1
        else:
            stock = 0

        normal_price = soup.find('p', 'texto_gris_indiv')

        if not normal_price:
            return []

        normal_price = Decimal(normal_price.find('span').text.replace(
            ',', '').replace('$', '').replace('.', ''))

        price_container = soup.find('span', 'prodPlanCuo')

        if not price_container:
            price_container = soup.find('span', 'precio_big_indivGris')

        offer_price = Decimal(price_container.text.replace(
            ',', '').replace('$', '').replace('.', ''))

        description = html_to_markdown(
            str(soup.find('div', {'id': 'ContenedorDescripciones'})))

        picture_urls = ['https:' + tag.find('a')['data-zoom-image'] for
                        tag in soup.findAll('div', {'id': 'imgAux'})]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            'ARS',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
