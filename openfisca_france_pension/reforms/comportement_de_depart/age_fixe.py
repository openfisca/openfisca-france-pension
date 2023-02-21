"""Réfrome du comportement de départ à age fixe."""

import numpy as np
from openfisca_core.model_api import ETERNITY, Reform, Variable, date

from openfisca_france_pension.entities import Person


def create_depart_a_age_fixe(age_fixe = 65):
    """Crée une réforme de départ à age fixe. Defaults to 65.

    Args:
        age_fixe (int): age de départ

    Returns:
        Reform: Une date de liquidation correspondant à un départ à un age fixé

    """
    class depart_a_age_fixe(Reform):
        name = "Départ à âge donné (défaut à 65 ans)"

        class regime_general_cnav_liquidation_date(Variable):
            value_type = date
            entity = Person
            definition_period = ETERNITY
            label = 'Date de liquidation'

            def formula(individu, period):
                date_de_naissance = individu("date_de_naissance", period)
                age_de_depart = individu("age_de_depart", period)

                days = (np.floor(365.25 * (age_de_depart - np.floor(age_de_depart)))).astype(int).astype("timedelta64[D]")
                date_de_liquidation = (
                    date_de_naissance.astype('datetime64[Y]') + np.floor(age_de_depart).astype(int)
                    + (
                        date_de_naissance.astype('datetime64[D]')
                        - date_de_naissance.astype('datetime64[Y]')
                        )
                    + days
                    )
                return date_de_liquidation

        class age_de_depart(Variable):
            value_type = float
            entity = Person
            definition_period = ETERNITY
            label = 'Age décimal à la liquidation'
            default_value = age_fixe

        def apply(self):
            self.update_variable(self.regime_general_cnav_liquidation_date)
            self.add_variable(self.age_de_depart)

    return depart_a_age_fixe
