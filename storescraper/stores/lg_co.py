from .lg_v6 import LgV6
from storescraper.categories import (
    TELEVISION,
    STEREO_SYSTEM,
    REFRIGERATOR,
    WASHING_MACHINE,
    MONITOR,
    PROJECTOR,
    DISH_WASHER,
    AIR_CONDITIONER,
    HEADPHONES,
    OVEN,
    STOVE,
)


class LgCo(LgV6):
    region_code = "CO"
    currency = "COP"
    price_approximation = "0"

    @classmethod
    def _category_paths(cls):
        return [
            # Todos los TVs y Soundbars
            ("CT52002006", TELEVISION),
            # Object collection - Pose
            ("CT52002038", TELEVISION),
            # Flex
            ("CT52002048", TELEVISION),
            # Audifonos
            ("CT52002016", HEADPHONES),
            # To do Audio
            ("CT52002017", STEREO_SYSTEM),
            # Proyectores
            ("CT52002019", PROJECTOR),
            # Refrigeradores
            ("CT52002008", REFRIGERATOR),
            # Lavadoras
            ("CT52002011", WASHING_MACHINE),
            # Lavavajillas
            ("CT52002014", DISH_WASHER),
            # Microondas
            ("CT52002697", OVEN),
            # "Estufas" (cocinas)
            ("CT52002668", STOVE),
            # Monitores
            ("CT52002009", MONITOR),
            # Aires acondicionados
            ("CT52002010", AIR_CONDITIONER),
        ]
