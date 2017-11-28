import json

import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class MovistarOne(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        product_urls = []

        if category == 'Cell':
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
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        panel_ids = ['pack2', 'pack1']
        description = ''
        for panel_id in panel_ids:
            panel = soup.find('div', {'id': panel_id})
            description += html_to_markdown(str(panel)) + '\n\n'

        manufacturer = soup.find('p', 'top-name').text.strip()
        model = soup.find('h1', {'id': 'devicename'}).text.strip()
        name = '{} {}'.format(manufacturer, model)

        base_sku = re.search(r'dispositivo-(\d+)', url).groups()[0]

        products = []
        cell_prices = []

        plan_combinations = [
            ('lineaNueva', ''),
            ('portabilidad', ' Portabilidad')
        ]

        for dom_element_id, plan_combination_suffix in plan_combinations:
            plan_combination_table = soup.find(
                'div', {'id': dom_element_id}).find('table')
            cell_refs = plan_combination_table.find('tbody').findAll(
                'strong', 'textfeat01')

            for cell_ref in cell_refs:
                row = cell_ref.findParent('tr')
                if not row.find('span', 'c-blue'):
                    # Movistar One price
                    continue
                try:
                    order = row['data-order']
                except KeyError:
                    continue

                plan_name = row.find('td', 'w2')

                if not plan_name:
                    continue

                plan_name = plan_name.find(
                    'strong').contents[0].strip() + plan_combination_suffix

                initial_payment = Decimal(remove_words(row.find(
                    'p', {'id': 'priceOffer'}).find('strong').text.strip()))

                monthly_payment = row.find('p', 'textfeat02').find('strong')

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
            picture_urls = ['http://www.movistar.cl' +
                            container.find('span')[
                                'data-desktop-image-retina']]

            variant_name = '{} Color {}'.format(name, color_name)

            for plan_name, initial_payment, monthly_payment in cell_prices:
                product = Product(
                    variant_name,
                    cls.__name__,
                    'Cell',
                    url,
                    url,
                    '{} {} {}'.format(base_sku, color_name, plan_name),
                    -1,
                    initial_payment,
                    initial_payment,
                    'CLP',
                    cell_plan_name=plan_name,
                    picture_urls=picture_urls,
                    description=description,
                    cell_monthly_payment=monthly_payment
                )
                products.append(product)

        return products
