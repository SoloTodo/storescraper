import json
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import TELEVISION


class LaCuracaoOnline(Store):
    country = ''
    currency = ''
    currency_iso = ''

    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # KEEPS ONLY LG PRODUCTS

        session = session_with_proxy(extra_args)
        product_urls = []

        if category != TELEVISION:
            return []

        page = 1
        done = False

        while not done:
            if page >= 15:
                raise Exception('Page overflow')

            url = 'https://www.lacuracaonline.com/{}/catalogsearch/' \
                  'result/index/?q=marca+lg&p={}' \
                  ''.format(cls.country, page)

            response = session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            product_containers = soup.findAll('li', 'product')

            if not product_containers and page == 1:
                raise Exception('Empty section: {}'.format(url))

            for container in product_containers:
                brand = container.find('strong', 'product-item-category')
                if brand is None or "LG" != brand.text.strip():
                    continue
                product_url = container.find('a')['href']

                if product_url in product_urls:
                    done = True
                    break
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        for i in range(5):
            response = session.get(url)

            if response.status_code == 404:
                return []

            if response.status_code == 200:
                break
        else:
            # Called if no "break" was executed
            raise Exception('Could not bypass Incapsulata')

        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('span', {'itemprop': 'name'}).text.strip()
        sku = soup.find('div', {'itemprop': 'sku'}).text.strip()
        price = Decimal(soup.find(
            'meta', {'property': 'product:price:amount'})['content'].strip())
        stock = -1

        pictures_data = re.search(r'"mage/gallery/gallery": ([\s\S]*?)\}\n',
                                  response.text).groups()[0]
        pictures_json = json.loads(pictures_data + '}')
        picture_urls = [tag['full'] for tag in pictures_json['data']]

        description = '{}\n\n{}'.format(
            html_to_markdown(
                str(soup.find('div', 'additional-attributes-wrapper'))),
            html_to_markdown(str(soup.find('div', 'description')))
        )

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
            cls.currency_iso,
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )

        return [p]
