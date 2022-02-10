"""Régime de base de la fonction publique."""

import numpy as np

from openfisca_core.model_api import *

from openfisca_france_pension.entities import Person
from openfisca_france_pension.regimes.regime import AbstractRegimeDeBase


class RegimeFonctionPublique(AbstractRegimeDeBase):
    name = "Régime de base de la fonction publique"
    variable_prefix = "fonction_publique"
    parameters_prefix = "secteur_public"

    class duree_assurance(Variable):
        value_type = int
        entity = Person
        definition_period = YEAR
        label = "Durée d'assurance (trimestres validés dans la fonction publique)"

    class duree_assurance_cotisee(Variable):
        value_type = int
        entity = Person
        definition_period = YEAR
        label = "Durée d'assurance (trimestres cotisés dans la fonction publique)"

    # Utiliser la duréee de service

    # def FP_to_RG(self, data, trim_cot_by_year, sal_cot):
    #     ''' Détermine les personnes à rapporter au régime général'''
    #     P = reduce(getattr, self.param_name.split('.'), self.P)
    #     # N_min donné en mois
    #     trim_cot = trim_cot_by_year.sum(axis=1)
    #     last_fp = data.workstate.last_time_in(self.code_regime)
    #     to_RG_actif = (3 * trim_cot < P.actif.N_min) * (last_fp == self.code_actif)
    #     to_RG_sedentaire = (3 * trim_cot < P.sedentaire.N_min) * (last_fp == self.code_sedentaire)
    #     return (to_RG_actif + to_RG_sedentaire)

    # def sal_FP_to_RG(self, sal_cot, FP_to_RG):
    #     sal = sal_cot.copy()
    #     sal[~FP_to_RG] = 0
    #     return sal

    # def trim_FP_to_RG(self, trim_cot_by_year, FP_to_RG):
    #     trim = trim_cot_by_year.copy()
    #     trim[~FP_to_RG] = 0
    #     return trim

    # def wages(self, sal_cot, FP_to_RG):
    #     sal = sal_cot.copy()
    #     sal[FP_to_RG] = 0
    #     return sal

    # def trimesters(self, trim_cot_by_year, FP_to_RG):
    #     trim = trim_cot_by_year.copy()
    #     trim[FP_to_RG] = 0
    #     return trim

    # def nb_trimesters(self, trimesters):
    #     return trimesters.sum(axis=1)

    # def trim_maj_mda_ini(self, info_ind, nb_trimesters):
        # P_mda = self.P.public.fp.mda
        # return trim_mda(info_ind, self.name, P_mda) * (nb_trimesters > 0)

    # def trim_maj_mda_RG(self, regime='RG'):
    #     pass

    # def trim_maj_mda_RSI(self, regime='RSI'):
    #     pass

    # def trim_maj_mda(self, trim_maj_mda_ini, nb_trimesters, trim_maj_mda_RG,
    #                  trim_maj_mda_RSI):
    #     ''' La Mda (attribuée par tous les régimes de base), ne peut être
    #     accordé par plus d'un régime.
    #     Régle d'attribution : a cotisé au régime + si polypensionnés ->
    #       ordre d'attribution : RG, RSI, FP
    #     Rq : Pas beau mais temporaire, pour comparaison Destinie'''
    #     if sum(trim_maj_mda_RG) + sum(trim_maj_mda_RSI) > 0:
    #         return 0 * trim_maj_mda_RG
    #     return trim_maj_mda_ini * (nb_trimesters > 0)

    # def trim_maj_5eme(self, nb_trimesters):
    #     # TODO: 5*4 ? d'ou ca vient ?
    #     # TODO: Add bonification au cinquième pour les superactifs
    #     # (policiers, surveillants pénitentiaires, contrôleurs aériens...)
    #     super_actif = 0  # condition superactif à définir
    #     taux_5eme = 0.2
    #     bonif_5eme = minimum(nb_trimesters * taux_5eme, 5 * 4)
    #     return array(bonif_5eme * super_actif) * (nb_trimesters > 0)

    # def trim_maj_ini(self, trim_maj_mda_ini, trim_maj_5eme):
    #     return trim_maj_mda_ini + trim_maj_5eme

    # def trim_maj(self, trim_maj_mda, trim_maj_5eme):
    #     return trim_maj_mda + trim_maj_5eme

    # # coeff_proratisation
    # def CP_5eme(self, nb_trimesters, trim_maj_5eme):
    #     print self.P.public.fp
    #     N_CP = self.P.public.fp.plein.n_trim
    #     return minimum(divide(nb_trimesters + trim_maj_5eme, N_CP), 1)

    # def CP_CPCM(self, nb_trimesters, trim_maj_mda_ini):
    #     # TODO: change to not trim_maj_mda instead of trim_maj_mda_ini ?
    #     P = self.P.public.fp
    #     N_CP = P.plein.n_trim
    #     taux = P.plein.taux
    #     taux_bonif = P.taux_bonif
    #     return minimum(divide(maximum(nb_trimesters, N_CP) + trim_maj_mda_ini,
    #                           N_CP),
    #                    divide(taux_bonif, taux))

    # def coeff_proratisation_Destinie(self, nb_trimesters, trim_maj_mda_ini):
    #     P = self.P.public.fp
    #     N_CP = P.plein.n_trim
    #     return minimum(divide(nb_trimesters + trim_maj_mda_ini, N_CP), 1)

    class coefficient_de_proratisation(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Coefficient de proratisation"

        def formula(individu, period, parameters):
            date_de_naissance = individu('date_de_naissance', period)
            duree_de_service_effective = individu("regime_name_duree_assurance", period)
            # TODO
            bonification_cpcm = 0
            super_actif = False  # individu('regime_name_super_actif', period)
            bonification_du_cinquieme = (
                super_actif * min_(
                    duree_de_service_effective / 5,
                    5
                    )
                )
            duree_assurance_requise = parameters(period).regime_name.trimtp.nombre_trimestres_cibles_taux_plein_par_generation[date_de_naissance]
            coefficient_de_proratisation = max_(
                min_(
                    1,
                    (duree_de_service_effective + bonification_du_cinquieme)
                    / duree_assurance_requise
                    ),
                min_(
                    80 / 75,
                    (
                        min_(duree_de_service_effective, duree_assurance_requise)
                        + bonification_cpcm
                        ) / duree_assurance_requise
                    )
                )
            return coefficient_de_proratisation

    class aod(Variable):
        value_type = int
        entity = Person
        definition_period = YEAR
        label = "Äge d'ouvertue des droits"

        def formula(individu, period, parameters):
            date_de_naissance = individu('date_de_naissance', period)
            aod_active = parameters(period).regime_name.aod_a.age_ouverture_droits_fonction_publique_active_selon_annee_naissance[date_de_naissance]
            aod_sedentaire = parameters(period).regime_name.aod_s.age_ouverture_droits_fonction_publique_sedentaire_selon_annee_naissance[date_de_naissance]
            statut = individu('statut', period)
            # TODO
            # actif pour les fonctionnaires actif en fin de carrière ou carrière mixte ayant une durée de service actif
            # suffisante
            return select(
                [statut == 'fonction_publique_active', statut == 'fonction_publique_sedentaire'],
                [aod_active, aod_sedentaire, 99]
                )

    class limite_d_age(Variable):
        value_type = int
        entity = Person
        definition_period = ETERNITY
        label = "Limite d'âge"

        def formula(individu, period, parameters):
            date_de_naissance = individu('date_de_naissance', period)
            limite_age_sedentaire = parameters(period).regime_name.la_s.age_limite_fonction_publique_sedentaire_selon_annee_naissance
            # limite_age_active = parameters(period).regime_name.la_a.age_limite_fonction_publique_active_selon_annee_naissance
            # statut = individu('statut', period)
            # return select(
            #     [statut == 'fonction_publique_active', statut == 'fonction_publique_sedentaire'],
            #     [limite_age_active, limite_age_sedentaire, 99]
            #     )

            if period.start.year <= 2011:
                limite_age_sedentaire_annee = limite_age_sedentaire.before_1951_07_01.annee
                limite_age_sedentaire_mois = 0
            else:
                limite_age_sedentaire_annee = limite_age_sedentaire[date_de_naissance].annee
                limite_age_sedentaire_mois = limite_age_sedentaire[date_de_naissance].mois

            return limite_age_sedentaire_annee + limite_age_sedentaire_mois / 4

    # def trim_decote(self, data, trimesters_tot, trim_maj_enf_tot):
    #     ''' Détermination de la décote à appliquer aux pensions '''
    #     P = reduce(getattr, self.param_name.split('.'), self.P)
    #     if P.decote.nb_trim_max != 0:
    #         agem = data.info_ind['agem']
    #         trim_decote = nb_trim_decote(trimesters_tot, trim_maj_enf_tot,
    #                                      agem, P)
    #         return trim_decote
    #     else:
    #         return zeros(data.info_ind.shape[0])

    class decote(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Décote"

        # TODO Manque réforme 2013 où seuls les bonifications comptent
        def formula_2006(individu, period, parameters):
            date_de_naissance = individu('date_de_naissance', period)
            # Âge d'ouverture des droits
            # aod_active_annee = parameters(period).regime_name.aod_a.age_ouverture_droits_fonction_publique_active_selon_annee_naissance[date_de_naissance].annee
            # aod_active_mois = parameters(period).regime_name.aod_a.age_ouverture_droits_fonction_publique_active_selon_annee_naissance[date_de_naissance].mois
            aod_sedentaire = parameters(period).regime_name.aod_s.age_ouverture_droits_fonction_publique_sedentaire_selon_annee_naissance
            if period.start.year <= 2011:
                aod_sedentaire_annee = aod_sedentaire.before_1951_07_01.annee
                aod_sedentaire_mois = 0
            else:
                aod_sedentaire_annee = aod_sedentaire[date_de_naissance].annee
                aod_sedentaire_mois = aod_sedentaire[date_de_naissance].mois

            # Âge d'annulation de la décôte
            aad_en_nombre_trimestres_par_rapport_limite_age = parameters(period).regime_name.aad.age_annulation_decote_selon_annee_ouverture_droits_en_nombre_trimestres_par_rapport_limite_age

            # statut = individu('statut', period)
            # TODO
            # actif pour les fonctionnaires actif en fin de carrière ou carrière mixte ayant une durée de service actif
            # suffisante
            # aod = select(
            #     [statut == 'fonction_publique_active', statut == 'fonction_publique_sedentaire'],
            #     [aod_active, aod_sedentaire, 99]
            #     )
            aod_annee = aod_sedentaire_annee
            aod_mois = aod_sedentaire_mois
            annee_age_ouverture_droits = np.trunc(
                date_de_naissance.astype('datetime64[Y]').astype('int') + 1970
                + aod_annee
                + (
                    (date_de_naissance.astype('datetime64[M]') - date_de_naissance.astype('datetime64[Y]')).astype('int')
                    + aod_mois
                    ) / 12
                ).astype(int)
            reduction_add_en_mois = where(
                # Double condition car cette réduction de l'AAD s'éteint en 2020 et vaut -1 en 2019
                (2019 >= annee_age_ouverture_droits) * (annee_age_ouverture_droits >= 2006),
                # aad_en_nombre_trimestres_par_rapport_limite_age est négatif et non renseigné en 2020 ni avant 2006 exclu
                # d'où le clip pour éviter l'erreur
                3 * aad_en_nombre_trimestres_par_rapport_limite_age[np.clip(annee_age_ouverture_droits, 2006, 2019)],
                0
                )

            aad_en_mois = individu("regime_name_limite_d_age", period) * 12 + reduction_add_en_mois
            age_en_mois_a_la_liquidation = (
                individu('regime_name_liquidation_date', period)
                - individu('date_de_naissance', period)
                ).astype("timedelta64[M]").astype(int)
            trimestres_avant_aad = max_(
                0,
                np.trunc(
                    (aad_en_mois - age_en_mois_a_la_liquidation) / 3
                    )
                )
            duree_assurance_requise = parameters(period).regime_name.trimtp.nombre_trimestres_cibles_taux_plein_par_generation[date_de_naissance]
            trimestres = individu('duree_assurance_tous_regimes', period)
            decote_trimestres = max_(
                0,
                min_(
                    trimestres_avant_aad,
                    duree_assurance_requise - trimestres
                    )
                )
            taux_decote = (
                (annee_age_ouverture_droits >= 2006)  # TODO check condtion on 2015 ?
                * parameters(period).regime_name.decote.taux_decote_selon_annee_age_ouverture_droits.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants[
                    np.clip(annee_age_ouverture_droits, 2006, 2015)
                    ]
                )
            return taux_decote * decote_trimestres

    class surcote(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Surcote"

        def formula_2004(individu, period, parameters):
            date_de_naissance = individu('date_de_naissance', period)
            # Âge d'ouverture des droits
            # aod_active_annee = parameters(period).regime_name.aod_a.age_ouverture_droits_fonction_publique_active_selon_annee_naissance[date_de_naissance].annee
            # aod_active_annee = parameters(period).regime_name.aod_a.age_ouverture_droits_fonction_publique_active_selon_annee_naissance[date_de_naissance].mois
            aod_sedentaire = parameters(period).regime_name.aod_s.age_ouverture_droits_fonction_publique_sedentaire_selon_annee_naissance
            if period.start.year <= 2011:
                aod_sedentaire_annee = aod_sedentaire.before_1951_07_01.annee
                aod_sedentaire_mois = 0
            else:
                aod_sedentaire_annee = aod_sedentaire[date_de_naissance].annee
                aod_sedentaire_mois = aod_sedentaire[date_de_naissance].mois

            aod_annee = aod_sedentaire_annee
            aod_mois = aod_sedentaire_mois

            age_en_mois_a_la_liquidation = (
                individu('regime_name_liquidation_date', period)
                - individu('date_de_naissance', period)
                ).astype("timedelta64[M]").astype(int)
            trimestres_apres_aod = max_(
                0,
                np.trunc(
                    (age_en_mois_a_la_liquidation - 12 * aod_annee + aod_mois) / 3
                    )
                )
            duree_assurance_requise = parameters(period).regime_name.trimtp.nombre_trimestres_cibles_taux_plein_par_generation[date_de_naissance]
            duree_assurance_excedentaire = (
                individu('duree_assurance_tous_regimes', period)
                - duree_assurance_requise
                )
            trimestres_surcote = max_(
                0,
                min_(
                    trimestres_apres_aod,
                    duree_assurance_excedentaire
                    )
                )
            # TODO correction réforme 2013 voir guide page 1937
            taux_surcote = parameters(period).regime_name.surcote.taux_surcote_par_trimestre
            return taux_surcote * trimestres_surcote

    class dernier_indice_atteint(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Dernier indice connu dans la fonction publique"

        def formula(individu, period, parameters):
            # Devrait être dernier indice atteint pendant 6 mois
            salaire_de_base = individu("salaire_de_base", period)
            taux_de_prime = individu("taux_de_prime", period)
            valeur_point_indice = parameters(period).marche_travail.remuneration_dans_fonction_publique.indicefp.point_indice_en_euros
            dernier_indice = where(
                salaire_de_base > 0,  # and statut = fonction_publique,
                salaire_de_base / (1 + taux_de_prime) / valeur_point_indice,
                individu("regime_name_dernier_indice_atteint", period.last_year)
                )
            return dernier_indice

    class salaire_de_reference(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Traitement de référence"

        def formula(individu, period, parameters):
            dernier_indice_atteint = individu("regime_name_dernier_indice_atteint", period)
            valeur_point_indice = parameters(period).marche_travail.remuneration_dans_fonction_publique.indicefp.point_indice_en_euros
            return dernier_indice_atteint * valeur_point_indice

    # def plafond_pension(self, pension_brute):
    #     return pension_brute

    # def minimum_pension(self, nb_trimesters, pension_brute):
    #     return 0 * pension_brute

    # def cotisations(self, data):
    #     ''' Calcul des cotisations passées par année'''
    #     sali = data.sali * data.workstate.isin(self.code_regime).astype(int)
    #     Pcot_regime = reduce(getattr, self.param_name.split('.'), self.P_cot)
    #     # getattr(self.P_longit.prive.complementaire,  self.name)
    #     taux_prime = array(data.info_ind['tauxprime'])
    #     taux_pat = Pcot_regime.cot_pat
    #     taux_sal = Pcot_regime.cot_sal
    #     assert len(taux_pat) == sali.shape[1] == len(taux_sal)
    #     cot_sal_by_year = zeros(sali.shape)
    #     cot_pat_by_year = zeros(sali.shape)
    #     denominator = (1 + taux_prime)
    #     if 'ath' in data.info_ind:
    #         ath = array(data.info_ind['ath'])
    #         denominator = ath * denominator
    #     for ix_year in range(sali.shape[1]):
    #         cot_sal_by_year[:, ix_year] = taux_sal[ix_year] * sali[:, ix_year] / denominator
    #         cot_pat_by_year[:, ix_year] = taux_pat[ix_year] * sali[:, ix_year] / denominator
    #     return {'sal': cot_sal_by_year, 'pat': cot_pat_by_year}

    # TODO majoration et bonification
