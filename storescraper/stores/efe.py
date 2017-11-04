import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Efe(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['3074457345616709688', 'Notebook'],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            url = 'http://www.efe.com.pe/webapp/wcs/stores/servlet/' \
                  'ProductListingView?resultsPerPage=1000&storeId=10152&' \
                  'categoryId=' + category_path
            soup = BeautifulSoup(session.get(url).text, 'html.parser')

            a_links = soup.findAll('div', 'product')

            if not a_links:
                raise Exception('Empty category: ' + url)

            for container in a_links:
                product_url = container.find('a')['href']
                product_urls.append(product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('h1').text
        sku = soup.find('meta', {'name': 'pageIdentifier'})['content'].strip()

        price_container = soup.find('span', {'itemprop': 'price'}).text
        price = Decimal(price_container.split('/.')[1].replace(',', ''))

        description = '\n\n'.join([html_to_markdown(str(panel)) for panel in
                                   soup.findAll('div', {'role': 'tabpanel'})])

        picture_paths = [soup.find('img', {'id': 'productMainImage'})['src']]

        picture_paths.extend(
            re.findall(r"JavaScript:changeThumbNail\('.+?','(.+?)'\)",
                       page_source)[:-1])

        picture_urls = ['http://www.efe.com.pe' + path for path in
                        picture_paths]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            -1,
            price,
            price,
            'PEN',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
