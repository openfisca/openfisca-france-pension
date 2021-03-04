"""Régime de base du secteur privé: régime général de la CNAV."""

import functools
import numpy as np


from openfisca_core.periods import ETERNITY, MONTH, YEAR
from openfisca_core.variables import Variable
from openfisca_core.model_api import *

# Import the Entities specifically defined for this tax and benefit system
from openfisca_france_pension.entities import Household, Person


from openfisca_france_pension.regimes.regime import AbstractRegimeDeBase
from openfisca_france_pension.tools import mean_over_k_nonzero_largest


class RegimePrive(AbstractRegimeDeBase):
    name = "Régime de base du secteur privé: régime général de la Cnav"
    variable_prefix = "regime_general_cnav"
    parameters_prefix = "secteur_prive.regime_general_cnav"

    class trimestres(Variable):
        value_type = int
        entity = Person
        definition_period = YEAR
        label = "Trimestres cotisés au régime général"

        # assert self.P_longit is not None, 'self.P_longit is None'
        # P_long = reduce(getattr, self.param_name.split('.'), self.P_longit)
        # salref = P_long.salref
        # plafond = 4  # nombre de trimestres dans l'année
        # ratio = divide(sal_cot, salref).astype(int)
        # return minimum(ratio, plafond)

    # def nb_trimesters(self, trimesters):
    #     return trimesters.sum(axis=1)

    # def trim_maj_ini(self, trim_maj_mda_ini):  # sert à comparer avec pensipp
    #     return trim_maj_mda_ini

    # def trim_maj(self, data, trim_maj_mda):
    #     if 'maj_other_RG' in data.info_ind.dtype.names:
    #         trim_maj = trim_maj_mda + data.info_ind.trim_other_RG
    #     else:
    #         trim_maj = trim_maj_mda
    #     return trim_maj


    # def salref(self, data, sal_regime):
    #     ''' SAM : Calcul du salaire annuel moyen de référence :
    #     notamment application du plafonnement à un PSS et de la revalorisation sur les prix
    #     des salaires portés aux comptes'''
    #     P = reduce(getattr, self.param_name_bis.split('.'), self.P)
    #     nb_best_years_to_take = P.nb_years
    #     plafond = self.P_longit.common.plaf_ss
    #     revalo = self.P_longit.prive.RG.revalo

    #     revalo = array(revalo)
    #     for i in range(1, len(revalo)):
    #         revalo[:i] *= revalo[i]
    #     sal_regime.translate_frequency(output_frequency='year', method='sum', inplace=True)
    #     years_sali = (sal_regime != 0).sum(axis=1)
    #     nb_best_years_to_take = array(nb_best_years_to_take)
    #     nb_best_years_to_take[years_sali < nb_best_years_to_take] = \
    #         years_sali[years_sali < nb_best_years_to_take]
    #     if plafond is not None:
    #         assert sal_regime.shape[1] == len(plafond)
    #         sal_regime = minimum(sal_regime, plafond)
    #     if revalo is not None:
    #         assert sal_regime.shape[1] == len(revalo)
    #         sal_regime = multiply(sal_regime, revalo)
    #     salref = sal_regime.best_dates_mean(nb_best_years_to_take)
    #     return salref.round(2)

    class salaire_de_reference(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Salaire annuel moyen de base dit salaire de référence"

        def formula_1994(individu, period, parameters):
            OFFSET = 10 # do not start working before 10 year
            date_de_naissance = individu('date_de_naissance', period)
            annee_de_naissance = int(individu('date_de_naissance', period).astype('datetime64[Y]').astype(int) + 1970)
            annees_de_naissance_distinctes = np.unique(annee_de_naissance)
            salaire_de_refererence = 0
            for _annee_de_naissance in sorted(annees_de_naissance_distinctes):
                n = int(
                    parameters(period).secteur_prive.regime_general_cnav.sam.nombre_annees_carriere_entrant_en_jeu_dans_determination_salaire_annuel_moyen[
                        date_de_naissance
                        ]
                    )
                mean_over_largest = functools.partial(mean_over_k_nonzero_largest, k = n)
                revalorisation = dict()
                revalorisation[period.start.year] = 1
                for annee_salaire in range(annee_de_naissance + OFFSET, period.start.year + 1):
                    # Pour un salaire 2020 tu le multiplies par le coefficient 01/01/2021 si tu veux sa valeur après le 1er janvier 21
                    revalorisation[annee_salaire] = (
                        np.prod(
                            np.array([
                                parameters(_annee).secteur_prive.regime_general_cnav.reval_s.coefficient
                                for _annee in range(annee_salaire + 1, period.start.year + 1)
                                ])
                            )
                        )
                salaire_de_refererence = where(
                    annee_de_naissance == _annee_de_naissance,
                    np.apply_along_axis(
                        mean_over_largest,
                        axis = 0,
                        arr = np.vstack([
                            min_(
                                individu('salaire_de_base', period = year),
                                parameters(year).prelevements_sociaux.pss.plafond_securite_sociale_annuel
                                )
                            * revalorisation[year]
                            for year in range(period.start.year, _annee_de_naissance + OFFSET, -1)
                            ]),
                        ),
                    salaire_de_refererence,
                    )
            return salaire_de_refererence

        def formula_1972(individu, period, parameters):
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
        definition_period = ETERNITY
        label = "Coefficient de proratisation"

        def formula_2011_07_01(individu, period, parameters):
            date_de_naissance = individu('date_de_naissance', period)
            duree_de_proratisation = (
                parameters(period).regime_name.prorat.nombre_trimestres_maximal_pris_en_compte_proratisation_par_generation[date_de_naissance]
                )
            aad_annee = parameters(period).regime_name.aad.age_annulation_decote_en_fonction_date_naissance[date_de_naissance].annee
            aad_mois = parameters(period).regime_name.aad.age_annulation_decote_en_fonction_date_naissance[date_de_naissance].mois
            coefficient_minoration_par_trimestre = parameters(period).regime_name.decote.coefficient_minoration_par_trimestres_manquants.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants[date_de_naissance]
            liquidation_date = individu('regime_name_liquidation_date', period)
            age_en_mois_a_la_liquidation = (
                liquidation_date -
                individu('date_de_naissance', period)
                ).astype("timedelta64[M]").astype(int)
            # TODO definition exacte trimestres ?
            trimestres_apres_add = max_(
                0,
                np.trunc(
                    (age_en_mois_a_la_liquidation - aad_annee * 12 - aad_mois) / 3
                    )
                )
            age = individu('age_au_31_decembre', period)
            trimestres = individu('regime_name_trimestres', period)
            duree_assurance_corrigee = min_(
                duree_de_proratisation,
                trimestres * (
                    1
                    + trimestres_apres_add * coefficient_minoration_par_trimestre
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
                liquidation_date -
                individu('date_de_naissance', period)
                ).astype("timedelta64[M]").astype(int)
            # TODO definition exacte trimestres ?
            trimestres_apres_add = max_(
                0,
                np.trunc(
                    (age_en_mois_a_la_liquidation - aad * 12) / 3
                    )
                )
            age = individu('age_au_31_decembre', period)
            trimestres = individu('regime_name_trimestres', period)
            duree_assurance_corrigee = min_(
                duree_de_proratisation,
                trimestres * (
                    1
                    + trimestres_apres_add * coefficient_minoration_par_trimestre
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


    class decote(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Décote"

        def formula_2011_07_01(individu, period, parameters):
            date_de_naissance = individu('date_de_naissance', period)
            aad_annee = parameters(period).regime_name.aad.age_annulation_decote_en_fonction_date_naissance[date_de_naissance].annee
            aad_mois = parameters(period).regime_name.aad.age_annulation_decote_en_fonction_date_naissance[date_de_naissance].mois
            coefficient_minoration_par_trimestre = parameters(period).regime_name.decote.coefficient_minoration_par_trimestres_manquants.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants[date_de_naissance]
            trimestres_cibles_taux_plein = (
                parameters(period).regime_name.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]
                )
            age_en_mois_a_la_liquidation = (
                individu('regime_name_liquidation_date', period)
                - individu('date_de_naissance', period)
                ).astype("timedelta64[M]").astype(int)
            trimestres_apres_add = np.trunc(
                (aad_annee * 12 + aad_mois - age_en_mois_a_la_liquidation) / 3
                )
            trimestres = individu('regime_name_trimestres', period)
            decote = coefficient_minoration_par_trimestre * max_(
                0,
                min_(
                    trimestres_cibles_taux_plein - trimestres,
                    trimestres_apres_add
                    )
                )
            return decote

        def formula_1983_04_01(individu, period, parameters):
            # TODO add as a parameter
            aad = 65
            date_de_naissance = individu('date_de_naissance', period)
            coefficient_minoration_par_trimestre = parameters(period).regime_name.decote.coefficient_minoration_par_trimestres_manquants.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants[date_de_naissance]
            trimestres_cibles_taux_plein = (
                parameters(period).regime_name.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]
                )
            liquidation_date = individu('regime_name_liquidation_date', period)
            age_en_mois_a_la_liquidation = (
                liquidation_date -
                individu('date_de_naissance', period)
                ).astype("timedelta64[M]").astype(int)
            trimestres_apres_add = np.trunc(
                    (aad * 12 - age_en_mois_a_la_liquidation) / 3
                    )
            trimestres = individu('regime_name_trimestres', period)
            decote = coefficient_minoration_par_trimestre * max_(
                0,
                min_(
                    trimestres_cibles_taux_plein - trimestres,
                    trimestres_apres_add
                    )
                )
            return decote

        def formula_1945(individu, period, parameters):
            coefficient_minoration_par_trimestre = parameters(period).regime_name.decote.coefficient_minoration_par_trimestres_manquants.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants.ne_avant_1944_01_01
            # TODO extract age by generation
            aad = 65
            # (
            #     parameters(period).regime_name.age_annulation_decote_en_fonction_date_naissance.ne_avant_1951_07_01
            #     )
            liquidation_date = individu('regime_name_liquidation_date', period)
            age_en_mois_a_la_liquidation = (
                liquidation_date -
                individu('date_de_naissance', period)
                ).astype("timedelta64[M]").astype(int)
            # TODO definition exacte trimestres ?
            trimestres_apres_add = max_(
                0,
                np.trunc(
                    (aad * 12 - age_en_mois_a_la_liquidation) / 3
                    )
                )
            return coefficient_minoration_par_trimestre * trimestres_apres_add


    class liquidation_date(Variable):
        value_type = date
        entity = Person
        definition_period = ETERNITY
        label = "Date de liquidation"


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
                liquidation_date -
                individu('date_de_naissance', period)
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
            taux_surcote_par_trimestre_moins_de_4_trimestres = (
                parameters(period).regime_name.surcote.taux_surcote_par_trimestre_cotise_selon_date_cotisation.apres_01_01_2004['moins_de_4_trimestres']
                )
            taux_surcote_par_trimestre_plus_de_5_trimestres = (
                parameters(period).regime_name.surcote.taux_surcote_par_trimestre_cotise_selon_date_cotisation.apres_01_01_2004['plus_de_5_trimestres']
                )
            taux_surcote_par_trimestre_partir_65_ans = (
                parameters(period).regime_name.surcote.taux_surcote_par_trimestre_cotise_selon_date_cotisation.apres_01_01_2004['partir_65_ans']
                )

            date_de_naissance = individu('date_de_naissance', period)
            liquidation_date = individu('regime_name_liquidation_date', period)
            age_en_mois_a_la_liquidation = (
                liquidation_date -
                individu('date_de_naissance', period)
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
                liquidation_date -
                individu('date_de_naissance', period)
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
                liquidation_date -
                individu('date_de_naissance', period)
                ).astype("timedelta64[M]").astype(int)
            # TODO definition exacte trimestres ?
            trimestres_apres_add = max_(
                0,
                np.trunc(
                    (age_en_mois_a_la_liquidation - aad * 12) / 3
                    )
                )
            return coefficient_majoration_par_trimestre * trimestres_apres_add

        # def formulat(individu, period, parmaters):
        #     pass
    # def surcote(self, data, trimesters, trimesters_tot, date_start_surcote):
    #     ''' Détermination de la surcote à appliquer aux pensions.'''
    #     P = reduce(getattr, self.param_name.split('.'), self.P)
    #     P_long = reduce(getattr, self.param_name.split('.'), self.P_longit)
    #     # dispositif de type 0
    #     n_trim = array(P.plein.n_trim, dtype=float)
    #     trim_tot = trimesters_tot.sum(axis=1)
    #     surcote = P.surcote.dispositif0.taux * (trim_tot - n_trim) * (trim_tot > n_trim)
    #     # Note surcote = 0 après 1983
    #     # dispositif de type 1
    #     agem = data.info_ind['agem']
    #     datesim = self.dateleg.liam
    #     if P.surcote.dispositif1.taux > 0:
    #         trick = P.surcote.dispositif1.date_trick
    #         trick = str(int(trick))
    #         selected_dates = getattr(P_long.surcote.dispositif1, 'dates' + trick)
    #         if sum(selected_dates) > 0:
    #             surcote += P.surcote.dispositif1.taux * \
    #                 nb_trim_surcote(trimesters, selected_dates,
    #                                 date_start_surcote)

    #     # dispositif de type 2
    #     P2 = P.surcote.dispositif2
    #     if P2.taux0 > 0:
    #         selected_dates = P_long.surcote.dispositif2.dates
    #         basic_trim = nb_trim_surcote(trimesters, selected_dates,
    #                                      date_start_surcote)
    #         age_by_year = array([array(agem) - 12 * i for i in reversed(range(trimesters.shape[1]))])
    #         nb_years_surcote_age = greater(age_by_year, P2.age_majoration * 12).T.sum(axis=1)
    #         start_surcote_age = [datesim - nb_year * 100 if nb_year > 0 else 2100 * 100 + 1
    #                              for nb_year in nb_years_surcote_age]
    #         maj_age_trim = nb_trim_surcote(trimesters, selected_dates,
    #                                        start_surcote_age)
    #         basic_trim = basic_trim - maj_age_trim
    #         trim_with_majo = (basic_trim - P2.trim_majoration) * \
    #                          ((basic_trim - P2.trim_majoration) >= 0)
    #         basic_trim = basic_trim - trim_with_majo
    #         surcote += P2.taux0 * basic_trim + \
    #             P2.taux_maj_trim * trim_with_majo + \
    #             P2.taux_maj_age * maj_age_trim
    #     return surcote

    # def trimestres_excess_taux_plein(self, data, trimesters, trimesters_tot):
    #     ''' Détermination nb de trimestres au delà du taux plein.'''
    #     P = reduce(getattr, self.param_name.split('.'), self.P)
    #     # dispositif de type 0
    #     n_trim = array(P.plein.n_trim, dtype=float)
    #     trim_tot = trimesters_tot.sum(axis=1)
    #     return (trim_tot - n_trim) * (trim_tot > n_trim)

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

        # def formula(indiivdu, period, paramaters):
        #     pass

        # ''' plafonnement à 50% du PSS
        # TODO: gérer les plus de 65 ans au 1er janvier 1983'''
        # PSS = self.P.common.plaf_ss
        # P = reduce(getattr, self.param_name.split('.'), self.P)
        # taux_plein = P.plein.taux
        # taux_PSS = P.plafond
        # pension_surcote_RG = taux_plein * salref * coeff_proratisation * surcote
        # return minimum(pension_brute - pension_surcote_RG, taux_PSS * PSS) + \
            # pension_surcote_RG
