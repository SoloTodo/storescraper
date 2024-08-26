from storescraper.stores.la_curacao_online import LaCuracaoOnline


class LaCuracaoOnlineGuatemala(LaCuracaoOnline):
    country = "guatemala"
    currency = "Q"
    currency_iso = "GTQ"

    @classmethod
    def format_url(cls, page):
        return f"https://www.lacuracaonline.com/{cls.country}/search/lg?p={page}"
