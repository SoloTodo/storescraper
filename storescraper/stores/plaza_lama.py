import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import AIR_CONDITIONER, STOVE, CELL_ACCESORY, \
    OVEN, WASHING_MACHINE, REFRIGERATOR, STEREO_SYSTEM, OPTICAL_DISK_PLAYER, \
    TELEVISION


class PlazaLama(Store):
    @classmethod
    def categories(cls):
        return [
            AIR_CONDITIONER,
            STOVE,
            CELL_ACCESORY,
            OVEN,
            WASHING_MACHINE,
            REFRIGERATOR,
            STEREO_SYSTEM,
            OPTICAL_DISK_PLAYER,
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('453-aires', AIR_CONDITIONER),
            ('459-estufa', STOVE),
            ('460-extractor', CELL_ACCESORY),
            ('464-microondas', OVEN),
            ('501-accesorio-para-lavadora', WASHING_MACHINE),
            ('502-lavadora', WASHING_MACHINE),
            ('503-lavadora-secadora', WASHING_MACHINE),
            ('504-secadora', WASHING_MACHINE),
            ('511-neveras', REFRIGERATOR),
            ('514-bocinas-portatiles', STEREO_SYSTEM),
            ('515-sound-bar', STEREO_SYSTEM),
            ('1388-minicomponentes', STEREO_SYSTEM),
            ('517-dvd', OPTICAL_DISK_PLAYER),
            ('518-televisores', TELEVISION),
            ('553-accesorios-tec', CELL_ACCESORY),
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            page = 1
            done = False

            while not done:
                if page >= 30:
                    raise Exception('Page overflow')

                url = 'https://plazalama.com.do/{}?page={}'.format(
                    category_path, page)
                print(url)

                response = session.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                with open('pl.html', 'w') as f:
                    f.write(str(soup))
                items = soup.findAll('div', 'js-product-miniature-wrapper')

                if not items:
                    if page == 1:
                        logging.warning('Empty category:' + url)
                    break

                for item in items:
                    product_link = item.find('h3', 'product-title').find('a')
                    if 'LG' not in product_link.text.upper():
                        continue
                    product_urls.append(product_link['href'])

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        sku = soup.find('span', {'itemprop': 'sku'}).text.strip()
        name = soup.find('h1', 'page-title').text.strip()
        add_to_cart_button = soup.find('button', 'add-to-cart')

        if 'disabled' in add_to_cart_button.attrs:
            stock = 0
        else:
            stock = -1

        price = Decimal(soup.find('span', {'itemprop': 'price'})['content'])
        picture_urls = [x['data-image-large-src']
                        for x in soup.findAll('img')
                        if 'data-image-large-src' in x.attrs]

        description = html_to_markdown(
            str(soup.find('div', 'product-description')))

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
            'DOP',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )

        return [p]
