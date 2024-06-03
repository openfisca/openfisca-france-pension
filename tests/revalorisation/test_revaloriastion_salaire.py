# import numpy as np
# import pandas as pd


# from openfisca_france_pension.regimes.regime_general_cnav import coefficient_de_revalorisation


# from openfisca_core.taxbenefitsystems import TaxBenefitSystem
# from openfisca_france_pension import COUNTRY_DIR
# from openfisca_france_pension import entities
# class ParametersOnlyFrancePension(TaxBenefitSystem):
#     def __init__(self):
#         super(ParametersOnlyFrancePension, self).__init__(entities.entities)
#         param_path = os.path.join(COUNTRY_DIR, 'parameters')
#         self.load_parameters(param_path)


# def test_coefficient_de_revalorisation_salaire():
#     tbs = ParametersOnlyFrancePension()
#     parameters = tbs.parameters
#     revalorisation_salaire_cummulee = parameters.secteur_prive.regime_general_cnav.revalorisation_salaire_cummulee

#     salaire_year = 2000
#     periods_str = [
#         "2021-12-31",
#         "2009-02-01",
#         "2009-05-01",
#         ]

#     liquidation_date = pd.to_datetime(periods_str).values

#     results = np.array([
#         revalorisation_salaire_cummulee.children[str(salaire_year)](period)
#         for period in periods_str
#         ])

#     assert (results == coefficient_de_revalorisation(salaire_year, liquidation_date)).all()


# test_coefficient_de_revalorisation_salaire()
