import json
import time

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy,\
    HeadlessChrome
from storescraper import banner_sections as bs


class Hites(Store):
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
            'VideoGameConsole',
            'AllInOne',
            'SpaceHeater',
            'CellAccesory',
            'Keyboard',
            'KeyboardMouseCombo',
            'Mouse',
            'Headphones',
            'ExternalStorageDrive',
            'Monitor',
            'Projector',
            'AirConditioner',
            'WaterHeater',
            'UsbFlashDrive',
            'Wearable'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['electro-hogar/refrigeradores', 'Refrigerator'],
            ['electro-hogar/lavado-y-secado/lavadoras', 'WashingMachine'],
            ['electro-hogar/lavado-y-secado/lavadoras-secadoras',
             'WashingMachine'],
            ['electro-hogar/lavado-y-secado/secadoras', 'WashingMachine'],
            # ['electro-hogar/lavado-y-secado/centrifugas', 'WashingMachine'],
            ['electro-hogar/cocina/hornos-empotrados', 'Oven'],
            ['electro-hogar/cocina/hornos-electricos', 'Oven'],
            ['electro-hogar/cocina/microondas', 'Oven'],
            ['electro-hogar/electrodomesticos/hornos-electricos', 'Oven'],
            ['electro-hogar/electrodomesticos/microondas', 'Oven'],
            ['electro-hogar/climatizacion/aire-acondicionado',
             'AirConditioner'],
            ['electro-hogar/climatizacion/estufa-a-lena', 'SpaceHeater'],
            ['electro-hogar/climatizacion/calefont-y-termos', 'WaterHeater'],
            ['tecnologia/tv-video/todos-los-led', 'Television'],
            ['tecnologia/tv-video/dvd-y-blu-ray', 'OpticalDiskPlayer'],
            ['tecnologia/computacion/notebook', 'Notebook'],
            ['tecnologia/computacion/tablets', 'Tablet'],
            ['tecnologia/computacion/impresoras-y-multifuncionales',
             'Printer'],
            ['tecnologia/computacion/pendrive', 'UsbFlashDrive'],
            ['tecnologia/computacion/monitores-y-proyectores', 'Monitor'],
            ['tecnologia/computacion/all-in-one', 'AllInOne'],
            ['tecnologia/computacion/disco-duro', 'ExternalStorageDrive'],
            ['tecnologia/video-juego/consolas', 'VideoGameConsole'],
            ['tecnologia/video-juego/consolas', 'VideoGameConsole'],
            ['tecnologia/audio/parlantes-bluetooth', 'StereoSystem'],
            ['tecnologia/audio/karaokes', 'StereoSystem'],
            ['tecnologia/audio/minicomponentes', 'StereoSystem'],
            ['tecnologia/audio/soundbar-y-home-theater', 'StereoSystem'],
            ['tecnologia/audio/microcomponentes', 'StereoSystem'],
            ['tecnologia/audio/audifonos', 'Headphones'],
            ['celulares/accesorios/audifonos', 'Headphones'],
            ['tecnologia/accesorios-y-otros/mouse-y-teclados', 'Mouse'],
            ['tecnologia/accesorios-y-otros/tarjetas-de-memoria',
             'MemoryCard'],
            ['celulares/smartphone/smartphone', 'Cell'],
            ['celulares/smartphone/smartphone-liberados', 'Cell'],
            ['celulares/smartphone/celulares-basicos', 'Cell'],
            ['electro-hogar/electrodomesticos/aspiradoras-y-enceradoras',
             'VacuumCleaner'],
            ['celulares/smartphone/smartwatch', 'Wearable']
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_id, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1

            while True:
                category_url = 'https://www.hites.com/{}?pageSize=48&page={}' \
                               ''.format(category_id, page)

                if page >= 20:
                    raise Exception('Page overflow: ' + category_url)

                print(category_url)

                response = session.get(category_url, timeout=30)

                if response.status_code in [404, 500]:
                    if page == 1:
                        raise Exception('Empty category: ' + category_url)
                    break

                soup = BeautifulSoup(response.text, 'html.parser')
                json_data = json.loads(soup.find(
                    'script', {'id': 'hy-data'}).text)
                product_entries = json_data['result']['products']

                if not product_entries:
                    if page == 1:
                        raise Exception('Empty category: ' + category_url)
                    break

                for product_entry in product_entries:
                    slug = product_entry['productString']
                    product_url = 'https://www.hites.com/' + slug
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url, timeout=10)

        if response.status_code == 404:
            return []

        page_source = response.text
        soup = BeautifulSoup(page_source, 'html.parser')

        if soup.find('img', {'src': '/public/statics/images/404.svg'}):
            return []

        json_data = json.loads(soup.find('script', {'id': 'hy-data'}).text)[
            'product']

        name = json_data['name']
        sku = json_data['partNumber']

        if json_data['isOutOfStock']:
            picture_urls = [json_data['fullImage']]
            stock = 0
        else:
            picture_urls = json_data['children'][0]['images']
            stock = 0
            for attribute in json_data['children'][0]['attributes']:
                if attribute['identifier'] == 'SHIPMODE_HOMEDEL':
                    if attribute['value'] == '1':
                        stock = -1

        normal_price = Decimal(json_data['prices']['offerPrice'])
        offer_price = Decimal(json_data['prices']['cardPrice'])

        if offer_price > normal_price:
            offer_price = normal_price

        description = html_to_markdown(
            json_data.get('longDescription', '') or ''
        )

        for attribute in json_data['attributes']:
            if attribute['displayable']:
                description += '\n{} {}'.format(attribute['name'],
                                                attribute['value'])

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
        base_url = 'https://www.hites.com/{}'

        sections_data = [
            [bs.HOME, 'Home', bs.SUBSECTION_TYPE_HOME, ''],
            [bs.TELEVISIONS, 'TV Video', bs.SUBSECTION_TYPE_MOSAIC,
             'tecnologia/tv-video'],
            [bs.TELEVISIONS, 'Todos los Led', bs.SUBSECTION_TYPE_MOSAIC,
             'tecnologia/tv-video/todos-los-led'],
            [bs.TELEVISIONS, 'Smart TV', bs.SUBSECTION_TYPE_MOSAIC,
             'tecnologia/tv-video/smart-tv'],
            [bs.TELEVISIONS, 'Led Extra Grandes', bs.SUBSECTION_TYPE_MOSAIC,
             'tecnologia/tv-video/led-extra-grandes'],
            [bs.CELLS, 'Smartphone', bs.SUBSECTION_TYPE_MOSAIC,
             'celulares/smartphone'],
            [bs.CELLS, 'Smartphone-Smartphone', bs.SUBSECTION_TYPE_MOSAIC,
             'celulares/smartphone/smartphone'],
            [bs.CELLS, 'Smartphone Liberados', bs.SUBSECTION_TYPE_MOSAIC,
             'celulares/smartphone/smartphone-liberados'],
            [bs.REFRIGERATION, 'Refrigeradores', bs.SUBSECTION_TYPE_MOSAIC,
             'electro-hogar/refrigeradores'],
            [bs.REFRIGERATION, 'No Frost', bs.SUBSECTION_TYPE_MOSAIC,
             'electro-hogar/refrigeradores/no-frost'],
            [bs.REFRIGERATION, 'Side by Side', bs.SUBSECTION_TYPE_MOSAIC,
             'electro-hogar/refrigeradores/side-by-side'],
            [bs.WASHING_MACHINES, 'Lavado y Secado', bs.SUBSECTION_TYPE_MOSAIC,
             'electro-hogar/lavado-y-secado'],
            [bs.WASHING_MACHINES, 'Lavadoras', bs.SUBSECTION_TYPE_MOSAIC,
             'electro-hogar/lavado-y-secado/lavadoras'],
            [bs.WASHING_MACHINES, 'Lavadoras-Secadoras',
             bs.SUBSECTION_TYPE_MOSAIC,
             'electro-hogar/lavado-y-secado/lavadoras-secadoras'],
            [bs.WASHING_MACHINES, 'Secadoras', bs.SUBSECTION_TYPE_MOSAIC,
             'electro-hogar/lavado-y-secado/secadoras'],
            [bs.AUDIO, 'Audio', bs.SUBSECTION_TYPE_MOSAIC, 'tecnologia/audio'],
            [bs.AUDIO, 'Minicomponentes', bs.SUBSECTION_TYPE_MOSAIC,
             'tecnologia/audio/minicomponentes'],
            [bs.AUDIO, 'Soundbar y Home Theater', bs.SUBSECTION_TYPE_MOSAIC,
             'tecnologia/audio/soundbar-y-home-theater']
        ]

        session = session_with_proxy(extra_args)
        banners = []

        for section, subsection, subsection_type, url_suffix in sections_data:
            url = base_url.format(url_suffix)
            print(url)

            if subsection_type == bs.SUBSECTION_TYPE_HOME:
                with HeadlessChrome(images_enabled=True) as driver:
                    driver.set_window_size(1920, 1080)
                    driver.get(url)

                    pictures = []

                    banner_container = driver\
                        .find_element_by_class_name('slick-list')

                    controls = driver\
                        .find_element_by_class_name('carousel__controls')\
                        .find_elements_by_class_name('slider-controls__dots')

                    for control in controls:
                        control.click()
                        time.sleep(0.5)
                        pictures.append(
                            banner_container.screenshot_as_base64)

                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    images = soup.find('div', 'slick-track')\
                        .findAll('li', 'slick-slide')

                    images = [a for a in images if
                              'slick-cloned' not in a['class']]

                    assert len(images) == len(pictures)

                    for index, image in enumerate(images):
                        product_box = image.find('div', 'boxproductos')

                        if not product_box:
                            product_box = image.find('div', 'box-producto')

                        key_container = product_box.find('source')

                        if key_container:
                            key = key_container['srcset']
                        else:
                            key = product_box.find('img')['src']

                        destination_urls = [d['href'] for d in
                                            image.findAll('a')]
                        destination_urls = list(set(destination_urls))

                        banners.append({
                            'url': url,
                            'picture': pictures[index],
                            'destination_urls': destination_urls,
                            'key': key,
                            'position': index + 1,
                            'section': section,
                            'subsection': subsection,
                            'type': subsection_type
                        })
            elif subsection_type == bs.SUBSECTION_TYPE_MOSAIC:
                response = session.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')

                banners_container = soup.find('section')\
                    .findAll('div', 'espot', recursive=False)

                for index, banner in enumerate(banners_container):
                    destination_urls = [d['href'] for d in
                                        banner.findAll('a')]

                    destination_urls = list(set(destination_urls))

                    picture_container = banner.find('picture')

                    if picture_container:
                        picture_url = picture_container\
                            .find('source')['srcset']
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
                    else:
                        with HeadlessChrome(images_enabled=True) as driver:
                            driver.set_window_size(1920, 1080)
                            driver.get(url)

                            s_banner = driver.find_elements_by_css_selector(
                                '#main>.espot')[index]

                            key = banner.find('img')['src']

                            picture = s_banner.screenshot_as_base64
                            banners.append({
                                'url': url,
                                'picture': picture,
                                'destination_urls': destination_urls,
                                'key': 'https:{}'.format(key),
                                'position': index + 1,
                                'section': section,
                                'subsection': subsection,
                                'type': subsection_type
                            })

        return banners
