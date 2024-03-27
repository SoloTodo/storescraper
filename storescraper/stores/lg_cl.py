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
    OVEN,
)


class LgCl(LgV6):
    region_code = "CL"
    currency = "CLP"
    price_approximation = "0"

    @classmethod
    def _category_paths(cls):
        return [
            # Todos los TVs y Soundbars
            ("CT52000104", TELEVISION),
            # Object collection - Pose
            ("CT52000790", TELEVISION),
            # Flex
            ("CT52000799", TELEVISION),
            # StandbyMe
            ("CT52020281", TELEVISION),
            # To do Audio
            ("CT52000100", STEREO_SYSTEM),
            # Proyectores
            ("CT52000784", PROJECTOR),
            # Refrigeradores
            ("CT52000103", REFRIGERATOR),
            # Lavadoras
            ("CT52000102", WASHING_MACHINE),
            # Lavavajillas
            ("CT52000105", DISH_WASHER),
            # Monitores
            ("CT52000106", MONITOR),
            # Aires acondicionados
            ("CT52002586", AIR_CONDITIONER),
            # Microondas
            ("CT52020321", OVEN),
        ]
