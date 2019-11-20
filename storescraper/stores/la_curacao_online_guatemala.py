from storescraper.stores.la_curacao_online import LaCuracaoOnline


class LaCuracaoOnlineGuatemala(LaCuracaoOnline):
    country = 'guatemala'
    currency = 'Q'
    currency_iso = 'GTQ'
    category_filters = [
        # ('electronica/celulares.html', 'Cell'),
        ('audio-y-video/televisores.html', 'Television'),
        ('audio-y-video/equipos-de-sonido.html', 'StereoSystem'),
        ('audio-y-video/reproductores-de-video.html', 'OpticalDiskPlayer'),
        ('hogar/ventilacion/aires-acondicionados.html', 'AirConditioner'),
        # ('electrodomesticos/hornillas.html', 'Stove'),
        ('refrigeracion/refrigeradoras.html', 'Refrigerator'),
        ('refrigeracion/congeladores.html', 'Refrigerator'),
        ('lavadoras-y-secadoras/lavadoras.html', 'WashingMachine'),
        ('cocinas/microondas.html', 'Oven'),
        ('cocinas/cocinas-de-gas.html', 'Stove'),
    ]
