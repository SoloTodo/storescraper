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
            'Tablet',
            'Television',
            'OpticalDiskPlayer',
            'Cell',
            'Printer',
            'ExternalStorageDrive',
            'Mouse',
            'UsbFlashDrive',
            'StereoSystem',
            'Headphones',
            'VideoGameConsole',
            'WashingMachine',
            'Refrigerator',
            'Stove',
            'Oven',
            'VacuumCleaner',
            'WaterHeater',
            'SpaceHeater',
            'AirConditioner',
            'Wearable',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        extensions = [
            ['notebooks', 'Notebook'],
            ['tablet', 'Tablet'],
            ['led', 'Television'],
            ['smart-tv', 'Television'],
            ['oled-i-qled-i-curvo', 'Television'],
            ['dvd-i-blu-ray', 'OpticalDiskPlayer'],
            ['smartphones', 'Cell'],
            ['teléfonos-básicos', 'Cell'],
            ['impresoras-laser', 'Printer'],
            # ['impresoras-a-tinta', 'Printer'],
            ['multifuncionales', 'Printer'],
            ['disco-duro-externo', 'ExternalStorageDrive'],
            ['mouse-i-teclados', 'Mouse'],
            ['pendrives', 'UsbFlashDrive'],
            ['parlantes', 'StereoSystem'],
            ['equipos-de-música', 'StereoSystem'],
            ['karaoke', 'StereoSystem'],
            ['home-theater', 'StereoSystem'],
            ['audífonos', 'Headphones'],
            ['todo-consolas', 'VideoGameConsole'],
            ['lavadoras', 'WashingMachine'],
            ['lavadoras---secadoras', 'WashingMachine'],
            ['secadoras', 'WashingMachine'],
            ['centrífugas', 'WashingMachine'],
            ['side-by-side', 'Refrigerator'],
            ['no-frost', 'Refrigerator'],
            ['frío-directo', 'Refrigerator'],
            ['frigobar', 'Refrigerator'],
            ['freezer', 'Refrigerator'],
            ['cocinas-a-gas', 'Stove'],
            ['encimeras', 'Stove'],
            ['microondas', 'Oven'],
            ['hornos-eléctricos', 'Oven'],
            ['aspiradoras', 'VacuumCleaner'],
            ['calefont', 'WaterHeater'],
            ['estufas-a-parafina', 'SpaceHeater'],
            ['estufas-a-gas', 'SpaceHeater'],
            ['estufas-eléctricas', 'SpaceHeater'],
            ['enfriadores', 'AirConditioner'],
            ['accesorios-teléfonos', 'Wearable']
        ]

        session = session_with_proxy(extra_args)

        product_urls = []

        for extension, local_category in extensions:
            if local_category != category:
                continue

            url = 'https://www.lapolar.cl/on/demandware.store/' \
                  'Sites-LaPolar-Site/es_CL/Search-UpdateGrid?' \
                  'cgid={}&srule=most-popular&start=0&sz=150'.format(extension)

            print(url)
            response = session.get(url).text
            soup = BeautifulSoup(response, 'html.parser')

            products = soup.findAll('div', 'lp-product-tile')
            product_urls = []

            for product in products:
                product_url = 'https://www.lapolar.cl{}'\
                    .format(product.find('a')['href'])
                product_urls.append(product_url)

        # if category == 'Cell':
        #     url = 'https://www.lapolar.cl/internet/catalogo/fbind/postplu/' \
        #           'destacados-smartphones'
        #     cells_data = json.loads(session.get(url).text)['lista_completa']
        #
        #     for row in cells_data:
        #         for cell in row['sub_lista']:
        #             product_url = 'https://tienda.lapolar.cl/producto/sku/{}'
        #                           ''.format(cell['prid'])
        #             product_urls.append(product_url)

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

        name = soup.find('div', 'product-name').text.strip()
        sku = soup.find('span', 'sku-code-value').text.strip()

        prices = soup.find('div', 'prices')
        normal_price = prices.find('p', 'internet')

        offer_price = prices.find('p', 'la-polar') \
            .find('span', 'price-value').text.strip() \
            .replace('$', '').replace('.', '')
        offer_price = Decimal(offer_price)

        if not normal_price:
            normal_price = offer_price
        else:
            normal_price = normal_price \
                .find('span', 'price-value').text.strip() \
                .replace('$', '').replace('.', '')
            normal_price = Decimal(normal_price)

        if offer_price > normal_price:
            offer_price = normal_price

        stock = -1

        description = html_to_markdown(
            str(soup.find('div', 'description-wrapper')))

        picture_containers = soup.findAll('div', 'primary-image')
        picture_urls = [picture.find('img')['src'] for picture in picture_containers]

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
             'https://www.lapolar.cl/'],
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
                images = soup.findAll('div', 'hero-banner-wrapper')

                for index, image in enumerate(images):
                    picture_url = 'https://www.lapolar.cl{}'\
                        .format(image.find('img')['data-src'])
                    destination_urls = [image.find('a')['href']]

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
                    destination_urls = [image.find('a')['href']]

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
