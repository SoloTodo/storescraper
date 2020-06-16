from .claro import Claro


class ClaroUp(Claro):
    combinations = [
        (' Cuotas', 'papcn_cup_valor_cuota_inicial', 'papcn_cup_12_cuotas_de'),
        (' Portabilidad Cuotas', 'pap_cup_valor_cuota_inicial',
         'pap_cup_12_cuotas_de'),
    ]
    include_prepago_price = False

    @classmethod
    def categories(cls):
        return [
            'Cell',
        ]
