from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy, \
    remove_words
from storescraper import banner_sections as bs


class Paris(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Television',
            'Tablet',
            'Refrigerator',
            'Printer',
            'Oven',
            'VacuumCleaner',
            'WashingMachine',
            'Cell',
            'Camera',
            'StereoSystem',
            'OpticalDiskPlayer',
            'ExternalStorageDrive',
            'UsbFlashDrive',
            'MemoryCard',
            'Projector',
            'VideoGameConsole',
            'Monitor',
            'AllInOne',
            'AirConditioner',
            'WaterHeater',
            'SolidStateDrive',
            'SpaceHeater',
            'Wearable',
            'Mouse',
            'Keyboard',
            'KeyboardMouseCombo',
            'Headphones',
            'ComputerCase',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['tecnologia/computadores/notebooks', 'Notebook'],
            ['tecnologia/computadores/pc-gamer', 'Notebook'],
            ['tecnologia/gamer/notebooks', 'Notebook'],
            ['tecnologia/computadores/convertibles-2-en-1', 'Notebook'],
            ['tecnologia/computadores/apple', 'Notebook'],
            ['tecnologia/computadores/ipad-tablet', 'Tablet'],
            ['tecnologia/computadores/desktop-all-in-one', 'AllInOne'],
            ['electro/television/todas', 'Television'],
            ['electro/television/smart-tv', 'Television'],
            ['electro/television/ultra-hd', 'Television'],
            ['electro/television/curvo-oled-qled', 'Television'],
            ['electro/television/monitores-tv', 'Television'],
            ['electro/accesorios-tv/soundbar-home-theater', 'StereoSystem'],
            ['electro/audio-hifi/home-theater', 'StereoSystem'],
            ['electro/accesorios-tv/bluray-dvd', 'OpticalDiskPlayer'],
            ['electro/accesorios-tv/proyectores', 'Projector'],
            ['tecnologia/accesorios-computacion/proyectores', 'Projector'],
            ['electro/audio/parlantes-bluetooth-portables', 'StereoSystem'],
            ['electro/audio/micro-minicomponentes', 'StereoSystem'],
            ['electro/audo-hifi/audio', 'StereoSystem'],
            ['electro/audio-hifi/parlantes', 'StereoSystem'],
            ['electro/audio-hifi/combos', 'StereoSystem'],
            ['electro/audio/audifonos', 'Headphones'],
            ['electro/audio-hifi/audifonos', 'Headphones'],
            ['tecnologia/gamer/headset', 'Headphones'],
            ['tecnologia/celulares/smartphones', 'Cell'],
            ['tecnologia/celulares/basicos', 'Cell'],
            ['tecnologia/gamer/consolas', 'VideoGameConsole'],
            ['tecnologia/consolas-videojuegos/ps4', 'VideoGameConsole'],
            ['tecnologia/consolas-videojuegos/xbox-one', 'VideoGameConsole'],
            ['tecnologia/consolas-videojuegos/nintendo', 'VideoGameConsole'],
            ['tecnologia/consolas-videojuegos/nintendo', 'VideoGameConsole'],
            ['tecnologia/gamer/teclados', 'Keyboard'],
            ['tecnologia/accesorios-computacion/mouse-teclados', 'Mouse'],
            ['tecnologia/gamer/monitores', 'Monitor'],
            ['tecnologia/accesorios-computacion/monitor-gamer', 'Monitor'],
            # ['tecnologia/gamer/gabinetes', 'ComputerCase'],
            ['tecnologia/impresion/multifuncionales', 'Printer'],
            ['tecnologia/impresion/laser', 'Printer'],
            ['tecnologia/accesorios-fotografia/tarjetas-memoria',
             'MemoryCard'],
            ['tecnologia/accesorios-computacion/discos-duros',
             'ExternalStorageDrive'],
            ['tecnologia/celulares/smartwatch-wearables', 'Wearable'],
            ['linea-blanca/refrigeracion', 'Refrigerator'],
            ['linea-blanca/lavado-secado', 'WashingMachine'],
            ['linea-blanca/estufas', 'SpaceHeater'],
            ['linea-blanca/cocina/microondas', 'Oven'],
            ['linea-blanca/cocina/hornos-empotrables', 'Oven'],
            ['linea-blanca/electrodomesticos/microondas', 'Oven'],
            ['linea-blanca/electrodomesticos/hornos-electricos', 'Oven'],
            ['linea-blanca/climatizacion/aires-acondicionado',
             'AirConditioner'],
            ['linea-blanca/climatizacion/calefont', 'WaterHeater'],
            ['tecnologia/accesorios-computacion/pendrives', 'UsbFlashDrive'],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if category != local_category:
                continue

            offset = 0

            while True:
                if offset > 1000:
                    raise Exception('Page overflow: ' + category_path)

                category_url = 'https://www.paris.cl/{}/?sz=40&start={}' \
                               ''.format(category_path, offset)
                print(category_url)
                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')

                containers = soup.findAll('li', 'flex-item-products')

                if not containers:
                    if offset == 0:
                        raise Exception('Empty category: ' + category_path)
                    break

                for container in containers:
                    product_url = container.find('a')['href'].split('?')[0]
                    if 'https' not in product_url:
                        product_url = 'https://www.paris.cl' + product_url
                    product_urls.append(product_url)

                offset += 40

        return list(set(product_urls))

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 410:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h4', {'itemprop': 'name'}).text.strip()
        sku = soup.find('div', 'pdp-main')['data-pid'].strip()
        offer_price_container = soup.find('div', 'cencosud-price')

        if soup.find('div', 'out-of-stock') or \
                soup.find('img', {'src': '/on/demandware.static/-/Sites/es_CL/'
                                         'dw8802c553/marketing/home/promotext/'
                                         'promotext-plp-event3-SF.png'}):
            stock = 0
        else:
            stock = -1

        if offer_price_container:
            offer_price = Decimal(remove_words(offer_price_container.text))
            normal_price = Decimal(remove_words(soup.find(
                'div', 'price-internet').text.split('$')[1].split('\n')[0]))
        else:
            price_text = soup.find('div', 'default-price').text.strip()
            if price_text == 'N/A':
                return []
            normal_price = Decimal(remove_words(price_text))
            offer_price = normal_price

        picture_urls = []
        for tag in soup.findAll('a', 'thumbnail-link'):
            picture_url = tag['href'].split('?')[0]
            picture_urls.append(picture_url)

        description = html_to_markdown(
            str(soup.find('div', {'id': 'collapseDetails'})))

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
            'CLP',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]

    @classmethod
    def banners(cls, extra_args=None):
        base_url = 'https://www.paris.cl/{}'

        sections_data = [
            [bs.HOME, 'Home', bs.SUBSECTION_TYPE_HOME, ''],
            [bs.LINEA_BLANCA_PARIS, 'Línea Blanca Paris',
             bs.SUBSECTION_TYPE_CATEGORY_PAGE, 'linea-blanca/'],
            [bs.ELECTRO_PARIS, 'Electro Paris',
             bs.SUBSECTION_TYPE_CATEGORY_PAGE, 'electro/'],
            [bs.TECNO_PARIS, 'Tecno Paris',
             bs.SUBSECTION_TYPE_CATEGORY_PAGE, 'tecnologia/'],
            [bs.REFRIGERATION, 'Refrigeración',
             bs.SUBSECTION_TYPE_MOSAIC, 'linea-blanca/refrigeracion/'],
            [bs.REFRIGERATION, 'No Frost', bs.SUBSECTION_TYPE_MOSAIC,
             'linea-blanca/refrigeracion/no-frost/'],
            [bs.REFRIGERATION, 'Side by Side', bs.SUBSECTION_TYPE_MOSAIC,
             'linea-blanca/refrigeracion/side-by-side/'],
            [bs.WASHING_MACHINES, 'Lavado y Secado',
             bs.SUBSECTION_TYPE_MOSAIC, 'linea-blanca/lavado-secado/'],
            [bs.WASHING_MACHINES, 'Todas las Lavadoras',
             bs.SUBSECTION_TYPE_MOSAIC, 'linea-blanca/lavado-secado/todas/'],
            [bs.WASHING_MACHINES, 'Lavadora-Secadoras',
             bs.SUBSECTION_TYPE_MOSAIC,
             'linea-blanca/lavado-secado/lavadoras-secadoras/'],
            [bs.WASHING_MACHINES, 'Secadoras y Centrifugas',
             bs.SUBSECTION_TYPE_MOSAIC,
             'linea-blanca/lavado-secado/secadoras-centrifugas/'],
            [bs.TELEVISIONS, 'Televisión', bs.SUBSECTION_TYPE_MOSAIC,
             'electro/television/'],
            [bs.TELEVISIONS, 'Todas las TV', bs.SUBSECTION_TYPE_MOSAIC,
             'electro/television/todas/'],
            [bs.TELEVISIONS, 'Smart TV', bs.SUBSECTION_TYPE_MOSAIC,
             'electro/television/smart-tv/'],
            [bs.TELEVISIONS, 'Ultra HD', bs.SUBSECTION_TYPE_MOSAIC,
             'electro/television/ultra-hd/'],
            [bs.TELEVISIONS, 'Curvo, Oled y Qled', bs.SUBSECTION_TYPE_MOSAIC,
             'electro/television/curvo-oled-qled/'],
            [bs.TELEVISIONS, 'Monitor TV', bs.SUBSECTION_TYPE_MOSAIC,
             'electro/television/monitores-tv/'],
            [bs.AUDIO, 'Audio', bs.SUBSECTION_TYPE_MOSAIC, 'electro/audio/'],
            [bs.AUDIO, 'Parlantes Bluetooth y Portables',
             bs.SUBSECTION_TYPE_MOSAIC,
             'electro/audio/parlantes-bluetooth-portables/'],
            [bs.AUDIO, ' Micro y Minicomponentes',
             bs.SUBSECTION_TYPE_MOSAIC,
             'electro/audio/micro-minicomponentes/'],
            [bs.CELLS, 'Celulares', bs.SUBSECTION_TYPE_MOSAIC,
             'tecnologia/celulares/'],
            [bs.CELLS, 'Smartphones', bs.SUBSECTION_TYPE_MOSAIC,
             'tecnologia/celulares/smartphones/']
        ]

        session = session_with_proxy(extra_args)
        banners = []

        for section, subsection, subsection_type, url_suffix in sections_data:
            url = base_url.format(url_suffix)
            response = session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            if subsection_type == bs.SUBSECTION_TYPE_MOSAIC:
                image = soup.find('div', 'desktop-plp-2')

                if not image:
                    continue

                picture = image.find('picture')

                if not picture:
                    continue

                picture_url = picture.find('source')['srcset']
                banners.append({
                    'url': url,
                    'picture_url': picture_url,
                    'destination_urls': [],
                    'key': picture_url,
                    'position': 1,
                    'section': section,
                    'subsection': subsection,
                    'type': subsection_type
                })

            else:
                if subsection_type == bs.SUBSECTION_TYPE_HOME:
                    images = soup.find('div', 'home-slider').findAll('a')
                elif subsection_type == bs.SUBSECTION_TYPE_CATEGORY_PAGE:
                    images = soup.find('div', 'hero-slider').findAll('a')
                else:
                    raise Exception('Invalid subsection type '
                                    '{}'.format(subsection_type))

                assert len(images) > 0

                for index, image in enumerate(images):
                    picture_url = image.find('source')['srcset']

                    destination_url = image['href']

                    if len(destination_url) > 255:
                        continue

                    banners.append({
                        'url': url,
                        'picture_url': picture_url,
                        'destination_urls': [destination_url],
                        'key': picture_url,
                        'position': index + 1,
                        'section': section,
                        'subsection': subsection,
                        'type': subsection_type
                    })

        return banners
