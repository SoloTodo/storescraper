import json
import time
import base64

from decimal import Decimal
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO

from selenium.common.exceptions import NoSuchElementException

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy
from storescraper import banner_sections as bs
from storescraper.utils import HeadlessChrome

from .falabella import Falabella


class FalabellaCf(Store):
    # Special Falabella scraper that bypasses Cloudflare but retrieves less
    # info for each product

    preferred_discover_urls_concurrency = 1
    preferred_products_for_url_concurrency = 1

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
            'CellAccesory',
            'AllInOne',
            'AirConditioner',
            'Monitor',
            'WaterHeater',
            'SolidStateDrive',
            'Mouse',
            'SpaceHeater',
            'Keyboard',
            'KeyboardMouseCombo',
            'Wearable',
            'Headphones',
            'DishWasher'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        return [category]

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        category_paths = [
            ['cat70057', ['Notebook'],
             'Home > Computación-Notebooks', 1],
            # ['cat5860031', ['Notebook'],
            #  'Home > Computación-Notebooks > Notebooks Tradicionales', 1],
            ['cat2028', ['Notebook'],
             'Home > Computación-Notebooks Gamers', 1],
            ['cat2450060', ['Notebook'],
             'Home > Computación-Notebooks > Notebooks Convertibles 2en1', 1],
            # ['cat15880017', ['Notebook'],
            #  'Home > Especiales-Gamer', 1],
            ['cat5860030', ['Notebook'],
             'Home > Computación-Notebooks > MacBooks', 1],
            ['cat4850013', ['Notebook'],
             'Home > Computación-Computación Gamer', 1],
            ['cat1012', ['Television'],
             'Home > Tecnología-TV', 1],
            ['cat7190148', ['Television'],
             'Home > Tecnología-TV > Televisores LED', 1],
            ['cat11161614', ['Television'],
             'Home > Tecnología-TV > LEDs menores a 50 pulgadas', 1],
            ['cat11161675', ['Television'],
             'Home > Tecnología-TV > LEDs entre 50 - 55 pulgadas', 1],
            ['cat11161679', ['Television'],
             'Home > Tecnología-TV > LEDs sobre 55 pulgadas', 1],
            # ['cat2850016', ['Television'],
            #  'Home > TV-Televisores OLED', 1],
            ['cat10020021', ['Television'],
             'Home > TV-Televisores QLED', 1],
            # ['cat18110001', ['Television'],
            #  'Home > Tecnología-Premium', 1],
            ['cat7230007', ['Tablet'],
             'Home > Computación-Tablets', 1],
            ['cat3205', ['Refrigerator'],
             'Home > Refrigeración-Refrigeradores', 1],
            ['cat4074', ['Refrigerator'],
             'Home > Refrigeración-No Frost', 1],
            ['cat4091', ['Refrigerator'],
             'Home > Refrigeración-Side by Side', 1],
            ['cat4036', ['Refrigerator'],
             'Home > Refrigeración-Frío Directo', 1],
            ['cat4048', ['Refrigerator'],
             'Home > Refrigeración-Freezers', 1],
            ['cat4049', ['Refrigerator'],
             'Home > Refrigeración-Frigobar', 1],
            ['cat1840004', ['Refrigerator'],
             'Home > Refrigeración-Cavas', 1],
            ['cat3205', ['Refrigerator'],
             'Home > Refrigeración-Bottom freezer', 1,
             'f.product.attribute.Tipo=Bottom+freezer'],
            ['cat3205', ['Refrigerator'],
             'Home > Refrigeración-Top mount', 1,
             'f.product.attribute.Tipo=Top+mount'],
            ['cat1820006', ['Printer'],
             'Home > Computación-Impresión > Impresoras Multifuncionales', 1],
            # ['cat6680042/Impresoras-Tradicionales', 'Printer'],
            # ['cat11970007/Impresoras-Laser', 'Printer'],
            # ['cat11970009/Impresoras-Fotograficas', 'Printer'],
            ['cat3151', ['Oven'],
             'Home > Microondas', 1],
            ['cat3114', ['Oven'],
             'Home > Electrodomésticos Cocina- Electrodomésticos de cocina > '
             'Hornos Eléctricos', 1],
            # ['cat3025', ['VacuumCleaner'],
            #  'Home > Electrohogar- Aspirado y Limpieza > Aspiradoras', 1],
            ['cat3136', ['WashingMachine'],
             'Home > Electrohogar-Lavado > Lavado', 1],
            ['cat4060', ['WashingMachine'],
             'Home > Electrohogar-Lavado > Lavadoras', 1],
            ['cat1700002', ['WashingMachine'],
             'Home > Electrohogar-Lavado > Lavadoras-Secadoras', 1],
            ['cat4088', ['WashingMachine'],
             'Home > Electrohogar-Lavado > Secadoras', 1],
            ['cat1280018', ['Cell'],
             'Home > Telefonía- Celulares y Teléfonos > Celulares Básicos', 1],
            ['cat720161', ['Cell'],
             'Home > Telefonía- Celulares y Teléfonos > Smartphones', 1],
            ['cat70028', ['Camera'],
             'Home > Fotografía-Cámaras Compactas', 1],
            ['cat70029', ['Camera'],
             'Home > Fotografía-Cámaras Semiprofesionales', 1],
            ['cat3091', ['StereoSystem'],
             'Home > Audio-Equipos de Música y Karaokes', 1],
            ['cat3171', ['StereoSystem'],
             'Home > Computación- Accesorios Tecnología > Accesorios Audio > '
             'Parlantes Bluetooth', 1],
            ['cat2045', ['StereoSystem'],
             'Home > Audio-Soundbar y Home Theater', 1],
            ['cat1130010', ['StereoSystem'],
             'Home > Audio- Hi-Fi > Tornamesas', 1],
            ['cat6260041', ['StereoSystem'],
             'Home > Día del Niño Chile- Tecnología > Audio > Karaoke', 1],
            ['cat2032', ['OpticalDiskPlayer'],
             'Home > TV-Blu Ray y DVD', 1],
            ['cat3087', ['ExternalStorageDrive'],
             'Home > Computación- Almacenamiento > Discos duros', 1],
            ['cat3177', ['UsbFlashDrive'],
             'Home > Computación- Almacenamiento > Pendrives', 1],
            ['cat70037', ['MemoryCard'],
             'Home > Computación- Accesorios Tecnología > '
             'Accesorios Fotografía > Tarjetas de Memoria', 1],
            ['cat2070', ['Projector'],
             'Home > TV-Proyectores', 1],
            ['cat3770004', ['VideoGameConsole'],
             'Home > Tecnología- Videojuegos > Consolas', 1],
            ['cat40051', ['AllInOne'],
             'Home > Computación-All In One', 1],
            ['cat7830015', ['AirConditioner'],
             'Home > Electrohogar- Aire Acondicionado > Portátiles', 1],
            ['cat7830014', ['AirConditioner'],
             'Home > Electrohogar- Aire Acondicionado >Split', 1],
            ['cat3197', ['AirConditioner'],
             'Home > Electrohogar- Aire Acondicionado > Purificadores', 1],
            ['cat2062', ['Monitor'],
             'Home > Computación-Monitores', 1],
            ['cat2013', ['WaterHeater'],
             'Home > Electrohogar- Aire Acondicionado > Calefont y Termos', 1],
            ['cat3155', ['Mouse'],
             'Home > Computación- Accesorios Tecnología > '
             'Accesorios Computación > Mouse', 1],
            ['cat9900007', ['SpaceHeater'],
             'Home > Electrohogar- Calefacción > Estufas Parafina Láser', 1],
            ['cat9910024', ['SpaceHeater'],
             'Home > Electrohogar- Calefacción > Estufas Gas', 1],
            ['cat9910006', ['SpaceHeater'],
             'Home > Electrohogar- Calefacción > Estufas Eléctricas', 1],
            ['cat9910027', ['SpaceHeater'],
             'Home > Electrohogar- Calefacción > Estufas Pellet y Leña', 1],
            ['cat4290063', ['Wearable'],
             'Home > Telefonía- Wearables > SmartWatch', 1],
            ['cat4730023', ['Keyboard'],
             'Home > Computación- Accesorios Tecnología > '
             'Accesorios Computación > Teclados > Teclados Gamers', 1],
            ['cat2370002', ['Keyboard'],
             'Home > Computación- Accesorios Tecnología > '
             'Accesorios Computación > Teclados', 1],
            # ['cat2930003', ['Keyboard'],
            #  'Home > Computación- Accesorios Tecnología > Accesorios TV > '
            #  'Teclados Smart', 1],
            ['cat1640002', ['Headphones'],
             'Home > Computación- Accesorios Tecnología > Accesorios Audio > '
             'Audífonos', 1],
            ['cat4061', ['DishWasher'],
             'Home > Lavado-Lavavajillas', 1],
        ]

        product_dict = {}
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = 'curl/7.64.1'

        for e in category_paths:
            category_id, local_categories, section_name, category_weight = \
                e[:4]

            if len(e) > 4:
                extra_query_params = e[4]
            else:
                extra_query_params = None

            if category not in local_categories:
                continue

            base_url = 'https://www.falabella.com/s/browse/v1/listing/cl?' \
                       'zone=13&categoryId={}&page={}'

            if extra_query_params:
                base_url += '&' + extra_query_params

            page = 1
            position = 1

            while True:
                if page > 60:
                    raise Exception('Page overflow: ' + category_id)

                pag_url = base_url.format(category_id, page)
                res = session.get(pag_url, timeout=None)
                res = json.loads(res.content.decode('utf-8'))['data']

                if 'results' not in res:
                    if page == 1:
                        raise Exception(
                            'Empty category: {}'.format(category_id))
                    break

                for result in res['results']:
                    local_products = cls._assemble_products(
                        result, category, session)

                    for product in local_products:
                        if product.sku in product_dict:
                            product_to_update = product_dict[product.sku]
                        else:
                            product_dict[product.sku] = product
                            product_to_update = product

                        # For some unkown reason the same SKU may appear
                        # more than once on the same section, so set the
                        # position of the sku only if it hasn't been set
                        # beforce (i.e. keep the lowest position)
                        if section_name not in product_to_update.positions:
                            product_to_update.positions[section_name] = \
                                position

                    position += 1
                page += 1

        products_list = [p for p in product_dict.values()]

        return products_list

    @classmethod
    def _assemble_products(cls, result, category, session):
        url = result['url']
        name = result['displayName']
        sku = result['skuId']
        seller = result['sellerId'] \
            if result['sellerId'] != 'FALABELLA' else None

        if 'totalReviews' in result:
            review_count = int(result['totalReviews'])
            review_avg_score = float(result['rating'])
        else:
            review_count = None
            review_avg_score = None

        if result.get('brand', 'N/A').upper() in ['LG', 'SAMSUNG'] or \
                'LG' in name or 'Samsung' in name:
            picture_urls = Falabella._get_picture_urls(session, sku)
        else:
            picture_urls = [
                'https://falabella.scene7.com/is/image/'
                'Falabella/{}?scl=1.0'.format(sku)]

        stock = -1
        offer_price = None
        normal_price = None
        backup_price = None

        for price in result['prices']:
            if price['icons']:
                offer_price = Decimal(
                    price['price'][0].replace('.', ''))
            elif price['label']:
                normal_price = Decimal(
                    price['price'][0].replace('.', ''))
            else:
                backup_price = Decimal(
                    price['price'][0].replace('.', ''))

        if not normal_price:
            normal_price = backup_price

        if not offer_price:
            offer_price = normal_price

        variants = result['variants'][0]['options']

        if variants:
            products = []
            for variant in variants:
                name += ' ({})'.format(variant['label'])
                sku = variant['mediaId']

                # Only rewrite the picture urls if there is at least two
                # variants of the product. For some reason there are SKUs
                # (e.g. 10761120) that only have one variant and have the
                # variants field loaded. This prevents resetting the images
                # possibly loadded for LG and Samsung products above
                if len(variants) > 1:
                    picture_urls = [
                        'https://falabella.scene7.com/is/image/'
                        'Falabella/{}?scl=1.0'.format(sku)]

                products.append(Product(
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
                    picture_urls=picture_urls,
                    seller=seller,
                    review_count=review_count,
                    review_avg_score=review_avg_score
                ))
        else:
            products = [
                Product(
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
                    picture_urls=picture_urls,
                    seller=seller,
                    review_count=review_count,
                    review_avg_score=review_avg_score
                )
            ]

        return products

    @classmethod
    def discover_urls_for_keyword(cls, keyword, threshold, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = 'curl/7.64.1'

        base_url = "https://www.falabella.com/falabella-cl/search?" \
                   "Ntt={}&page={}"

        discovered_urls = []
        page = 1
        while True:
            if page > 60:
                raise Exception('Page overflow ' + keyword)

            search_url = base_url.format(keyword, page)
            res = session.get(search_url, timeout=None)

            if res.status_code == 500:
                break

            soup = BeautifulSoup(res.text, 'html.parser')

            script = soup.find('script', {'id': '__NEXT_DATA__'})
            json_data = json.loads(script.text)

            for product_data in json_data['props']['pageProps']['results']:
                product_url = product_data['url']
                discovered_urls.append(product_url)

                if len(discovered_urls) == threshold:
                    return discovered_urls

            page += 1

        return discovered_urls

    @classmethod
    def banners(cls, extra_args=None):
        base_url = 'https://www.falabella.com/falabella-cl/{}'

        sections_data = [
            [bs.HOME, 'Home', bs.SUBSECTION_TYPE_HOME, ''],
            # # CATEGORY PAGES # #
            # Currently displaying a smart picker
            [bs.REFRIGERATION, 'Electrohogar-Refrigeradores',
             bs.SUBSECTION_TYPE_CATEGORY_PAGE,
             'category/cat3205/Refrigeradores'],
            [bs.WASHING_MACHINES, 'Electrohogar-Lavado',
             bs.SUBSECTION_TYPE_CATEGORY_PAGE, 'category/cat3136/Lavado'],
            [bs.TELEVISIONS, 'TV', bs.SUBSECTION_TYPE_CATEGORY_PAGE,
             'category/cat1012/TV'],
            [bs.AUDIO, 'Audio', bs.SUBSECTION_TYPE_CATEGORY_PAGE,
             'category/cat2005/Audio'],
            [bs.CELLS, 'Telefonía-Celulares y Teléfonos',
             bs.SUBSECTION_TYPE_CATEGORY_PAGE,
             'category/cat2018/Celulares-y-Telefonos'],

            # # MOSAICS ##
            [bs.LINEA_BLANCA_FALABELLA, 'Electro y Tecnología-Línea Blanca',
             bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat7090035/Linea-Blanca?isPLP=1'],
            [bs.REFRIGERATION, 'Refrigeradores-No Frost',
             bs.SUBSECTION_TYPE_MOSAIC, 'category/cat4074/No-Frost'],
            [bs.REFRIGERATION, 'Refrigeradores-Side by Side',
             bs.SUBSECTION_TYPE_MOSAIC, 'category/cat4091/Side-by-Side'],
            # [bs.WASHING_MACHINES, 'Lavadoras', bs.SUBSECTION_TYPE_MOSAIC,
            #  'category/cat3136/Lavadoras '],
            [bs.WASHING_MACHINES, 'Lavadoras-Lavadoras',
             bs.SUBSECTION_TYPE_MOSAIC, 'category/cat4060/Lavadoras'],
            [bs.WASHING_MACHINES, 'Lavadoras-Lavadoras-Secadoras',
             bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat1700002/Lavadoras-Secadoras'],
            [bs.WASHING_MACHINES, 'Lavadoras-Secadoras',
             bs.SUBSECTION_TYPE_MOSAIC, 'category/cat4088/Secadoras'],
            [bs.WASHING_MACHINES, ' Lavadoras-Lavadoras Doble Carga',
             bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat11400002/Lavadoras-Doble-Carga'],
            [bs.TELEVISIONS, 'Tecnología-TV', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat1012/TV?isPLP=1'],
            [bs.TELEVISIONS, 'Televisores LED', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat7190148/Televisores-LED'],
            [bs.TELEVISIONS, 'LEDs menores a 50 pulgadas',
             bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat11161614/LEDs-menores-a-50-pulgadas'],
            [bs.TELEVISIONS, 'LEDs entre 50 - 55 pulgadas',
             bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat11161675/LEDs-entre-50---55-pulgadas'],
            [bs.TELEVISIONS, 'LEDs sobre 55 pulgadas',
             bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat11161679/LEDs-sobre-55-pulgadas'],

            # [bs.TELEVISIONS, 'TV-LED', bs.SUBSECTION_TYPE_MOSAIC,
            #  'category/cat2850014/LED'],
            # [bs.TELEVISIONS, 'TV-Smart TV', bs.SUBSECTION_TYPE_MOSAIC,
            #  'category/cat3040054/Smart-TV'],
            # [bs.TELEVISIONS, 'TV-4K UHD', bs.SUBSECTION_TYPE_MOSAIC,
            #  'category/cat3990038/4K-UHD'],
            # [bs.TELEVISIONS, 'TV-Televisores OLED',
            # bs.SUBSECTION_TYPE_MOSAIC,
            #  'category/cat2850016/Televisores-OLED'],
            # [bs.TELEVISIONS, 'TV-Pulgadas Altas',
            #  bs.SUBSECTION_TYPE_MOSAIC,
            #  'category/cat12910024/Televisores-LED-Desde-65"'],
            [bs.AUDIO, 'Audio-Soundbar y Home Theater',
             bs.SUBSECTION_TYPE_MOSAIC, 'category/cat2045/Home-Theater'],
            [bs.AUDIO, 'Home Theater', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat3050040/Home-Theater'],
            [bs.AUDIO, 'Soundbar', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat1700004/Soundbar'],
            [bs.AUDIO, 'Minicomponente', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat70018/Minicomponente'],
            [bs.AUDIO, 'Audio-Equipos de Música y Karaokes',
             bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat3091/?mkid=CA_P2_MIO1_024794'],
            [bs.AUDIO, 'Audio-Hi-Fi', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat3203/Hi-Fi'],
            [bs.AUDIO, 'Audio', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat2005/Audio?isPLP=1'],
            [bs.CELLS, 'Smartphones', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat720161/Smartphones'],
            [bs.CELLS, 'Electro y Tecnología-Teléfonos',
             bs.SUBSECTION_TYPE_MOSAIC, 'category/cat2018/Telefonos?isPLP=1'],
        ]

        banners = []

        proxy = None
        if 'proxy' in extra_args:
            proxy = extra_args['proxy']

        for section, subsection, subsection_type, url_suffix in sections_data:
            url = base_url.format(url_suffix)

            if subsection_type == bs.SUBSECTION_TYPE_HOME:
                with HeadlessChrome(
                        images_enabled=True, proxy=proxy) as driver:
                    driver.set_window_size(1920, 1080)
                    driver.get(url)

                    images = driver\
                        .find_element_by_class_name('swiper-container')\
                        .find_elements_by_class_name('dy_unit')[1:-1]

                    index = 1

                    for image_url in images:
                        picture_array = image_url.find_element_by_tag_name(
                            'picture').find_elements_by_tag_name('source')
                        destination_urls = [
                            d.get_property('href') for d in
                            image_url.find_elements_by_tag_name('a')]
                        destination_urls = list(set(destination_urls))
                        for picture in picture_array:
                            picture_url = picture.get_property(
                                'srcset').split(' ')[0]

                            if 'https://www.falabella.com' not in picture_url:
                                picture_url = 'https://www.falabella.com' \
                                              '{}'.format(picture_url)

                            if picture_url:
                                banners.append({
                                    'url': url,
                                    'picture_url': picture_url,
                                    'destination_urls': destination_urls,
                                    'key': picture_url,
                                    'position': index,
                                    'section': section,
                                    'subsection': subsection,
                                    'type': subsection_type
                                })
                                break
                        else:
                            raise Exception(
                                'No valid banners found for {} in position '
                                '{}'.format(url, index + 1))
                        index += 1
            elif subsection_type == bs.SUBSECTION_TYPE_CATEGORY_PAGE:
                with HeadlessChrome(images_enabled=True, proxy=proxy,
                                    timeout=99) as driver:
                    driver.set_window_size(1920, 1080)
                    driver.get(url)

                    pictures = []

                    try:
                        pips_container = driver.find_element_by_class_name(
                            'fb-hero-carousel__pips')

                        driver.execute_script(
                            "arguments[0].setAttribute('style', "
                            "'display:block !important;');", pips_container)

                        elements = driver.find_element_by_class_name(
                            'fb-hero-carousel__pips')\
                            .find_elements_by_class_name(
                            'fb-hero-carousel__pips__pip')

                        for element in elements:
                            element.click()
                            time.sleep(2)
                            image_url = Image.open(
                                BytesIO(driver.get_screenshot_as_png()))
                            image_url = image_url.crop((0, 187, 1920, 769))
                            buffered = BytesIO()
                            image_url.save(buffered, format='PNG')
                            pictures.append(
                                base64.b64encode(buffered.getvalue()))
                    except NoSuchElementException:
                        image_url = Image.open(
                            BytesIO(driver.get_screenshot_as_png()))
                        image_url = image_url.crop((0, 187, 1920, 769))
                        buffered = BytesIO()
                        image_url.save(buffered, format='PNG')
                        pictures.append(base64.b64encode(buffered.getvalue()))

                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    images_div = soup.findAll('div', 'fb-hero-carousel-slide')
                    images_article = soup.findAll('article',
                                                  'fb-hero-carousel-slide')
                    images_module = soup.findAll('div',
                                                 'hero fb-module-wrapper')

                    images = images_div + images_article + images_module

                    assert len(images) == len(pictures)

                    for index, image_url in enumerate(images):
                        picture_array = image_url.findAll(
                            'picture')[-1].findAll('source')
                        destination_urls = [d['href'] for d in
                                            image_url.findAll('a')]
                        destination_urls = list(set(destination_urls))

                        for picture in picture_array:
                            key = picture['srcset'].split(' ')[0]

                            if 'https' not in key:
                                key = 'https://www.falabella.com' + key

                            if 'webp' not in key:
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
                                break
                        else:
                            raise Exception(
                                'No valid banners found for {} in position '
                                '{}'.format(url, index + 1))
            elif subsection_type == bs.SUBSECTION_TYPE_MOSAIC:
                session = session_with_proxy(extra_args)
                session.headers['user-agent'] = 'curl/7.64.1'
                soup = BeautifulSoup(session.get(url).text, 'html.parser')

                banner = soup.find('div', 'fb-huincha-main-wrap')

                if not banner:
                    continue

                image_url = banner.find('source')['srcset']
                dest_url = banner.find('a')['href']

                banners.append({
                    'url': url,
                    'picture_url': image_url,
                    'destination_urls': [dest_url],
                    'key': image_url,
                    'position': 1,
                    'section': section,
                    'subsection': subsection,
                    'type': subsection_type})

        return banners
