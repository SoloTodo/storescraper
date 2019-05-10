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
            'DishWasher',
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        category_paths = [
            ['electro/television', ['Television'], 'Electro > Televisión', 1],
            ['electro/television/todas', ['Television'],
             'Electro > Televisión > Todas las TV', 1],
            ['electro/television/smart-tv', ['Television'],
             'Electro > Televisión > Smart TV', 1],
            ['electro/television/ultra-hd', ['Television'],
             'Electro > Televisión > Ultra HD', 1],
            ['electro/television/curvo-oled-qled', ['Television'],
             'Electro > Televisión > Curvo, Oled y Qled', 1],
            ['electro/television/monitores-tv', ['Television'],
             'Electro > Televisión > Monitor TV', 1],
            # Also contains other accesories
            ['electro/accesorios-tv',
             ['StereoSystem', 'OpticalDiskPlayer', 'Projector'],
             'Electro > Accesorios para TV', 0],
            ['electro/accesorios-tv/soundbar-home-theater', ['StereoSystem'],
             'Electro > Accesorios para TV > Soundbar y Home Theater', 1],
            ['electro/accesorios-tv/bluray-dvd', ['OpticalDiskPlayer'],
             'Electro > Accesorios para TV > Bluray y DVD', 1],
            ['electro/accesorios-tv/proyectores', ['Projector'],
             'Electro > Accesorios para TV > Proyectores', 1],
            # Also contains other audio products
            ['electro/audio', ['StereoSystem', 'Headphones'],
             'Electro > Audio', 0],
            ['electro/audio/parlantes-bluetooth-portables', ['StereoSystem'],
             'Electro > Audio > Parlantes Bluetooth y Portables', 1],
            ['electro/audio/micro-minicomponentes', ['StereoSystem'],
             'Electro > Audio > Micro y Minicomponentes', 1],
            ['electro/audio/audifonos', ['Headphones'],
             'Electro > Audio > Audífonos', 1],
            # Also contains other audio products
            ['electro/audio-hifi', ['Headphones', 'StereoSystem'],
             'Electro > HiFi', 0],
            ['electro/audio-hifi/audifonos', ['Headphones'],
             'Electro > HiFi > Audifonos HiFi', 1],
            ['electro/audio-hifi/home-theater', ['StereoSystem'],
             'Electro > HiFi > Home Cinema', 1],
            ['electro/audio-hifi/audio', ['StereoSystem'],
             'Electro > HiFi > Audio HiFi', 1],
            ['electro/audio-hifi/parlantes', ['StereoSystem'],
             'Electro > HiFi > Parlantes HIFI', 1],
            ['electro/audio-hifi/combos', ['StereoSystem'],
             'Electro > HiFi > Combos HIFI', 1],
            ['electro/elige-tu-pulgada', ['Television'],
             'Electro > Elige tu pulgada', 1],
            ['electro/elige-tu-pulgada/hasta-29-pulgadas', ['Television'],
             'Electro > Elige tu pulgada > Hasta 29"', 1],
            ['electro/elige-tu-pulgada/30-a-39-pulgadas', ['Television'],
             'Electro > Elige tu pulgada > 30" a 39"', 1],
            ['electro/elige-tu-pulgada/40-a-49-pulgadas', ['Television'],
             'Electro > Elige tu pulgada > 40" a 49"', 1],
            ['electro/elige-tu-pulgada/50-a-59-pulgadas', ['Television'],
             'Electro > Elige tu pulgada > 50" a 59"', 1],
            ['electro/elige-tu-pulgada/60-o-mas-pulgadas', ['Television'],
             'Electro > Elige tu pulgada > 60" o más', 1],
            ['electro/ofertas', ['Television', 'StereoSystem'],
             'Electro > Ofertas', 0.5],
            ['electro/ofertas/television', ['Television'],
             'Electro > Ofertas > Ofertas TV', 1],
            ['electro/ofertas/audio', ['StereoSystem'],
             'Electro > Ofertas > Ofertas Audio', 1],
            ['tecnologia/computadores', ['Notebook', 'Tablet', 'AllInOne'],
             'Tecno > Computadores', 0.5],
            ['tecnologia/computadores/notebooks', ['Notebook'],
             'Tecno > Computadores > Notebooks', 1],
            ['tecnologia/computadores/pc-gamer', ['Notebook'],
             'Tecno > Computadores > PC Gamers', 1],
            ['tecnologia/computadores/desktop-all-in-one', ['AllInOne'],
             'Tecno > Computadores > Desktop y All InOne', 1],
            ['tecnologia/computadores/convertibles-2-en-1', ['Notebook'],
             'Tecno > Computadores > Convertibles 2 en 1', 1],
            ['tecnologia/computadores/ipad-tablet', ['Tablet'],
             'Tecno > Computadores > iPad y Tablet', 1],
            # Also includes accesories
            ['tecnologia/celulares', ['Cell', 'Wearables'],
             'Tecno > Celulares', 0],
            ['tecnologia/celulares/smartphones', ['Cell'],
             'Tecno > Celulares > Smartphones', 1],
            ['tecnologia/celulares/basicos', ['Cell'],
             'Tecno > Celulares > Básicos', 1],
            ['tecnologia/celulares/smartwatch-wearables', ['Wearable'],
             'Tecno > Celulares > Smartwatch y Wearables', 1],
            ['tecnologia/gamers',
             ['Notebook', 'VideoGameConsole', 'Keyboard', 'Headphones'],
             'Tecno > Gamers', 0.5],
            ['tecnologia/gamer/notebooks', ['Notebook'],
             'Tecno > Gamers > Notebooks', 1],
            ['tecnologia/gamer/consolas', ['VideoGameConsole'],
             'Tecno > Gamers > Consolas', 1],
            ['tecnologia/gamer/teclados', ['Keyboard'],
             'Tecno > Gamers > Teclados y Mouse', 1],
            ['tecnologia/gamer/headset', ['Headphones'],
             'Tecno > Gamers > Headset', 1],
            # Also includes videogames
            ['tecnologia/consolas-videojuegos', ['VideoGameConsole'],
             'Tecno > Consolas VideoJuegos', 0],
            ['tecnologia/consolas-videojuegos/ps4', ['VideoGameConsole'],
             'Tecno > Consolas VideoJuegos > Consolas PS4', 1],
            ['tecnologia/consolas-videojuegos/xbox-one', ['VideoGameConsole'],
             'Tecno > Consolas VideoJuegos > Consolas Xbox One', 1],
            ['tecnologia/consolas-videojuegos/nintendo', ['VideoGameConsole'],
             'Tecno > Consolas VideoJuegos > Consolas Nintendo', 1],
            ['tecnologia/impresion', ['Printer'], 'Tecno > Impresión', 0],
            ['tecnologia/impresion/multifuncionales', ['Printer'],
             'Tecno > Impresión > Multifuncionales', 1],
            ['tecnologia/impresion/laser', ['Printer'],
             'Tecno > Impresión > Impresoras Láser', 1],
            # Also includes other accesories
            ['tecnologia/accesorios-fotografia',
             ['MemoryCard'], 'Tecno > Accesorios Fotografía', 0],
            ['tecnologia/accesorios-fotografia/tarjetas-memoria',
             ['MemoryCard'],
             'Tecno > Accesorios Fotografía > Tarjetas de Memoria', 1],
            # Also includes other accesories
            ['tecnologia/accesorios-computacion',
             ['Projector', 'Monitor', 'Mouse', 'ExternalStorageDrive',
              'UsbFlashDrive'], 'Tecno > Accesorios Computación', 0],
            ['tecnologia/accesorios-computacion/monitor-gamer', ['Monitor'],
             'Tecno > Accesorios Computación > Monitores Gamer', 1],
            ['tecnologia/accesorios-computacion/discos-duros',
             ['ExternalStorageDrive'],
             'Tecno > Accesorios Computación > Discos Duros', 1],
            ['tecnologia/accesorios-computacion/proyectores', ['Projector'],
             'Tecno > Accesorios Computación > Proyectores', 1],
            ['tecnologia/accesorios-computacion/mouse-teclados', ['Mouse'],
             'Tecno > Accesorios Computación > Mouse y Teclados', 1],
            ['tecnologia/accesorios-computacion/pendrives', ['UsbFlashDrive'],
             'Tecno > Accesorios Computación > Pendrives', 1],
            ['linea-blanca/refrigeracion', ['Refrigerator'],
             'Línea Blanca > Refrigeración', 1],
            ['linea-blanca/refrigeracion/no-frost', ['Refrigerator'],
             'Línea Blanca > Refrigeración > No Frost', 1],
            ['linea-blanca/refrigeracion/side-by-side', ['Refrigerator'],
             'Línea Blanca > Refrigeración > Side by Side', 1],
            ['linea-blanca/refrigeracion/frio-directo', ['Refrigerator'],
             'Línea Blanca > Refrigeración > Frío Directo', 1],
            ['linea-blanca/refrigeracion/freezer', ['Refrigerator'],
             'Línea Blanca > Refrigeración > Freezer', 1],
            ['linea-blanca/refrigeracion/frigobar-cavas', ['Refrigerator'],
             'Línea Blanca > Refrigeración > Frigobares y Cavas', 1],
            ['linea-blanca/lavado-secado', ['WashingMachine', 'DishWasher'],
             'Línea Blanca > Lavado y Secado', 0.5],
            ['linea-blanca/lavado-secado/todas', ['WashingMachine'],
             'Línea Blanca > Lavado y Secado > Todas las Lavadoras', 1],
            ['linea-blanca/lavado-secado/lavadoras-secadoras',
             ['WashingMachine'],
             'Línea Blanca > Lavado y Secado > Lavadora-Secadoras', 1],
            ['linea-blanca/lavado-secado/secadoras-centrifugas',
             ['WashingMachine'],
             'Línea Blanca > Lavado y Secado > Secadoras y Centrifugas', 1],
            ['linea-blanca/lavado-secado/lavavajillas',
             ['DishWasher'],
             'Línea Blanca > Lavado y Secado > Lavavajillas', 1],
            # Also includes campanas
            ['linea-blanca/cocina', ['Oven', 'Stove'],
             'Línea Blanca > Cocinas', 0],
            ['linea-blanca/cocina/encimeras', ['Oven'],
             'Línea Blanca > Cocinas > Encimeras', 1],
            ['linea-blanca/cocina/hornos-empotrables', ['Oven'],
             'Línea Blanca > Cocinas > Hornos empotrables', 1],
            ['linea-blanca/cocina/microondas', ['Oven'],
             'Línea Blanca > Cocinas > Microondas',
             1],
            # Also includes other electrodomésticos
            ['linea-blanca/electrodomesticos', ['Oven'],
             'Línea Blanca > Electrodomésticos', 0],
            ['linea-blanca/electrodomesticos/microondas', ['Oven'],
             'Línea Blanca > Electrodomésticos > Microondas', 1],
            # Also includes ventiladores
            ['linea-blanca/climatizacion',
             ['SpaceHeater', 'WaterHeater', 'AirConditioner'],
             'Línea Blanca > Climatización', 0],
            ['linea-blanca/climatizacion/aires-acondicionado',
             ['AirConditioner'],
             'Línea Blanca > Climatización > Aire Acondicionado', 1],
            ['linea-blanca/climatizacion/calefont', ['WaterHeater'],
             'Línea Blanca > Climatización > Calefont', 1],
            ['linea-blanca/estufas', ['SpaceHeater'],
             'Línea Blanca > Estufas', 1],
            ['linea-blanca/estufas/electricas', ['SpaceHeater'],
             'Línea Blanca > Estufas > Estufas Eléctricas', 1],
            ['linea-blanca/estufas/infrarrojas', ['SpaceHeater'],
             'Línea Blanca > Estufas > Estufas Infrarrojas', 1],
            ['linea-blanca/estufas/laser', ['SpaceHeater'],
             'Línea Blanca > Estufas > Estufas Láser', 1],
            ['linea-blanca/estufas/gas', ['SpaceHeater'],
             'Línea Blanca > Estufas > Estufas a Gas', 1],
            ['linea-blanca/estufas/parafina', ['SpaceHeater'],
             'Línea Blanca > Estufas > Estufas a Parafina', 1],
        ]

        session = session_with_proxy(extra_args)
        product_entries = defaultdict(lambda: [])

        for e in category_paths:
            category_path, local_categories, section_name, category_weight = e

            if category not in local_categories:
                continue

            page = 0

            while True:
                if page > 50:
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
                        'category_weight': category_weight,
                        'section_name': section_name,
                        'value': 40 * page + idx + 1,
                    })

                page += 1

        return product_entries

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
                if subsection_type not in [bs.SUBSECTION_TYPE_HOME, bs.SUBSECTION_TYPE_CATEGORY_PAGE]:
                    raise Exception('Invalid subsection type '
                                    '{}'.format(subsection_type))

                image_container = soup.find('div', 'home-slider')
                if not image_container:
                    image_container = soup.find('div', 'hero-slider')

                images = image_container.findAll('a')

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
