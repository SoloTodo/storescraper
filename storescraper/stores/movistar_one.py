import json

import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class MovistarOne(Store):

    @classmethod
    def categories(cls):
        return [
            'Cell'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != 'Cell':
            return []

        req_url = 'http://www.movistar.cl/web/movistar/tienda/equipos/' \
                  'catalogo-de-equipos?p_p_id=colportalcatalog_WAR_' \
                  'colportalcatalogoportlet_INSTANCE_fPJVYJKGELWc&p_p_' \
                  'lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_' \
                  'cacheability=cacheLevelPage&p_p_col_id=' \
                  'column-layout-2&p_p_col_count=3'

        data_template = \
            '_colportalcatalog_WAR_colportalcatalogoportlet_INSTANCE_' \
            'fPJVYJKGELWc_action=3&_colportalcatalog_WAR_colportal' \
            'catalogoportlet_INSTANCE_fPJVYJKGELWc_lowerLimit=1&_col' \
            'portalcatalog_WAR_colportalcatalogoportlet_INSTANCE_' \
            'fPJVYJKGELWc_upperLimit=8&_colportalcatalog_WAR_colportal' \
            'catalogoportlet_INSTANCE_fPJVYJKGELWc_currentPage={}' \
            '&_colportalcatalog_WAR_colportalcatalogoportlet_INSTANCE_' \
            'fPJVYJKGELWc_totalRecords=77&_colportalcatalog' \
            '_WAR_colportalcatalogoportlet_INSTANCE_fPJVYJKGELWc_' \
            'sortBy={}&'

        session = session_with_proxy(extra_args)
        session.headers[
            'Content-Type'] = 'application/x-www-form-urlencoded'

        product_urls = []

        for sorting_option in [0, 1, 2, 3]:
            page = 1
            while True:
                print(sorting_option, page)
                data = data_template.format(page, sorting_option)
                response = session.post(req_url, data)

                json_data = json.loads(response.text)

                for device in json_data['Devices']:
                    device_soup = BeautifulSoup(
                        device['Device'], 'html.parser')

                    device_link = device_soup.find('a')
                    if not device_link:
                        continue

                    url = 'http://www.movistar.cl' + device_link['href']
                    if url not in product_urls:
                        product_urls.append(url)

                if page >= json_data['paginator']['totalPage']:
                    break

                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)

        device_id = re.search('(\d+)$', url).groups()[0]

        products = []
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        manufacturer = soup.find('p', 'top-name').string.strip()
        cell_name = soup.find('h1', {'id': 'devicename'}).text.strip()

        cell_name = '{} {}'.format(manufacturer, cell_name)

        cell_prices = []

        plan_combinations = [
            ('lineaNueva', None),
            ('portabilidad', ' Portabilidad')
        ]

        for dom_element_id, plan_combination_suffix in plan_combinations:
            for internet_prefix in [None, ' Exclusivo Web']:
                plan_combination_table = soup.find(
                    'div', {'id': dom_element_id}).find('table')

                anchor_elements = plan_combination_table.findAll('p', {
                    'id': 'priceOffer'})
                rows = [tag.find_parent('tr') for tag in anchor_elements]

                rows_with_plans = []

                for row in rows:
                    if not row.find('span', 'c-blue'):
                        # Movistar Normal price
                        continue

                    try:
                        order = row['data-order']
                        rows_with_plans.append(row)
                    except KeyError:
                        continue

                for row in rows_with_plans:
                    plan_name = row.find('td', 'w2')

                    if not plan_name:
                        continue

                    if plan_name.find('img'):
                        plan_name = plan_name.find(
                            'strong').contents[1].strip()
                    else:
                        plan_name = plan_name.find(
                            'strong').contents[0].strip()

                    if internet_prefix:
                        plan_name += internet_prefix
                    if plan_combination_suffix:
                        plan_name += plan_combination_suffix

                    initial_payment = Decimal(remove_words(row.find(
                        'p', {'id': 'priceOffer'}).find(
                        'strong').text.strip()))

                    monthly_payment = row.find('p', 'textfeat02').find(
                        'strong')

                    if monthly_payment:
                        monthly_payment = Decimal(remove_words(
                            monthly_payment.text.strip()))
                    else:
                        monthly_payment = Decimal('0')

                    cell_prices.append(
                        (plan_name, initial_payment, monthly_payment))

        color_variants = soup.find('ul', 'list-colors')
        for container in color_variants.findAll('li')[1:]:
            color_name = container.findAll('span')[-1].text.strip()

            variant_name = '{} Color {}'.format(cell_name, color_name)

            for plan_name, initial_payment, monthly_payment in cell_prices:
                products.append(Product(
                    variant_name,
                    cls.__name__,
                    'Cell',
                    url,
                    url,
                    '{} - {}'.format(device_id, plan_name),
                    -1,
                    initial_payment,
                    initial_payment,
                    'CLP',
                    cell_plan_name=plan_name,
                    cell_monthly_payment=monthly_payment
                ))

        return products
