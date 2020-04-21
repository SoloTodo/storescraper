from decimal import Decimal
from bs4 import BeautifulSoup

from storescraper.store import Store
from storescraper.product import Product
from storescraper.utils import html_to_markdown, session_with_proxy


class Proglobal(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
            'Wearable',
            'Projector',
            'MemoryCard',
            'UsbFlashDrive',
            'StorageDrive',
            'SolidStateDrive',
            'ExternalStorageDrive',
            'Headphones',
            'Mouse',
            'Keyboard',
            'ComputerCase',
            'Ram',
            'PowerSupply',
            'Monitor',
            'StereoSystem'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['celulares/smartphone', 'Cell'],
            ['celulares/pulseras-inteligentes', 'Wearable'],
            # ['computacion-y-gamer/proyectores/proyectores-led', 'Projector'],
            ['computacion-y-gamer/almacenamiento/microsd-alta-velocidad',
             'MemoryCard'],
            ['computacion-y-gamer/almacenamiento/tarjetas-sd', 'MemoryCard'],
            ['computacion-y-gamer/almacenamiento/pendrives', 'UsbFlashDrive'],
            ['computacion-y-gamer/almacenamiento/discos-duros',
             'ExternalStorageDrive'],
            ['computacion-y-gamer/gamers/audifonos', 'Headphones'],
            ['computacion-y-gamer/gamers/mouse', 'Mouse'],
            ['computacion-y-gamer/gamers/teclados', 'Keyboard'],
            ['computacion-y-gamer/gamers/gabinete-para-pc', 'ComputerCase'],
            # ['computacion-y-gamer/gamers/memoria-ram', 'Ram'],
            # ['computacion-y-gamer/gamers/fuentes-de-poder', 'PowerSupply'],
            # ['computacion-y-gamer/gamers/monitores', 'Monitor'],
            ['camaras-audio-video/audio/audio-alta-fidelidad', 'StereoSystem'],
            ['camaras-audio-video/audio/audifonos-inalambricos', 'Headphones'],
            ['camaras-audio-video/audio/audifonos-alambricos', 'Headphones'],
            ['camaras-audio-video/audio/parlantes', 'StereoSystem']
        ]

        session = session_with_proxy(extra_args)
        base_url = 'https://www.proglobal.cl/{}'
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                if page > 30:
                    raise Exception('Page overflow')

                url = 'https://proglobal.cl/c/{}/pagina-{}'\
                    .format(category_path, page)
                print(url)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                product_containers = soup.findAll(
                    'div', 'producto-carrusel-home')

                if not len(product_containers):
                    if page == 1:
                        raise Exception('Empty category: {}'.format(url))
                    break

                for container in product_containers:
                    product_urls.append(
                        base_url.format(container.find('a')['href']))

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        data = session.get(url)
        soup = BeautifulSoup(data.text, 'html.parser')

        name = soup.find('h3').text
        sku = soup.find('p', 'sku').text.replace('SKU:', '').strip()

        if soup.find('a', 'notificar_stock'):
            stock = 0
        else:
            stock = -1

        price = Decimal(soup.find('span', 'precio-ficha')
                        .text.replace('Precio final:', '')
                        .replace('$', '')
                        .replace('.-', '')
                        .replace('.', '').strip())

        pictures_containers = soup.findAll('a', 'miniatura_galeria')
        base_url = 'https://www.proglobal.cl/{}'
        picture_urls = []

        for picture in pictures_containers:
            picture_url = base_url.format(picture['data-zoom'])
            picture_urls.append(picture_url)

        description = html_to_markdown(
            str(soup.find('div', {'id': 'descripcion'})))

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
            picture_urls=picture_urls,
            description=description
        )

        return [p]
