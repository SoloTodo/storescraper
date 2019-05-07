import json
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
            ['frio-directo', ['Refrigerator'],
             'Inicio > Electrohogar > Refrigeración > Frío Directo', 1],
            ['no-frost', ['Refrigerator'],
             'Inicio > Electrohogar > Refrigeración > No Frost', 1],
            ['freezer', ['Refrigerator'],
             'Inicio > Electrohogar > Refrigeración > Freezer', 1],
            ['frigobar', ['Refrigerator'],
             'Inicio > Electrohogar > Refrigeración > Frigobar', 1],
            ['side-by-side', ['Refrigerator'],
             'Inicio > Electrohogar > Refrigeración > Side by Side', 1],

            ['hornos-electricos', ['Oven'],
             'Inicio > Electrohogar > Cocina > Hornos Eléctricos', 1],
            ['hornos-empotrables', ['Oven'],
             'Inicio > Electrohogar > Cocina > Hornos Empotrables', 1],
            ['microondas', ['Oven'],
             'Inicio > Electrohogar > Cocina > Microondas', 1],

            ['aspiradoras', ['VacuumCleaner'],
             'Inicio > Electrohogar > Electrodomésticos > Aspiradoras', 1],

            ['lavadoras', ['WashingMachine'],
             'Inicio > Electrohogar > Lavado y Secado > Lavadoras', 1],
            ['lavadora-secadora', ['WashingMachine'],
             'Inicio > Electrohogar > Lavado y Secado > Lavadoras-Secadoras',
             1],
            ['secadoras', ['WashingMachine'],
             'Inicio > Electrohogar > Lavado y Secado > Secadoras', 1],
            ['lavavajillas', ['DishWasher'],
             'Inicio > Electrohogar > Lavado y Secado > Lavavajillas', 1],

            # ['reproductores', 'OpticalDiskPlayer'],

            ['iluminación-led', ['Lamp'],
             'Inicio > Iluminación > Iluminación Led', 1],

            ['calefont-gas-licuado', ['WaterHeater'],
             'Inicio > Electrohogar > Calefones y Termos > '
             'Calefones Gas Licuado', 1],
            ['calefont-gas-natural', ['WaterHeater'],
             'Inicio > Electrohogar > Calefones y Termos > '
             'Calefones Gas Natural', 1],
            ['termos', ['WaterHeater'],
             'Inicio > Electrohogar > Calefones y Termos > Termos', 1],

            ['estufas-electrica', ['SpaceHeater'],
             'Inicio > Electrohogar > Calefacción > Estufas Eléctricas', 1],
            ['estufas-a-gas', ['SpaceHeater'],
             'Inicio > Electrohogar > Calefacción > Estufas a Gas', 1],
            ['estufas-a-parafina', ['SpaceHeater'],
             'Inicio > Electrohogar > Calefacción > Estufas a Parafina', 1],
            ['calefactores-a-leña', ['SpaceHeater'],
             'Inicio > Electrohogar > Calefacción > Estufas a Leña', 1],
            ['calefactores-a-pellet', ['SpaceHeater'],
             'Inicio > Electrohogar > Calefacción > Estufas a Pellet', 1],
            # ['estufas-infrarrojas', 'SpaceHeater'],
            # ['chimeneas-electricas', 'SpaceHeater'],
            # ['paneles-calefactores', 'SpaceHeater'],
            # ['termoventiladores', 'SpaceHeater'],


            ['aire-acondicionado-y-enfriadores-de-aire', ['AirConditioner'],
             'Inicio > Electrohogar > Climatización > '
             'Aire acondicionado y Enfriadores de aire', 1],

            ['parlantes', ['StereoSystem'],
             'Inicio > Electrohogar > Tecnología > Parlantes', 1],
            ['audifonos', ['Headphones'],
             'Inicio > Electrohogar > Tecnología > Audífonos', 1]
        ]

        base_prod_url = 'https://www.easy.cl/tienda/producto/{}'
        cat_url = 'https://www.easy.cl/api/cateasy/_search'
        prods_url = 'https://www.easy.cl/api//prodeasy/_search'
        product_entries = defaultdict(lambda: [])
        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/json'

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

            cat_response = session.post(cat_url, data=json.dumps(cat_data))
            cat_json = json.loads(cat_response.text)
            cat_hits = cat_json['hits']['hits']

            if not cat_hits:
                raise Exception('Bad cat id {}'.format(category_path))

            cat_value = cat_hits[0]['_source']['value']
            cat_field = cat_hits[0]['_source']['field'] + ".raw"

            prods_data = {
                "query": {
                    "function_score": {
                        "query": {
                            "bool": {
                                "must": [
                                    {"term": {cat_field: cat_value}},
                                    {"match_all": {}}]}}}},
                "size": 450,
                "from": 0}

            prods_response = session.post(prods_url,
                                          data=json.dumps(prods_data))
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
