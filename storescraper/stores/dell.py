import urllib

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Dell(Store):
    @classmethod
    def categories(cls):
        return [
            'Monitor',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != 'Monitor':
            return []

        product_urls = []
        session = session_with_proxy(extra_args)

        route = 'http://accessories.la.dell.com/sna/category.aspx?c=cl&' \
                'category_id=6481&cs=cldhs1&l=es&s=dhs&~ck=anav&sort=price&p='

        page = 1

        while True:
            url_webpage = route + str(page)

            soup = BeautifulSoup(session.get(url_webpage).text, 'html.parser')
            product_links = soup.findAll('a', 'hv_cluetip')

            if not product_links:
                if page == 1:
                    raise Exception('Empty category: ' + url_webpage)
                break

            for product_link in product_links:
                product_url = 'http://accessories.la.dell.com' + \
                               product_link['href']
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1').text.strip()
        price = soup.find('span', 'pricing_retail_nodiscount_price')
        stock = -1

        query_string = urllib.parse.urlparse(url).query
        sku = urllib.parse.parse_qs(query_string)['sku'][0]

        description = html_to_markdown(
            str(soup.find('div', {'id': 'cntTabsCnt'})))
        picture_urls = [
            soup.find('div', {'id': 'maincontentcnt'}).findAll('img')[1]['src']
        ]

        if price:
            price = Decimal(remove_words(price.string.split('$')[1]))
        else:
            configure_link_image = soup.find(
                'img', {'alt': 'Configurar y cotizar'})
            configure_link = configure_link_image.parent['href']
            soup = BeautifulSoup(session.get(configure_link).text,
                                 'html.parser')
            price = soup.find('span', 'pricing_retail_nodiscount_price')

            if not price:
                stock = 0
                price = Decimal(0)
            else:
                price = Decimal(remove_words(price.string.split('$')[1]))

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
            description=description,
            picture_urls=picture_urls
        )

        return [p]
