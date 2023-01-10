from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MONITOR, NOTEBOOK, TABLET, MOUSE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class UltraPc(Store):

    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            TABLET,
            MOUSE,
            MONITOR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['equipos-de-computo', NOTEBOOK],
            ['tablets-e-ipads', TABLET],
            ['monitores', MONITOR],
            ['accesorios', MOUSE],

        ]
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            url_webpage = 'https://www.ultrapc.cl/categoria-producto/{}/' \
                          '?ppp=-1'.format(url_extension)
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, 'html.parser')
            products_container = soup.find('ul', 'products')

            if not products_container:
                continue

            for cont in products_container.findAll('div', 'product-outer'):
                product_url = \
                    cont.find('a', 'woocommerce-LoopProduct-link')[
                        'href']
                product_urls.append(product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text
        sku = soup.find('link', {'type': 'application/json'})['href'].split(
            '/')[-1]
        if soup.find('span', 'electro-stock-availability').find('p', 'stock'):
            stock = -1
        else:
            stock = 0

        offer_price_tags = ['product:sale_price:amount',
                            'product:price:amount']
        for tag in offer_price_tags:
            price_tag = soup.find('meta', {'property': tag})
            if price_tag:
                offer_price = Decimal(price_tag['content'])
                break
        else:
            raise Exception('No offer price found')

        normal_price_tags = ['precio_oferta', 'precio_con_iva_tbk']
        for tag in normal_price_tags:
            price_tag = soup.find('span', tag)
            if price_tag:
                normal_price = Decimal(remove_words(price_tag.text))
                break
        else:
            raise Exception('No normal price found')

        picture_urls = [tag['src'] for tag in soup.find(
            'div', 'woocommerce-product-gallery').findAll(
            'img')]
        condition_text = soup.find(
            'span', 'condicion_item_ultrapc').text.strip()
        if condition_text == 'NUEVO':
            condition = 'https://schema.org/NewCondition'
        else:
            condition = 'https://schema.org/RefurbishedCondition'

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
            condition=condition
        )
        return [p]
