# -*- coding: utf-8 -*-

import os

from openfisca_core.taxbenefitsystems import TaxBenefitSystem

from openfisca_france_pension import entities


COUNTRY_DIR = os.path.dirname(os.path.abspath(__file__))


# Our country tax and benefit class inherits from the general TaxBenefitSystem class.
# The name CountryTaxBenefitSystem must not be changed, as all tools of the OpenFisca ecosystem expect a CountryTaxBenefitSystem class to be exposed in the __init__ module of a country package.
class CountryTaxBenefitSystem(TaxBenefitSystem):
    def __init__(self):
        # We initialize our tax and benefit system with the general constructor
        super(CountryTaxBenefitSystem, self).__init__(entities.entities)

        # We add to our tax and benefit system all the variables
        self.add_variables_from_directory(os.path.join(COUNTRY_DIR, 'variables'))
        # We add to our tax and benefit system all the legislation parameters defined in the  parameters files
        param_path = os.path.join(COUNTRY_DIR, 'parameters')

        self.load_parameters(param_path)
        # print(self.parameters)

        from openfisca_core.parameters import Parameter
        taux_plein = Parameter("taux_plein", data = {
            "1972-01-01": .5,
            "1946-01-01": .4
            })
        self.parameters.secteur_prive.regime_general_cnav.add_child("taux_plein", taux_plein)
        print(self.parameters.secteur_prive.regime_general_cnav.taux_plein)
        print(self.variables.keys())