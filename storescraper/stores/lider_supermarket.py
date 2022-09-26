from storescraper.categories import GROCERIES
from storescraper.stores.lider import Lider


class LiderSupermarket(Lider):
    tenant = 'supermercado'
    category_paths = [
        ['Despensa/Pastas y Salsas', [GROCERIES],
            'Despensa > Pastas y Salsas', 1],
        ['Despensa/Harinas', [GROCERIES], 'Despensa > Harinas', 1],
        ['Despensa/Arroz y Legumbres', [GROCERIES],
            'Despensa > Arroz y Legumbres', 1],
        ['Despensa/Salsas', [GROCERIES], 'Despensa > Salsas', 1],
        ['Despensa/Aceites y Aderezos', [GROCERIES],
            'Despensa > Aceites y Aderezos', 1],
        ['Despensa/Cóctel y Snack', [GROCERIES],
            'Despensa > Cóctel y Snack', 1],
        ['Despensa/Conservas', [GROCERIES], 'Despensa > Conservas', 1],
        ['Despensa/Alimentos Instantáneos', [GROCERIES],
            'Despensa > Alimentos Instantáneos', 1],
        ['Despensa/Comida Étnica', [GROCERIES], 'Despensa > Comida Étnica', 1],
    ]

    @classmethod
    def categories(cls):
        return [
            GROCERIES
        ]
