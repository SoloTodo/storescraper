import json
import logging
import re
from collections import defaultdict
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Easy(Store):
    @classmethod
    def categories(cls):
        return [
            'Refrigerator',
            'Television',
            'Oven',
            'VacuumCleaner',
            'WashingMachine',
            'Cell',
            'StereoSystem',
            'OpticalDiskPlayer',
            'Lamp',
            'LightTube'
            'LightProjector',
            'WaterHeater',
            'SpaceHeater',
            'AirConditioner',
            'Headphones'
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        category_paths = [
            # Electrohogar y climatización

            # Calefacción
            ['estufas-electricas-', ['SpaceHeater'],
             'Inicio > Electrohogar > Calefacción > Estufas Eléctricas', 1],
            ['estufas-a-pellet-', ['SpaceHeater'],
             'Inicio > Electrohogar > Calefacción > Estufas a Pellet', 1],
            ['estufas-a-gas-', ['SpaceHeater'],
             'Inicio > Electrohogar > Calefacción > Estufas a Gas', 1],
            ['estufas-a-parafina-', ['SpaceHeater'],
             'Inicio > Electrohogar > Calefacción > Estufas a Parafina', 1],
            ['calefont-8', ['WaterHeater'],
             'Inicio > Electrohogar y Climatización > Calefacción > '
             'Calefont', 1],
            ['estufas-a-lena', ['SpaceHeater'],
             'Inicio > Electrohogar > Calefacción > Estufas a leña', 1],
            ['termos-calderas', ['WaterHeater'],
             'Inicio > Electrohogar y Climatización > Calefacción > '
             'Termos y calderas', 1],
            ['purificadores-y-humificadores', ['AirConditioner'],
             'Inicio > Electrohogar y Climatización > Calefacción > '
             'Purificadores y humidificadores', 1],

            # Calefont y Termos
            ['calefont-8', ['WaterHeater'],
             'Inicio > Electrohogar y Climatización > Calefont y Termos > '
             'Calefont', 1],
            ['termos-calderas', ['WaterHeater'],
             'Inicio > Electrohogar y Climatización > Calefont y Termos > '
             'Termos y calderas', 1],

            # Refrigeración
            ['refrigeracion-refrigeradores', ['Refrigerator'],
             'Inicio > Electrohogar y Climatización > Refrigeración > '
             'Refrigeradores', 1],
            ['refrigeracion-freezer', ['Refrigerator'],
             'Inicio > Electrohogar y Climatización > Refrigeración > '
             'Freezer', 1],
            ['refrigeracion-frigobar', ['Refrigerator'],
             'Inicio > Electrohogar y Climatización > Refrigeración > '
             'Frigobar', 1],

            # Cocina
            ['hornos-empotrables-8', ['Oven'],
             'Inicio > Electrohogar y Climatización > Cocina > '
             'Hornos Empotrables', 1],
            ['microondas-8', ['Oven'],
             'Inicio > Electrohogar y Climatización > Cocina > Microondas', 1],

            # Lavado y planchado
            ['lavadoras-8', ['WashingMachine'],
             'Inicio > Electrohogar y Climatización > Lavado y planchado > '
             'Lavadoras', 1],
            ['secadoras-8', ['WashingMachine'],
             'Inicio > Electrohogar y Climatización > Lavado y planchado > '
             'Secadoras', 1],
            ['lava-seca', ['WashingMachine'],
             'Inicio > Electrohogar y Climatización > Lavado y planchado > '
             'Lava - seca', 1],

            # Aspirado y limpieza
            ['aspiradoras-', ['VacuumCleaner'],
             'Inicio > Electrohogar y Climatización > Aspirado y limpieza > '
             'Aspiradoras', 1],
            ['robots-de-limpieza', ['VacuumCleaner'],
             'Inicio > Electrohogar y Climatización > Aspirado y limpieza > '
             'Robots de limpieza', 1],

            # Electrodomésticos
            ['hornos-electricos-8', ['Oven'],
             'Inicio > Electrohogar y Climatización > Electrodomésticos > '
             'Hornos eléctricos', 1],
            ['microondas-8', ['Oven'],
             'Inicio > Electrohogar y Climatización > Electrodomésticos > '
             'Microondas', 1],

            # Ventilación
            ['ventilacion-aire-acondicionado-portatil', ['AirConditioner'],
             'Inicio > Electrohogar y Climatización > Ventilación > '
             'Aire acondicionado portátil', 1],
            ['ventilacion-aire-acondicionado-split', ['AirConditioner'],
             'Inicio > Electrohogar y Climatización > Ventilación > '
             'Aire Acondicionado split', 1],
            ['purificadores-y-humificadores', ['AirConditioner'],
             'Inicio > Electrohogar y Climatización > Ventilación > '
             'Purificadores y humidificadores', 1],
        ]

        base_prod_url = 'https://www.easy.cl/tienda/producto/{}'
        cat_url = 'https://www.easy.cl/api/cateasy/_search'
        prods_url = 'https://www.easy.cl/api/prodeasy/_search'
        product_entries = defaultdict(lambda: [])
        session = session_with_proxy(extra_args)

        for e in category_paths:
            category_path, local_categories, section_name, category_weight = e

            if category not in local_categories:
                continue

            cat_data = {
                "query": {
                    "term":
                        {"seo_url.keyword": category_path}
                }
            }

            cat_response = session.post(cat_url, json=cat_data)
            cat_json = json.loads(cat_response.content.decode('utf-8'))
            cat_hits = cat_json['hits']['hits']

            if not cat_hits:
                logging.warning('Empty category: {}'.format(category_path))
                raise Exception
                continue

            cat_value = cat_hits[0]['_source']['value']
            cat_field = cat_hits[0]['_source']['field'] + ".raw"

            prods_data = {
                "query": {
                    "function_score": {
                        "query": {
                            "bool": {
                                "must": [
                                    {
                                        "term": {
                                            cat_field: cat_value
                                        }
                                    }
                                ]
                            }
                        }
                    }
                },
                "size": 10000
            }

            prods_response = session.post(prods_url, json=prods_data)
            prods_json = json.loads(prods_response.text)
            prods_hits = prods_json['hits']['hits']

            if not prods_hits:
                raise Exception('Empty section {}'.format(category_path))

            for idx, prods_hit in enumerate(prods_hits):
                product_url = base_prod_url.format(prods_hit['_source']['url'])
                product_entries[product_url].append({
                    'category_weight': category_weight,
                    'section_name': section_name,
                    'value': idx + 1
                })

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
        prod_url = 'https://www.easy.cl/api/prodeasy*/_search'
        prod_keyword = url.split('/')[-1]
        prod_data = {
            "query": {
                "bool": {
                    "minimum_should_match": 1,
                    "should": [
                        {"term": {"url.keyword": prod_keyword}},
                        {"term": {"children.url.keyword": prod_keyword}}]}}}

        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/json'

        prod_response = session.post(prod_url, data=json.dumps(prod_data))
        prod_json = json.loads(prod_response.text)
        prod_hit = prod_json['hits']['hits'][0]

        name = prod_hit['_source']['name'].strip()
        sku = prod_hit['_source']['partNumber']
        stock = prod_hit['_source']['stock']

        normal_price = prod_hit['_source']['price_internet']
        offer_price = prod_hit['_source']['price_tc']

        if not normal_price:
            return []
        else:
            normal_price = Decimal(normal_price)

        if not offer_price:
            offer_price = normal_price
        else:
            offer_price = Decimal(offer_price)

        description = '| Caracteristica | Valor | \n' \
                      '| -------------- | ----- | \n'

        for spec in prod_hit['_source']['specs_open']:
            description += '| {} | {} |\n'.format(spec['key'], spec['value'])

        images_base_url = 'https://s7d2.scene7.com/is/image/EasySA/{}?' \
                          'req=set,json&callback=s7jsonResponse'

        images_key = sku.replace('P', '')
        images_response = session.get(images_base_url.format(images_key))

        picture_urls = []

        if 's7jsonResponse' in images_response.text:
            images_json = json.loads(
                re.search(r's7jsonResponse\((.+),""\);',
                          images_response.text).groups()[0])
            picture_entries = images_json['set']['item']
            if not isinstance(picture_entries, list):
                picture_entries = [picture_entries]

            for picture_entry in picture_entries:
                if 'i'in picture_entry:
                    picture_url = 'https://s7d2.scene7.com/is/image/' \
                                  '{}?scl=1.0'.format(picture_entry['i']['n'])
                    picture_urls.append(picture_url)

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
