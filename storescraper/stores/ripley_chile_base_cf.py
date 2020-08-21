import json
import time

import requests
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import get_cf_session, session_with_proxy, \
    HeadlessChrome, CF_REQUEST_HEADERS


class RipleyChileBaseCf(Store):
    preferred_products_for_url_concurrency = 3

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
            'DishWasher'
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
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        return [category]

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        return cls._products_for_url(url, category, extra_args)

    @classmethod
    def _products_for_url(cls, url, category=None, extra_args=None, retries=9):
        category_paths = [
            ['tecno/computacion/notebooks', ['Notebook'],
             'Tecno > Computación > Notebooks', 1],
            ['tecno/computacion/notebooks-gamer', ['Notebook'],
             'Tecno > Computación > Notebooks gamer', 1],
            ['tecno/computacion/tablets-y-e-readers', ['Tablet'],
             'Tecno > Computación > Tablets y E-readers', 1],
            ['tecno/impresoras-y-tintas', ['Printer'],
             'Tecno > Computación > Impresoras y Tintas', 1],
            ['tecno/computacion/almacenamiento',
             ['UsbFlashDrive', 'ExternalStorageDrive'],
             'Tecno > Computación > Almacenamiento', 0.5],
            ['tecno/computacion/pc-all-in-one', ['AllInOne'],
             'Tecno > Computación > PC/All in one', 1],
            ['tecno/computacion/proyectores-y-monitores',
             ['Monitor', 'Projector'],
             'Tecno > Computación > Proyectores y monitores', 0.5],
            ['tecno/television', ['Television'],
             'Tecno > Televisión', 1],
            ['tecno/television/smart-tv', ['Television'],
             'Tecno > Televisión > Smart TV', 1],
            ['electro/refrigeracion', ['Refrigerator'],
             'Electro > Refrigeración', 1],
            ['electro/refrigeracion/side-by-side', ['Refrigerator'],
             'Electro > Refrigeración > Side by Side', 1],
            ['electro/refrigeracion/refrigeradores', ['Refrigerator'],
             'Electro > Refrigeración > Refrigeradores', 1],
            ['electro/refrigeracion/freezers-y-congeladores', ['Refrigerator'],
             'Electro > Refrigeración > Freezers y congeladores', 1],
            ['electro/refrigeracion/frigobar', ['Refrigerator'],
             'Electro > Refrigeración > Frigobar', 1],
            ['electro/refrigeracion/door-in-door', ['Refrigerator'],
             'Electro > Refrigeración > Door in Door', 1],
            ['electro/cocina/cocinas', ['Stove'],
             'Electro > Cocina > Cocinas', 1],
            ['electro/electrodomesticos/hornos-y-microondas', ['Oven'],
             'Electro > Electrodomésticos > Hornos y Microondas', 1],
            ['electro/cocina/lavavajillas', ['DishWasher'],
             'Electro > Cocina > Lavavajillas', 1],
            ['electro/aseo/aspiradoras-y-enceradoras', ['VacuumCleaner'],
             'Electro > Aseo > Aspiradoras y enceradoras', 1],
            ['electro/lavanderia', ['WashingMachine'],
             'Electro > Lavandería', 1],
            ['electro/lavanderia/lavadoras', ['WashingMachine'],
             'Electro > Lavandería > Lavadoras', 1],
            ['electro/lavanderia/secadoras', ['WashingMachine'],
             'Electro > Lavandería > Secadoras', 1],
            ['electro/lavanderia/lavadora-secadora', ['WashingMachine'],
             'Electro > Lavandería > Lavadora-secadora', 1],
            ['electro/lavanderia/doble-carga', ['WashingMachine'],
             'Electro > Lavandería > Doble carga', 1],
            # ['tecno/telefonia/android', ['Cell'],
            #  'Tecno > Telefonía > Android', 1],
            ['tecno/telefonia/iphone', ['Cell'],
             'Tecno > Telefonía > iPhone', 1],
            ['tecno/telefonia/samsung', ['Cell'],
             'Tecno > Telefonía > Samsung', 1],
            ['tecno/telefonia/huawei', ['Cell'],
             'Tecno > Telefonía > Huawei', 1],
            ['tecno/telefonia/xiaomi', ['Cell'],
             'Tecno > Telefonía > Xiaomi', 1],
            ['tecno/telefonia/motorola', ['Cell'],
             'Tecno > Telefonía > Motorola', 1],
            ['tecno/telefonia/basicos', ['Cell'],
             'Tecno > Telefonía > Básicos', 1],
            ['tecno/fotografia-y-video/camaras-reflex', ['Camera'],
             'Tecno > Fotografía y Video > Camaras reflex', 1],
            ['tecno/fotografia-y-video/semi-profesionales', ['Camera'],
             'Tecno > Fotografía y Video > Semi profesionales', 1],
            ['tecno/audio-y-musica/equipos-de-musica', ['StereoSystem'],
             'Tecno > Audio y Música > Equipos de música', 1],
            ['tecno/audio-y-musica/parlantes-portables', ['StereoSystem'],
             'Tecno > Audio y Música > Parlantes Portables', 1],
            ['tecno/audio-y-musica/soundbar-y-home-theater', ['StereoSystem'],
             'Tecno > Audio y Música > Soundbar y Home theater', 1],
            ['tecno/television/bluray-dvd-y-tv-portatil',
             ['OpticalDiskPlayer'],
             'Tecno > Televisión > Bluray -DVD y TV Portátil', 1],
            ['tecno/playstation/consolas', ['VideoGameConsole'],
             'Tecno > PlayStation > Consolas', 1],
            ['tecno/nintendo/consolas', ['VideoGameConsole'],
             'Tecno > Nintendo > Consolas', 1],
            # ['tecno/xbox/consolas', ['VideoGameConsole'],
            #  'Tecno > Xbox > Consolas', 1],
            ['electro/climatizacion/aire-acondicionado',
             ['AirConditioner'],
             'Electro > Climatización > Ventiladores y aire acondicionado', 1],
            ['electro/climatizacion/purificadores-y-humificadores',
             ['AirConditioner'],
             'Electro > Climatización > Purificadores y humidificadores', 1],
            ['electro/climatizacion/estufas-y-calefactores',
             ['SpaceHeater'],
             'Electro > Climatización > Estufas y calefactores', 1],
            ['tecno/corner-smartwatch/garmin', ['Wearable'],
             'Tecno > Telefonía > Smartwatches y Wearables > Garmin', 1],
            ['tecno/corner-smartwatch/polar', ['Wearable'],
             'Tecno > Telefonía > Smartwatches y Wearables > Polar', 1],
            ['tecno/corner-smartwatch/apple-watch', ['Wearable'],
             'Tecno > Telefonía > Smartwatches y Wearables > Apple Watch', 1],
            ['tecno/corner-smartwatch/samsung', ['Wearable'],
             'Tecno > Telefonía > Smartwatches y Wearables > Samsung', 1],
            ['tecno/corner-smartwatch/huawei', ['Wearable'],
             'Tecno > Telefonía > Smartwatches y Wearables > Huawei', 1],
            ['tecno/especial-audifonos', ['Headphones'],
             'Tecno > Audio y Música > Audífonos', 1],
        ]

        debug = extra_args.get('debug', False)
        if debug:
            session = session_with_proxy(extra_args)
        else:
            session = get_cf_session(extra_args)

        url_base = 'https://simple.ripley.cl/{}?page={}'
        product_dict = {}

        for e in category_paths:
            category_path, local_categories, section_name, category_weight = e

            if category not in local_categories:
                continue

            page = 1
            position = 1

            while True:
                if page > 100:
                    raise Exception('Page overflow')

                category_url = url_base.format(category_path, page)
                # print(category_url)
                response = session.get(category_url, allow_redirects=False)

                if response.status_code != 200 and page == 1:
                    if debug:
                        print('Invalid section: ' + category_url)
                        break
                    else:
                        raise Exception('Invalid section: ' + category_url)

                soup = BeautifulSoup(response.text, 'html.parser')
                products_data = soup.find('script',
                                          {'type': 'application/ld+json'})

                products_soup = soup.find('div', 'catalog-container')

                if debug:
                    if not products_data or not products_soup:
                        print('Empty path: {}'.format(url))

                    break

                if not products_data or not products_soup:
                    if page == 1:
                        raise Exception('Empty path: {}'.format(url))
                    else:
                        break

                products_elements = products_soup.findAll(
                    'div', 'ProductItem__Row')

                if not products_elements:
                    products_elements = products_soup.findAll(
                        'a', 'catalog-product-item')

                products_json = json.loads(products_data.text)[
                    'itemListElement']

                assert(len(products_elements) == len(products_json))

                for product_json in products_json:
                    product_element = products_elements[
                        int(product_json['position']) - 1]
                    product_data = product_json['item']

                    brand = product_data.get('brand', '').upper()

                    # If the product is LG or Samsung and is sold directly by
                    # Ripley (not marketplace) obtain the full data
                    if brand in ['LG', 'SAMSUNG'] and 'MPM' not in \
                            product_data['sku']:
                        from storescraper.stores import Ripley

                        product = product_dict.get(product_data['sku'], None)
                        if not product:
                            url = cls._get_entry_url(product_element)
                            print(url)
                            products = Ripley.products_for_url(
                                url, category, extra_args)
                            if products:
                                product = products[0]
                    else:
                        product = cls._assemble_product(
                            product_data, product_element, category)

                    if product:
                        if product.sku in product_dict:
                            product_to_update = product_dict[product.sku]
                        else:
                            product_dict[product.sku] = product
                            product_to_update = product

                        product_to_update.positions[section_name] = position

                    position += 1

                page += 1

        products_list = [p for p in product_dict.values()]

        return products_list

    @classmethod
    def _get_entry_url(cls, element):
        # Element Data (Varies by page)
        if element.name == 'div':
            url_extension = element.find('a')['href']
        else:
            url_extension = element['href']

        url = 'https://simple.ripley.cl{}'.format(url_extension)
        return url

    @classmethod
    def _assemble_product(cls, data, element, category):
        # Element Data (Varies by page)
        if element.name == 'div':
            element_name = element.find(
                'a', 'ProductItem__Name').text.replace('  ', ' ').strip()
        else:
            element_name = element.find(
                'div', 'catalog-product-details__name')\
                .text.replace('  ', ' ').strip()

        # Common

        # This is removing extra white spaces in between words
        # If not done, sometimes it will not be equal to element name
        data_name = " ".join([a for a in data['name'].split(' ') if a != ''])\
            .strip()

        assert(element_name == data_name)

        # Remove weird characters, e.g.
        # https://simple.ripley.cl/tv-portatil-7-negro-mpm00003032468
        name = data_name.encode('ascii', 'ignore').decode('ascii')
        sku = data['sku']
        url = cls._get_entry_url(element)
        picture_urls = ['https:{}'.format(data['image'])]

        if data['offers']['price'] == 'undefined':
            return None

        offer_price = Decimal(data['offers']['price'])
        normal_price_container = element.find(
            'li', 'catalog-prices__offer-price')

        if normal_price_container:
            normal_price = Decimal(
                element.find('li', 'catalog-prices__offer-price')
                .text.replace('$', '').replace('.', ''))
        else:
            normal_price = offer_price

        if normal_price < offer_price:
            offer_price = normal_price

        stock = 0
        if data['offers']['availability'] == 'http://schema.org/InStock':
            stock = -1

        if '-mpm' in url:
            seller = 'External seller'
        else:
            seller = None

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
            picture_urls=picture_urls,
            seller=seller
        )

        return p

    @classmethod
    def preflight(cls, extra_args=None):
        # Obtain Cloudflare bypass cookie
        if extra_args is None:
            raise Exception("extra_args should contain the parameters to "
                            "obtain the Cloudflare session cookie or the "
                            "'debug' flag if testing locally")
        if 'debug' in extra_args:
            return {}

        proxy = 'http://{}:{}@{}:{}'.format(
            extra_args['PROXY_USERNAME'],
            extra_args['PROXY_PASSWORD'],
            extra_args['PROXY_IP'],
            extra_args['PROXY_PORT'],
        )
        with HeadlessChrome(images_enabled=True, proxy=proxy,
                            headless=True) as driver:
            driver.get('https://simple.ripley.cl')
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            hcaptcha_script_tag = soup.find('script', {'data-type': 'normal'})
            website_key = hcaptcha_script_tag['data-sitekey']

            # Anti captcha request
            request_body = {
                "clientKey": extra_args['KEY'],
                "task":
                    {
                        "type": "HCaptchaTask",
                        "websiteURL": "https://simple.ripley.cl/",
                        "websiteKey": website_key,
                        "proxyType": "http",
                        "proxyAddress": extra_args['PROXY_IP'],
                        "proxyPort": extra_args['PROXY_PORT'],
                        "proxyLogin": extra_args['PROXY_USERNAME'],
                        "proxyPassword": extra_args['PROXY_PASSWORD'],
                        "userAgent": CF_REQUEST_HEADERS['User-Agent']
                    }
            }
            print('Sending anti-captcha task')
            print(json.dumps(request_body, indent=2))
            anticaptcha_session = requests.Session()
            anticaptcha_session.headers['Content-Type'] = 'application/json'
            response = json.loads(anticaptcha_session.post(
                'http://api.anti-captcha.com/createTask',
                json=request_body).text)

            print('Anti-captcha task request response')
            print(json.dumps(response, indent=2))

            assert response['errorId'] == 0

            task_id = response['taskId']
            print('TaskId', task_id)

            # Wait until the task is ready...
            get_task_result_params = {
                "clientKey": extra_args['KEY'],
                "taskId": task_id
            }
            print(
                'Querying for anti-captcha response (wait 10 secs per retry)')
            print(json.dumps(get_task_result_params, indent=4))
            retries = 1
            hcaptcha_response = None
            while not hcaptcha_response:
                if retries > 60:
                    raise Exception('Failed to get a token in time')
                print('Retry #{}'.format(retries))
                time.sleep(10)
                res = json.loads(anticaptcha_session.post(
                    'https://api.anti-captcha.com/getTaskResult',
                    json=get_task_result_params).text)

                assert res['errorId'] == 0, res
                assert res['status'] in ['processing', 'ready'], res
                if res['status'] == 'ready':
                    print('Solution found')
                    hcaptcha_response = res['solution']['gRecaptchaResponse']
                    break
                retries += 1

            print(hcaptcha_response)
            for field in ['g-recaptcha-response', 'h-captcha-response']:
                driver.execute_script("document.querySelector('[name=\""
                                      "{0}\"]').remove(); "
                                      "var foo = document.createElement('"
                                      "input'); foo.setAttribute('name', "
                                      "'{0}'); "
                                      "foo.setAttribute('value','{1}'); "
                                      "document.getElementsByTagName('form')"
                                      "[0].appendChild(foo);".format(
                                        field, hcaptcha_response))
            driver.execute_script("document.getElementsByTagName('form')"
                                  "[0].submit()")

            d = {
                "proxy": proxy,
                "cf_clearance": driver.get_cookie('cf_clearance')['value'],
                "__cfduid": driver.get_cookie('__cfduid')['value']
            }
            return d
