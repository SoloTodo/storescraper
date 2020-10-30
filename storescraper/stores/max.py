import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import TELEVISION, STEREO_SYSTEM, CELL, \
    REFRIGERATOR, OVEN, AIR_CONDITIONER, WASHING_MACHINE, \
    OPTICAL_DISK_PLAYER, STOVE, MONITOR, PROJECTOR, HEADPHONES


class Max(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION,
            STEREO_SYSTEM,
            CELL,
            REFRIGERATOR,
            OVEN,
            AIR_CONDITIONER,
            WASHING_MACHINE,
            OPTICAL_DISK_PLAYER,
            STOVE,
            MONITOR,
            PROJECTOR,
            HEADPHONES
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('video/televisores', TELEVISION),
            ('video/cine-en-casa', STEREO_SYSTEM),
            ('video/reproductores-dvd', OPTICAL_DISK_PLAYER),
            ('celulares/prepago', CELL),
            ('celulares/prepago/tigo', CELL),
            ('celulares/prepago/claro', CELL),
            ('celulares/prepago/movistar', CELL),
            ('celulares/liberados', CELL),
            ('lineablanca/combos-lavadora-y-secadora', WASHING_MACHINE),
            ('lineablanca/secadoras', WASHING_MACHINE),
            ('lineablanca/lavadoras', WASHING_MACHINE),
            ('lineablanca/empotrables', OVEN),
            ('lineablanca/estufas/hornos-empotrables', OVEN),
            ('electrodomesticos/microondas', OVEN),
            ('lineablanca/refrigeradoras/refrigeradoras', REFRIGERATOR),
            ('lineablanca/refrigeradoras/congeladores', REFRIGERATOR),
            ('lineablanca/estufas/estufas-a-gas', STOVE),
            ('lineablanca/estufas/estufas-electricas', STOVE),
            ('lineablanca/estufas/cooktops-a-gas', STOVE),
            ('lineablanca/estufas/cooktops-electricos', STOVE),
            ('computacion/proyectores', PROJECTOR),
            ('audio', STEREO_SYSTEM),
            ('audio/audio-para-casa/micro-componente', STEREO_SYSTEM),
            ('audio/audio-para-casa/mini-componente', STEREO_SYSTEM),
            ('audio/audio-para-casa/audio-vertical', STEREO_SYSTEM),
            ('audio/audio-portatil', STEREO_SYSTEM),
            ('audio/audio-multizona', STEREO_SYSTEM),
            ('computacion/pc-gaming/monitores', MONITOR),
            ('computacion/proyectores', PROJECTOR),
            ('audifonos', HEADPHONES),
        ]

        session = session_with_proxy(extra_args)

        product_urls = []
        lg_product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            page = 1
            done = False
            local_urls = []

            while not done:
                if page >= 10:
                    raise Exception('Page overflow')

                url = 'https://www.max.com.gt/{}?limit=30&p={}'.format(
                    category_path, page)
                soup = BeautifulSoup(session.get(url).text, 'html.parser')

                items = soup.findAll('div', 'item')

                if not items:
                    if page == 1:
                        logging.warning('No products for url {}'.format(url))
                    break

                for container in items:
                    logo = container.find('div', 'brand').find('img')
                    product_url = container.find('a')['href']

                    if product_url in local_urls:
                        done = True
                        break

                    if logo and logo['src'] == \
                            'https://www.max.com.gt/media/marcas/lg.jpg':
                        lg_product_urls.append(product_url)
                    local_urls.append(container.find('a')['href'])

                page += 1

            product_urls.extend(local_urls)

        return list(set(lg_product_urls))

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        data = session.get(url).text
        soup = BeautifulSoup(data, 'html.parser')

        sku_container = soup.find('h6', 'sku')
        if sku_container:
            sku = sku_container.text.strip()
        else:
            sku = soup.find('input', {'name': 'product'})['value']

        name = '{} ({})'.format(soup.find('h1').text.strip(), sku)

        if soup.find('input', {'id': 'qty_stock'}):
            stock = int(soup.find('input', {'id': 'qty_stock'})['value'])
        else:
            stock = -1

        price_container = soup.find('span', {'itemprop': 'price'})
        price = Decimal(price_container.text.replace('Q', '').replace(',', ''))

        picture_urls = [tag['href'] for tag in
                        soup.findAll('a', 'fancybox-button')]
        description = html_to_markdown(
            str(soup.find('div', 'tab-product-detail')))

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            'GTQ',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )

        return [p]
