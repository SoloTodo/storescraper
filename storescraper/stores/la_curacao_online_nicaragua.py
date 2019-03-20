from storescraper.stores.la_curacao_online import LaCuracaoOnline


class LaCuracaoOnlineNicaragua(LaCuracaoOnline):
    country = 'nicaragua'
    currency = 'C$'
    currency_iso = 'NIO'
    category_filters = [
        ('electronica/celulares.html', 'Cell'),
        ('audio-y-video/televisores.html', 'Television'),
        ('audio-y-video/equipos-de-sonido.html', 'StereoSystem'),
        ('audio-y-video/reproductores-de-video.html', 'OpticalDiskPlayer'),
        ('hogar/aires-acondicionados.html', 'AirConditioner'),
        # ('electrodomesticos/hornillas.html', 'Stove'),
        ('refrigeracion/refrigeradoras.html', 'Refrigerator'),
        ('refrigeracion/congeladores.html', 'Refrigerator'),
        ('lavadoras-y-secadoras/lavadoras.html', 'WashingMachine'),
        ('cocina/microondas.html', 'Oven'),
    ]
