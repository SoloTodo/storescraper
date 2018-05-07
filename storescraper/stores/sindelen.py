import time

from decimal import Decimal

import re
from selenium import webdriver

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, PhantomJS


class Sindelen(Store):
    preferred_discover_urls_concurrency = 1
    preferred_products_for_url_concurrency = 1

    PATHS = [
        ('33', 'Refrigerator', 'linea_blanca.aspx'),
        ('7', 'Oven', 'linea_blanca.aspx'),
        ('8', 'WashingMachine', 'linea_blanca.aspx'),
        ('11', 'Refrigerator', 'linea_blanca.aspx'),
        ('12', 'WashingMachine', 'linea_blanca.aspx'),
        ('38', 'WaterHeater', 'linea_blanca.aspx'),
        ('39', 'WaterHeater', 'linea_blanca.aspx'),
        ('41', 'SpaceHeater', 'linea_blanca.aspx'),
        ('5', 'SpaceHeater', 'linea_blanca.aspx'),
        ('6', 'SpaceHeater', 'linea_blanca.aspx'),
        ('14', 'VacuumCleaner', 'electro.aspx'),
        ('22', 'Oven', 'electro.aspx'),
        ('23', 'Oven', 'electro.aspx'),
    ]

    @classmethod
    def categories(cls):
        return [
            'Refrigerator',
            'WashingMachine',
            'Oven',
            'VacuumCleaner',
            'WaterHeater',
            'SpaceHeater',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        discovered_urls = set()

        for category_code, local_category, path in cls.PATHS:
            if local_category != category:
                continue

            discovered_url = 'http://www.sindelen.cl/{}'.format(path)
            discovered_urls.add(discovered_url)

        return list(discovered_urls)

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        with PhantomJS() as driver:
            driver.get(url)

            products = []

            for category_code, local_category, path in cls.PATHS:
                if local_category != category or path not in url:
                    continue

                driver.execute_script(
                    "__doPostBack('ctl00$ContentPlaceHolder1$Menu1', '{}')"
                    "".format(category_code))

                time.sleep(1)
                submenu = driver.find_element_by_id(
                    'ctl00_ContentPlaceHolder1_Menu2')
                product_links = submenu.find_elements_by_tag_name('a')

                js_commands = [link.get_attribute('href').split(':')[1]
                               for link in product_links
                               if link.get_attribute('href')
                               ]

                for command in js_commands:
                    driver.execute_script(command)

                    time.sleep(1)

                    product_name = '{} - {}'.format(
                        category, driver.find_element_by_id(
                            'ctl00_ContentPlaceHolder1_LabelProducto'
                        ).text.strip())

                    try:
                        price_container = driver.find_element_by_id(
                            'ctl00_ContentPlaceHolder1_LabelPrecioOferta').text
                    except Exception:
                        price_container = driver.find_element_by_id(
                            'ctl00_ContentPlaceHolder1_LabelPrecioInternet'
                            '').text

                    if 'No Disponible' in price_container:
                        stock = 0
                        product_price = Decimal(0)
                    else:
                        stock = -1
                        product_price = Decimal(remove_words(price_container))
                    sku = re.search(r"'(\d+)'", command).groups()[0]

                    p = Product(
                        product_name,
                        cls.__name__,
                        category,
                        url,
                        url,
                        sku,
                        stock,
                        product_price,
                        product_price,
                        'CLP',
                        sku=sku,
                    )

                    products.append(p)

        return products
