import json
import urllib

import requests
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class GrupoCva(Store):
    SESSION_COOKIES = None

    @classmethod
    def categories(cls):
        return [
            'ExternalStorageDrive',
            'StorageDrive',
            'SolidStateDrive',
            'MemoryCard',
            'UsbFlashDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/x-www-form-urlencoded'

        category_paths = [
            ('fGrupo=7361&gpo1=7363', 'ExternalStorageDrive'),
            # DD Externos
            ('fGrupo=7361&gpo1=7362&gpo2=7364', 'StorageDrive'),
            # DD Desktop
            ('fGrupo=7361&gpo1=7362&gpo2=7365', 'StorageDrive'),
            # DD Movilidad
            ('fGrupo=7361&gpo1=7362&gpo2=7366', 'SolidStateDrive'),
            # DD Estado Solido
            ('fGrupo=7361&gpo1=7362&gpo2=12363', 'SolidStateDrive'),
            # DD M.2
            ('fGrupo=7361&gpo1=7362&gpo2=12362', 'SolidStateDrive'),
            # DD MSATA
            ('fGrupo=291&gpo1=584', 'MemoryCard'),  # Compact Flash
            ('fGrupo=291&gpo1=582', 'MemoryCard'),  # MEMORY STICK (DUO)
            ('fGrupo=291&gpo1=583', 'MemoryCard'),  # MEMORY STICK PRO
            ('fGrupo=291&gpo1=578', 'MemoryCard'),  # Micro MMC
            ('fGrupo=291&gpo1=581', 'MemoryCard'),  # MicroSD
            ('fGrupo=291&gpo1=761', 'MemoryCard'),  # MicroStick
            ('fGrupo=291&gpo1=577', 'MemoryCard'),  # Mini MMC
            ('fGrupo=291&gpo1=580', 'MemoryCard'),  # Mini SD
            ('fGrupo=291&gpo1=576', 'MemoryCard'),  # MMC
            ('fGrupo=291&gpo1=579', 'MemoryCard'),  # SD
            ('fGrupo=291&gpo1=1121', 'MemoryCard'),  # SDHC
            ('fGrupo=291&gpo1=587', 'MemoryCard'),  # XD
            ('fGrupo=291&gpo1=13722', 'UsbFlashDrive'),  # Lightning
            ('fGrupo=291&gpo1=585', 'UsbFlashDrive'),  # USB
        ]

        product_urls = []

        currencies_dict = {
            'Dolares': 'USD',
            'Pesos': 'MXN'
        }

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            response = cls._retrieve_page(
                session,
                'https://www.grupocva.com/me_bpm/Cotizaciones/'
                'CotizaPrecioLista.php',
                category_path + '&fOrden=2&fMarca=%25',
                extra_args)
            soup = BeautifulSoup(response.text, 'html.parser')

            for row in soup.findAll('tr', 'mestyle'):
                product_id = row.find('input', {'id': 'ProdID'})['value']
                product_price_containers = row.findAll('span', 'style6')

                if len(product_price_containers) != 3:
                    continue

                pricing_contents = product_price_containers[-1].contents
                price = Decimal(pricing_contents[0])
                currency = currencies_dict[pricing_contents[2]]

                product_url = 'https://www.grupocva.com/me_bpm/' \
                              'detalle_articulo/me_articulo.php?fProdId={}' \
                              '&price={}&currency={}'.format(product_id,
                                                             price, currency)
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        query_string = urllib.parse.urlparse(url).query
        params = urllib.parse.parse_qs(query_string)
        price = Decimal(params['price'][0])
        currency = params['currency'][0]
        id = params['fProdId'][0]

        product_url = 'https://www.grupocva.com/me_bpm/' \
                      'detalle_articulo/me_articulo.php?fProdId=' + id

        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/x-www-form-urlencoded'

        request_payload = 'accion=getArticulo&id=' + id
        response = cls._retrieve_page(
            session,
            'https://www.grupocva.com/me_bpm/detalle_articulo/'
            'fcDetArticulo.php', request_payload, extra_args)

        json_data = json.loads(response.text)

        name = json_data['descripcion'][:255]
        sku = json_data['clave']
        key = json_data['idProd']
        part_number = json_data['fabricante']
        description = html_to_markdown(json_data['desT'])
        picture_urls = ['https://www.grupocva.com/me_bpm/'
                        'detalle_articulo/imagen_art.php?fProd=' + key]

        stock_url = 'https://www.grupocva.com/me_bpm/' \
                    'existencia/exs_general.php?fPID=' + key
        stock_soup = BeautifulSoup(requests.get(
            stock_url,
            cookies=cls.SESSION_COOKIES,
            timeout=30).text, 'html.parser')

        stock = int(stock_soup.find(
            'strong', text='Total General').next.next.next.text)

        p = Product(
            name,
            cls.__name__,
            category,
            product_url,
            product_url,
            key,
            stock,
            price,
            price,
            currency,
            sku=sku,
            part_number=part_number,
            description=description,
            picture_urls=picture_urls
        )

        return [p]

    @classmethod
    def _retrieve_page(cls, session, url, data, extra_args, refresh=False):
        cookies = cls._session_cookies(session, extra_args, refresh)
        response = session.post(url, data=data, cookies=cookies, timeout=30)

        if response.url == 'https://www.grupocva.com/me_bpm/no_log.php':
            if refresh:
                raise Exception('Invalid username / password')
            else:
                return cls._retrieve_page(session, url, data, extra_args,
                                          refresh=True)
        else:
            return response

    @classmethod
    def _session_cookies(cls, session, extra_args, refresh=True):
        if not cls.SESSION_COOKIES or refresh:
            login_payload = 'fUsuarioNew={}&fContraseniaNew={}'.format(
                extra_args['username'], extra_args['password'])

            session.post(
                'https://www.grupocva.com/me_bpm/ControlInicioSesion.php',
                login_payload,
                timeout=30)

            cls.SESSION_COOKIES = session.cookies.get_dict()

        return cls.SESSION_COOKIES
