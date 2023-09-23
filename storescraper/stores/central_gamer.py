import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MOTHERBOARD, COMPUTER_CASE, CPU_COOLER, \
    POWER_SUPPLY, MONITOR, HEADPHONES, MOUSE, KEYBOARD, GAMING_CHAIR, \
    PROCESSOR, VIDEO_CARD, RAM, SOLID_STATE_DRIVE
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words


class CentralGamer(StoreWithUrlExtensions):
    url_extensions = [
        ['open-box/tarjetas-de-video-openbox', VIDEO_CARD],
        ['open-box/sillas-open-box', GAMING_CHAIR],
        ['sillas-gamer-y-alfombras', GAMING_CHAIR],
        ['monitores-gamers', MONITOR],
        ['audifonos-gamer', HEADPHONES],
        ['teclados-gamer', KEYBOARD],
        ['mouses-gamer', MOUSE],
        ['tarjetas-de-video', VIDEO_CARD],
        ['placas-madre-pc', MOTHERBOARD],
        ['procesadores', PROCESSOR],
        ['todo-para-pc-gamer/memoria-ram', RAM],
        ['almacenamiento-para-pc', SOLID_STATE_DRIVE],
        ['gabinetes-gamer', COMPUTER_CASE],
        ['todo-para-pc-gamer/refrigeracion', CPU_COOLER],
        ['fuentes-de-poder', POWER_SUPPLY],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception('page overflow: ' + url_extension)
            url_webpage = 'https://www.centralgamer.cl/{}?page={}'.format(
                url_extension, page)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html.parser')
            product_containers = soup.findAll('div',
                                              'product-block__wrapper')
            if not product_containers:
                if page == 1:
                    logging.warning('Empty category: ' + url_extension)
                break
            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append(
                    'https://www.centralgamer.cl' + product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        if 'Lo sentimos, no pudimos encontrar esa página' in soup.text:
            return []

        name = soup.find('h1', 'product-heading__title').text
        form = soup.find('form', 'product-form')
        if form:
            key = form['action'].split('/')[-1]
        else:
            key = soup.find('meta', {'property': 'og:id'})['content']
        span_sku = soup.find('span', 'product-heading__detail--sku')
        if span_sku:
            sku = span_sku.text.replace('SKU: ', '')
        else:
            sku = None

        stock_tag = soup.find('meta', {'property': 'product:availability'})

        if stock_tag['content'] == 'instock':
            stock = -1
        else:
            stock = 0

        price_tags = soup.findAll('h2', 'product-heading__pricing')

        if len(price_tags) % 2 == 0:
            if 'product-heading__pricing--has-discount' in \
                    price_tags[0]['class']:
                offer_price = Decimal(remove_words(
                    price_tags[0].find('span').text))
                normal_price = Decimal(remove_words(
                    price_tags[1].find('span').text))
            else:
                offer_price = Decimal(remove_words(price_tags[0].text))
                normal_price = Decimal(remove_words(price_tags[1].text))
        elif len(price_tags) % 1 == 1:
            if 'product-heading__pricing--has-discount' in \
                    price_tags[0]['class']:
                offer_price = Decimal(remove_words(
                    price_tags[0].find('span').text))
            else:
                offer_price = Decimal(remove_words(price_tags[0].text))
            normal_price = offer_price
        else:
            raise Exception('Invalid price tags')

        picture_slider = soup.find('div', 'product-gallery__slider')
        if picture_slider:
            picture_urls = [tag['src'].split('?')[0] for tag in
                            picture_slider.findAll('img')]
        else:
            picture_urls = [
                soup.find('div', 'product-gallery').find('img')['data-src']]
        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            part_number=sku,
            picture_urls=picture_urls
        )
        return [p]
