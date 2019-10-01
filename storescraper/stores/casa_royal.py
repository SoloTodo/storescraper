from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


class CasaRoyal(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
            'Wearable',
            'Mouse',
            'Headphones',
            'StereoSystem',
            'Keyboard',
            'Printer',
            'SolidStateDrive',
            'UsbFlashDrive',
            'MemoryCard',
            'VideoGameConsole',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['telefonia/celulares/smartphones', 'Cell'],
            ['telefonia/celulares/basicos-senior', 'Cell'],
            ['telefonia/wearables', 'Wearable'],
            ['computacion/perifericos-y-adaptadores/mouse', 'Mouse'],
            ['audio/audifonos', 'Headphones'],
            ['audio/audio-hogar', 'StereoSystem'],
            # ['audio/audio-profesional/bafles', 'StereoSystem'],
            ['computacion/perifericos-y-adaptadores/teclados', 'Keyboard'],
            ['computacion/impresoras-y-tintas/impresoras', 'Printer'],
            ['computacion/almacenamiento/discos-duros', 'SolidStateDrive'],
            ['computacion/almacenamiento/pendrives', 'UsbFlashDrive'],
            ['computacion/almacenamiento/tarjetas-de-memoria', 'MemoryCard'],
            ['computacion/gamers/consolas', 'VideoGameConsole']
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in url_extensions:
            if local_category != category:
                continue

            done = False
            page = 1

            while not done:
                if page >= 15:
                    raise Exception('Page overflow: ' + category_path)

                category_url = 'https://www.casaroyal.cl/{}?p={}'\
                    .format(category_path, page)
                soup = BeautifulSoup(
                    session.get(category_url).text, 'html.parser')

                link_containers = soup.findAll('li', 'item')

                if not link_containers:
                    if page == 1:
                        raise Exception('Empty category: ' + category_path)

                for link_container in link_containers:
                    product_url = link_container.find('a')['href']
                    if product_url in product_urls:
                        done = True
                        break
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', {'itemprop': 'name'}).text.strip()
        sku = soup.find('div', 'sku').find('span', 'value').text.strip()

        stock = -1

        price = soup.find('span', 'price').text.strip()
        price = Decimal(price.replace('$', '').replace('.', ''))

        description_panels = soup.find('div', 'tabs-panels')\
            .findAll('div', 'panel')

        description = html_to_markdown(
            str(description_panels[0]) + '\n' + str(description_panels[1]))

        if 'reacond' in name.lower() or 'reacond' in description.lower():
            condition = 'https://schema.org/RefurbishedCondition'
        else:
            condition = 'https://schema.org/NewCondition'

        picture_urls = []

        for container in soup.find(
                'div', {'id': 'amasty_gallery'}).findAll('a'):
            try:
                picture_url = container['data-zoom-image']
                if picture_url.strip():
                    picture_urls.append(picture_url.strip())
            except KeyError:
                pass

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
            picture_urls=picture_urls,
            condition=condition
        )

        return [p]
