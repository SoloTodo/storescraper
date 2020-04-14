import json
import re

import demjson
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class LgV5(Store):
    base_url = 'https://www.lg.com'
    region_code = property(lambda self: 'Subclasses must implement this')

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = cls._category_paths()
        discovered_urls = []
        session = session_with_proxy(extra_args)
        session.headers['content-type'] = 'application/x-www-form-urlencoded'

        endpoint_url = 'https://www.lg.com/{}/mkt/ajax/category/' \
                       'retrieveCategoryProductList'.format(cls.region_code)

        for category_id, local_category, is_active in \
                category_paths:
            if local_category != category:
                continue

            if is_active:
                status = 'ACTIVE'
            else:
                status = 'DISCONTINUED'

            payload = 'categoryId={}&modelStatusCode={}&bizType=B2C&viewAll' \
                      '=Y'.format(category_id, status)
            json_response = json.loads(
                session.post(endpoint_url, payload).text)
            product_entries = json_response['data'][0]['productList']

            if not product_entries:
                raise Exception('Empty category: {} - {}'.format(
                    category_id, is_active))

            for product_entry in product_entries:
                product_url = cls.base_url + product_entry['modelUrlPath']
                discovered_urls.append(product_url)

        return discovered_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url, timeout=20)

        if response.url != url:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        sibling_urls = []
        sibling_areas = soup.findAll('div', 'size-list')

        if len(sibling_areas) == 2:
            sibling_urls.append(url)
        else:
            sibling_links = sibling_areas[-1].findAll('a')
            if not sibling_links:
                raise Exception('Siblings error')
            for sibling_link in sibling_links:
                sibling_path = sibling_link['href']
                if '#' in sibling_path:
                    continue
                sibling_url = cls.base_url + sibling_path
                sibling_urls.append(sibling_url)

        # For the case of https://www.lg.com/cac/televisores/lg-43UM7300PDA
        if not sibling_urls:
            sibling_urls = [url]

        products = []

        for sibling_url in sibling_urls:
            response = session.get(sibling_url, timeout=20)
            # Because https://www.lg.com/pa/telefonos-celulares/lg-G2-D805
            page_content = response.text.replace('5,2"', '5,2')

            products.extend(cls._retrieve_single_product(
                sibling_url, category, page_content))

        return products

    @classmethod
    def _retrieve_single_product(cls, url, category, content):
        print(url)
        soup = BeautifulSoup(content, 'html.parser')
        model_name = soup.find('meta', {'itemprop': 'mpn'})['content'].strip()
        short_description = soup.findAll(
            'meta', {'itemprop': 'name'})[1]['content'].strip()

        base_name = '{} - {}'.format(model_name, short_description)

        pictures_container = soup.find('div', {'id': 'modal_detail_target'})
        picture_tags = pictures_container.findAll('img', 'pc')
        picture_urls = [cls.base_url + x['data-lazy'].replace(' ', '%20')
                        for x in picture_tags]

        model_id = soup.find('input', {'name': 'modelId'})['value']

        section_data = re.search(r'_dl =([{\S\s]+\});', content)
        section_data = demjson.decode(section_data.groups()[0])

        field_candidates = [
            'page_category_l4', 'page_category_l3', 'page_category_l2',
            'page_category_l1'
        ]

        for candidate in field_candidates:
            if not section_data[candidate]:
                continue

            section_paths = section_data[candidate].split(':')[1:]
            section_path = ' > '.join([x for x in section_paths if x.strip()])
            positions = {
                section_path: 1
            }
            break
        else:
            raise Exception('At least one of the section candidates should '
                            'have matched')

        colors_container = soup.findAll('div', 'color-list')
        if len(colors_container) == 2:
            colors_container = None
        else:
            colors_container = colors_container[-1]

        # Because Q6 doesn't have valid model ids
        # https://www.lg.com/cac/telefonos-celulares/lg-LGM700DSK-astro-black
        if colors_container and model_id != 'MD05890236':
            products = []

            for idx, color_link in enumerate(colors_container.findAll('a')):
                color_name = color_link.text.strip()
                sub_model_id = color_link['data-model-id']

                if idx == 0:
                    key = '{}_{}'.format(model_id, sub_model_id)
                else:
                    key = sub_model_id

                name = '{} {}'.format(base_name, color_name)[:250]

                products.append(Product(
                    name,
                    cls.__name__,
                    category,
                    url,
                    url,
                    key,
                    -1,
                    Decimal(0),
                    Decimal(0),
                    'USD',
                    sku=model_name,
                    picture_urls=picture_urls,
                    positions=positions
                ))

            return products
        else:
            return [Product(
                base_name[:250],
                cls.__name__,
                category,
                url,
                url,
                model_id,
                -1,
                Decimal(0),
                Decimal(0),
                'USD',
                sku=model_name,
                picture_urls=picture_urls,
                positions=positions
            )]

    @classmethod
    def _category_paths(cls):
        return [
            ('CT20106005', 'CT20106005', 'Television', True),
            ('CT20106005', 'CT20106005', 'Television', False),
            ('CT20106017', 'CT20106017', 'OpticalDiskPlayer', False),
            ('CT20106017', 'CT20106019', 'OpticalDiskPlayer', True),
            ('CT20106017', 'CT20106019', 'OpticalDiskPlayer', False),
            ('CT20106020', 'CT20106021', 'StereoSystem', True),
            ('CT20106020', 'CT20106021', 'StereoSystem', False),
            ('CT30016640', 'CT30016642', 'StereoSystem', True),
            ('CT30016640', 'CT31903290', 'StereoSystem', True),
            ('CT20106023', 'CT20106025', 'StereoSystem', True),
            ('CT20106023', 'CT20106025', 'StereoSystem', False),
            ('CT30006480', 'CT30006480', 'Projector', True),
            ('CT20106027', 'CT20106027', 'Cell', True),
            ('CT20106027', 'CT20106027', 'Cell', False),
            ('CT30011860', 'CT30011860', 'Cell', True),
            ('CT20106034', 'CT20106034', 'Refrigerator', True),
            ('CT20106034', 'CT20106034', 'Refrigerator', False),
            ('CT20106039', 'CT20106039', 'Oven', True),
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
            ('CT32004943', 'CT32004943', 'B2B', True),  # Carteleria digital
            ('CT32004944', 'CT32004944', 'B2B', True),  # Commercial TV
            ('CT32004945', 'CT32004957', 'B2B', True),  # Wall Paper
        ]
