import urllib

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Conelectric(Store):
    @classmethod
    def categories(cls):
        return [
            'Lamp',
            'LightTube',
            'LightProjector'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        base_url = 'https://conelectric.cl'
        category_codes = [
            # Ampolletas LED
            ['30', 'Lamp'],
            # Tubos LED
            ['383', 'LightTube'],
            # Proyectores LED
            ['393', 'LightProjector'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/x-www-form-urlencoded'

        for category_code, local_category in category_codes:
            if local_category != category:
                continue

            offset = 0

            while True:
                if offset >= 200:
                    raise Exception('Page overflow:' + category_code)

                request_body = 'num={}&page=dinamic&key={}&id=0'.format(
                    offset, category_code)
                soup = BeautifulSoup(session.post(
                    base_url + '/add/', request_body).text, 'html.parser')

                containers = soup.findAll('article', 'box-productos')
                if not containers:
                    if offset == 0:
                        raise Exception('Empty category: ' + category_code)
                    break

                for container in containers:
                    product_url = base_url + container.find('a')['href']

                    encoded_path = urllib.parse.quote(urllib.parse.urlparse(
                        product_url).path)
                    product_url = 'https://conelectric.cl' + encoded_path

                    product_urls.append(product_url)

                offset += 20

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', 'title-producto').text.strip()
        sku = soup.findAll('span', 'azul')[1].text.strip()

        price = soup.find('p', 'box-actual').text

        if not price or price == u'$ ':
            stock = 0
            price = Decimal(0)
        else:
            stock = -1
            price = Decimal(remove_words(price))

        description = html_to_markdown(str(soup.find('ul', 'listAtributos')))

        picture_tag = soup.find(
            'article', {'id': 'ficha-producto'}).find('figure').find('img')
        picture_urls = ['https://conelectric.cl' +
                        picture_tag['src'].replace(' ', '%20')]

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
