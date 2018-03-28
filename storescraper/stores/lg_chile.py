from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class LgChile(Store):
    base_url = 'http://www.lg.com'

    @classmethod
    def categories(cls):
        return [
            'Television',
            'OpticalDiskPlayer',
            'StereoSystem',
            'HomeTheater',
            'Projector',
            'Cell',
            'Refrigerator',
            'Oven',
            'WashingMachine',
            'VacuumCleaner',
            'Monitor',
            'CellAccesory',
            'Notebook',
            'OpticalDrive'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ('CT20106005', 'CT20106005', 'Television', True),
            ('CT20106005', 'CT20106005', 'Television', False),
            ('CT20106017', 'CT20106017', 'OpticalDiskPlayer', False),
            ('CT20106017', 'CT20106019', 'OpticalDiskPlayer', True),
            ('CT20106017', 'CT20106019', 'OpticalDiskPlayer', False),
            ('CT20106020', 'CT20106021', 'StereoSystem', True),
            ('CT20106020', 'CT20106021', 'StereoSystem', False),
            ('CT30016640', 'CT30016642', 'StereoSystem', True),
            ('CT30016640', 'CT31903290', 'StereoSystem', True),
            ('CT20106023', 'CT20106025', 'HomeTheater', True),
            ('CT20106023', 'CT20106025', 'HomeTheater', False),
            ('CT30006480', 'CT30006480', 'Projector', True),
            ('CT20106027', 'CT20106027', 'Cell', True),
            ('CT20106027', 'CT20106027', 'Cell', False),
            ('CT30011860', 'CT30011860', 'Cell', True),
            ('CT20106034', 'CT20106034', 'Refrigerator', True),
            ('CT20106034', 'CT20106034', 'Refrigerator', False),
            ('CT20106039', 'CT20106039', 'Oven', False),
            ('CT20106044', 'CT20106044', 'WashingMachine', True),
            ('CT20106044', 'CT20106044', 'WashingMachine', False),
            ('CT20106040', 'CT20106040', 'WashingMachine', True),
            ('CT20106040', 'CT20106040', 'WashingMachine', False),
            ('CT20106045', 'CT20106045', 'VacuumCleaner', False),
            ('CT20106054', 'CT20106054', 'Monitor', True),
            ('CT20106054', 'CT20106054', 'Monitor', False),
            ('CT31903594', 'CT31903594', 'CellAccesory', True),
            ('CT30018920', 'CT30018920', 'Notebook', True),
            ('CT32002362', 'CT32002362', 'Notebook', True),
            ('CT20106055', 'CT20106055', 'OpticalDrive', True),
            ('CT20106055', 'CT20106055', 'OpticalDrive', False),
            # ('CT30016640', 'CT30016642', 'StereoSystem', False),
            # ('CT30016640', 'CT31903290', 'StereoSystem', False),
            # ('CT30006480', 'CT30006480', 'Projector', False),
            # ('CT30011860', 'CT30011860', 'Cell', False),
            # ('CT20106039', 'CT20106039', 'Oven', True),
            # ('CT20106045', 'CT20106045', 'VacuumCleaner', True),
        ]

        discovered_urls = []

        session = session_with_proxy(extra_args)

        for category_id, subcategory_id, local_category, is_active in \
                category_paths:
            if local_category != category:
                continue
            print(category_id, subcategory_id, local_category, is_active)

            if is_active:
                status = 'ACTIVE'
            else:
                status = 'DISCONTINUED'

            category_url = '{}/cl/lgcompf4/category/filter.lg?page=view-all&' \
                           'categoryId={}&subCategoryId={}&status={}'.format(
                            cls.base_url, category_id, subcategory_id, status)

            print(category_url)

            soup = BeautifulSoup(session.get(category_url, timeout=20).text,
                                 'html.parser')

            article_containers = soup.findAll(
                'li', {'itemtype': 'http://schema.org/Product'})

            if not article_containers:
                raise Exception('Empty category: {} - {} - {}'.format(
                    category_id, subcategory_id, is_active))

            for article in article_containers:
                product_url = cls.base_url + article.find(
                    'p', 'model-name').find('a')['href']
                discovered_urls.append(product_url)

        return discovered_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url, timeout=20)

        if response.url != url:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        variant_urls = []

        colors_container = soup.find('div', 'list-colors')

        if colors_container:
            for color_link in colors_container.findAll('a'):
                variant_url = cls.base_url + color_link['href']
                variant_urls.append(variant_url)

        sizes_container = soup.find('div', 'list-sizes')

        if sizes_container:
            for size_link in sizes_container.findAll('a'):
                variant_url = cls.base_url + size_link['href']
                variant_urls.append(variant_url)

        products = []

        if variant_urls:
            for variant_url in variant_urls:
                variant_soup = BeautifulSoup(session.get(
                    variant_url, timeout=20).text, 'html.parser')
                products.append(cls._retrieve_single_product(
                    variant_url, category, variant_soup))
        else:
            products.append(cls._retrieve_single_product(url, category, soup))

        return products

    @classmethod
    def _retrieve_single_product(cls, url, category, soup):
        model_name = soup.find('title').text.split('|')[0].strip()
        commercial_name = soup.find('h2', {'itemprop': 'name'}).text.strip()

        name = '{} {}'.format(commercial_name, model_name)

        key = soup.find('html')['data-product-id']

        picture_urls = [cls.base_url + soup.find(
            'img', {'itemprop': 'contentUrl'})['src'].replace(' ', '%20')]

        return Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            -1,
            Decimal(0),
            Decimal(0),
            'CLP',
            picture_urls=picture_urls
        )
