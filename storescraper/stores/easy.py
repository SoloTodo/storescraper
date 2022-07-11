import json
import logging
from collections import defaultdict
from decimal import Decimal

from bs4 import BeautifulSoup
from storescraper.categories import AIR_CONDITIONER, OVEN, REFRIGERATOR, \
    SPACE_HEATER, VACUUM_CLEANER, WASHING_MACHINE, WATER_HEATER

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Easy(Store):
    @classmethod
    def categories(cls):
        return [
            REFRIGERATOR,
            OVEN,
            VACUUM_CLEANER,
            WASHING_MACHINE,
            AIR_CONDITIONER,
            SPACE_HEATER,
            WATER_HEATER
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        category_paths = [
            # Electrohogar y climatización

            # Calefacción
            ['electrohogar-y-climatizacion/calefaccion/estufas-electricas',
             [SPACE_HEATER],
             'Inicio > Electrohogar > Calefacción > Estufas Eléctricas', 1],
            ['electrohogar-y-climatizacion/calefaccion/estufas-a-pellet',
             [SPACE_HEATER],
             'Inicio > Electrohogar > Calefacción > Estufas a Pellet', 1],
            ['electrohogar-y-climatizacion/calefaccion/estufas-a-gas',
             [SPACE_HEATER],
             'Inicio > Electrohogar > Calefacción > Estufas a Gas', 1],
            ['electrohogar-y-climatizacion/calefaccion/estufas-a-parafina',
             [SPACE_HEATER],
             'Inicio > Electrohogar > Calefacción > Estufas a Parafina', 1],
            ['electrohogar-y-climatizacion/calefaccion/estufas-a-lena',
             [SPACE_HEATER],
             'Inicio > Electrohogar > Calefacción > Estufas a leña', 1],

            # Calefont y Termos
            ['electrohogar-y-climatizacion/calefont-y-termos/calefont',
             [WATER_HEATER],
             'Inicio > Electrohogar y Climatización > Calefont y Termos > '
             'Calefont', 1],
            ['electrohogar-y-climatizacion/calefont-y-termos/termos-y-'
             'calderas', [WATER_HEATER],
             'Inicio > Electrohogar y Climatización > Calefont y Termos > '
             'Termos y calderas', 1],

            # Refrigeración
            ['electrohogar-y-climatizacion/refrigeracion/refrigeradores',
             [REFRIGERATOR],
             'Inicio > Electrohogar y Climatización > Refrigeración > '
             'Refrigeradores', 1],
            ['electrohogar-y-climatizacion/refrigeracion/freezer',
             [REFRIGERATOR],
             'Inicio > Electrohogar y Climatización > Refrigeración > '
             'Freezer', 1],
            ['electrohogar-y-climatizacion/refrigeracion/frigobar',
             [REFRIGERATOR],
             'Inicio > Electrohogar y Climatización > Refrigeración > '
             'Frigobar', 1],

            # Cocina
            ['electrohogar-y-climatizacion/cocina/hornos-empotrables',
             [OVEN],
             'Inicio > Electrohogar y Climatización > Cocina > '
             'Hornos Empotrables', 1],
            ['electrohogar-y-climatizacion/electrodomesticos/microondas',
             [OVEN],
             'Inicio > Electrohogar y Climatización > Cocina > Microondas', 1],

            # Lavado y planchado
            ['electrohogar-y-climatizacion/lavado-y-planchado/lavadoras',
             [WASHING_MACHINE],
             'Inicio > Electrohogar y Climatización > Lavado y planchado > '
             'Lavadoras', 1],
            ['electrohogar-y-climatizacion/lavado-y-planchado/secadoras',
             [WASHING_MACHINE],
             'Inicio > Electrohogar y Climatización > Lavado y planchado > '
             'Secadoras', 1],
            ['electrohogar-y-climatizacion/lavado-y-planchado/lavadoras-'
             'secadoras', [WASHING_MACHINE],
             'Inicio > Electrohogar y Climatización > Lavado y planchado > '
             'Lava - seca', 1],

            # Aspirado y limpieza
            ['electrohogar-y-climatizacion/aspirado-y-limpieza/aspiradoras',
             [VACUUM_CLEANER],
             'Inicio > Electrohogar y Climatización > Aspirado y limpieza > '
             'Aspiradoras', 1],
            ['electrohogar-y-climatizacion/aspirado-y-limpieza/robots-de-'
             'limpieza', [VACUUM_CLEANER],
             'Inicio > Electrohogar y Climatización > Aspirado y limpieza > '
             'Robots de limpieza', 1],

            # Electrodomésticos
            ['electrohogar-y-climatizacion/electrodomesticos/hornos-'
             'electricos', [OVEN],
             'Inicio > Electrohogar y Climatización > Electrodomésticos > '
             'Hornos eléctricos', 1],
            ['electrohogar-y-climatizacion/electrodomesticos/microondas',
             [OVEN],
             'Inicio > Electrohogar y Climatización > Electrodomésticos > '
             'Microondas', 1],

            # Ventilación
            ['electrohogar-y-climatizacion/ventilacion/aire-acondicionado-'
             'portatil', [AIR_CONDITIONER],
             'Inicio > Electrohogar y Climatización > Ventilación > '
             'Aire acondicionado portátil', 1],
            ['electrohogar-y-climatizacion/ventilacion/aire-acondicionado-'
             'split', [AIR_CONDITIONER],
             'Inicio > Electrohogar y Climatización > Ventilación > '
             'Aire Acondicionado split', 1],
            ['electrohogar-y-climatizacion/ventilacion/purificadores-y-'
             'humidificadores', [AIR_CONDITIONER],
             'Inicio > Electrohogar y Climatización > Ventilación > '
             'Purificadores y humidificadores', 1],
        ]

        product_entries = defaultdict(lambda: [])
        session = session_with_proxy(extra_args)

        for e in category_paths:
            category_path, local_categories, section_name, category_weight = e

            if category not in local_categories:
                continue

            page = 1
            while True:
                if page > 20:
                    raise Exception('page overflow: ' + category_path)

                url_webpage = 'https://www.easy.cl/{}?page={}'.format(
                    category_path, page)
                print(url_webpage)

                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                page_state_tag = soup.find(
                    'template', {'data-varname': '__STATE__'})
                page_state = json.loads(page_state_tag.text)
                done = True

                idx = 0
                for key, value in page_state.items():
                    if key.startswith('Product:') and 'linkText' in value:
                        product_url = 'https://www.easy.cl/' + \
                            value['linkText'] + '/p'
                        product_entries[product_url].append({
                            'category_weight': category_weight,
                            'section_name': section_name,
                            'value': idx + 1
                        })
                        idx += 1
                        done = False

                if done:
                    if page == 1:
                        logging.warning('Empty category: ' + category_path)
                    break
                page += 1

        return product_entries

    @classmethod
    def discover_urls_for_keyword(cls, keyword, threshold, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/json'
        product_urls = []

        base_prod_url = 'https://www.easy.cl/tienda/producto/{}'
        prods_url = 'https://www.easy.cl/api//prodeasy/_search'

        prods_data = {
            "query": {
                "function_score": {
                    "query": {
                        "bool": {
                            "must": [{
                                "bool": {
                                    "should": [{
                                        "function_score": {
                                            "query": {
                                                "multi_match": {
                                                    "query": keyword,
                                                    "fields": [
                                                        "name^1000",
                                                        "brand",
                                                        "cat_3.stop",
                                                        "partNumber"],
                                                    "type":"best_fields",
                                                    "operator":"and"}},
                                            "field_value_factor": {
                                                "field": "boost",
                                                "factor": 6}}}, {
                                        "multi_match": {
                                            "query": keyword,
                                            "fields": [
                                                "name^8",
                                                "cat_3.stop"],
                                            "type": "best_fields",
                                            "operator": "or"}}, {
                                        "span_first": {
                                            "match": {
                                                "span_term": {
                                                    "name.dym": keyword}},
                                            "end": 1,
                                            "boost": 2000}}],
                                    "minimum_should_match": "1"}}]}},
                    "boost_mode": "sum",
                    "score_mode": "max"}},
            "size": 450,
            "from": 0}

        prods_response = session.post(
            prods_url, data=json.dumps(prods_data))

        prods_json = json.loads(prods_response.text)
        prods_hits = prods_json['hits']['hits']

        if not prods_hits:
            return []

        for prods_hit in prods_hits:
            product_url = base_prod_url.format(prods_hit['_source']['url'])
            product_urls.append(product_url)

            if len(product_urls) == threshold:
                return product_urls

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        res = session.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        product_data = json.loads(soup.find(
            'template', {'data-varname': '__STATE__'}).text)

        base_json_keys = list(product_data.keys())

        if not base_json_keys:
            return []

        base_json_key = base_json_keys[0]
        product_specs = product_data[base_json_key]

        key = product_specs['productId']
        name = product_specs['productName']
        sku = product_specs['productReference']
        description = html_to_markdown(product_specs.get('description', None))

        pricing_key = '${}.items.0.sellers.0.commertialOffer'.format(
            base_json_key)
        pricing_data = product_data[pricing_key]

        normal_price = Decimal(pricing_data['Price'])

        offer_price_key = '{}.teasers.0.effects.parameters.0'.format(
            pricing_key)
        offer_price_json_value = product_data.get(offer_price_key, None)
        if offer_price_json_value:
            offer_price = Decimal(offer_price_json_value['value']) \
                / Decimal(100)
            if offer_price > normal_price:
                offer_price = normal_price
        else:
            offer_price = normal_price

        stock = pricing_data['AvailableQuantity']
        picture_list_key = '{}.items.0'.format(base_json_key)
        picture_list_node = product_data[picture_list_key]
        picture_ids = [x['id'] for x in picture_list_node['images']]

        picture_urls = []
        for picture_id in picture_ids:
            picture_node = product_data[picture_id]
            picture_urls.append(picture_node['imageUrl'].split('?')[0])

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
