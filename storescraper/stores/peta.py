from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Peta(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'VideoCard',
            'Processor',
            'Monitor',
            'Television',
            'Motherboard',
            'Ram',
            'StorageDrive',
            'SolidStateDrive',
            'ExternalStorageDrive',
            'PowerSupply',
            'ComputerCase',
            'Tablet',
            'Printer',
            'Mouse',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['equipos-computadores-tablets-aio-ebooks/moviles/notebooks.html',
             'Notebook'],
            ['equipos-computadores-tablets-aio-ebooks/moviles/ultrabooks.html',
             'Notebook'],
            ['apple/mac/macbook.html', 'Notebook'],
            ['apple/mac/macbook-air.html', 'Notebook'],
            ['apple/mac/macbook-pro.html', 'Notebook'],
            ['apple/mac/macbook-pro-retina.html', 'Notebook'],
            ['partes-y-piezas/display/tarjetas-de-video.html', 'VideoCard'],
            ['partes-y-piezas/componentes/cpu-procesadores.html',
             'Processor'],
            ['partes-y-piezas/display/monitores.html', 'Monitor'],
            ['partes-y-piezas/componentes/placas-madre.html', 'Motherboard'],
            ['partes-y-piezas/componentes/memorias/memorias.html', 'Ram'],
            ['partes-y-piezas/componentes/memorias/'
             'memorias-p-pc-escritorio.html', 'Ram'],
            ['partes-y-piezas/almacenamiento/discos-internos.html',
             'StorageDrive'],
            ['partes-y-piezas/almacenamiento/discos-de-estado-solido-ssd.html',
             'SolidStateDrive'],
            ['partes-y-piezas/componentes/fuentes-de-poder/'
             'fuentes-de-poder.html', 'PowerSupply'],
            ['partes-y-piezas/componentes/gabinetes.html', 'ComputerCase'],
            ['partes-y-piezas/display/televisores.html', 'Television'],
            ['equipos-computadores-tablets-aio-ebooks/moviles/tablets.html',
             'Tablet'],
            ['apple/ipad.html', 'Tablet'],
            ['partes-y-piezas/impresoras/inyeccion-de-tinta.html', 'Printer'],
            ['partes-y-piezas/impresoras/http-laserwaca-com.html', 'Printer'],
            ['partes-y-piezas/almacenamiento/externos.html',
             'ExternalStorageDrive'],
            ['accesorios/perifericos/mouse.html', 'Mouse'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            url = 'http://www.peta.cl/index.php/' + category_path
            page = 1

            # Peta tends to change the path to its categories, and that
            # causes the pagination to break, so we load the first page
            # of the category and refresh the value of the base url for it
            url = session.get(url).url

            while True:
                print(category_path, page)
                complete_url = url + '?limit=60&p=' + str(page)

                if page >= 10:
                    raise Exception('Page overflow: ' + complete_url)

                soup = BeautifulSoup(session.get(complete_url).text,
                                     'html.parser')

                p_rows = soup.findAll('ul', 'products-grid')

                for row in p_rows:
                    for cell in row.findAll('li', 'item'):
                        product_url = cell.find('a')['href']
                        product_urls.append(product_url)

                pager = soup.find('div', 'pages')
                if not pager or not pager.find('a', 'next'):
                    break

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', {'itemprop': 'name'}).text.strip()
        sku = soup.find(
            'meta', {'itemprop': 'productID'})['content'].split(':', 1)[1]

        product_container = soup.find('div', 'product-shop')

        if product_container.find('p', 'out-of-stock'):
            stock = 0
        else:
            stock = -1

        price_containers = soup.find('div', 'price-box').findAll(
            'span', 'price')

        offer_price = Decimal(remove_words(price_containers[0].text))
        normal_price = Decimal(remove_words(price_containers[1].text))

        picture_urls = [tag['href'] for tag in
                        soup.findAll('a', 'fancy-images')]

        description = html_to_markdown(
            str(soup.find('div', 'short-description')))

        for section in soup.findAll('div', 'tab-content'):
            description += '\n\n' + html_to_markdown(str(section))

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
            part_number=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
