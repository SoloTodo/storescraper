from collections import defaultdict
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
    def discover_entries_for_category(cls, category, extra_args=None):
        category_paths = [
            ['tecnologia/computadores/notebooks', 'Notebook', 'Notebooks'],
            ['tecnologia/computadores/pc-gamer', 'Notebook', 'PC Gamers'],
            ['tecnologia/gamer/notebooks', 'Notebook', 'Notebooks Gamers'],
            ['tecnologia/computadores/convertibles-2-en-1', 'Notebook',
             'Convertibles 2 en 1'],
            ['tecnologia/computadores/apple', 'Notebook', 'Apple'],
            ['tecnologia/computadores/ipad-tablet', 'Tablet', 'iPad y Tablet'],
            ['tecnologia/computadores/desktop-all-in-one', 'AllInOne',
             'Desktop y All InOne'],
            ['electro/television/todas', 'Television', 'Todas las TV'],
            ['electro/television/smart-tv', 'Television', 'Smart TV'],
            ['electro/television/ultra-hd', 'Television', 'Ultra HD'],
            ['electro/television/curvo-oled-qled', 'Television',
             'Curvo, Oled y Qled'],
            ['electro/television/monitores-tv', 'Television', 'Monitor TV'],
            ['electro/accesorios-tv/soundbar-home-theater', 'StereoSystem',
             'Soundbar y Home Theater'],
            ['electro/audio-hifi/home-theater', 'StereoSystem', 'Home Cinema'],
            ['electro/accesorios-tv/bluray-dvd', 'OpticalDiskPlayer',
             'Bluray y DVD'],
            ['electro/accesorios-tv/proyectores', 'Projector',
             'Proyectores Electro'],
            ['tecnologia/accesorios-computacion/proyectores', 'Projector',
             'Proyectores Tecno'],
            ['electro/audio/parlantes-bluetooth-portables', 'StereoSystem',
             'Parlantes Bluetooth y Portables'],
            ['electro/audio/micro-minicomponentes', 'StereoSystem',
             'Micro y Minicomponentes'],
            ['electro/audo-hifi/audio', 'StereoSystem', 'Audio HIFI'],
            ['electro/audio-hifi/parlantes', 'StereoSystem', 'Parlantes HIFI'],
            ['electro/audio-hifi/combos', 'StereoSystem', 'Combos HIFI'],
            ['electro/audio/audifonos', 'Headphones', 'Audífonos'],
            ['electro/audio-hifi/audifonos', 'Headphones', 'Audifonos HiFi'],
            ['tecnologia/gamer/headset', 'Headphones', 'Headset'],
            ['tecnologia/celulares/smartphones', 'Cell', 'Smartphones'],
            ['tecnologia/celulares/basicos', 'Cell', 'Básicos'],
            ['tecnologia/gamer/consolas', 'VideoGameConsole', 'Consolas'],
            ['tecnologia/consolas-videojuegos/ps4', 'VideoGameConsole',
             'Consolas PS4'],
            ['tecnologia/consolas-videojuegos/xbox-one', 'VideoGameConsole',
             'Consolas Xbox One'],
            ['tecnologia/consolas-videojuegos/nintendo', 'VideoGameConsole',
             'Consolas Nintendo'],
            ['tecnologia/gamer/teclados', 'Keyboard', 'Teclados y Mouse'],
            ['tecnologia/accesorios-computacion/mouse-teclados', 'Mouse',
             'Mouse y Teclados'],
            ['tecnologia/gamer/monitores', 'Monitor', 'Monitores'],
            ['tecnologia/accesorios-computacion/monitor-gamer', 'Monitor',
             'Monitores Gamer'],
            # ['tecnologia/gamer/gabinetes', 'ComputerCase', 'Gabinetes'],
            ['tecnologia/impresion/multifuncionales', 'Printer',
             'Multifuncionales'],
            ['tecnologia/impresion/laser', 'Printer', 'Impresoras Láser'],
            ['tecnologia/accesorios-fotografia/tarjetas-memoria',
             'MemoryCard', 'Tarjetas de Memoria'],
            ['tecnologia/accesorios-computacion/discos-duros',
             'ExternalStorageDrive', 'Discos Duros'],
            ['tecnologia/celulares/smartwatch-wearables', 'Wearable',
             'Smartwatch y Wearables'],
            ['linea-blanca/refrigeracion', 'Refrigerator', 'Refrigeración'],
            ['linea-blanca/lavado-secado', 'WashingMachine',
             'Lavado y Secado'],
            ['linea-blanca/estufas', 'SpaceHeater', 'Estufas'],
            ['linea-blanca/cocina/microondas', 'Oven', 'Microondas Cocina'],
            ['linea-blanca/cocina/hornos-empotrables', 'Oven',
             'Hornos empotrables'],
            ['linea-blanca/electrodomesticos/microondas', 'Oven',
             'Microondas Electro'],
            ['linea-blanca/electrodomesticos/hornos-electricos', 'Oven',
             'Hornos Eléctricos'],
            ['linea-blanca/climatizacion/aires-acondicionado',
             'AirConditioner', 'Aire Acondicionado'],
            ['linea-blanca/climatizacion/calefont', 'WaterHeater', 'Calefont'],
            ['tecnologia/accesorios-computacion/pendrives', 'UsbFlashDrive',
             'Pendrives'],
        ]

        session = session_with_proxy(extra_args)
        product_entries = defaultdict(lambda: [])

        for category_path, local_category, section_name in category_paths:
            if category != local_category:
                continue

            section_url = 'https://www.paris.cl/{}/'.format(category_path)
            page = 0

            while True:
                if page > 1000:
                    raise Exception('Page overflow: ' + category_path)

                category_url = 'https://www.paris.cl/{}/?sz=40&start={}' \
                               ''.format(category_path, page * 40)
                print(category_url)
                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')

                containers = soup.findAll('li', 'flex-item-products')

                if not containers:
                    if page == 0:
                        raise Exception('Empty category: ' + category_path)
                    break

                for idx, container in enumerate(containers):
                    product_url = container.find('a')['href'].split('?')[0]
                    if 'https' not in product_url:
                        product_url = 'https://www.paris.cl' + product_url
                    product_entries[product_url].append({
                        'value': 40 * page + idx + 1,
                        'section_url': section_url,
                        'section_name': section_name
                    })

                page += 1

        return [{'url': key, 'positions': value}
                for key, value in product_entries.items()]

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
