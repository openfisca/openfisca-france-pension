"""Régime de base du secteur privé: régime général de la CNAV."""

import functools

import numpy as np

from openfisca_core.model_api import *
from openfisca_core.parameters import ParameterNotFound
from openfisca_core.periods import YEAR
from openfisca_core.variables import Variable

from openfisca_france_pension.entities import Person
from openfisca_france_pension.regimes.regime import AbstractRegimeDeBase
from openfisca_france_pension.tools import mean_over_k_nonzero_largest
from openfisca_france_pension.variables.hors_regime import TypesCategorieSalarie


def compute_salaire_de_reference(mean_over_largest, arr, salaire_de_refererence, filter):
    salaire_de_refererence[filter] = np.apply_along_axis(
        mean_over_largest,
        axis = 0,
        arr = arr,
        )


def make_mean_over_largest(k):
    def mean_over_largest(vector):
        return mean_over_k_nonzero_largest(vector, k = k)

    return mean_over_largest


class RegimeGeneralCnav(AbstractRegimeDeBase):
    name = "Régime de base du secteur privé: régime général de la Cnav"
    variable_prefix = "regime_general_cnav"
    parameters_prefix = "secteur_prive.regime_general_cnav"

    class trimestres(Variable):
        value_type = int
        entity = Person
        definition_period = YEAR
        label = "Trimestres validés au régime général"

        def formula(individu, period, parameters):
            salaire_de_base = individu("salaire_de_base", period)
            try:
                salaire_validant_un_trimestre = parameters(period).regime_name.salval.salaire_validant_trimestre.metropole
            except ParameterNotFound:
                import openfisca_core.periods as periods
                salaire_validant_un_trimestre = parameters(periods.period(1930)).regime_name.salval.salaire_validant_trimestre.metropole
            trimestres_valides_avant_cette_annee = individu("regime_name_trimestres", period.last_year)
            trimestres_valides_dans_l_annee = min_(
                (salaire_de_base / salaire_validant_un_trimestre).astype(int),
                4
                )
            return trimestres_valides_avant_cette_annee + trimestres_valides_dans_l_annee

    # def trim_maj_ini(self, trim_maj_mda_ini):  # sert à comparer avec pensipp
    #     return trim_maj_mda_ini

    # def trim_maj(self, data, trim_maj_mda):
    #     if 'maj_other_RG' in data.info_ind.dtype.names:
    #         trim_maj = trim_maj_mda + data.info_ind.trim_other_RG
    #     else:
    #         trim_maj = trim_maj_mda
    #     return trim_maj

    class salaire_de_reference(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Salaire annuel moyen de base dit salaire de référence"

        def formula_1994(individu, period, parameters):
            OFFSET = 10  # do not start working before 10 year
            liquidation_date = individu('regime_name_liquidation_date', period)
            annee_de_naissance = (
                individu('date_de_naissance', period).astype('datetime64[Y]').astype(int) + 1970
                )
            annees_de_naissance_distinctes = np.unique(
                annee_de_naissance[liquidation_date >= np.datetime64(period.start)]
                )
            salaire_de_reference = individu.empty_array()
            for _annee_de_naissance in sorted(annees_de_naissance_distinctes):
                if _annee_de_naissance + OFFSET >= period.start.year:
                    break
                k = int(
                    parameters(period).secteur_prive.regime_general_cnav.sam.nombre_annees_carriere_entrant_en_jeu_dans_determination_salaire_annuel_moyen[
                        np.array(str(_annee_de_naissance), dtype="datetime64[Y]")
                        ]
                    )
                mean_over_largest = make_mean_over_largest(k)
                revalorisation = dict()
                revalorisation[period.start.year] = 1
                for annee_salaire in range(_annee_de_naissance + OFFSET, period.start.year + 1):
                    # Pour un salaire 2020 tu le multiplies par le coefficient 01/01/2021 si tu veux sa valeur après le 1er janvier 21
                    revalorisation[annee_salaire] = (
                        np.prod(
                            np.array([
                                parameters(_annee).secteur_prive.regime_general_cnav.reval_s.coefficient
                                for _annee in range(annee_salaire + 1, period.start.year + 1)
                                ])
                            )
                        )
                # print(period.start.year, _annee_de_naissance + OFFSET)
                filter = annee_de_naissance == _annee_de_naissance,
                # TODO try boolean indexing instead of where to lighten the burden on vstack and apply along_axis ?
                arr = np.vstack([
                    min_(
                        individu('salaire_de_base', period = year)[filter],
                        parameters(year).prelevements_sociaux.pss.plafond_securite_sociale_annuel
                        )
                    * revalorisation[year]
                    for year in range(period.start.year, _annee_de_naissance + OFFSET, -1)
                    ])
                compute_salaire_de_reference(mean_over_largest, arr, salaire_de_reference, filter)

            return salaire_de_reference

        def formula_1972(individu, period, parameters):
            # TODO test and adapt like 1994 formula
            n = parameters(period).regime_name.sam.nombre_annees_carriere_entrant_en_jeu_dans_determination_salaire_annuel_moyen.ne_avant_1934_01_01
            mean_over_largest = functools.partial(mean_over_k_nonzero_largest, k = n)
            annee_initiale = (individu('date_de_naissance', period).astype('datetime64[Y]').astype(int) + 1970).min()
            salaire_de_refererence = np.apply_along_axis(
                mean_over_largest,
                axis = 0,
                arr = np.vstack([
                    min_(
                        individu('salaire_de_base', period = year),
                        parameters(year).prelevements_sociaux.pss.plafond_securite_sociale_annuel
                        )
                    for year in range(period.start.year, annee_initiale, -1)
                    ]),
                )
            return salaire_de_refererence

    class coefficient_de_proratisation(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Coefficient de proratisation"

        def formula_2011_07_01(individu, period, parameters):
            date_de_naissance = individu('date_de_naissance', period)
            duree_de_proratisation = (
                parameters(period).regime_name.prorat.nombre_trimestres_maximal_pris_en_compte_proratisation_par_generation[date_de_naissance]
                )
            aad = parameters(period).regime_name.aad.age_annulation_decote_en_fonction_date_naissance[date_de_naissance]
            coefficient_minoration_par_trimestre = parameters(period).regime_name.decote.coefficient_minoration_par_trimestres_manquants.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants[date_de_naissance]
            liquidation_date = individu('regime_name_liquidation_date', period)
            age_en_mois_a_la_liquidation = (
                liquidation_date
                - individu('date_de_naissance', period)
                ).astype("timedelta64[M]").astype(int)
            # TODO definition exacte trimestres ?
            trimestres_apres_aad = max_(
                0,
                np.trunc(
                    (age_en_mois_a_la_liquidation - aad.annee * 12 - aad.mois) / 3
                    )
                )
            trimestres = individu('regime_name_trimestres', period)
            duree_assurance_corrigee = min_(
                duree_de_proratisation,
                trimestres * (
                    1
                    + trimestres_apres_aad * coefficient_minoration_par_trimestre
                    )
                )
            coefficient = min_(1, duree_assurance_corrigee / duree_de_proratisation)
            return coefficient

        def formula_1983_04_01(individu, period, parameters):
            date_de_naissance = individu('date_de_naissance', period)
            duree_de_proratisation = (
                parameters(period).regime_name.prorat.nombre_trimestres_maximal_pris_en_compte_proratisation_par_generation[date_de_naissance]
                )
            aad = parameters(period).regime_name.aad.age_annulation_decote_en_fonction_date_naissance.ne_avant_1951_07_01.annee
            coefficient_minoration_par_trimestre = parameters(period).regime_name.decote.coefficient_minoration_par_trimestres_manquants.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants[date_de_naissance]
            liquidation_date = individu('regime_name_liquidation_date', period)
            age_en_mois_a_la_liquidation = (
                liquidation_date
                - individu('date_de_naissance', period)
                ).astype("timedelta64[M]").astype(int)
            # TODO definition exacte trimestres ?
            trimestres_apres_aad = max_(
                0,
                np.trunc(
                    (age_en_mois_a_la_liquidation - aad * 12) / 3
                    )
                )
            trimestres = individu('regime_name_trimestres', period)
            duree_assurance_corrigee = min_(
                duree_de_proratisation,
                trimestres * (
                    1
                    + trimestres_apres_aad * coefficient_minoration_par_trimestre
                    )
                )
            coefficient = min_(1, duree_assurance_corrigee / duree_de_proratisation)
            return coefficient

        def formula_1948(individu, period, parameters):
            trimestres = individu('regime_name_trimestres', period)
            duree_de_proratisation = (
                parameters(period).regime_name.prorat.nombre_trimestres_maximal_pris_en_compte_proratisation_par_generation.ne_avant_1944_01_01
                )
            duree_assurance_corrigee = (
                trimestres
                + (duree_de_proratisation - trimestres) / 2
                )
            coefficient = min_(1, duree_assurance_corrigee / duree_de_proratisation)
            return coefficient

        def formula_1946(individu, period, parameters):
            duree_de_proratisation = (
                parameters(period).regime_name.prorat.nombre_trimestres_maximal_pris_en_compte_proratisation_par_generation.ne_avant_1944_01_01
                )
            trimestres = individu('regime_name_trimestres', period)
            coefficient = min_(1, trimestres / duree_de_proratisation)
            return coefficient

    class cotisation_employeur(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Cotisation employeur"

        def formula(individu, period, parameters):
            categorie_salarie = individu("categorie_salarie", period)
            salaire_de_base = individu("salaire_de_base", period)
            plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel
            employeur = parameters(period).regime_name.prelevements_sociaux.employeur
            salarie_concerne = (
                (categorie_salarie == TypesCategorieSalarie.prive_non_cadre)
                + (categorie_salarie == TypesCategorieSalarie.prive_cadre)
                + (categorie_salarie == TypesCategorieSalarie.public_non_titulaire)
                )
            return salarie_concerne * (
                employeur.vieillesse_deplafonnee.calc(salaire_de_base, factor = plafond_securite_sociale)
                + employeur.vieillesse_plafonnee.calc(salaire_de_base, factor = plafond_securite_sociale)
                )

    class cotisation_salarie(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Cotisation salarié"

        def formula(individu, period, parameters):
            categorie_salarie = individu("categorie_salarie", period)
            salaire_de_base = individu("salaire_de_base", period)
            plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel
            salarie = parameters(period).regime_name.prelevements_sociaux.salarie
            salarie_concerne = (
                (categorie_salarie == TypesCategorieSalarie.prive_non_cadre)
                + (categorie_salarie == TypesCategorieSalarie.prive_cadre)
                + (categorie_salarie == TypesCategorieSalarie.public_non_titulaire)
                )
            return salarie_concerne * (
                salarie.vieillesse_deplafonnee.calc(salaire_de_base, factor = plafond_securite_sociale)
                + salarie.vieillesse_plafonnee.calc(salaire_de_base, factor = plafond_securite_sociale)
                )

    class decote(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Décote"

        def formula_1983_04_01(individu, period, parameters):
            date_de_naissance = individu('date_de_naissance', period)
            coefficient_minoration_par_trimestre = parameters(period).regime_name.decote.coefficient_minoration_par_trimestres_manquants.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants[date_de_naissance]
            decote_trimestres = individu('regime_name_decote_trimestres', period)
            decote = coefficient_minoration_par_trimestre * decote_trimestres
            return decote

        def formula_1945(individu, period, parameters):
            decote_trimestres = individu('regime_name_decote_trimestres', period)
            coefficient_minoration_par_trimestre = parameters(period).regime_name.decote.coefficient_minoration_par_trimestres_manquants.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants.ne_avant_1944_01_01
            return coefficient_minoration_par_trimestre * decote_trimestres

    class decote_trimestres(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Trimestres de décote"

        def formula_2011_07_01(individu, period, parameters):
            date_de_naissance = individu('date_de_naissance', period)
            aad_annee = parameters(period).regime_name.aad.age_annulation_decote_en_fonction_date_naissance[date_de_naissance].annee
            aad_mois = parameters(period).regime_name.aad.age_annulation_decote_en_fonction_date_naissance[date_de_naissance].mois
            trimestres_cibles_taux_plein = (
                parameters(period).regime_name.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]
                )
            age_en_mois_a_la_liquidation = (
                individu('regime_name_liquidation_date', period)
                - individu('date_de_naissance', period)
                ).astype("timedelta64[M]").astype(int)
            trimestres_avant_aad = np.trunc(
                (aad_annee * 12 + aad_mois - age_en_mois_a_la_liquidation) / 3
                )
            trimestres = individu('regime_name_trimestres', period)
            decote_trimestres = max_(
                0,
                min_(
                    trimestres_cibles_taux_plein - trimestres,
                    trimestres_avant_aad
                    )
                )
            return decote_trimestres

        def formula_1983_04_01(individu, period, parameters):
            # TODO Age annulation de la décôte (aad) as a parameter
            aad = 65
            date_de_naissance = individu('date_de_naissance', period)
            trimestres_cibles_taux_plein = (
                parameters(period).regime_name.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]
                )
            age_en_mois_a_la_liquidation = (
                individu('regime_name_liquidation_date', period)
                - individu('date_de_naissance', period)
                ).astype("timedelta64[M]").astype(int)
            trimestres_avant_aad = np.trunc(
                (aad * 12 - age_en_mois_a_la_liquidation) / 3
                )
            trimestres = individu('regime_name_trimestres', period)
            decote_trimestres = max_(
                0,
                min_(
                    trimestres_cibles_taux_plein - trimestres,
                    trimestres_avant_aad
                    )
                )
            return decote_trimestres

        def formula_1945(individu, period, parameters):
            # TODO extract age by generation
            aad = 65
            # (
            #     parameters(period).regime_name.age_annulation_decote_en_fonction_date_naissance.ne_avant_1951_07_01
            #     )
            liquidation_date = individu('regime_name_liquidation_date', period)
            age_en_mois_a_la_liquidation = (
                liquidation_date
                - individu('date_de_naissance', period)
                ).astype("timedelta64[M]").astype(int)
            # TODO definition exacte trimestres ?
            decote_trimestres = max_(
                0,
                np.trunc(
                    (aad * 12 - age_en_mois_a_la_liquidation) / 3
                    )
                )
            return decote_trimestres

    class surcote(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Surcote"

        def formula_2009_04_01(individu, period, parameters):
            aod = 65
            taux_surcote = (
                parameters(period).regime_name.surcote.taux_surcote_par_trimestre_cotise_selon_date_cotisation.apres_01_01_2004['partir_65_ans']
                )
            date_de_naissance = individu('date_de_naissance', period)
            liquidation_date = individu('regime_name_liquidation_date', period)
            age_en_mois_a_la_liquidation = (
                liquidation_date
                - individu('date_de_naissance', period)
                ).astype("timedelta64[M]").astype(int)
            # TODO definition exacte trimestres ?
            trimestres_apres_aod = max_(
                0,
                np.trunc(
                    (age_en_mois_a_la_liquidation - aod * 12) / 3
                    )
                )
            distance_a_2004_en_trimestres = max_(
                0,
                np.trunc(
                    (liquidation_date - np.datetime64("2004-01-01")).astype("timedelta64[M]").astype(int)
                    / 3
                    )
                )
            trimestres = individu('regime_name_trimestres', period)
            trimestres_cibles_taux_plein = (
                parameters(period).regime_name.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]
                )
            trimestres_surcote = max_(
                0,
                min_(
                    min_(
                        distance_a_2004_en_trimestres,
                        trimestres_apres_aod
                        ),
                    trimestres - trimestres_cibles_taux_plein
                    )
                )
            return taux_surcote * trimestres_surcote

        def formula_2007_01_01(individu, period, parameters):
            aod = 65
            taux_surcote_par_trimestre = parameters(period).regime_name.surcote.taux_surcote_par_trimestre_cotise_selon_date_cotisation.apres_01_01_2004
            taux_surcote_par_trimestre_moins_de_4_trimestres = taux_surcote_par_trimestre['moins_de_4_trimestres']
            taux_surcote_par_trimestre_plus_de_5_trimestres = taux_surcote_par_trimestre['plus_de_5_trimestres']
            taux_surcote_par_trimestre_partir_65_ans = taux_surcote_par_trimestre['partir_65_ans']

            date_de_naissance = individu('date_de_naissance', period)
            liquidation_date = individu('regime_name_liquidation_date', period)
            age_en_mois_a_la_liquidation = (
                liquidation_date
                - individu('date_de_naissance', period)
                ).astype("timedelta64[M]").astype(int)
            # TODO definition exacte trimestres ?
            trimestres_apres_aod = max_(
                0,
                np.trunc(
                    (age_en_mois_a_la_liquidation - aod * 12) / 3
                    )
                )
            distance_a_2004_en_trimestres = max_(
                0,
                np.trunc(
                    (liquidation_date - np.datetime64("2004-01-01")).astype("timedelta64[M]").astype(int)
                    / 3
                    )
                )
            trimestres = individu('regime_name_trimestres', period)
            trimestres_cibles_taux_plein = (
                parameters(period).regime_name.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]
                )
            trimestres_surcote = max_(
                0,
                min_(
                    min_(
                        distance_a_2004_en_trimestres,
                        trimestres_apres_aod
                        ),
                    trimestres - trimestres_cibles_taux_plein
                    )
                )
            trimestres_surcote_au_dela_de_65_ans = min_(
                trimestres_surcote,
                max_(
                    0,
                    np.trunc(
                            (age_en_mois_a_la_liquidation - 65 * 12) / 3
                        )
                    )
                )
            trimestres_surcote_en_deca_de_65_ans = max_(
                0,
                (
                    trimestres_surcote
                    - trimestres_surcote_au_dela_de_65_ans
                    )
                )
            surcote = (
                taux_surcote_par_trimestre_moins_de_4_trimestres * min_(4, trimestres_surcote_en_deca_de_65_ans)
                + taux_surcote_par_trimestre_plus_de_5_trimestres * max_(0, trimestres_surcote_en_deca_de_65_ans - 4)
                + taux_surcote_par_trimestre_partir_65_ans * trimestres_surcote_au_dela_de_65_ans
                )
            return surcote

        def formula_2004_01_01(individu, period, parameters):
            aod = 65
            taux_surcote_par_trimestre_moins_de_4_trimestres = (
                parameters(period).regime_name.surcote.taux_surcote_par_trimestre_cotise_selon_date_cotisation.apres_01_01_2004['moins_de_4_trimestres']
                )
            date_de_naissance = individu('date_de_naissance', period)
            liquidation_date = individu('regime_name_liquidation_date', period)
            age_en_mois_a_la_liquidation = (
                liquidation_date
                - individu('date_de_naissance', period)
                ).astype("timedelta64[M]").astype(int)
            # TODO definition exacte trimestres ?
            trimestres_apres_aod = max_(
                0,
                np.trunc(
                    (age_en_mois_a_la_liquidation - aod * 12) / 3
                    )
                )
            distance_a_2004_en_trimestres = max_(
                0,
                np.trunc(
                    (liquidation_date - np.datetime64("2004-01-01")).astype("timedelta64[M]").astype(int)
                    / 3
                    )
                )
            trimestres = individu('regime_name_trimestres', period)
            trimestres_cibles_taux_plein = (
                parameters(period).regime_name.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]
                )
            trimestres_surcote = max_(
                0,
                min_(
                    min_(
                        distance_a_2004_en_trimestres,
                        trimestres_apres_aod
                        ),
                    trimestres - trimestres_cibles_taux_plein
                    )
                )
            return taux_surcote_par_trimestre_moins_de_4_trimestres * trimestres_surcote

        def formula_1983_04_01(individu, period):
            return individu.empty_array()

        def formula_1945(individu, period):
            # TODO absent des paramètres
            coefficient_majoration_par_trimestre = .1 / 4
            aad = 65
            liquidation_date = individu('regime_name_liquidation_date', period)
            age_en_mois_a_la_liquidation = (
                liquidation_date
                - individu('date_de_naissance', period)
                ).astype("timedelta64[M]").astype(int)
            # TODO definition exacte trimestres ?
            trimestres_apres_aad = max_(
                0,
                np.trunc(
                    (age_en_mois_a_la_liquidation - aad * 12) / 3
                    )
                )
            return coefficient_majoration_par_trimestre * trimestres_apres_aad

    class pension_minimale(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Pension minimale"

        # def formula(indiivdu, period, paramaters):
        #     pass

        # ''' MICO du régime général : allocation différentielle
        # RQ :
        # 1) ASPA et minimum vieillesse sont gérés par OF
        # 2) Le minimum contributif est calculé sans prendre ne compte les majoration pour enfants à charge
        # et la surcote (rajouté ensuite)

        # Il est attribué quels que soient les revenus dont dispose le retraité en plus de ses pensions :
        # loyers, revenus du capital, activité professionnelle...
        # + mécanisme de répartition si cotisations à plusieurs régimes
        # TODO: coder toutes les évolutions et rebondissements 2004/2008'''
        # P = reduce(getattr, self.param_name.split('.'), self.P)
        # # pension_RG, pension, trim_RG, trim_cot, trim
        # trim_regime = nb_trimesters + trim_maj
        # coeff = minimum(1, divide(trim_regime, P.prorat.n_trim))
        # if P.mico.dispositif == 0:
        #     # Avant le 1er janvier 1983, comparé à l'AVTS
        #     min_pension = self.P.common.avts
        #     return maximum(min_pension - pension_brute, 0) * coeff
        # elif P.mico.dispositif == 1:
        #     # TODO: Voir comment gérer la limite de cumul relativement
        #     # complexe (Doc n°5 du COR)
        #     mico = P.mico.entier
        #     return maximum(mico - pension_brute, 0) * coeff
        # elif P.mico.dispositif == 2:
        #     # A partir du 1er janvier 2004 les périodes cotisées interviennent
        #     # (+ dispositif transitoire de 2004)
        #     nb_trim = P.prorat.n_trim
        #     trim_regime = nb_trimesters  # + sum(trim_maj)
        #     mico_entier = P.mico.entier * minimum(divide(trim_regime, nb_trim), 1)
        #     maj = (P.mico.entier_maj - P.mico.entier) * divide(trimesters_tot.sum(axis=1), nb_trim)
        #     mico = mico_entier + maj * (trimesters_tot.sum(axis=1) >= P.mico.trim_min)
        #     return (mico - pension_brute) * (mico > pension_brute) * (pension_brute > 0)

    class pension_maximale(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Pension maximale"

        def formula(individu, period, parameters):

            # TODO: gérer les plus de 65 ans au 1er janvier 1983'''
            plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel
            taux_plein = parameters(period).regime_name.taux_plein.taux_plein
            pension_plafond_hors_sucote = taux_plein * plafond_securite_sociale
            pension_brute = individu('regime_name_pension_brute', period)
            taux_de_liquidation = individu('regime_name_taux_de_liquidation', period)
            surcote = individu('regime_name_surcote', period)
            pension_surcote = (pension_brute / taux_de_liquidation) * taux_plein * surcote
            return min_(pension_brute - pension_surcote, pension_plafond_hors_sucote) + pension_surcote
