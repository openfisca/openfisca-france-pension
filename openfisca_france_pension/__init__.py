"""OpenFisca France Pension tax-benefit system."""

import logging
import os

from openfisca_core.parameters import ParameterNode
from openfisca_core.taxbenefitsystems import TaxBenefitSystem

from openfisca_france_pension import entities
from openfisca_france_pension.scripts_ast import script_ast


COUNTRY_DIR = os.path.dirname(os.path.abspath(__file__))

logging.getLogger('numba.core.ssa').disabled = True
logging.getLogger('numba.core.byteflow').disabled = True
logging.getLogger('numba.core.interpreter').disabled = True

# Convert regimes classes to OpenFisca variables.
script_ast.main(verbose = False)


def build_regimes_prelevements_sociaux(parameters):
    regime_general_cnav = parameters.prelevements_sociaux.cotisations_securite_sociale_regime_general.cnav
    parameters.secteur_prive.regime_general_cnav.add_child(
        "prelevements_sociaux",
        regime_general_cnav,
        )
    arrco = parameters.prelevements_sociaux.regimes_complementaires_retraite_secteur_prive.arrco
    parameters.secteur_prive.regimes_complementaires.arrco.add_child(
        "prelevements_sociaux",
        arrco,
        )
    agirc = parameters.prelevements_sociaux.regimes_complementaires_retraite_secteur_prive.agirc
    parameters.secteur_prive.regimes_complementaires.agirc.add_child(
        "prelevements_sociaux",
        agirc,
        )
    # Régime unifié depuis 2019
    agirc_arrco = parameters.prelevements_sociaux.regimes_complementaires_retraite_secteur_prive.agirc_arrco
    parameters.secteur_prive.regimes_complementaires.arrco.prelevements_sociaux.add_child(
        "agirc_arrco",
        agirc_arrco,
        )
    parameters.secteur_prive.regimes_complementaires.agirc.prelevements_sociaux.add_child(
        "agirc_arrco",
        agirc_arrco,
        )


def build_secteur_public_reval_p(parameters):
    reval_p = parameters.secteur_prive.regime_general_cnav.reval_p
    parameters.secteur_public.add_child(
        "reval_p",
        reval_p,
        )


class CountryTaxBenefitSystem(TaxBenefitSystem):
    def __init__(self):
        super(CountryTaxBenefitSystem, self).__init__(entities.entities)
        self.add_variables_from_directory(os.path.join(COUNTRY_DIR, 'variables'))
        param_path = os.path.join(COUNTRY_DIR, 'parameters')
        self.load_parameters(param_path)
        taux_plein = ParameterNode(
            "taux_plein",
            data = {
                "taux_plein": {
                    "values": {
                        "1948-01-01": .75
                        }
                    }
                }
            )
        self.parameters.secteur_public.add_child("taux_plein", taux_plein)
        build_regimes_prelevements_sociaux(self.parameters)

        arrco = self.parameters.secteur_prive.regimes_complementaires.arrco.salaire_de_reference.salaire_reference_en_euros
        unirs = self.parameters.secteur_prive.regimes_complementaires.unirs.salaire_de_reference.salaire_reference_en_euros
        arrco.values_list = arrco.values_list + unirs.values_list

        arrco = self.parameters.secteur_prive.regimes_complementaires.arrco.salaire_de_reference.salaire_reference_en_euros
        unirs = self.parameters.secteur_prive.regimes_complementaires.unirs.salaire_de_reference.salaire_reference_en_euros
        arrco.values_list = arrco.values_list + unirs.values_list

        arrco = self.parameters.secteur_prive.regimes_complementaires.arrco.point.valeur_point_en_euros
        unirs = self.parameters.secteur_prive.regimes_complementaires.unirs.point.valeur_point_en_euros
        arrco.values_list = arrco.values_list + unirs.values_list

        build_secteur_public_reval_p(self.parameters)

        self.cache_blacklist = [
            "duree_assurance_travail_avpf_annuelle",
            "duree_assurance_travail_emploi_annuelle",
            ]
