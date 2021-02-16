"""Régime de base du secteur privé: régime général de la CNAV."""

from datetime import timedelta
import numpy as np

from openfisca_france_pension.regimes.regime import AbstractRegimeDeBase

from openfisca_core.periods import ETERNITY, MONTH, YEAR
from openfisca_core.variables import Variable
from openfisca_core.model_api import *

# Import the Entities specifically defined for this tax and benefit system
from openfisca_france_pension.entities import Household, Person


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


    class age_ouverture_des_droits(Variable):
        value_type = float
        entity = Person
        definition_period = ETERNITY
        label = "Age d'ouverture des droits"


    # def age_min_retirement(self):
    #     P = reduce(getattr, self.param_name.split('.'), self.P)
    #     return P.age_min


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


    # def trim_decote(self, data, trimesters_tot, trim_maj_enf_tot):
    #     ''' Détermination de la décote à appliquer aux pensions '''
    #     # TODO: Imagine a better way to include external sources
    #     P = reduce(getattr, self.param_name.split('.'), self.P)
    #     agem = data.info_ind['agem']
    #     duree_assurance_from_external = data.info_ind['duree_assurance_tot_RG']
    #     if P.decote.dispositif == 1:
    #         age_annulation = P.decote.age_null
    #         trim_decote = max(divide(age_annulation - agem, 3), 0)
    #     elif P.decote.dispositif == 2:
    #         if (duree_assurance_from_external == 0).all():
    #             trim_decote = nb_trim_decote(trimesters_tot, trim_maj_enf_tot, agem, P)
    #         else:
    #             trim_tot_ref = maximum(duree_assurance_from_external, trimesters_tot.sum(axis=1))
    #             trim_decote = nb_trim_decote_from_external(trim_tot_ref, agem, P)
    #     return trim_decote

    class age_annulation_decote(Variable):
        value_type = float
        entity = Person
        definition_period = ETERNITY
        label = "Age d'annulation de la décôte"

        # ''' Détermination de l'âge d'annularion de la décote '''
        # P = reduce(getattr, self.param_name.split('.'), self.P)
        # return P.decote.age_null

    class coefficient_de_proratisation(Variable):
        value_type = float
        entity = Person
        definition_period = ETERNITY
        label = "Coefficient de proratisation"

        # def _assurance_corrigee(trim_regime, agem):
        #     '''
        #     Deux types de corrections :
        #     - correction de 1948-1982
        #     - Détermination de la durée d'assurance corrigée introduite par la réforme Boulin
        #     (majoration quand départ à la retraite après 65 ans) à partir de 1983'''
        #     P = reduce(getattr, self.param_name.split('.'), self.P)

        #     if P.prorat.dispositif == 1:
        #         correction = (P.prorat.n_trim - trim_regime) / 2
        #         return trim_regime + correction
        #     elif P.prorat.dispositif == 2:
        #         age_taux_plein = P.decote.age_null
        #         trim_majo = divide(agem - age_taux_plein, 3) * (agem > age_taux_plein)
        #         elig_majo = (trim_regime < P.prorat.n_trim)
        #         correction = trim_regime * P.tx_maj * trim_majo * elig_majo
        #         return trim_regime + correction
        #     else:
        #         return trim_regime

        # P = reduce(getattr, self.param_name.split('.'), self.P)
        # trim_regime = trim_maj + nb_trimesters
        # if 'maj_other_RG' in info_ind.dtype.names:
        #     trim_maj_other = info_ind['maj_other_RG']
        #     trim_regime += trim_maj_other  # _assurance_corrigee(trim_regime, agem)
        # # disposition pour montée en charge de la loi Boulin (ne s'applique qu'entre 72 et 74) :
        # if P.prorat.application_plaf == 1:
        #     trim_regime = minimum(trim_regime, P.prorat.plaf)

        def formula_1983_04_01(individu, period, parameters):
            duree_de_proratisation = (
                parameters(period).regime_name.prorat_rg.duree_de_proratisation_pris_en_compte_proratisation_par_generation.ne_avant_1944
                )
            # TODO
            aad = 65
            coefficient_minoration_par_trimetre = parameters(period).regime_name.decote_rg.coefficient_minoration_par_trimestres_manquants.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants.ne_avant_01_01_1944
            age = individu('age_au_31_decembre', period)
            trimestres = individu('regime_name_trimestres', period)
            duree_assurance_corrigee = min_(
                duree_de_proratisation,
                trimestres * (
                    1
                    + 4 * max_(0, age - aad) * coefficient_minoration_par_trimetre
                    )
                )
            coefficient = min_(1, duree_assurance_corrigee / duree_de_proratisation)
            return coefficient

        def formula_1948(individu, period, parameters):
            trimestres = individu('regime_name_trimestres', period)
            duree_de_proratisation = (
                parameters(period).regime_name.prorat_rg.duree_de_proratisation_pris_en_compte_proratisation_par_generation.ne_avant_1944
                )
            duree_assurance_corrigee = (
                trimestres
                + (trimestres - duree_de_proratisation) / duree_de_proratisation
                )
            coefficient = min_(1, duree_assurance_corrigee / duree_de_proratisation)
            return coefficient

        def formula_1946(individu, period, parameters):
            duree_de_proratisation = (
                parameters(period).regime_name.prorat_rg.duree_de_proratisation_pris_en_compte_proratisation_par_generation.ne_avant_1944
                )
            trimestres = individu('regime_name_trimestres', period)
            coefficient = min_(1, trimestres / duree_de_proratisation)
            return coefficient


    class decote(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Décote"

        def formula_1983_04_01(individu, period, parameters):
            # TODO add as a parameter
            aad = 65
            coefficient_minoration_par_trimetre = parameters(period).regime_name.decote_rg.coefficient_minoration_par_trimestres_manquants.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants.ne_avant_01_01_1944
            duree_de_proratisation = (
                parameters(period).regime_name.prorat_rg.duree_de_proratisation_pris_en_compte_proratisation_par_generation.ne_avant_1944
                )
            liquidation_date = individu('regime_name_liquidation_date', period)
            age_en_mois_a_la_liquidation = (
                liquidation_date -
                individu('date_de_naissance', period)
                ).astype("timedelta64[M]").astype(int)
            trimestres_avant_add = np.trunc(
                    (aad * 12 - age_en_mois_a_la_liquidation) / 3
                    )
            trimestres = individu('regime_name_trimestres', period)
            decote = coefficient_minoration_par_trimetre * max_(
                0,
                min_(
                    trimestres - duree_de_proratisation,
                    trimestres_avant_add
                    )
                )
            return decote

        def formula_1945(individu, period, parameters):
            coefficient_minoration_par_trimestre = parameters(period).regime_name.decote_rg.coefficient_minoration_par_trimestres_manquants.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants.ne_avant_01_01_1944
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
            trimestres_avant_add = max_(
                0,
                np.trunc(
                    (aad * 12 - age_en_mois_a_la_liquidation) / 3
                    )
                )
            return coefficient_minoration_par_trimestre * trimestres_avant_add


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
