"""Régimes complémentaires du secteur privé."""


import numpy as np


from openfisca_core.model_api import *
from openfisca_core.variables import Variable

from openfisca_france_pension.entities import Person
from openfisca_france_pension.regimes.regime import AbstractRegimeComplementaire
from openfisca_france_pension.variables.hors_regime import TypesCategorieSalarie
from openfisca_france_pension.regimes.regime_general_cnav import conversion_parametre_en_euros


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

        def formula(individu, period, parameters):
            categorie_salarie = individu("categorie_salarie", period)
            salaire_de_base = individu("regime_general_cnav_salaire_de_base", period)
            plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel * conversion_parametre_en_euros(period.start.year)
            employeur = parameters(period).regime_name.prelevements_sociaux.employeur

            employeur_non_cadre = employeur.noncadre.arrco.calc(salaire_de_base, factor = plafond_securite_sociale)
            employeur_cadre = employeur.cadre.arrco.calc(salaire_de_base, factor = plafond_securite_sociale)
            salarie = parameters(period).regime_name.prelevements_sociaux.salarie
            salarie_non_cadre = salarie.noncadre.arrco.calc(salaire_de_base, factor = plafond_securite_sociale)
            salarie_cadre = salarie.cadre.arrco.calc(salaire_de_base, factor = plafond_securite_sociale)

            return select(
                [categorie_salarie == TypesCategorieSalarie.prive_non_cadre, categorie_salarie == TypesCategorieSalarie.prive_cadre],
                [employeur_non_cadre + salarie_non_cadre, employeur_cadre + salarie_cadre],
                )

#     def pension(self, data, coefficient_age, pension_brute_b,
#                 majoration_pension, trim_decote):
#         ''' le régime Arrco ne tient pas compte du coefficient de
#         minoration pour le calcul des majorations pour enfants '''

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

    #  def nb_points_enf(self, data, nombre_points):

#         P = reduce(getattr, self.param_name.split('.'), self.P)
#         P_long = reduce(getattr, self.param_name.split('.'), self.P_longit).maj_enf
#         nb_pac = data.info_ind['nb_pac'].copy()
#         nb_born = data.info_ind['nb_enf_all'].copy()
#         # 1- Calcul des points pour enfants à charge
#         taux_pac = P.maj_enf.pac.taux
#         points_pac = nombre_points.sum(axis=1) * taux_pac * nb_pac

#         # 2- Calcul des points pour enfants nés ou élevés
#         points_born = zeros(len(nb_pac))
#         nb_enf_maj = zeros(len(nb_pac))
#         for num_dispo in [0, 1]:
#             P_dispositif = getattr(P.maj_enf.born, 'dispositif' + str(num_dispo))
#             selected_dates = getattr(P_long.born, 'dispositif' + str(num_dispo)).dates
#             taux_dispositif = P_dispositif.taux
#             nb_enf_min = P_dispositif.nb_enf_min
#             nb_points_dates = multiply(nombre_points, selected_dates).sum(axis=1)
#             nb_points_enf = nb_points_dates * taux_dispositif * (nb_born >= nb_enf_min)
#             if hasattr(P_dispositif, 'taux_maj'):
#                 taux_maj = P_dispositif.taux_maj
#                 plaf_nb = P_dispositif.nb_enf_count
#                 nb_enf_maj = maximum(minimum(nb_born, plaf_nb) - nb_enf_min, 0)
#                 nb_points_enf += nb_enf_maj * taux_maj * nb_points_dates

#             points_born += nb_points_enf
#         # Retourne la situation la plus avantageuse
#         return maximum(points_born, points_pac)


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

        def formula(individu, period, parameters):
            categorie_salarie = individu("categorie_salarie", period)
            salaire_de_base = individu("regime_general_cnav_salaire_de_base", period)
            plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel * conversion_parametre_en_euros(period.start.year)
            employeur = parameters(period).regime_name.prelevements_sociaux.employeur.agirc
            salarie = parameters(period).regime_name.prelevements_sociaux.salarie.agirc

            agirc = employeur.copy()
            agirc.add_tax_scale(salarie)
            # # Ajout de la GMP dans le barème
            points_gmp = parameters(period).regime_name.gmp.garantie_minimale_points

            try:
                salaire_de_reference = parameters(period).regime_name.salaire_de_reference.salaire_reference_en_euros
                taux_appel = parameters(period).regime_name.prelevements_sociaux.taux_appel
            except ParameterNotFound:
                return individu.empty_array()

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
