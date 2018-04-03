import time

from decimal import Decimal
from selenium import webdriver

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import check_ean13


class IngramMicro(Store):
    preferred_discover_urls_concurrency = 1
    preferred_products_for_url_concurrency = 1

    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'StorageDrive',
            'SolidStateDrive',
            'ExternalStorageDrive',
            'UsbFlashDrive',
            'MemoryCard',
            'Printer',
            'VideoCard',
            'Motherboard',
            'Processor'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ('4294948168+4293946954', 'Notebook'),
            ('4294966665+4294124479', 'StorageDrive'),
            ('4294966665+4294966664', 'StorageDrive'),
            ('4294966665+4294966254+4294966184', 'UsbFlashDrive'),
            ('4294966665+4294966254+4294966253', 'MemoryCard'),
            ('4293946979+4293946978', 'Printer'),
            ('4293946979+4293944935', 'Printer'),
            ('4294966677+4293939789', 'VideoCard'),
            ('4294966677+4294965496', 'Motherboard'),
            ('4294966677+4294965687', 'Processor'),
        ]

        discovered_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            url = 'https://cl.ingrammicro.com/_layouts/CommerceServer/IM/' \
                  'search2.aspx#PNavDS=N:{0}+202'.format(category_path)

            discovered_urls.append(url)

        return discovered_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        driver = cls._session_driver(extra_args)
        driver.get(url)

        time.sleep(5)

        first_url_of_last_page = None
        products = []

        while True:
            slept = False
            containers = driver.find_elements_by_class_name(
                'single-result')

            for idx, container in enumerate(containers):
                product_url = container.find_element_by_class_name(
                    'ellipsis-multiline').get_attribute('href')

                if idx == 0 and product_url == first_url_of_last_page:
                    time.sleep(5)
                    slept = True
                    break

                if idx == 0:
                    first_url_of_last_page = product_url

                if container.text.strip():

                    pricing_spans = container.find_element_by_class_name(
                        'prod-number-container').find_elements_by_tag_name(
                        'span')

                    part_number = pricing_spans[0].text

                    if len(pricing_spans) == 3:
                        ean = pricing_spans[1].text

                        if len(ean) == 12:
                            ean = '0' + ean
                        if not check_ean13(ean):
                            ean = None

                        sku = pricing_spans[2].text
                    elif len(pricing_spans) == 2:
                        ean = None
                        sku = pricing_spans[1].text
                    else:
                        raise Exception('Invalid container')

                    name = container.find_element_by_class_name(
                        'ellipsis-multiline').text

                    price = container.find_elements_by_class_name(
                        'resprice')[1].text.split('$')

                    if len(price) > 1:
                        price = Decimal(price[1].replace(
                            '.', '').replace(',', '.'))
                        stock_tag = container.find_element_by_class_name(
                            'in-stock')
                        stock = int(
                            stock_tag.get_attribute('data-stock-qty-' + sku))
                    else:
                        price = Decimal(0)
                        stock = 0

                    if 'BAD BOX' in name:
                        condition = 'https://schema.org/DamagedCondition'
                    else:
                        condition = 'https://schema.org/NewCondition'

                    product = Product(
                        name,
                        cls.__name__,
                        category,
                        product_url,
                        url,
                        sku,
                        stock,
                        price,
                        price,
                        'USD',
                        sku=sku,
                        ean=ean,
                        condition=condition,
                        part_number=part_number
                    )

                    products.append(product)

            if slept:
                continue

            next_button = driver.find_elements_by_id('next')
            if next_button:
                next_button[0].click()
            else:
                break

        driver.close()

        return products

    @classmethod
    def _session_driver(cls, extra_args):
        time.sleep(1)
        # Browser initialization
        driver = webdriver.PhantomJS()
        # driver = webdriver.Chrome()

        driver.get('https://cl.ingrammicro.com/_layouts/'
                   'CommerceServer/IM/Login.aspx')

        driver.find_element_by_id(
            'ctl00_PlaceHolderMain_txtUserEmail').send_keys(
            extra_args['username'])
        driver.find_element_by_id(
            'ctl00_PlaceHolderMain_txtPassword').send_keys(
            extra_args['password'])
        driver.find_element_by_id(
            'ctl00_PlaceHolderMain_btnLogin').click()

        time.sleep(3)

        return driver
