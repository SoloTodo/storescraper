from storescraper.stores.la_curacao_online import LaCuracaoOnline


class LaCuracaoOnlineNicaragua(LaCuracaoOnline):
    country = "nicaragua"
    currency = "C$"
    currency_iso = "NIO"

    @classmethod
    def format_url(cls, page):
        return f"https://www.lacuracaonline.com/{cls.country}/search/lg?p={page}"
