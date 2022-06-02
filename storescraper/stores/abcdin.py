import json
import logging
from collections import defaultdict

from bs4 import BeautifulSoup
from decimal import Decimal
from urllib.parse import urlparse, parse_qs, urlencode

from storescraper.categories import TELEVISION, STEREO_SYSTEM, HEADPHONES, \
    SPACE_HEATER, REFRIGERATOR, WASHING_MACHINE, DISH_WASHER, VACUUM_CLEANER, \
    OVEN, WATER_HEATER, CELL, WEARABLE, CELL_ACCESORY, NOTEBOOK, TABLET, \
    MOUSE, GAMING_CHAIR, ALL_IN_ONE, MONITOR, EXTERNAL_STORAGE_DRIVE, \
    PRINTER, VIDEO_GAME_CONSOLE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy
from storescraper import banner_sections as bs


class AbcDin(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION,
            STEREO_SYSTEM,
            HEADPHONES,
            SPACE_HEATER,
            REFRIGERATOR,
            WASHING_MACHINE,
            DISH_WASHER,
            VACUUM_CLEANER,
            OVEN,
            WATER_HEATER,
            CELL,
            WEARABLE,
            CELL_ACCESORY,
            NOTEBOOK,
            TABLET,
            MOUSE,
            GAMING_CHAIR,
            ALL_IN_ONE,
            MONITOR,
            EXTERNAL_STORAGE_DRIVE,
            PRINTER,
            VIDEO_GAME_CONSOLE
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        ajax_resources = [
            ['electro/tv-y-video', [TELEVISION], 'Electro / TV y Video', 0],
            ['electro/tv-y-video/televisores-led', [TELEVISION],
             'Electro / TV y Video / Televisores LED', 1],
            ['electro/audio', [STEREO_SYSTEM], 'Electro / Audio', 0],
            ['electro/audio/parlantes-portatiles', [STEREO_SYSTEM],
             'Electro / Audio / Parlantes Portátiles', 1],
            # ['electro/audio/audio-profesional', [STEREO_SYSTEM],
            #  'Electro / Audio / Audio Profesional', 1],
            ['electro/audio/minicomponentes', [STEREO_SYSTEM],
             'Electro / Audio / Minicomponentes', 1],
            # ['electro/audio/microcomponentes', [STEREO_SYSTEM],
            #  'Electro / Audio / Microcomponentes', 1],
            ['electro/audio/home-theater', [STEREO_SYSTEM],
             'Electro / Audio / Home Theater', 1],
            ['electro/audio/radios', [STEREO_SYSTEM],
             'Electro / Audio / Radios', 1],
            # ['electro/audio/reproductores-de-musica', [STEREO_SYSTEM],
            #  'Electro / Audio / Reproductores de Música', 1],
            ['electro/audio/tornamesas', [STEREO_SYSTEM],
             'Electro / Audio / Tornamesas', 1],
            # ['electro/audio/radio-y-parlantes-de-auto', [STEREO_SYSTEM],
            #  'Electro / Audio / Radio Y Parlantes De Auto', 0],
            ['electro/audifonos', [HEADPHONES], 'Electro / Audífonos', 1],
            ['electro/audifonos/in-ear', [HEADPHONES],
             'Electro / Audífonos / In Ear', 1],
            ['electro/audifonos/over-ear', [HEADPHONES],
             'Electro / Audífonos / Over Ear', 1],
            # ['electro/audifonos/deportivos', [HEADPHONES],
            #  'Electro / Audífonos / Deportivos', 1],
            ['linea-blanca/climatizacion', [SPACE_HEATER],
             'Línea Blanca / Climatización', 1],
            ['linea-blanca/refrigeradores', [REFRIGERATOR],
             'Línea Blanca / Refrigeradores', 1],
            ['linea-blanca/refrigeradores/refrigeradores-frio-directo',
             [REFRIGERATOR],
             'Línea Blanca / Refrigeradores / Refrigeradores Frio Directo', 1],
            ['linea-blanca/refrigeradores/refrigeradores-no-frost',
             [REFRIGERATOR],
             'Línea Blanca / Refrigeradores / Refrigeradores No Frost', 1],
            ['linea-blanca/refrigeradores/refrigeradores-side-by-side',
             [REFRIGERATOR],
             'Línea Blanca / Refrigeradores / Refrigeradores Side by Side', 1],
            ['linea-blanca/refrigeradores/frigobar', [REFRIGERATOR],
             'Línea Blanca / Refrigeradores / Frigobar', 1],
            ['linea-blanca/refrigeradores/freezers', [REFRIGERATOR],
             'Línea Blanca / Refrigeradores / Freezers', 1],
            ['linea-blanca/lavado-y-secado', [WASHING_MACHINE, DISH_WASHER],
             'Línea Blanca / Lavado y Secado', 0.5],
            ['linea-blanca/lavado-y-secado/lavadoras', [WASHING_MACHINE],
             'Línea Blanca / Lavado y Secado / Lavadoras', 1],
            ['linea-blanca/lavado-y-secado/lavadoras-secadoras',
             [WASHING_MACHINE],
             'Línea Blanca / Lavado y Secado / Lavadoras-Secadoras', 1],
            ['linea-blanca/lavado-y-secado/secadoras', [WASHING_MACHINE],
             'Línea Blanca / Lavado y Secado / Secadoras', 1],
            ['linea-blanca/lavado-y-secado/centrifugas', [WASHING_MACHINE],
             'Línea Blanca / Lavado y Secado / Centrífugas', 1],
            ['linea-blanca/lavado-y-secado/lavavajillas', [DISH_WASHER],
             'Línea Blanca / Lavado y Secado / Lavavajillas', 1],
            ['linea-blanca/electrodomesticos', [VACUUM_CLEANER, OVEN],
             'Línea Blanca / Electrodomésticos', 0],
            ['linea-blanca/electrodomesticos/aspiradoras-y-enceradoras',
             [VACUUM_CLEANER],
             'Línea Blanca / Electrodomésticos / Aspiradoras y Enceradoras',
             1],
            ['linea-blanca/electrodomesticos/microondas', [OVEN],
             'Línea Blanca / Electrodomésticos / Microondas', 1],
            ['linea-blanca/electrodomesticos/hornos-electricos', [OVEN],
             'Línea Blanca / Electrodomésticos / Hornos Eléctricos', 1],
            ['linea-blanca/calefont', [WATER_HEATER],
             'Línea Blanca / Calefont', 1],
            ['telefonia/smartphones', [CELL], 'Telefonía / Smartphones', 1],
            ['telefonia/smartwatch', [WEARABLE], 'Telefonía / Smartwatch', 1],
            ['telefonia/accesorios-telefonia', [CELL_ACCESORY],
             'Telefonía / Accesorios telefonía', 1],
            ['computacion/notebooks', [NOTEBOOK],
             'Computación / Notebooks', 1],
            ['computacion/tablets', [TABLET], 'Computación / Tablets', 1],
            ['computacion/accesorios-computacion', [MOUSE],
             'Computación / Accesorios Computación', 1],
            ['computacion/accesorios-computacion', [MOUSE],
             'Computación / Accesorios Computación', 1],
            ['computacion/mundo-gamer', [GAMING_CHAIR],
             'Computación / Mundo Gamer', 1],
            ['computacion/all-in-one', [ALL_IN_ONE],
             'Computación / All In One', 1],
            ['computacion/monitores-y-proyectores', [MONITOR],
             'Computación / Monitores y Proyectores', 1],
            ['computacion/almacenamiento', [EXTERNAL_STORAGE_DRIVE],
             'Computación / Almacenamiento', 1],
            ['computacion/impresoras-y-multifuncionales', [PRINTER],
             'Computación / Impresoras y Multifuncionales', 1],
            # ['entretenimiento/videojuegos', [VIDEO_GAME_CONSOLE],
            #  'Entretenimiento / Videojuegos', 1],
        ]

        discovered_entries = defaultdict(lambda: [])
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'

        for category_id, local_categories, section_name, category_weight in \
                ajax_resources:
            if category not in local_categories:
                continue

            page = 1
            local_urls = []
            done = False

            while not done:
                url = 'https://www.abcdin.cl/{}?p={}'.format(category_id, page)
                print(url)

                if page > 50:
                    raise Exception('Page overflow: ' + url)

                res = session.get(url)
                soup = BeautifulSoup(res.text, 'html.parser')
                products_grid = soup.find('ol',
                                          'products list items product-items')

                if not products_grid:
                    if page == 1:
                        raise Exception('Empty section: {}'.format(url))
                    else:
                        break

                product_cells = products_grid.findAll('li')

                for product_cell in product_cells:
                    sku = product_cell.find(
                        'div', 'price-final_price')['data-product-id']
                    product_url = 'https://www.abcdin.cl/catalog/product/' \
                                  'view/id/' + sku

                    if product_url in local_urls:
                        done = True
                        break

                    local_urls.append(product_url)
                page += 1

            for idx, product_url in enumerate(local_urls):
                discovered_entries[product_url].append({
                    'category_weight': category_weight,
                    'section_name': section_name,
                    'value': idx + 1
                })

        return discovered_entries

    @classmethod
    def discover_urls_for_keyword(cls, keyword, threshold, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        product_urls = []

        keyword = keyword.replace(' ', '+')

        url = 'https://www.abcdin.cl/tienda/ProductListingView?' \
              'ajaxStoreImageDir=%2Fwcsstore%2FABCDIN%2F&searchType=10' \
              '&resultCatEntryType=2&searchTerm={}&resultsPerPage=24' \
              '&sType=SimpleSearch&disableProductCompare=false' \
              '&catalogId=10001&langId=-1000&enableSKUListView=false' \
              '&ddkey=ProductListingView_6_-2011_1410&storeId=10001' \
              '&pageSize=1000'.format(keyword)

        soup = BeautifulSoup(session.get(url).text, 'html.parser')
        products_grid = soup.find('ul', 'grid_mode')

        if not products_grid:
            return []

        product_cells = products_grid.findAll('li')

        for product_cell in product_cells:
            product_listed_url = product_cell.find('a')['href']
            if 'ProductDisplay' in product_listed_url:
                parsed_product = urlparse(product_listed_url)
                parameters = parse_qs(parsed_product.query)

                parameters = {
                    k: v for k, v in parameters.items()
                    if k in ['productId', 'storeId']}

                newqs = urlencode(parameters, doseq=True)

                product_url = 'https://www.abcdin.cl/tienda/es/abcdin/' \
                              'ProductDisplay?' + newqs
            else:
                slug_with_sku = product_listed_url.split('/')[-1]
                product_url = 'https://www.abcdin.cl/tienda/es/abcdin/' \
                              + slug_with_sku

            product_urls.append(product_url)

            if len(product_urls) == threshold:
                return product_urls

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        response = session.get(url)

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        json_data = json.loads(
            soup.find('script', {'type': 'application/ld+json'}).text)
        model = json_data['model']

        if 'brand' in json_data:
            brand_tag = json_data['brand']
            name = '{} {}'.format(brand_tag.strip(), model)
        else:
            name = model

        prices_box = soup.find('div', 'price-final_price')
        normal_price = Decimal(remove_words(prices_box.find(
            'span', 'internet-price').find('span', 'price').text))
        offer_price_tag = prices_box.find('span', 'card-price')

        if offer_price_tag:
            offer_price = Decimal(remove_words(offer_price_tag.find(
                'span', 'price').text))
            if offer_price > normal_price:
                offer_price = normal_price
        else:
            offer_price = normal_price

        if soup.find('button', {'id': 'product-addtocart-button'}):
            stock = -1
        else:
            stock = 0

        sku = json_data['sku']
        description = ''
        for tag in soup.findAll('div', 'item-content-container'):
            description += '\n\n' + html_to_markdown(str(tag))

        picture_urls = []
        picture_tag_candidates = soup.findAll(
            'script', {'type': 'text/x-magento-init'})
        for picture_tag_candidate in picture_tag_candidates:
            if '[data-gallery-role=gallery-placeholder]' not in \
                    picture_tag_candidate.text:
                continue
            pictures_data = json.loads(picture_tag_candidate.text)
            for entry in pictures_data[
                    '[data-gallery-role=gallery-placeholder]'][
                    'mage/gallery/gallery']['data']:
                picture_urls.append(entry['full'])
            break

        if 'reacondicionado' in name.lower():
            condition = 'https://schema.org/RefurbishedCondition'
        else:
            condition = 'https://schema.org/NewCondition'

        product = Product(
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
            picture_urls=picture_urls,
            # video_urls=video_urls,
            # flixmedia_id=flixmedia_id,
            condition=condition,
            # has_virtual_assistant=has_virtual_assistant
        )

        return [product]

    @classmethod
    def banners(cls, extra_args=None):
        base_url = 'https://www.abcdin.cl/{}'

        sections_data = [
            [bs.HOME, 'Home', bs.SUBSECTION_TYPE_HOME, ''],
            [bs.ELECTRO_ABCDIN, 'Electro',
             bs.SUBSECTION_TYPE_CATEGORY_PAGE, 'electro'],
            [bs.ELECTRO_ABCDIN, 'Electro / TV y Video',
             bs.SUBSECTION_TYPE_MOSAIC,
             'electro/tv-y-video'],
            [bs.ELECTRO_ABCDIN, 'Electro / Audio', bs.SUBSECTION_TYPE_MOSAIC,
             'electro/audio'],
            [bs.ELECTRO_ABCDIN, 'Electro / Audífonos',
             bs.SUBSECTION_TYPE_MOSAIC,
             'electro/audifonos'],
            [bs.LINEA_BLANCA_ABCDIN, 'Línea Blanca',
             bs.SUBSECTION_TYPE_CATEGORY_PAGE,
             'linea-blanca'],
            [bs.LINEA_BLANCA_ABCDIN, 'Línea Blanca / Climatización',
             bs.SUBSECTION_TYPE_CATEGORY_PAGE,
             'linea-blanca/climatizacion'],
            [bs.LINEA_BLANCA_ABCDIN, 'Línea Blanca / Refrigeradores',
             bs.SUBSECTION_TYPE_CATEGORY_PAGE,
             'linea-blanca/refrigeradores'],
            [bs.LINEA_BLANCA_ABCDIN, 'Línea Blanca / Electrodomésticos',
             bs.SUBSECTION_TYPE_CATEGORY_PAGE,
             'linea-blanca/electrodomesticos'],
            [bs.TELEFONIA_ABCDIN, 'Telefonía',
             bs.SUBSECTION_TYPE_CATEGORY_PAGE, 'telefonia'],
            [bs.TELEFONIA_ABCDIN, 'Telefonía / Smartphones',
             bs.SUBSECTION_TYPE_MOSAIC, 'telefonia/smartphones'],
            [bs.TELEFONIA_ABCDIN, 'Telefonía / Smartwatch',
             bs.SUBSECTION_TYPE_MOSAIC, 'telefonia/smartwatch'],
            [bs.TELEFONIA_ABCDIN, 'Telefonía / Accesorios telefonía',
             bs.SUBSECTION_TYPE_MOSAIC, 'telefonia/accesorios-telefonia'],
            [bs.COMPUTACION_ABCDIN, 'Computación',
             bs.SUBSECTION_TYPE_CATEGORY_PAGE, 'computacion'],
            [bs.COMPUTACION_ABCDIN, 'Computación / Notebooks',
             bs.SUBSECTION_TYPE_MOSAIC, 'computacion/notebooks'],
            [bs.COMPUTACION_ABCDIN, 'Computación / Tablets',
             bs.SUBSECTION_TYPE_MOSAIC, 'computacion/tablets'],
            [bs.COMPUTACION_ABCDIN, 'Computación / Accesorios Computación',
             bs.SUBSECTION_TYPE_MOSAIC, 'computacion/accesorios-computacion'],
            [bs.COMPUTACION_ABCDIN, 'Computación / Mundo Gamer',
             bs.SUBSECTION_TYPE_MOSAIC, 'computacion/mundo-gamer'],
            [bs.COMPUTACION_ABCDIN, 'Computación / All In One',
             bs.SUBSECTION_TYPE_MOSAIC, 'computacion/all-in-one'],
            [bs.COMPUTACION_ABCDIN, 'Computación / Monitores y Proyectores',
             bs.SUBSECTION_TYPE_MOSAIC, 'computacion/monitores-y-proyectores'],
            [bs.COMPUTACION_ABCDIN, 'Computación / Monitores y Proyectores',
             bs.SUBSECTION_TYPE_MOSAIC, 'computacion/monitores-y-proyectores'],
            [bs.COMPUTACION_ABCDIN, 'Computación / Almacenamiento',
             bs.SUBSECTION_TYPE_MOSAIC, 'computacion/almacenamiento'],
            [bs.COMPUTACION_ABCDIN,
             'Computación / Impresoras y Multifuncionales',
             bs.SUBSECTION_TYPE_MOSAIC,
             'computacion/impresoras-y-multifuncionales'],
            [bs.ENTRETENIMIENTO_ABCDIN, 'Entretenimiento',
             bs.SUBSECTION_TYPE_CATEGORY_PAGE, 'entretenimiento'],
            [bs.ENTRETENIMIENTO_ABCDIN, 'Entretenimiento / Videojuegos',
             bs.SUBSECTION_TYPE_MOSAIC, 'entretenimiento/videojuegos'],
        ]

        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        banners = []

        for section, subsection, subsection_type, url_suffix in sections_data:
            url = base_url.format(url_suffix)
            print(url)

            if subsection_type == bs.SUBSECTION_TYPE_HOME:
                soup = BeautifulSoup(session.get(
                    'https://www.abcdin.cl/').text, 'html.parser')
                slider_tags = soup.find(
                    'div', 'owl-carousel-custom-2').findAll('a')

                for index, slider_tag in enumerate(slider_tags):
                    destination_urls = ['https://www.abcdin.cl' +
                                        slider_tag['href']]
                    picture_url = slider_tag.find('img')['data-src-desktop']

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
                response = session.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                slider_container_tag = soup.find('div', 'custom-slider')

                if not slider_container_tag:
                    logging.warning('Section without banners: ' + url)
                    continue

                slider_tags = slider_container_tag.findAll(
                    'div', 'banner-item')

                for index, slider_tag in enumerate(slider_tags):
                    if slider_tag.find('a'):
                        destination_urls = ['https://www.abcdin.cl' +
                                            slider_tag.find('a')['href']]
                    else:
                        destination_urls = []

                    image_tag = slider_tag.find('img')

                    if 'data-src-desktop' not in image_tag.attrs:
                        continue

                    picture_url = image_tag['data-src-desktop']
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
