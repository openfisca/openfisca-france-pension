"""Régimes complémentaires du secteur privé."""


import numpy as np


from openfisca_core.model_api import *
from openfisca_core.variables import Variable

from openfisca_france_pension.entities import Person
from openfisca_france_pension.regimes.regime import AbstractRegimeEnPoints
from openfisca_france_pension.variables.hors_regime import TypesCategorieSalarie
from openfisca_france_pension.regimes.regime_general_cnav import conversion_parametre_en_euros


class AbstractRegimeAgircArrco(AbstractRegimeEnPoints):
    name = "Régime abstrait type régime complémentaire Agirc-Arrco"

    class majoration_pension(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Majoration de pension"

        def formula_2019(individu, period, parameters):
            points_enfants = individu('regime_name_points_enfants', period)
            valeur_du_point = parameters(period).retraites.secteur_prive.regimes_complementaires.agirc_arrco.point.valeur_point_en_euros
            # Plafond fixé à 1000 € en 2012 et évoluant comme le point
            plafond = 1000 * valeur_du_point / parameters(2012).retraites.secteur_prive.regimes_complementaires.arrco.point.valeur_point_en_euros
            return where(
                individu('date_de_naissance', period) >= np.datetime64("1951-08-02"),
                min_(points_enfants * valeur_du_point, plafond),
                points_enfants * valeur_du_point
                )

        def formula_2012(individu, period, parameters):
            points_enfants = individu('regime_name_points_enfants', period)
            valeur_du_point = parameters(period).regime_name.point.valeur_point_en_euros
            # Plafond fixé à 1000 € en 2012 et évoluant comme le point
            plafond = 1000 * valeur_du_point / parameters(2012).regime_name.point.valeur_point_en_euros
            return where(
                individu('date_de_naissance', period) >= np.datetime64("1951-08-02"),
                min_(points_enfants * valeur_du_point, plafond),
                points_enfants * valeur_du_point
                )

        def formula_1999(individu, period, parameters):
            points_enfants = individu('regime_name_points_enfants', period)
            valeur_du_point = parameters(period).regime_name.point.valeur_point_en_euros
            return points_enfants * valeur_du_point

        def formula(individu, period, parameters):
            return individu.empty_array()

    class pension_brute(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Pension brute"

        def formula_2019(individu, period, parameters):
            valeur_du_point = parameters(period).retraites.secteur_prive.regimes_complementaires.agirc_arrco.point.valeur_point_en_euros
            points = individu("regime_name_points", period)
            points_minimum_garantis = individu("regime_name_points_minimum_garantis", period)
            pension_brute = (points + points_minimum_garantis) * valeur_du_point
            return pension_brute

        def formula(individu, period, parameters):
            valeur_du_point = parameters(period).regime_name.point.valeur_point_en_euros
            points = individu("regime_name_points", period)
            points_minimum_garantis = individu("regime_name_points_minimum_garantis", period)
            pension_brute = (points + points_minimum_garantis) * valeur_du_point
            return pension_brute

    class points_enfants_a_charge(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Points enfants à charge"

    class points_enfants_nes_et_eleves(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Points enfants nés et élevés"

    class points_enfants(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Points enfants"

        def formula(individu, period):
            """
            Deux types de majorations pour enfants peuvent s'appliquer:
            - pour enfant à charge au moment du départ en retraite
            - pour enfant nés et élevés en cours de carrière (majoration sur la totalité des droits acquis)
            C'est la plus avantageuse qui s'applique.
            """
            points_enfants_a_charge = individu('regime_name_points_enfants_a_charge', period)
            points_enfants_nes_et_eleves = individu('regime_name_points_enfants_nes_et_eleves', period)
            return max_(points_enfants_a_charge, points_enfants_nes_et_eleves)

    class points_annuels(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Points annuels"

        def formula(individu, period):
            points_emploi_annuels = individu('regime_name_points_emploi_annuels', period)
            points_hors_emploi_annuels = individu('regime_name_points_hors_emploi_annuels', period)
            return points_emploi_annuels + points_hors_emploi_annuels

    class points_hors_emploi_annuels(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Points annuels hors emploi"


class RegimeArrco(AbstractRegimeAgircArrco):
    name = "Régime complémentaire Arrco"
    variable_prefix = "arrco"
    parameters_prefix = "retraites.secteur_prive.regimes_complementaires.arrco"

    class coefficient_de_minoration(Variable):
        value_type = float
        default_value = 1.0
        entity = Person
        definition_period = YEAR
        label = "Coefficient de minoration"

        def formula_1957_05_15(individu, period, parameters):
            # TODO find starting date
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

    class cotisation(Variable):
        value_type = float
        default_value = 0
        entity = Person
        definition_period = YEAR
        label = "Cotisation"

        def formula_2019(individu, period, parameters):
            categorie_salarie = individu("categorie_salarie", period)
            salaire_de_base = individu("regime_general_cnav_salaire_de_base", period)
            plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel * conversion_parametre_en_euros(period.start.year)
            employeur = parameters(period).regime_name.prelevements_sociaux.agirc_arrco.employeur
            salarie = parameters(period).regime_name.prelevements_sociaux.agirc_arrco.salarie
            return (
                (categorie_salarie == TypesCategorieSalarie.prive_non_cadre)
                * (
                    employeur.agirc_arrco.calc(salaire_de_base, factor = plafond_securite_sociale)
                    + salarie.agirc_arrco.calc(salaire_de_base, factor = plafond_securite_sociale)
                    )
                )

        def formula_1962(individu, period, parameters):
            categorie_salarie = individu("categorie_salarie", period)
            salaire_de_base = individu("regime_general_cnav_salaire_de_base", period)
            plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel * conversion_parametre_en_euros(period.start.year)
            employeur = parameters(period).regime_name.prelevements_sociaux.taux_effectifs_salaries_employeurs.employeur

            employeur_non_cadre = employeur.noncadre.arrco.calc(salaire_de_base, factor = plafond_securite_sociale)
            employeur_cadre = employeur.cadre.arrco.calc(salaire_de_base, factor = plafond_securite_sociale)
            salarie = parameters(period).regime_name.prelevements_sociaux.taux_effectifs_salaries_employeurs.salarie
            salarie_non_cadre = salarie.noncadre.arrco.calc(salaire_de_base, factor = plafond_securite_sociale)

            salarie_cadre = salarie.cadre.arrco.calc(salaire_de_base, factor = plafond_securite_sociale)

            return select(
                [
                    categorie_salarie == TypesCategorieSalarie.prive_non_cadre,
                    (categorie_salarie == TypesCategorieSalarie.prive_cadre) * (period.start.year >= 1976),
                    # D'après guide EIC pas obligatoire avant 1976 TODO: check
                    ],
                [
                    employeur_non_cadre + salarie_non_cadre,
                    employeur_cadre + salarie_cadre,
                    ],
                default = 0,
                )

#     def pension(self, data, coefficient_age, pension_brute_b,
#                 majoration_pension, trim_decote):
#         """ le régime Arrco ne tient pas compte du coefficient de
#         minoration pour le calcul des majorations pour enfants """

    class points_emploi_annuels(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Points annuels en emploi"

        def formula_2019(individu, period, parameters):
            agirc_arrco = parameters(period).retraites.secteur_prive.regimes_complementaires.agirc_arrco
            salaire_de_reference = agirc_arrco.salaire_de_reference.salaire_reference_en_euros
            taux_appel = agirc_arrco.prelevements_sociaux.taux_appel
            cotisation = individu("regime_name_cotisation", period)

            return cotisation / salaire_de_reference / taux_appel

        def formula_1962(individu, period, parameters):
            salaire_de_reference = parameters(period).regime_name.salaire_de_reference.salaire_reference_en_euros
            taux_appel = parameters(period).regime_name.prelevements_sociaux.taux_appel
            cotisation = individu("regime_name_cotisation", period)

            return cotisation / salaire_de_reference / taux_appel

    class points_enfants_a_charge(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Points enfants à charge"
        # https://www.agirc-arrco.fr/fileadmin/agircarrco/documents/notices/majorations_enfants.pdf
        # TODO retirer paramètres en dur

        def formula(individu, period, parameters):
            points = individu('regime_name_points', period)
            nombre_enfants_a_charge = individu('nombre_enfants_a_charge', period)
            return .05 * points * nombre_enfants_a_charge

    class points_enfants_nes_et_eleves(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Points enfants nés et élevés"
        # https://www.agirc-arrco.fr/fileadmin/agircarrco/documents/notices/majorations_enfants.pdf
        # TODO retirer paramètres en dur

        def formula_2012(individu, period, parameters):
            nombre_enfants_nes_et_eleves = individu('nombre_enfants', period)
            if all(nombre_enfants_nes_et_eleves == 0):
                return individu.empty_array()
            points = individu('regime_name_points', period) - individu('regime_name_points', 2011)
            points_enfants_nes_et_eleves_anterieurs = individu('regime_name_points_enfants_nes_et_eleves', 2011)
            return .1 * points * (nombre_enfants_nes_et_eleves >= 3) + points_enfants_nes_et_eleves_anterieurs

        def formula_1999(individu, period, parameters):
            nombre_enfants_nes_et_eleves = individu('nombre_enfants', period)
            if all(nombre_enfants_nes_et_eleves == 0):
                return individu.empty_array()
            points = individu('regime_name_points', period) - individu('regime_name_points', 1998)
            points_enfants_nes_et_eleves_anterieurs = individu('regime_name_points_enfants_nes_et_eleves', 1998)
            return .05 * points * (nombre_enfants_nes_et_eleves >= 3) + points_enfants_nes_et_eleves_anterieurs

        def formula_1945(individu, period, parameters):
            # TODO dépend de la caisse
            return individu.empty_array()


class RegimeAgirc(AbstractRegimeAgircArrco):
    name = "Régime complémentaire Agirc"
    variable_prefix = "agirc"
    parameters_prefix = "retraites.secteur_prive.regimes_complementaires.agirc"

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

    class cotisation(Variable):
        value_type = float
        default_value = 0
        entity = Person
        definition_period = YEAR
        label = "Cotisation"

        def formula_2019(individu, period, parameters):
            categorie_salarie = individu("categorie_salarie", period)
            salaire_de_base = individu("regime_general_cnav_salaire_de_base", period)
            plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel * conversion_parametre_en_euros(period.start.year)
            employeur = parameters(period).regime_name.prelevements_sociaux.agirc_arrco.employeur
            salarie = parameters(period).regime_name.prelevements_sociaux.agirc_arrco.salarie
            return (
                (categorie_salarie == TypesCategorieSalarie.prive_cadre)
                * (
                    employeur.agirc_arrco.calc(salaire_de_base, factor = plafond_securite_sociale)
                    + salarie.agirc_arrco.calc(salaire_de_base, factor = plafond_securite_sociale)
                    )
                )

        def formula_1948(individu, period, parameters):
            categorie_salarie = individu("categorie_salarie", period)
            salaire_de_base = individu("regime_general_cnav_salaire_de_base", period)
            plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel * conversion_parametre_en_euros(period.start.year)
            employeur = parameters(period).regime_name.prelevements_sociaux.taux_effectifs_salaries_employeurs.avant81.employeur.agirc.copy()
            salarie = parameters(period).regime_name.prelevements_sociaux.taux_effectifs_salaries_employeurs.avant81.salarie.agirc.copy()

            agirc = employeur
            agirc.add_tax_scale(salarie)

            # # Ajout de la GMP dans le barème
            points_gmp = parameters(period).regime_name.gmp.garantie_minimale_points
            salaire_de_reference = parameters(period).regime_name.salaire_de_reference.salaire_reference_en_euros
            taux_appel = parameters(period).regime_name.prelevements_sociaux.taux_appel
            cotisation_gmp_annuelle = points_gmp * salaire_de_reference * taux_appel
            base_gmp_annuelle = cotisation_gmp_annuelle / agirc.rates[1]
            salaire_charniere_annuel = plafond_securite_sociale + base_gmp_annuelle
            salaire_charniere = salaire_charniere_annuel / plafond_securite_sociale
            cotisation = cotisation_gmp_annuelle
            n = (cotisation + .1) * 12
            agirc.add_bracket(n / plafond_securite_sociale, 0)
            agirc.rates[0] = cotisation / n
            agirc.thresholds[2] = salaire_charniere

            return (
                (categorie_salarie == TypesCategorieSalarie.prive_cadre)
                * agirc.calc(salaire_de_base, factor = plafond_securite_sociale)
                )

    class points_emploi_annuels(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Points annuels en emploi"

        def formula_2019(individu, period, parameters):
            agirc_arrco = parameters(period).retraites.secteur_prive.regimes_complementaires.agirc_arrco
            salaire_de_reference = agirc_arrco.salaire_de_reference.salaire_reference_en_euros
            taux_appel = agirc_arrco.prelevements_sociaux.taux_appel
            cotisation = individu("regime_name_cotisation", period)

            return cotisation / salaire_de_reference / taux_appel

        def formula_1947(individu, period, parameters):
            salaire_de_reference = parameters(period).regime_name.salaire_de_reference.salaire_reference_en_euros
            taux_appel = parameters(period).regime_name.prelevements_sociaux.taux_appel
            cotisation = individu("regime_name_cotisation", period)
            return cotisation / salaire_de_reference / taux_appel

    class points_enfants_a_charge(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Points enfants à charge"
        # https://www.agirc-arrco.fr/fileadmin/agircarrco/documents/notices/majorations_enfants.pdf
        # TODO retirer paramètres en dur

        def formula_2012(individu, period, parameters):
            points = individu('regime_name_points', period)
            nombre_enfants_a_charge = individu('nombre_enfants_a_charge', period)
            return .05 * points * nombre_enfants_a_charge

    class points_enfants_nes_et_eleves(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Points enfants nés et élevés"
        # https://www.agirc-arrco.fr/fileadmin/agircarrco/documents/notices/majorations_enfants.pdf
        # TODO retirer paramètres en dur

        def formula_2012(individu, period):
            points = individu('regime_name_points', period) - individu('regime_name_points', 2011)
            nombre_enfants_nes_et_eleves = individu('nombre_enfants', period)
            points_enfants_nes_et_eleves_anterieurs = individu('regime_name_points_enfants_nes_et_eleves', 2011)
            return .1 * points * (nombre_enfants_nes_et_eleves >= 3) + points_enfants_nes_et_eleves_anterieurs

        def formula_1945(individu, period):
            points = individu('regime_name_points', period)
            nombre_enfants_nes_et_eleves = individu('nombre_enfants', period)
            return points * (
                (nombre_enfants_nes_et_eleves == 3) * .08
                + (nombre_enfants_nes_et_eleves == 4) * .12
                + (nombre_enfants_nes_et_eleves == 5) * .16
                + (nombre_enfants_nes_et_eleves == 6) * .20
                + (nombre_enfants_nes_et_eleves >= 7) * .24
                )
