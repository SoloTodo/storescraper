import logging
from bs4 import BeautifulSoup
from storescraper.categories import TELEVISION
from storescraper.stores.peru_stores import PeruStores
from storescraper.utils import session_with_proxy


class Multicenter(PeruStores):
    base_url = 'https://www.multicenter.com.bo'
    currency = 'BOB'

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Only returns LG products

        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        product_urls = []

        url_webpage = 'https://www.multicenter.com.bo/busca?ft=Lg'
        print(url_webpage)
        data = session.get(url_webpage).text
        soup = BeautifulSoup(data, 'html.parser')
        product_containers = soup.findAll('div', 'product-box')
        if not product_containers:
            logging.warning('Empty category')
        for container in product_containers:
            product_url = container.find('a')['href']
            product_urls.append(product_url)
        return product_urls
