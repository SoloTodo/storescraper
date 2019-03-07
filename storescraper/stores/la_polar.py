import json
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy
from storescraper import banner_sections as bs


class LaPolar(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Television',
            'Tablet',
            'Refrigerator',
            'Printer',
            'Monitor',
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
            'AllInOne',
            'AirConditioner',
            'WaterHeater',
            'VideoGameConsole',
            'Projector',
            'SpaceHeater',
            'Wearable',
            'Mouse',
            'Keyboard',
            'KeyboardMouseCombo',
            'Headphones',

        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        extensions = [
            ['tecnologia/computadores/todo_notebooks', 'Notebook'],
            ['electronica/televisores/led2', 'Television'],
            ['electronica/televisores/smart_tv', 'Television'],
            # ['electronica/televisores/oled_i_qled_i_curvo', 'Television'],
            ['electronica/tv_por_pulgadas/hasta_40_pulgadas', 'Television'],
            ['electronica/tv_por_pulgadas/42_pulgadas_a_50_pulgadas',
             'Television'],
            ['electronica/tv_por_pulgadas/55_pulgadas_mas', 'Television'],
            ['electronica/televisores/dvd_i_blu_ray', 'OpticalDiskPlayer'],
            ['tecnologia/computadores/tablet', 'Tablet'],
            ['linea_blanca/refrigeradores/side_by_side', 'Refrigerator'],
            ['linea_blanca/refrigeradores/no_frost', 'Refrigerator'],
            ['linea_blanca/refrigeradores/frio_directo', 'Refrigerator'],
            ['linea_blanca/refrigeradores/frigobar', 'Refrigerator'],
            ['linea_blanca/refrigeradores/freezer', 'Refrigerator'],
            # ['tecnologia/impresoras/impresoras_laser', 'Printer'],
            ['tecnologia/impresoras/impresoras_a_tinta', 'Printer'],
            ['tecnologia/impresoras/multifuncionales', 'Printer'],
            # ['electronica/celulares/smartphones', 'Cell'],
            ['electronica/celulares/telefonos_basicos', 'Cell'],
            ['electronica/audio/parlantes', 'StereoSystem'],
            ['electronica/audio/equipos_de_musica', 'StereoSystem'],
            ['electronica/audio/karaoke', 'StereoSystem'],
            # ['electronica/audio/tornamesas', 'StereoSystem'],
            ['electronica/audio/home_theater', 'StereoSystem'],
            ['electronica/videojuegos/todo_consolas', 'VideoGameConsole'],
            ['tecnologia/accesorios_computacion/disco_duro_externo',
             'ExternalStorageDrive'],
            # ['tecnologia/accesorios_computacion/proyectores', 'Projector'],
            ['tecnologia/accesorios_computacion/pendrives',
             'UsbFlashDrive'],
            ['linea_blanca/lavado_secado/lavadoras', 'WashingMachine'],
            ['linea_blanca/lavado_secado/lavadoras___secadoras',
             'WashingMachine'],
            ['linea_blanca/lavado_secado/secadoras', 'WashingMachine'],
            # ['linea_blanca/lavado_secado/centrifugas', 'WashingMachine'],
            ['linea_blanca/climatizacion/calefont', 'WaterHeater'],
            # ['linea_blanca/climatizacion/enfriadores', 'AirConditioner'],
            # ['linea_blanca/climatizacion/estufas_a_parafina', 'SpaceHeater'],
            ['linea_blanca/climatizacion/estufas_electricas', 'SpaceHeater'],
            ['linea_blanca/cocina/microondas', 'Oven'],
            ['linea_blanca/cocina/hornos_electricos', 'Oven'],
            ['linea_blanca/electrodomesticos/aspiradoras', 'VacuumCleaner'],
            ['tecnologia/accesorios_computacion/otros', 'MemoryCard'],
            ['tecnologia3/accesorios_computacion/mouse_i_teclados', 'Mouse'],
            ['electronica/audio/audifonos', 'Headphones'],
            ['moda_zapatos/relojes/relojes_mujer', 'Wearable'],
            ['moda_zapatos/relojes/relojes_hombre', 'Wearable'],
            ['electronica/celulares/accesorios_telefonos', 'Wearable']
        ]

        session = session_with_proxy(extra_args)

        product_urls = []

        for extension, local_category in extensions:
            if local_category != category:
                continue

            url = 'https://tienda.lapolar.cl/catalogo/{}?response=' \
                  'json&pageSize=1000'.format(extension)
            print(url)
            products_json = json.loads(session.get(url).text)

            entry_products = products_json['dataset']['products']

            if not entry_products:
                raise Exception('Empty category: ' + url)

            for entry in entry_products:
                product_url = 'https://tienda.lapolar.cl/producto/sku/{}' \
                              ''.format(entry['plu'])
                product_urls.append(product_url)

        if category == 'Cell':
            url = 'https://www.lapolar.cl/internet/catalogo/fbind/postplu/' \
                  'destacados-smartphones'
            cells_data = json.loads(session.get(url).text)['lista_completa']

            for row in cells_data:
                for cell in row['sub_lista']:
                    product_url = 'https://tienda.lapolar.cl/producto/sku/{}' \
                                  ''.format(cell['prid'])
                    product_urls.append(product_url)

        return list(set(product_urls))

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if not response.ok:
            return []

        page_source = response.text

        soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('h1', 'title').text.strip()
        sku = soup.find('span', {'id': 'spanProductPlu'}).text.strip()

        normal_price = Decimal(
            re.search(r'internet: Number\((\d+)\)', page_source).groups()[0])
        offer_price = Decimal(
            re.search(r'laPolarCard: Number\((\d+)\)',
                      page_source).groups()[0])

        if offer_price > normal_price:
            offer_price = normal_price

        available_online = int(
            re.search(r'isAvailableOnline: (\d+),', page_source).groups()[0])

        if available_online:
            stock = -1
        else:
            stock = 0

        if not offer_price:
            offer_price = normal_price

        description = html_to_markdown(
            str(soup.find('div', {'id': 'description'})))

        picture_tags = soup.findAll('img', {'temprop': 'thumbnailUrl'})
        picture_urls = [tag['data-img-large'] for tag in picture_tags]

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
        sections_data = [
            [bs.HOME, 'Home', bs.SUBSECTION_TYPE_HOME,
             'https://tienda.lapolar.cl/'],
            [bs.LINEA_BLANCA_LA_POLAR, 'Línea Blanca',
             bs.SUBSECTION_TYPE_CATEGORY_PAGE,
             'https://tienda.lapolar.cl/catalogo/linea_blanca'],
            [bs.ELECTRONICA_LA_POLAR, 'Electrónica',
             bs.SUBSECTION_TYPE_CATEGORY_PAGE,
             'https://tienda.lapolar.cl/catalogo/electronica'],
            [bs.CELLS, 'Smartphones', bs.SUBSECTION_TYPE_CATEGORY_PAGE,
             'https://www.lapolar.cl/especial/smartphones/']
        ]

        session = session_with_proxy(extra_args)
        banners = []

        for section, subsection, subsection_type, url in sections_data:
            print(url)
            response = session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            if subsection_type == bs.SUBSECTION_TYPE_HOME:
                images = soup.findAll('div', 'carousel-item')

                for index, image in enumerate(images):
                    picture_url = image.find('img')['src']
                    destination_urls = [image.find('area')['href']]

                    banners.append({
                        'url': url,
                        'picture_url': picture_url,
                        'destination_urls': destination_urls,
                        'key': picture_url,
                        'position': index + 1,
                        'section': section,
                        'subsection': subsection,
                        'type': subsection_type
                    })
            elif subsection_type == bs.SUBSECTION_TYPE_CATEGORY_PAGE:
                iframe = soup.find('iframe', 'full')
                if iframe:
                    content = session.get(iframe['src'])
                    soup = BeautifulSoup(content.text, 'html.parser')
                    picture_base_url = 'https://www.lapolar.cl{}'
                else:
                    picture_base_url = url + '{}'

                images = soup.findAll('div', 'swiper-slide')

                if not images:
                    images = soup.findAll('div', 'item')

                for index, image, in enumerate(images):
                    picture = image.find('picture')
                    if not picture:
                        picture_url = picture_base_url.format(
                            image.find('img')['src'])
                    else:
                        picture_url = picture_base_url.format(
                            image.findAll('source')[-1]['srcset']
                        )
                    destination_urls = image.find('a')['href']

                    banners.append({
                        'url': url,
                        'picture_url': picture_url,
                        'destination_urls': destination_urls,
                        'key': picture_url,
                        'position': index + 1,
                        'section': section,
                        'subsection': subsection,
                        'type': subsection_type
                    })
        return banners
