"""Réfrome du comportement de départ à age fixe."""

import numpy as np

from openfisca_core.model_api import Variable, date, ETERNITY, Reform
from openfisca_france_pension.entities import Person


def create_departt_a_age_fixe(age_fixe):
    """Crée une réforme de départ à age fixe

    Args:
        age_fixe (int): age de départ

    Returns:
        Reform: Une date de liquidation correspondant à un départ à un age fixé
    """
    class depart_a_age_fixe(Reform):
        name = f"Départ à âge fixe de {age_fixe}"

        class regime_general_cnav_liquidation_date(Variable):
            value_type = date
            entity = Person
            definition_period = ETERNITY
            label = 'Date de liquidation'

            def formula(individu, period):
                date_de_naissance = individu("date_de_naissance", period)
                date_de_liquiation = (
                    date_de_naissance.astype('datetime64[Y]') + 65
                    + (date_de_naissance.astype('datetime64[D]') - date_de_naissance.astype('datetime64[Y]'))
                    )
                return date_de_liquiation

        def apply(self):
            self.update_variable(self.regime_general_cnav_liquidation_date)

    return depart_a_age_fixe