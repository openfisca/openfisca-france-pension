"""Régimes complémentaires du secteur privé."""


import numpy as np


from openfisca_core.model_api import *
from openfisca_core.variables import Variable

from openfisca_france_pension.entities import Person
from openfisca_france_pension.regimes.regime import AbstractRegimeComplementaire
from openfisca_france_pension.variables.hors_regime import TypesCategorieSalarie


class RegimeArrco(AbstractRegimeComplementaire):
    name = "Régime complémentaire Arrco"
    variable_prefix = "arrco"
    parameters_prefix = "secteur_prive.regimes_complementaires.arrco"

    class coefficient_de_minoration(Variable):
        value_type = float
        default_value = 1.0
        entity = Person
        definition_period = YEAR
        label = "Coefficient de minoration"

        def formula_1957_05_15(individu, period, parameters):
            minoration = parameters(period).regime_name.coefficient_de_minoration
            coefficient_de_minoration_by_distance_aad_en_annee = minoration.coefficient_minoration_en_fonction_distance_age_annulation_decote_en_annee
            distances_age_annulation_decote_en_annee = np.asarray(list(coefficient_de_minoration_by_distance_aad_en_annee._children.keys())).astype('int')
            annees_de_decote = min_(
                max_(
                    (-individu('regime_general_cnav_decote_trimestres', period) / 4).astype(int),
                    distances_age_annulation_decote_en_annee.min()
                    ),
                distances_age_annulation_decote_en_annee.max()
                )
            coefficient_de_minoration = coefficient_de_minoration_by_distance_aad_en_annee[annees_de_decote]
            return coefficient_de_minoration

    class cotisation_employeur(Variable):
        value_type = float
        default_value = 0
        entity = Person
        definition_period = YEAR
        label = "Cotisation employeur"

        def formula_2019(individu, period, parameters):
            categorie_salarie = individu("categorie_salarie", period)
            salaire_de_base = individu("salaire_de_base", period)
            plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel
            employeur = parameters(period).regime_name.prelevements_sociaux.agirc_arrco.employeur
            return (
                (categorie_salarie == TypesCategorieSalarie.prive_non_cadre)
                * employeur.agirc_arrco.calc(salaire_de_base, factor = plafond_securite_sociale)
                )

        def formula(individu, period, parameters):
            categorie_salarie = individu("categorie_salarie", period)
            salaire_de_base = individu("salaire_de_base", period)
            plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel
            employeur = parameters(period).regime_name.prelevements_sociaux.employeur

            employeur_non_cadre = employeur.noncadre.arrco.calc(salaire_de_base, factor = plafond_securite_sociale)
            employeur_cadre = employeur.cadre.arrco.calc(salaire_de_base, factor = plafond_securite_sociale)

            return select(
                [categorie_salarie == TypesCategorieSalarie.prive_non_cadre, categorie_salarie == TypesCategorieSalarie.prive_cadre],
                [employeur_non_cadre, employeur_cadre],
                )

    class cotisation_salarie(Variable):
        value_type = float
        default_value = 0
        entity = Person
        definition_period = YEAR
        label = "Cotisation salarié"

        def formula_2019(individu, period, parameters):
            categorie_salarie = individu("categorie_salarie", period)
            salaire_de_base = individu("salaire_de_base", period)
            plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel
            salarie = parameters(period).regime_name.prelevements_sociaux.agirc_arrco.salarie
            return (
                (categorie_salarie == TypesCategorieSalarie.prive_non_cadre)
                * salarie.agirc_arrco.calc(salaire_de_base, factor = plafond_securite_sociale)
                )

        def formula(individu, period, parameters):
            categorie_salarie = individu("categorie_salarie", period)
            salaire_de_base = individu("salaire_de_base", period)
            plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel
            salarie = parameters(period).regime_name.prelevements_sociaux.salarie
            salarie_non_cadre = salarie.noncadre.arrco.calc(salaire_de_base, factor = plafond_securite_sociale)
            salarie_cadre = salarie.cadre.arrco.calc(salaire_de_base, factor = plafond_securite_sociale)

            return select(
                [categorie_salarie == TypesCategorieSalarie.prive_non_cadre, categorie_salarie == TypesCategorieSalarie.prive_cadre],
                [salarie_non_cadre, salarie_cadre],
                )


#     def pension(self, data, coefficient_age, pension_brute_b,
#                 majoration_pension, trim_decote):
#         ''' le régime Arrco ne tient pas compte du coefficient de
#         minoration pour le calcul des majorations pour enfants '''


class RegimeAgirc(AbstractRegimeComplementaire):
    name = "Régime complémentaire Agirc"
    variable_prefix = "agirc"
    parameters_prefix = "secteur_prive.regimes_complementaires.agirc"

    class coefficient_de_minoration(Variable):
        value_type = float
        default_value = 1.0
        entity = Person
        definition_period = YEAR
        label = "Coefficient de minoration"

        def formula_1947_03_14(individu, period, parameters):
            minoration = parameters(period).regime_name.coefficient_de_minoration
            coefficient_de_minoration_by_distance_aad_en_annee = minoration.coefficient_minoration_en_fonction_distance_age_annulation_decote_en_annee
            distances_age_annulation_decote_en_annee = np.asarray(list(coefficient_de_minoration_by_distance_aad_en_annee._children.keys())).astype('int')
            annees_de_decote = min_(
                max_(
                    (-individu('regime_general_cnav_decote_trimestres', period) / 4).astype(int),
                    distances_age_annulation_decote_en_annee.min()
                    ),
                distances_age_annulation_decote_en_annee.max()
                )
            coefficient_de_minoration = coefficient_de_minoration_by_distance_aad_en_annee[annees_de_decote]
            return coefficient_de_minoration

    class cotisation_employeur(Variable):
        value_type = float
        default_value = 0
        entity = Person
        definition_period = YEAR
        label = "Cotisation employeur"

        def formula_2019(individu, period, parameters):
            categorie_salarie = individu("categorie_salarie", period)
            salaire_de_base = individu("salaire_de_base", period)
            plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel
            employeur = parameters(period).regime_name.prelevements_sociaux.agirc_arrco.employeur
            return (
                (categorie_salarie == TypesCategorieSalarie.prive_cadre)
                * employeur.agirc_arrco.calc(salaire_de_base, factor = plafond_securite_sociale)
                )

        def formula(individu, period, parameters):
            categorie_salarie = individu("categorie_salarie", period)
            salaire_de_base = individu("salaire_de_base", period)
            plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel
            employeur = parameters(period).regime_name.prelevements_sociaux.employeur
            return (
                (categorie_salarie == TypesCategorieSalarie.prive_cadre)
                * employeur.agirc.calc(salaire_de_base, factor = plafond_securite_sociale)
                )

    class cotisation_salarie(Variable):
        value_type = float
        default_value = 0
        entity = Person
        definition_period = YEAR
        label = "Cotisation salarié"

        def formula_2019(individu, period, parameters):
            categorie_salarie = individu("categorie_salarie", period)
            salaire_de_base = individu("salaire_de_base", period)
            plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel
            salarie = parameters(period).regime_name.prelevements_sociaux.agirc_arrco.salarie
            return (
                (categorie_salarie == TypesCategorieSalarie.prive_cadre)
                * salarie.agirc_arrco.calc(salaire_de_base, factor = plafond_securite_sociale)
                )

        def formula(individu, period, parameters):
            categorie_salarie = individu("categorie_salarie", period)
            salaire_de_base = individu("salaire_de_base", period)
            plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel
            salarie = parameters(period).regime_name.prelevements_sociaux.salarie
            return (
                (categorie_salarie == TypesCategorieSalarie.prive_cadre)
                * salarie.agirc.calc(salaire_de_base, factor = plafond_securite_sociale)
                )
