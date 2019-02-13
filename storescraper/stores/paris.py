from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy, \
    remove_words


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
            ['tecnologia/gamer/gabinetes', 'ComputerCase'],
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

        if soup.find('div', 'out-of-stock'):
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
