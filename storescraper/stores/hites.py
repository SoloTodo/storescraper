import json
import logging
import re

import time
from collections import defaultdict

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.flixmedia import flixmedia_video_urls
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, HeadlessChrome
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
            'Stove',
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
            'Wearable',
            'DishWasher',
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        category_paths = [
            ['electro-hogar/refrigeradores', ['Refrigerator'],
             'Inicio > Electro Hogar > Refrigeradores', 1],
            ['electro-hogar/refrigeradores/refrigerador-frio-directo',
             ['Refrigerator'],
             'Inicio > Electro Hogar > Refrigeradores > Frío Directo', 1],
            ['electro-hogar/refrigeradores/refrigerador-no-frost',
             ['Refrigerator'],
             'Inicio > Electro Hogar > Refrigeradores > No Frost', 1],
            ['electro-hogar/refrigeradores/refrigerador-side-by-side',
             ['Refrigerator'],
             'Inicio > Electro Hogar > Refrigeradores > Side by Side', 1],
            ['electro-hogar/refrigeradores/freezer-y-frigobar',
             ['Refrigerator'],
             'Inicio > Electro Hogar > Refrigeradores > Freezers y Frigobar',
             1],
            ['electro-hogar/lavado-y-secado', ['WashingMachine', 'DishWasher'],
             'Inicio > Electro Hogar > Lavado y Secado', 0.5],
            ['electro-hogar/lavado-y-secado/lavadoras', ['WashingMachine'],
             'Inicio > Electro Hogar > Lavado y Secado > Lavadoras', 1],
            ['electro-hogar/lavado-y-secado/secadoras-y-centrifugas',
             ['WashingMachine'],
             'Inicio > Electro Hogar > Lavado y Secado > Secadoras', 1],
            ['electro-hogar/lavado-y-secado/lavadoras-secadoras',
             ['WashingMachine'],
             'Inicio > Electro Hogar > Lavado y Secado > Lavadoras-Secadoras',
             1],
            ['electro-hogar/lavado-y-secado/lavavajillas', ['DishWasher'],
             'Inicio > Electro Hogar > Lavado y Secado > Lavavajillas', 1],
            ['electro-hogar/cocina', ['Oven', 'Stove'],
             'Inicio > Electro Hogar > Cocina', 0],
            ['electro-hogar/cocina/cocina-a-gas', ['Stove'],
             'Inicio > Electro Hogar > Cocina > Cocina a gas', 1],
            ['electro-hogar/cocina/encimeras', ['Stove'],
             'Inicio > Electro Hogar > Cocina > Encimeras', 1],
            ['electro-hogar/cocina/hornos-empotrados', ['Oven'],
             'Inicio > Electro Hogar > Cocina > Hornos Empotrados', 1],
            ['electro-hogar/cocina/hornos-electricos', ['Oven'],
             'Inicio > Electro Hogar > Cocina > '
             'Hornos Eléctricos', 1],
            ['electro-hogar/electrodomesticos-cocina/microondas', ['Oven'],
             'Inicio > Electro Hogar > Electrodomesticos Cocina > Microondas',
             1],
            ['electro-hogar/climatizacion',
             ['AirConditioner', 'SpaceHeater', 'WaterHeater'],
             'Inicio > Electro Hogar > Climatización', 0],
            ['electro-hogar/climatizacion/aire-acondicionado',
             ['AirConditioner'], 'Inicio > Electro Hogar > Climatizacioń >  '
                                 'Aire Acondicionado', 1],
            ['electro-hogar/climatizacion/estufas-a-parafinas',
             ['SpaceHeater'],
             'Inicio > Electro Hogar > Climatizacioń > Estufas a Parafinas',
             1],
            ['electro-hogar/climatizacion/estufas-a-gas', ['SpaceHeater'],
             'Inicio > Electro Hogar > Climatización > Estufas a Gas', 1],
            ['electro-hogar/climatizacion/estufa-a-lena', ['SpaceHeater'],
             'Inicio > Electro Hogar > Climatización > Estufa a Leña', 1],
            ['electro-hogar/climatizacion/estufas-electricas', ['SpaceHeater'],
             'Inicio > Electro Hogar > Climatización > Estufas Eléctricas', 1],
            ['electro-hogar/climatizacion/calefont-y-termos',
             ['WaterHeater'],
             'Inicio > Electro Hogar > Climatización > Calefont y Termos', 1],
            ['tecnologia/tv-video', ['Television', 'OpticalDiskPlayer'],
             'Inicio > Tecnología > TV Video', 0],
            ['tecnologia/tv-video/smart-tv', ['Television'],
             'Inicio > Tecnología > Tv Video > Smart TV', 1],
            ['tecnologia/tv-video/smart-tv-premium', ['Television'],
             'Inicio > Tecnología > Tv Video > Smart TV Premium', 1],
            ['tecnologia/tv-video/smart-tv-hasta-49', ['Television'],
             'Inicio > Tecnología > Tv Video > Smart TV Hasta 49', 1],
            ['tecnologia/tv-video/smart-tv-entre-50-y-55', ['Television'],
             'Inicio > Tecnología > Tv Video > Smart TV Entre 50 y 55', 1],
            ['tecnologia/tv-video/smart-tv-desde-58', ['Television'],
             'Inicio > Tecnología > Tv Video > Smart TV Desde 58', 1],
            ['tecnologia/tv-video/smart-tv-samsung', ['Television'],
             'Inicio > Tecnología > Tv Video > Smart Tv Samsung', 1],
            ['tecnologia/tv-video/smart-tv-lg', ['Television'],
             'Inicio > Tecnología > Tv Video > Smart Tv LG', 1],
            ['tecnologia/computacion',
             ['Notebook', 'Tablet', 'Printer', 'Monitor', 'Projector',
              'Pendrive', 'ExternalStorageDrive'],
             'Inicio > Tecnología > Computación', 0],
            ['tecnologia/computacion/notebook', ['Notebook'],
             'Inicio > Tecnología > Computación > Notebook', 1],
            ['tecnologia/computacion/tablets', ['Tablet'],
             'Inicio > Tecnología > Computación > Tablets', 1],
            ['tecnologia/computacion/all-in-one', ['AllInOne'],
             'Inicio > Tecnología > Computacioń > All in One', 1],
            ['tecnologia/computacion/monitores',
             ['Monitor'],
             'Inicio > Tecnología > Computación > Monitores y Proyectores',
             1],
            ['tecnologia/computacion/impresoras-y-multifuncionales',
             ['Printer'],
             'Inicio > Tecnología > Computación > '
             'Impresoras y Multifuncionales', 1],
            ['tecnologia/accesorios-y-otros/pendrives-y-tarjetas-de-memoria',
             ['UsbFlashDrive', 'MemoryCard'],
             'Inicio > Tecnología > Accesorios y Otros > Pendrives y '
             'Tarjetas de Memoria', 1],
            ['tecnologia/computacion/disco-duro', ['ExternalStorageDrive'],
             'Inicio > Tecnología > Computación > Disco Duro', 1],
            ['tecnologia/video-juego/consolas', ['VideoGameConsole'],
             'Inicio > Tecnología > Video Juego > Consolas', 1],
            ['tecnologia/audio', ['StereoSystem', 'Headphones'],
             'Inicio > Tecnología > Audio', 0],
            ['tecnologia/audio/parlantes-bluetooth', ['StereoSystem'],
             'Inicio > Tecnología > Audio > Parlantes Bluetooth', 1],
            ['tecnologia/audio/karaokes', ['StereoSystem'],
             'Inicio > Tecnología > Audio > Karaokes', 1],
            ['tecnologia/audio/minicomponentes', ['StereoSystem'],
             'Inicio > Tecnología > Audio > Minicomponentes', 1],
            ['tecnologia/tv-video/soundbar-y-home-theater', ['StereoSystem'],
             'Inicio > Tecnología > TV Video > Soundbar y Home Theater', 1],
            ['celulares/accesorios-para-celulares/audifonos', ['Headphones'],
             'Inicio > Celulares > Accesorios para celulares > Audífonos', 1],
            ['tecnologia/accesorios-y-otros/mouse-y-teclados',
             ['Mouse', 'Keyboard'],
             'Inicio > Tecnología > Accesorios y Otros > Mouse y Teclados',
             0.5],
            ['tecnologia/accesorios-y-otros/tarjetas-de-memoria',
             ['MemoryCard'],
             'Inicio > Tecnología > Accesorios y Otros > Tarjetas de Memoria',
             1],
            ['celulares/smartphones', ['Cell', 'Wearable'],
             'Inicio > Celulares > Smartphones', 0],
            ['celulares/smartphones/smartphone', ['Cell'],
             'Inicio > Celulares > Smartphones > Smartphones', 1],
            ['celulares/smartphones/celulares-liberados', ['Cell'],
             'Inicio > Celulares > Smartphones > Celulares Liberados', 1],
            ['celulares/smartphones/celulares-basicos', ['Cell'],
             'Inicio > Celulares > Smartphone > Celulares Basicos', 1],
            ['celulares/accesorios-para-celulares/smartwatch', ['Wearable'],
             'Inicio > Celulares > Accesorios para celulares > Smartwatch', 1],
            ['electro-hogar/electrodomesticos-hogar/aspiradoras-y-enceradoras',
             ['VacuumCleaner'],
             'Inicio > Electro Hogar > Electrodomésticos > '
             'Aspiradoras y Enceradoras', 1]
        ]

        product_entries = defaultdict(lambda: [])
        session = session_with_proxy(extra_args)

        for e in category_paths:
            category_path, local_categories, section_name, category_weight = e

            if category not in local_categories:
                continue

            start = 0
            current_position = 1

            while True:
                category_url = 'https://www.hites.com/{}/?sz=24&start={}&' \
                               'srule=best-matches'.format(
                                category_path, start)
                print(category_url)

                if start >= 600:
                    raise Exception('Page overflow: ' + category_url)

                response = session.get(category_url, timeout=60)

                if response.url != category_url:
                    raise Exception('Page mismatch. Expencting {} Got {}'
                                    ''.format(category_url, response.url))

                if response.status_code in [404, 500]:
                    break

                soup = BeautifulSoup(response.text, 'html.parser')

                products = soup.findAll('div', 'product-tile')

                if not products:
                    # if start == 0:
                    #     raise Exception(category_url)
                    break

                for product_entry in products:
                    path = product_entry.find('a')['href']

                    if 'hites.com' in path:
                        product_url = path
                    else:
                        product_url = 'https://www.hites.com' + path

                    if product_url == 'https://www.hites.com/':
                        logging.warning('Invalid URL: ' + category_url)
                        continue

                    product_entries[product_url].append({
                        'category_weight': category_weight,
                        'section_name': section_name,
                        'value': current_position
                    })
                    current_position += 1

                start += 24

        return product_entries

    @classmethod
    def discover_urls_for_keyword(cls, keyword, threshold, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []

        page = 1

        while True:
            if page > 40:
                raise Exception('Page overflow')

            search_url = 'https://www.hites.com/search/{}?page={}'\
                .format(keyword, page)
            print(search_url)

            response = session.get(search_url, timeout=60)

            if response.status_code in [404, 500]:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            json_data = json.loads(soup.find(
                'script', {'id': 'hy-data'}).text)
            product_data = json_data['result']['products']

            if not product_data:
                break

            for product_entry in product_data:
                slug = product_entry['productString']
                product_url = 'https://www.hites.com/' + slug
                product_urls.append(product_url)
                if len(product_urls) == threshold:
                    return product_urls

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url, timeout=60)

        if response.status_code in [404, 410]:
            return []

        page_source = response.text
        soup = BeautifulSoup(page_source, 'html.parser')

        if soup.find('section', 'error-page'):
            return []

        if soup.find('img', {'src': '/public/statics/images/404.svg'}):
            return []

        name = soup.find('h1', 'product-name').text
        sku = soup.find('span', 'product-id').text

        availability_match = re.search(r'"availability":"(.+)"', response.text)
        availability_text = availability_match.groups()[0]

        if availability_text == 'http://schema.org/OutOfStock':
            stock = 0
        elif availability_text == 'http://schema.org/InStock':
            stock = -1
        else:
            raise Exception('Invalid availability text: {}'.format(
                availability_text))

        prices = soup.find('div', 'prices')

        offer_price_container = prices.find('span', 'hites-price')
        offer_price = None
        if offer_price_container:
            offer_price = Decimal(offer_price_container.text.strip()
                                  .replace('$', '').replace('.', ''))

        normal_price_container = prices.find('span', 'sales')
        if not normal_price_container:
            normal_price_container = prices.find('span', 'list')

        if not normal_price_container and not offer_price_container:
            return []

        normal_price = Decimal(
            normal_price_container.find('span', 'value')['content'])

        if not offer_price:
            offer_price = normal_price

        has_virtual_assistant = \
            'cdn.livechatinc.com/tracking.js' in response.text

        flixmedia_container = soup.find(
            'script', {'src': '//media.flixfacts.com/js/loader.js'})
        flixmedia_id = None
        video_urls = None

        if flixmedia_container:
            mpn = flixmedia_container['data-flix-mpn']
            video_urls = flixmedia_video_urls(mpn)
            if video_urls is not None:
                flixmedia_id = mpn

        if 'reacondicionado' in name.lower():
            condition = 'https://schema.org/RefurbishedCondition'
        else:
            condition = 'https://schema.org/NewCondition'

        images = soup.find('div', 'primary-images')\
            .findAll('div', 'carousel-item')

        picture_urls = [i.find('img')['src'].replace(' ', '%20')
                        for i in images if i.find('img') is not None]

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
            condition=condition,
            picture_urls=picture_urls,
            video_urls=video_urls,
            has_virtual_assistant=has_virtual_assistant,
            flixmedia_id=flixmedia_id
        )

        return [p]

    @classmethod
    def banners(cls, extra_args=None):
        base_url = 'https://www.hites.com/{}'

        sections_data = [
            [bs.HOME, 'Home', bs.SUBSECTION_TYPE_HOME, ''],
            [bs.TELEVISIONS, 'TV Video', bs.SUBSECTION_TYPE_MOSAIC,
             'tecnologia/tv-video'],
            [bs.TELEVISIONS, 'Smart TV', bs.SUBSECTION_TYPE_MOSAIC,
             'tecnologia/tv-video/smart-tv'],
            [bs.TELEVISIONS, 'Smart TV LG', bs.SUBSECTION_TYPE_MOSAIC,
             'tecnologia/tv-video/smart-tv-lg'],
            [bs.TELEVISIONS, 'Smart TV Samsung', bs.SUBSECTION_TYPE_MOSAIC,
             'tecnologia/tv-video/smart-tv-samsung'],
            [bs.TELEVISIONS, 'Smart TV Hisense', bs.SUBSECTION_TYPE_MOSAIC,
             'tecnologia/tv-video/smart-tv-hisense'],
            [bs.TELEVISIONS, 'Smart TV Premium', bs.SUBSECTION_TYPE_MOSAIC,
             'tecnologia/tv-video/smart-tv-premium'],
            [bs.CELLS, 'Smartphone', bs.SUBSECTION_TYPE_MOSAIC,
             'celulares/smartphones'],
            [bs.CELLS, 'Smartphone-Smartphone', bs.SUBSECTION_TYPE_MOSAIC,
             'celulares/smartphones/smartphone'],
            [bs.CELLS, 'Smartphone Liberados', bs.SUBSECTION_TYPE_MOSAIC,
             'celulares/smartphones/celulares-liberados'],
            [bs.REFRIGERATION, 'Refrigeradores', bs.SUBSECTION_TYPE_MOSAIC,
             'electro-hogar/refrigeradores'],
            [bs.REFRIGERATION, 'No Frost', bs.SUBSECTION_TYPE_MOSAIC,
             'electro-hogar/refrigeradores/refrigerador-no-frost'],
            [bs.REFRIGERATION, 'Side by Side', bs.SUBSECTION_TYPE_MOSAIC,
             'electro-hogar/refrigeradores/refrigerador-side-by-side'],
            [bs.WASHING_MACHINES, 'Lavado y Secado', bs.SUBSECTION_TYPE_MOSAIC,
             'electro-hogar/lavado-y-secado'],
            [bs.WASHING_MACHINES, 'Lavadoras', bs.SUBSECTION_TYPE_MOSAIC,
             'electro-hogar/lavado-y-secado/lavadoras'],
            [bs.WASHING_MACHINES, 'Lavadoras-Secadoras',
             bs.SUBSECTION_TYPE_MOSAIC,
             'electro-hogar/lavado-y-secado/lavadoras-secadoras'],
            # [bs.WASHING_MACHINES, 'Secadoras', bs.SUBSECTION_TYPE_MOSAIC,
            #  'electro-hogar/lavado-y-secado/secadoras'],
            [bs.AUDIO, 'Audio', bs.SUBSECTION_TYPE_MOSAIC, 'tecnologia/audio'],
            # [bs.AUDIO, 'Minicomponentes', bs.SUBSECTION_TYPE_MOSAIC,
            #  'tecnologia/audio/minicomponentes'],
            # [bs.AUDIO, 'Soundbar y Home Theater', bs.SUBSECTION_TYPE_MOSAIC,
            #  'tecnologia/audio/soundbar-y-home-theater']
        ]

        session = session_with_proxy(extra_args)
        banners = []

        for section, subsection, subsection_type, url_suffix in sections_data:
            url = base_url.format(url_suffix)
            print(url)

            if subsection_type == bs.SUBSECTION_TYPE_HOME:
                with HeadlessChrome(images_enabled=True,
                                    timeout=120) as driver:
                    driver.set_window_size(1920, 1080)
                    driver.get(url)

                    pictures = []

                    banner_container = driver\
                        .find_element_by_class_name('slick-list')

                    # banner_container = driver \
                    #     .find_element_by_class_name('owl-stage-outer')

                    controls = driver.find_element_by_class_name(
                        'slick-dots')\
                        .find_elements_by_tag_name('li')

                    # controls = driver.find_elements_by_class_name('owl-dot')

                    for control in controls:
                        control.click()
                        time.sleep(1)
                        pictures.append(
                            banner_container.screenshot_as_base64)

                    soup = BeautifulSoup(driver.page_source, 'html.parser')

                    images = soup.find('div', 'slick-track')\
                        .findAll('div', 'slick-slide')

                    # images = soup.find('div', 'owl-stage') \
                    #     .findAll('div', 'owl-item')

                    images = [a for a in images if
                              'slick-cloned' not in a['class']]

                    # images = [a for a in images if
                    #           'cloned' not in a['class']]

                    assert len(images) == len(pictures)

                    for index, image in enumerate(images):
                        product_box = image.find('div', 'boxproductos')

                        if not product_box:
                            product_box = image.find('div', 'box-producto')

                        if not product_box:
                            product_box = image.find('div', 'box-foto')

                        if not product_box:
                            product_box = image.find(
                                'div', 'slide-new__products')

                        if not product_box:
                            product_box = image.find('div', 'images_llamados')

                        if not product_box:
                            product_box = image.find(
                                'div', 'products-item__img')

                        if not product_box:
                            product_box = image.find('a', 'boxproducto')

                        if not product_box:
                            product_box = image

                        if not (product_box.find('source') or
                                product_box.find('img')):
                            product_box = image.find('div', 'img_boxproducto')

                        if not product_box:
                            product_box = image.find('div', 'logocampana')

                        key_container = product_box.find('source')

                        if key_container:
                            key = key_container['srcset']
                        else:
                            key = product_box.find('img')['src']

                        destinations = [d for d in image.findAll('a')]
                        destination_urls = []

                        for destination in destinations:
                            if destination.get('href'):
                                destination_urls.append(destination['href'])

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
                        picture_source = picture_container.find('source')

                        if not picture_source:
                            continue

                        picture_url = picture_source['srcset']
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
                        with HeadlessChrome(images_enabled=True, timeout=120) \
                                as driver:
                            driver.set_window_size(1920, 1080)
                            driver.get(url)

                            s_banner = driver.find_elements_by_css_selector(
                                '#main>.espot')[index]

                            key_container = banner.find('img')

                            if not key_container or \
                                    s_banner.size['height'] == 0:
                                continue

                            key = key_container['src']

                            picture = s_banner.screenshot_as_base64
                            banners.append({
                                'url': url,
                                'picture': picture,
                                'destination_urls': destination_urls,
                                'key': key,
                                'position': index + 1,
                                'section': section,
                                'subsection': subsection,
                                'type': subsection_type
                            })

        return banners
