import logging

import json

from collections import defaultdict
from decimal import Decimal
from bs4 import BeautifulSoup

from storescraper.categories import GAMING_CHAIR, NOTEBOOK, CELL, WEARABLE, \
    HEADPHONES, TELEVISION, STEREO_SYSTEM, ALL_IN_ONE, MONITOR, TABLET, \
    PRINTER, VIDEO_GAME_CONSOLE, MOUSE, EXTERNAL_STORAGE_DRIVE, REFRIGERATOR, \
    WASHING_MACHINE, OVEN, DISH_WASHER, AIR_CONDITIONER, SPACE_HEATER, WATER_HEATER
from storescraper.flixmedia import flixmedia_video_urls
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy
from storescraper import banner_sections as bs


class LaPolar(Store):
    @classmethod
    def categories(cls):
        return [
            GAMING_CHAIR,
            NOTEBOOK,
            CELL,
            WEARABLE,
            HEADPHONES,
            TELEVISION,
            STEREO_SYSTEM,
            ALL_IN_ONE,
            MONITOR,
            TABLET,
            PRINTER,
            VIDEO_GAME_CONSOLE,
            MOUSE,
            EXTERNAL_STORAGE_DRIVE,
            REFRIGERATOR,
            WASHING_MACHINE,
            OVEN,
            DISH_WASHER,
            AIR_CONDITIONER,
            SPACE_HEATER,
            WATER_HEATER
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        category_paths = [
            ['smartphones', [CELL],
             'Inicio > Tecnología > Celulares > Smartphones', 1],
            ['smartwatch', [WEARABLE],
             'Inicio > Tecnología > Celulares > Smartwatch', 1],
            ['accesorios-telefonos', [HEADPHONES],
             'Inicio > Tecnología > Celulares > Accesorios Teléfonos', 1],
            ['televisores', [TELEVISION],
             'Inicio > Tecnología > Televisores', 1],
            ['smart-tv', [TELEVISION],
             'Inicio > Tecnología > Televisores > Smart TV', 1],
            ['televisores-basicos', [TELEVISION],
             'Inicio > Tecnología > Televisores > Televisores Básicos', 1],
            ['soundbar', [STEREO_SYSTEM],
             'Inicio > Tecnología > Televisores > Soundbar', 1],
            ['notebooks', [NOTEBOOK],
             'Inicio > Tecnología > Computadores > Notebooks', 1],
            ['all-in-one-y-desktops', [ALL_IN_ONE],
             'Inicio > Tecnología > Computadores > All in One y Desktops', 1],
            ['monitores', [MONITOR],
             'Inicio > Tecnología > Computadores > Monitores', 1],
            ['tablet', [TABLET],
             'Inicio > Tecnología > Computadores > Tablet', 1],
            ['todo-impresoras', [PRINTER],
             'Inicio > Tecnología > Computadores > Impresoras', 1],
            ['notebooks-gamer', [NOTEBOOK],
             'Inicio > Tecnología > Mundo Gamer > Notebooks Gamer', 1],
            ['consolas', [VIDEO_GAME_CONSOLE],
             'Inicio > Tecnología > Mundo Gamer > Consolas', 1],
            ['audifonos-gamer', [HEADPHONES],
             'Inicio > Tecnología > Mundo Gamer > Audífonos Gamer', 1],
            ['sillas-gamer', [GAMING_CHAIR],
             'Inicio > Tecnología > Mundo Gamer > Sillas Gamer', 1],
            ['accesorios-gamer', [MOUSE],
             'Inicio > Tecnología > Mundo Gamer > Accesorios Gamer', 1],
            ['minicomponentes', [STEREO_SYSTEM],
             'Inicio > Tecnología > Audio > Minicomponentes', 1],
            ['parlantes-port%c3%a1tiles', [STEREO_SYSTEM],
             'Inicio > Tecnología > Audio > Parlantes Portátiles', 1],
            ['audifonos', [HEADPHONES],
             'Inicio > Tecnología > Audio > Audífonos', 1],
            ['soundbar', [STEREO_SYSTEM],
             'Inicio > Tecnología > Audio > Soundbar', 1],
            ['discos-duros', [EXTERNAL_STORAGE_DRIVE],
             'Inicio > Tecnología > Accesorios Computación > Discos Duros', 1],
            ['mouse-i-teclados', [MOUSE],
             'Inicio > Tecnología > Accesorios Computación > '
             'Mouse y Teclados', 1],
            ['refrigeradores', [REFRIGERATOR],
             'Inicio > Línea Blanca > Refrigeradorees', 1],
            ['freezer', [REFRIGERATOR],
             'Inicio > Línea Blanca > Refrigeradorees > Freezer', 1],
            ['side-by-side', [REFRIGERATOR],
             'Inicio > Línea Blanca > Refrigeradorees > Side by Side', 1],
            ['no-frost', [REFRIGERATOR],
             'Inicio > Línea Blanca > Refrigeradorees > No Frost', 1],
            ['frio-directo', [REFRIGERATOR],
             'Inicio > Línea Blanca > Refrigeradorees > Frío Directo', 1],
            ['frigobar', [REFRIGERATOR],
             'Inicio > Línea Blanca > Refrigeradorees > Frigobar', 1],
            ['lavado-y-secado', [WASHING_MACHINE],
             'Inicio > Línea Blanca > Lavado y Secado', 1],
            ['lavadoras', [WASHING_MACHINE],
             'Inicio > Línea Blanca > Lavado y Secado > Lavadoras', 1],
            ['secadoras', [WASHING_MACHINE],
             'Inicio > Línea Blanca > Lavado y Secado > Secadoras', 1],
            ['lavadoras-secadoras', [WASHING_MACHINE],
             'Inicio > Línea Blanca > Lavado y Secado > '
             'Lavadoras - Secadoras', 1],
            ['hornos-electricos', [OVEN],
             'Inicio > Línea Blanca > Electrodomésticos > '
             'Hornos Eléctricos', 1],
            ['microondas', [OVEN],
             'Inicio > Línea Blanca > Electrodomésticos > Microondas', 1],
            ['lavaplatos-y-lavavajillas', [DISH_WASHER],
             'Inicio > Línea Blanca > Cocina > Lavaplatos y Lavavajillas', 1],
            ['aires-acondicionados', [AIR_CONDITIONER],
             'Inicio > Línea Blanca > Climatización > '
             'Aires Acondicionados', 1],
            ['estufas', [SPACE_HEATER],
             'Inicio > Línea Blanca > Climatización > Estufas', 1],
            ['calefont-y-termos', [WATER_HEATER],
             'Inicio > Línea Blanca > Climatización > Calefont y Termos', 1],
        ]

        session = session_with_proxy(extra_args)

        product_entries = defaultdict(lambda: [])

        for e in category_paths:
            category_path, local_categories, section_name, category_weight = e

            if category not in local_categories:
                continue

            url = 'https://www.lapolar.cl/on/demandware.store/' \
                  'Sites-LaPolar-Site/es_CL/Search-UpdateGrid?' \
                  'cgid={}&srule=best-matches&start=0&sz=1000' \
                .format(category_path)

            response = session.get(url).text
            soup = BeautifulSoup(response, 'html.parser')

            products = soup.findAll('div', 'lp-product-tile')

            if not products:
                logging.warning('Empty category path: {} - {}'.format(
                    category, category_path))

            for idx, container in enumerate(products):
                product_url = 'https://www.lapolar.cl{}' \
                    .format(container.findAll('a')[-1]['href'])
                product_entries[product_url].append({
                    'category_weight': category_weight,
                    'section_name': section_name,
                    'value': idx + 1
                })

        return product_entries

    @classmethod
    def discover_urls_for_keyword(cls, keyword, threshold, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []

        url = 'https://www.lapolar.cl/on/demandware.store/' \
              'Sites-LaPolar-Site/es_CL/Search-UpdateGrid?' \
              'q={}&srule=product-outstanding' \
              '&start=0&sz=1000'.format(keyword)

        response = session.get(url).text
        soup = BeautifulSoup(response, 'html.parser')

        products = soup.findAll('div', 'lp-product-tile')

        if not products:
            return []

        for container in products:
            product_url = 'https://www.lapolar.cl{}' \
                .format(container.find('a')['href'])
            product_urls.append(product_url)

            if len(product_urls) == threshold:
                return product_urls

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if not response.ok:
            return []

        page_source = response.text

        soup = BeautifulSoup(page_source, 'html.parser')

        if not soup.find('div', 'product-name'):
            return []

        name = soup.find('div', 'product-name').text.strip()
        sku = soup.find('span', 'sku-code-value').text.strip()

        prices = soup.find('div', 'prices')
        la_polar_card = prices.find('p', 'js-tlp-price')

        if prices.find('p', 'la-polar'):
            highlighted_price = prices.find('p', 'la-polar')
        else:
            highlighted_price = prices.find('p', 'internet')
        highlighted_price = highlighted_price.find(
            'span', 'price-value') \
            .text.strip().replace('$', '').replace('.', '')
        highlighted_price = Decimal(highlighted_price)

        if la_polar_card:
            offer_price = highlighted_price

            normal_price = prices.find('p', 'internet').find(
                'span', 'price-value').text.strip() \
                .replace('$', '').replace('.', '')
            normal_price = Decimal(normal_price)
        else:
            offer_price = normal_price = highlighted_price

        description = html_to_markdown(
            str(soup.find('div', 'description-wrapper')))

        picture_containers = soup.findAll('div', 'primary-image')
        picture_urls = [
            picture.find('img')['src'].replace(' ', '%20')
            for picture in picture_containers]

        if 'reacondicionado' in name.lower():
            condition = 'https://schema.org/RefurbishedCondition'
        else:
            condition = 'https://schema.org/NewCondition'

        flixmedia_id = None
        video_urls = None

        if 'LG' in name and '//media.flixfacts.com/js/loader.js' in \
                response.text:
            details_tab = soup.find('div', 'details-tab')
            for label in details_tab.findAll('div', 'attr-label'):
                if label.text.strip() == 'Modelo:':
                    model = label.parent.find('div', 'attr-value').text.strip()
                    video_urls = flixmedia_video_urls(model)
                    if video_urls is not None:
                        flixmedia_id = model
                    break

        variation_container = soup.find('div', 'swatch-wrapper')
        variations = []

        if variation_container:
            variations = variation_container.findAll('a')

        products = []

        if variations:
            for variation in variations:
                variation_url = variation['href']
                variation_data = json.loads(session.get(variation_url).text)
                attributes = variation_data["product"]["variationAttributes"]

                for attribute in attributes:
                    if attribute["displayName"] != "Compañía":
                        continue
                    values = attribute["values"]
                    for value in values:
                        if value["selectable"]:
                            sv_data = json.loads(
                                session.get(value["url"]).text)
                            svas = sv_data[
                                "product"]["variationAttributes"]
                            for sva in svas:
                                if sva["displayName"] != "Color":
                                    continue
                                for v in sva["values"]:
                                    if v["selected"]:
                                        v_name = "{} {} ({})".format(
                                            name, value["displayValue"],
                                            v["displayValue"])
                                        v_sku = "{}-{}".format(
                                            sku, sv_data["product"][
                                                "selectedVariantID"])
                                        vis = sv_data[
                                            "product"]["images"]["large"]
                                        vpu = [i["url"] for i in vis]
                                        stock = sv_data['product'][
                                            'availability']['qty']
                                        products.append(Product(
                                            v_name,
                                            cls.__name__,
                                            category,
                                            url,
                                            url,
                                            v_sku,
                                            stock,
                                            normal_price,
                                            offer_price,
                                            'CLP',
                                            sku=v_sku,
                                            description=description,
                                            picture_urls=vpu,
                                            condition=condition))

            return products
        else:
            add_to_cart_button = soup.find('button', 'add-to-cart')
            if 'AGOTADO' in add_to_cart_button.text.upper():
                stock = 0
            else:
                stock = -1

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
            picture_urls=picture_urls,
            condition=condition,
            flixmedia_id=flixmedia_id,
            video_urls=video_urls
        )

        return [p]

    @classmethod
    def banners(cls, extra_args=None):
        sections_data = [
            [bs.HOME, 'Home', bs.SUBSECTION_TYPE_HOME,
             'https://www.lapolar.cl/'],
            [bs.TECHNOLOGY, 'Tecnología', bs.SUBSECTION_TYPE_CATEGORY_PAGE,
             'https://www.lapolar.cl/tecnologia/']
        ]

        session = session_with_proxy(extra_args)
        banners = []

        for section, subsection, subsection_type, url in sections_data:
            response = session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            if subsection_type == bs.SUBSECTION_TYPE_HOME:
                banner_tags = soup.findAll('div', 'rojoPolar')

                for index, banner_tag in enumerate(banner_tags):
                    picture_tag = banner_tag.find('source')
                    if picture_tag:
                        picture_url = picture_tag['srcset']
                    else:
                        picture_url = banner_tag.find('img')['src']
                    destination_urls = [banner_tag.find('a')['href']]

                    banners.append({
                        'url': url,
                        'picture_url': picture_url,
                        'destination_urls': destination_urls,
                        'key': picture_url[:250],
                        'position': index + 1,
                        'section': section,
                        'subsection': subsection,
                        'type': subsection_type
                    })
            elif subsection_type == bs.SUBSECTION_TYPE_CATEGORY_PAGE:
                banner_tag = soup.find('div', 'category-banner-module__image')

                if not banner_tag:
                    continue

                picture_url = banner_tag.find('source')['srcset']
                destination_urls = [banner_tag.find('a')['href'][:500]]

                banners.append({
                    'url': url,
                    'picture_url': picture_url,
                    'destination_urls': destination_urls,
                    'key': picture_url,
                    'position': 1,
                    'section': section,
                    'subsection': subsection,
                    'type': subsection_type
                })
        return banners
