import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import STORAGE_DRIVE, VIDEO_CARD, RAM, \
    COMPUTER_CASE, MOTHERBOARD, MONITOR, PROCESSOR, POWER_SUPPLY, CPU_COOLER, \
    VIDEO_GAME_CONSOLE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class TiendaCargoSud(Store):
    @classmethod
    def categories(cls):
        return [
            STORAGE_DRIVE,
            VIDEO_CARD,
            RAM,
            COMPUTER_CASE,
            MOTHERBOARD,
            MONITOR,
            PROCESSOR,
            POWER_SUPPLY,
            CPU_COOLER,
            VIDEO_GAME_CONSOLE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['almacenamiento', STORAGE_DRIVE],
            ['tarjetas-de-video', VIDEO_CARD],
            ['memorias-ram', RAM],
            ['gabinetes-de-pc', COMPUTER_CASE],
            ['placas-madres', MOTHERBOARD],
            ['monitor-de-pc', MONITOR],
            ['procesadores', PROCESSOR],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['refigeracion-liquida', CPU_COOLER],
            ['consolas-y-videojuegos', VIDEO_GAME_CONSOLE]
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)

                url_webpage = 'https://tiendacargosud.cl/collections' \
                              '/{}?page={}'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.find('div', {
                    'id': 'CollectionSection'}).findAll('div', 'grid__item')

                if len(product_containers) == 1:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(
                        'https://tiendacargosud.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'h2').text.strip()
        sku = soup.find('form', {'action': '/cart/add'})['id'].split('-')[-1]
        if soup.find('button', {'name': 'add'}).text.strip() == 'Agotado':
            stock = 0
        else:
            stock = int(soup.find('div', 'product__inventory').text.split()[0])
        if soup.find('span', 'product__price on-sale'):
            price = Decimal(remove_words(
                soup.find('span', 'product__price on-sale').text.strip()))
        else:
            price = Decimal(
                remove_words(soup.find('span', 'product__price').text.strip()))
        picture_urls = ['https:' + tag['href'] for tag in
                        soup.find('div', 'product__thumbs').findAll('a')]
        picture_urls.append(
            'https:' + soup.find('div', 'product-image-main').find('img')[
                'data-photoswipe-src'])
        description = html_to_markdown(str(
            soup.find('div', 'product-single__description')))
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
            'CLP',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )
        return [p]
