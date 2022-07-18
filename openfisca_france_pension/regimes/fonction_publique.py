"""Régime de base de la fonction publique."""

from certifi import where
import numpy as np

from openfisca_core.model_api import *
from openfisca_core.parameters import ParameterNotFound

from openfisca_france_pension.entities import Person
from openfisca_france_pension.regimes.regime import AbstractRegimeDeBase


class TypesCategorieActivite(Enum):
    __order__ = 'sedentaire actif'  # Needed to preserve the enum order in Python 2
    sedentaire = 'Sédentaire'
    actif = "Actif"


class RegimeFonctionPublique(AbstractRegimeDeBase):
    name = "Régime de base de la fonction publique"
    variable_prefix = "fonction_publique"
    parameters_prefix = "secteur_public"

    class actif_a_la_liquidation(Variable):
        value_type = bool
        entity = Person
        definition_period = YEAR
        label = "Atteinte des quinze ans d'activité"

        def formula(individu, period, parameters):
            date_quinze_ans_actif = individu('fonction_publique_date_quinze_ans_actif', period)
            actif_annee = parameters(period).regime_name.duree_seuil_actif.duree_service_minimale_considere_comme_actif[date_quinze_ans_actif]
            actif = individu('fonction_publique_nombre_annees_actif', period) >= actif_annee
            return actif

    class annee_age_ouverture_droits(Variable):
        value_type = int
        entity = Person
        definition_period = YEAR
        label = "Annee_age_ouverture_droits"

        def formula_2006(individu, period, parameters):
            date_de_naissance = individu('date_de_naissance', period)
            # Âge d'ouverture des droits
            aod_active = parameters(period).regime_name.aod_a.age_ouverture_droits_fonction_publique_active_selon_annee_naissance
            aod_sedentaire = parameters(period).regime_name.aod_s.age_ouverture_droits_fonction_publique_sedentaire_selon_annee_naissance
            if period.start.year <= 2011:
                aod_sedentaire_annee = aod_sedentaire.before_1951_07_01.annee
                aod_sedentaire_mois = 0
                aod_active_annee = aod_active.before_1956_07_01.annee
                aod_active_mois = 0
            else:
                aod_sedentaire_annee = aod_sedentaire[date_de_naissance].annee
                aod_sedentaire_mois = aod_sedentaire[date_de_naissance].mois
                aod_active_annee = aod_active[date_de_naissance].annee
                aod_active_mois = aod_active[date_de_naissance].mois

            # Âge d'annulation de la décôte
            actif_a_la_liquidation = individu('regime_name_actif_a_la_liquidation', period)
            aod_annee = where(actif_a_la_liquidation, aod_active_annee, aod_sedentaire_annee)
            aod_mois = where(actif_a_la_liquidation, aod_active_mois, aod_sedentaire_mois)
            annee_age_ouverture_droits = np.trunc(
                date_de_naissance.astype('datetime64[Y]').astype('int') + 1970
                + aod_annee
                + (
                    (date_de_naissance.astype('datetime64[M]') - date_de_naissance.astype('datetime64[Y]')).astype('int')
                    + aod_mois
                    ) / 12
                ).astype(int)
            print("annee_age_ouverture_droits",annee_age_ouverture_droits)
            conditions_pr_aod_depart_anticipe_parent_trois_enfants = individu('regime_name_conditions_pr_aod_depart_anticipe_parent_trois_enfants', period)
            condition_aod = annee_age_ouverture_droits < 2016
            return where(conditions_pr_aod_depart_anticipe_parent_trois_enfants * condition_aod, 0, annee_age_ouverture_droits)

    class aod(Variable):
        value_type = int
        entity = Person
        definition_period = YEAR
        label = "Äge d'ouvertue des droits"

        def formula(individu, period, parameters):
            date_de_naissance = individu('date_de_naissance', period)
            actif_a_la_liquidation = individu('fonction_publique_actif_a_la_liquidation', period)
            satisfaction_conditions_parent_trois_enfants = individu('regime_name_conditions_pr_aod_depart_anticipe_parent_trois_enfants',period)
            print("date_satisfaction_conditions_parent_trois_enfants",satisfaction_conditions_parent_trois_enfants)
            aod_active = parameters(period).regime_name.aod_a.age_ouverture_droits_fonction_publique_active_selon_annee_naissance
            aod_sedentaire = parameters(period).regime_name.aod_s.age_ouverture_droits_fonction_publique_sedentaire_selon_annee_naissance
            if period.start.year <= 2011:
                aod_sedentaire_annee = aod_sedentaire.before_1951_07_01.annee
                aod_sedentaire_mois = 0
                aod_active_annee = aod_active.before_1956_07_01.annee
                aod_active_mois = 0
            else:
                aod_sedentaire_annee = aod_sedentaire[date_de_naissance].annee
                aod_sedentaire_mois = aod_sedentaire[date_de_naissance].mois
                aod_active_annee = aod_active[date_de_naissance].annee
                aod_active_mois = aod_active[date_de_naissance].mois
            print("aod_active_mois",aod_active_mois)
            aod_p3e = where(satisfaction_conditions_parent_trois_enfants, satisfaction_conditions_parent_trois_enfants.astype("timedelta64[Y]").astype(int) - 60, aod_sedentaire_annee)
            print("aod_p3e",aod_p3e)
            a = select(
                [
                    actif_a_la_liquidation, 
                    satisfaction_conditions_parent_trois_enfants
                    ],
                [                
                    aod_active_annee + aod_active_mois, 
                    aod_p3e,
                    ],
                default = aod_sedentaire_annee + aod_sedentaire_mois
                )
            print("a:",a)
            return a

    class coefficient_de_proratisation(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Coefficient de proratisation"

        def formula(individu, period, parameters):
            date_de_naissance = individu('date_de_naissance', period)
            duree_de_service_effective = individu("fonction_publique_duree_de_service", period)
            # TODO
            majoration_duree_assurance = individu('fonction_publique_majoration_duree_assurance', period)
            super_actif = False  # individu('regime_name_super_actif', period)
            bonification_du_cinquieme = (
                super_actif * min_(
                    duree_de_service_effective / 5,
                    5
                    )
                )
            duree_de_service_requise = parameters(period).regime_name.trimtp.nombre_trimestres_cibles_taux_plein_par_generation[date_de_naissance]
            coefficient_de_proratisation = max_(
                min_(
                    1,
                    (duree_de_service_effective + bonification_du_cinquieme)
                    / duree_de_service_requise
                    ),
                min_(
                    80 / 75,
                    (min_(duree_de_service_effective, duree_de_service_requise) + majoration_duree_assurance)
                    / duree_de_service_requise
                    )
                )
            return coefficient_de_proratisation

    class categorie_activite(Variable):
        value_type = Enum
        possible_values = TypesCategorieActivite
        default_value = TypesCategorieActivite.sedentaire
        entity = Person
        label = "Catégorie d'activité des emplois publics"
        definition_period = YEAR
        set_input = set_input_dispatch_by_period

    class date_quinze_ans_actif(Variable):
        value_type = date
        entity = Person
        definition_period = YEAR
        label = "Date d'atteinte des quinze ans d'activité en tant qu'actif"

        def formula(individu, period):
            last_year = period.start.period('year').offset(-1)
            nombre_annees_actif_annee_courante = individu('regime_name_nombre_annees_actif', period)
            date_actif_annee_precedente = individu('regime_name_date_quinze_ans_actif', last_year)
            date = select(
                [
                    date_actif_annee_precedente < np.datetime64("2250-12-31"),
                    nombre_annees_actif_annee_courante <= 15,
                    date_actif_annee_precedente == np.datetime64("2250-12-31")
                    ],
                [
                    date_actif_annee_precedente,
                    np.datetime64("2250-12-31"),
                    np.datetime64(str(period.start))
                    ],
                default = np.datetime64("2250-12-31")
                )
            return date

    class date_quinze_ans_service(Variable):
        value_type = date
        entity = Person
        definition_period = YEAR
        label = "Date d'atteinte des quinze ans d'activité"

        def formula(individu, period):
            last_year = period.start.period('year').offset(-1)
            nombre_annees_service_annee_courante = individu('fonction_publique_duree_de_service', period)
            date_service_annee_precedente = individu('fonction_publique_date_quinze_ans_service', last_year)
            date = select(
                [
                    date_service_annee_precedente < np.datetime64("2250-12-31"),
                    nombre_annees_service_annee_courante <= 15,
                    date_service_annee_precedente == np.datetime64("2250-12-31")
                    ],
                [
                    date_service_annee_precedente,
                    np.datetime64("2250-12-31"),
                    np.datetime64(str(period.start))
                    ],
                default = np.datetime64("2250-12-31")
                )
            return date

    class date_satisfaction_condition_depart_anticipe_parents_trois_enfants(Variable):
        value_type = date
        entity = Person
        definition_period = YEAR
        label = "Date à laquelle les deux conditions permettant un depart anticipe pour motif de parent de trois enfant sont satisfaites"
        
        def formula(individu, period):
            date_naissance_enfant = individu('date_naissance_enfant', period)
            date_trois_enfants = date_naissance_enfant
            date_quinze_ans_service = individu('regime_name_date_quinze_ans_service', period)
            condition1 = date_quinze_ans_service == np.datetime64("1970-01-01")
            condition2 = date_trois_enfants == np.datetime64("1970-01-01")
            return where(condition1 * condition2, np.datetime64("2250-12-31"), max(date_trois_enfants, date_quinze_ans_service))
            
    class conditions_pr_aod_depart_anticipe_parent_trois_enfants(Variable):
        value_type = bool
        entity = Person
        definition_period = YEAR
        label = "Depart anticipé pour motif de parent de trois enfants"
        default_value = False

        def formula(individu, period):
            nombre_enfants_a_charge = individu('nombre_enfants_a_charge', period)
            duree_de_service_effective = individu("regime_name_duree_de_service", period)
            liquidation_date = individu('regime_name_liquidation_date', period)
            annee_satisfaction_condition_depart_anticipe_aprents_trois_enfants = individu('regime_name_date_satisfaction_condition_depart_anticipe_parents_trois_enfants', period).astype('datetime64[Y]').astype('int')
            condition_enfant = nombre_enfants_a_charge >= 3
            condition_service = duree_de_service_effective >= 60
            condition_date = annee_satisfaction_condition_depart_anticipe_aprents_trois_enfants < 2012
            condition_date_liquidation = liquidation_date < np.datetime64("2011-07-01")
            return condition_enfant * condition_service * condition_date_liquidation * condition_date

    class conditions_pr_decote_depart_anticipe_parent_trois_enfants(Variable):
        value_type = bool
        entity = Person
        definition_period = YEAR
        label = "Depart anticipé pour motif de parent de trois enfants"
        default_value = False

        def formula(individu, period):
            nombre_enfants_a_charge = individu('nombre_enfants_a_charge', period)
            duree_de_service_effective = individu("regime_name_duree_de_service", period)
            annee_age_ouverture_droits = individu('regime_name_annee_age_ouverture_droits', period)
            liquidation_date = individu('regime_name_liquidation_date', period)
            condition_enfant = nombre_enfants_a_charge >= 3
            condition_service = duree_de_service_effective >= 60
            condition_aod = annee_age_ouverture_droits < 2016
            condition_date_liquidation = liquidation_date < np.datetime64("2011-07-01")
            return condition_enfant * condition_service * condition_aod * condition_date_liquidation

    class decote_trimestres(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "decote trimestres"

        def formula_2006(individu, period, parameters):
            date_de_naissance = individu('date_de_naissance', period)
            actif_a_la_liquidation = individu('regime_name_actif_a_la_liquidation', period)
            annee_age_ouverture_droits_general = individu('fonction_publique_annee_age_ouverture_droits', period)
            print("annee_age_ouverture_droits_general:",annee_age_ouverture_droits_general)
            conditions_depart_anticipe_parent_trois_enfants = individu('regime_name_conditions_pr_decote_depart_anticipe_parent_trois_enfants', period)
            print("conditions_depart_anticipe_parent_trois_enfants",conditions_depart_anticipe_parent_trois_enfants)
            annee_age_ouverture_droits_p3e = individu('regime_name_date_satisfaction_condition_depart_anticipe_parents_trois_enfants', period).astype('datetime64[Y]').astype('int') + 1970
            print("annee_age_ouverture_droits_p3e:",annee_age_ouverture_droits_p3e)
            aad_en_nombre_trimestres_par_rapport_limite_age = parameters(period).regime_name.aad.age_annulation_decote_selon_annee_ouverture_droits_en_nombre_trimestres_par_rapport_limite_age
            print("aad_en_nombre_trimestres_par_rapport_limite_age:",aad_en_nombre_trimestres_par_rapport_limite_age)
            annee_age_ouverture_droits = (where(conditions_depart_anticipe_parent_trois_enfants, annee_age_ouverture_droits_p3e, annee_age_ouverture_droits_general))
            print("annee_age_ouverture_droits:",annee_age_ouverture_droits)
            reduction_add_en_mois = where(
                # Double condition car cette réduction de l'AAD s'éteint en 2020 et vaut -1 en 2019
                (2019 >= annee_age_ouverture_droits) * (annee_age_ouverture_droits >= 2006),
                # aad_en_nombre_trimestres_par_rapport_limite_age est négatif et non renseigné en 2020 ni avant 2006 exclu
                # d'où le clip pour éviter l'erreur
                3 * aad_en_nombre_trimestres_par_rapport_limite_age[np.clip(annee_age_ouverture_droits, 2006, 2019)],
                0
                )
            print("reduction_add_en_mois:",reduction_add_en_mois)
            #.astype('datetime64[Y]').astype('int') + 1970
            aad_en_mois_general = individu("regime_name_limite_d_age", period) * 12 + reduction_add_en_mois
            print("aad_en_mois_general",aad_en_mois_general)
            limit_age = individu("regime_name_aod",period) + 5
            print("limit_age",limit_age)
            aad_en_mois_parents_trois_enfants = limit_age * 12 + reduction_add_en_mois
            print("aad_en_mois_parents_trois_enfants",aad_en_mois_parents_trois_enfants)
            aad_en_mois = where(conditions_depart_anticipe_parent_trois_enfants, aad_en_mois_parents_trois_enfants, aad_en_mois_general)
            print("aad_en_mois",aad_en_mois)
            age_en_mois_a_la_liquidation = (
                individu('regime_name_liquidation_date', period)
                - individu('date_de_naissance', period)
                ).astype("timedelta64[M]").astype(int)
            trimestres_avant_aad = max_(
                0,
                np.ceil(
                    (aad_en_mois - age_en_mois_a_la_liquidation) / 3
                    )
                )
            duree_assurance_requise_sedentaires = parameters(period).regime_name.trimtp.nombre_trimestres_cibles_taux_plein_par_generation[date_de_naissance]
            duree_assurance_requise_actifs = parameters(period).regime_name.trimtp_a.nombre_trimestres_cibles_taux_plein_par_generation_actifs[date_de_naissance]
            duree_assurance_requise = where(actif_a_la_liquidation, duree_assurance_requise_actifs, duree_assurance_requise_sedentaires)
            trimestres = individu('duree_assurance_tous_regimes', period)
            decote_trimestres = min_(
                max_(
                    0,
                    min_(
                        trimestres_avant_aad,
                        duree_assurance_requise - trimestres
                        )
                    ),
                20,
                )
            return where(
                annee_age_ouverture_droits >= 2006,
                min_(decote_trimestres, 20),
                0
                )

    class decote(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "annee_age_ouverture_droits"

        def formula_2006(individu, period, parameters):
            annee_age_ouverture_droits = individu('regime_name_annee_age_ouverture_droits', period)
            decote_trimestres = individu('regime_name_decote_trimestres', period)
            taux_decote = (
                (annee_age_ouverture_droits >= 2006)  # TODO check condtion on 2015 ?
                * parameters(period).regime_name.decote.taux_decote_selon_annee_age_ouverture_droits.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants[
                    np.clip(annee_age_ouverture_droits, 2006, 2015)
                    ]
                )
            return taux_decote * decote_trimestres

    class dernier_indice_atteint(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Dernier indice connu dans la fonction publique"

        def formula_1970(individu, period, parameters):
            # Devrait être dernier indice atteint pendant 6 mois
            salaire_de_base = individu("regime_name_salaire_de_base", period)
            taux_de_prime = individu("taux_de_prime", period)
            valeur_point_indice = parameters(period).marche_travail.remuneration_dans_fonction_publique.indicefp.point_indice_en_euros
            dernier_indice = where(
                salaire_de_base > 0,  # TODO and statut = fonction_publique,
                salaire_de_base / (1 + taux_de_prime) / valeur_point_indice,
                individu("regime_name_dernier_indice_atteint", period.last_year)
                )
            return dernier_indice

    class duree_assurance(Variable):
        value_type = int
        entity = Person
        definition_period = YEAR
        label = "Durée d'assurance (trimestres validés dans la fonction publique)"

        def formula(individu, period, parameters):
            duree_assurance_validee = individu("regime_name_duree_assurance_validee", period)
            annee_de_liquidation = individu('regime_name_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
            majoration_duree_assurance = individu('regime_name_majoration_duree_assurance', period)
            return where(
                annee_de_liquidation == period.start.year,
                round_(duree_assurance_validee + majoration_duree_assurance),  # On arrondi l'année de la liquidation
                duree_assurance_validee
                )

    class duree_assurance_annuelle(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Durée d'assurance annuelle (trimestres validés dans la fonction publique hors majoration)"

        def formula(individu, period, parameters):
            quotite_de_travail = np.clip(individu("regime_name_quotite_de_travail", period), 0.0, 1.0)
            duree_de_service_cotisee_annuelle = individu("regime_name_duree_de_service_cotisee_annuelle", period)
            duree_de_service_cotisee_annuelle = where(
                quotite_de_travail == 0,
                0,
                duree_de_service_cotisee_annuelle
                )
            duree_assurance_cotisee_annuelle = duree_de_service_cotisee_annuelle / (quotite_de_travail + (quotite_de_travail == 0))  # To avoid division by zéro
            duree_assurance_rachetee_annuelle = individu("regime_name_duree_de_service_rachetee_annuelle", period)
            duree_assurance_service_national_annuelle = individu("regime_name_duree_assurance_service_national_annuelle", period)

            return np.clip(
                duree_assurance_cotisee_annuelle + duree_assurance_rachetee_annuelle + duree_assurance_service_national_annuelle,
                0,
                4
                )

    class duree_assurance_validee(Variable):
        value_type = int
        entity = Person
        definition_period = YEAR
        label = "Durée d'assurance (trimestres validés dans la fonction publique)"

        def formula(individu, period, parameters):
            duree_assurance_annuelle = individu("regime_name_duree_assurance_annuelle", period)
            duree_assurance_annee_precedente = individu("regime_name_duree_assurance", period.last_year)
            # TODO: hack to avoid infinite recursion depth loop
            if all((duree_assurance_annuelle == 0.0) & (duree_assurance_annee_precedente == 0.0)):
                return individu.empty_array()
            return duree_assurance_annee_precedente + duree_assurance_annuelle

    class duree_de_service(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Durée de service (trimestres cotisés dans la fonction publique) hors bonification cummulée"

        def formula(individu, period, parameters):
            duree_de_service_annuelle = individu("regime_name_duree_de_service_annuelle", period)
            duree_de_service_annee_precedente = individu("regime_name_duree_de_service", period.last_year)
            # TODO: hack to avoid infinite recursion depth loop
            if all((duree_de_service_annuelle == 0.0) & (duree_de_service_annee_precedente == 0.0)):
                return individu.empty_array()

            annee_de_liquidation = individu('regime_name_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
            majoration_duree_de_service = individu('regime_name_majoration_duree_de_service', period)
            return where(
                annee_de_liquidation == period.start.year,
                round_(
                    duree_de_service_annee_precedente
                    + duree_de_service_annuelle
                    + majoration_duree_de_service
                    ),  # On arrondi l'année de la liquidation
                duree_de_service_annee_precedente + duree_de_service_annuelle
                )

    class duree_de_service_annuelle(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Durée de service dans la fonction publique hors rachst et bonification dans l'année"

        def formula(individu, period, parameters):
            return np.clip(
                individu('regime_name_duree_de_service_cotisee_annuelle', period)
                + individu('regime_name_duree_de_service_rachetee_annuelle', period)
                + individu("regime_name_duree_assurance_service_national_annuelle", period),
                0,
                4
                )

    class duree_de_service_cotisee_annuelle(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Durée de service cotisée dans la fonction publique hors rachst et bonification dans l'année"

    class duree_de_service_rachetee_annuelle(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Durée de service rachetée (années d'études) dans la fonction publique hors rachst et bonification dans l'année"

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
    class limite_d_age(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Limite d'âge"

        def formula(individu, period, parameters):
            date_de_naissance = individu('date_de_naissance', period)
            actif_a_la_liquidation = individu('fonction_publique_actif_a_la_liquidation', period)
            limite_age_active = parameters(period).regime_name.la_a.age_limite_fonction_publique_active_selon_annee_naissance
            limite_age_sedentaire = parameters(period).regime_name.la_s.age_limite_fonction_publique_sedentaire_selon_annee_naissance
            if period.start.year <= 2011:
                limite_age_active_annee = limite_age_active.before_1956_07_01.annee
                limite_age_active_mois = 0
                limite_age_sedentaire_annee = limite_age_sedentaire.before_1951_07_01.annee
                limite_age_sedentaire_mois = 0

            else:
                limite_age_active_annee = limite_age_active[date_de_naissance].annee
                limite_age_active_mois = limite_age_active[date_de_naissance].mois
                limite_age_sedentaire_annee = limite_age_sedentaire[date_de_naissance].annee
                limite_age_sedentaire_mois = limite_age_sedentaire[date_de_naissance].mois

            limite_age_actif = limite_age_active_annee + limite_age_active_mois / 12
            limite_age_sedentaire = limite_age_sedentaire_annee + limite_age_sedentaire_mois / 12
            return where(
                actif_a_la_liquidation,
                limite_age_actif,
                limite_age_sedentaire
                )

    class majoration_pension(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Majoration de pension"
        reference = [
            "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000025076852/",  # Legislation Foncionnaires : art L.18  (1965)
            "https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI000006400888/",  # Legislation CNRACL : art 24  (2004)
            ]

        def formula_1965(individu, period):
            nombre_enfants = individu('nombre_enfants', period)
            pension_brute = individu('regime_name_pension_brute', period)
            return pension_brute * (.1 * (nombre_enfants >= 3) + .05 * max_(nombre_enfants - 3, 0))

    class majoration_duree_assurance_enfant(Variable):
        value_type = float
        entity = Person
        definition_period = ETERNITY
        label = "Bonification pour enfants selon le code des pensions civiles et militaires"
        definition_period = YEAR

        def formula_2004(individu, period, parameters):
            bonification_par_enfant_av_2004 = parameters(period).secteur_public.bonification_enfant.nombre_trimestres_par_enfant_bonification.before_2004_01_01
            nombre_enfants_nes_avant_2004 = individu('regime_name_nombre_enfants_nes_avant_2004', period)
            bonification_cpcm = bonification_par_enfant_av_2004 * nombre_enfants_nes_avant_2004
            bonification_par_enfant_pr_2004 = parameters(period).secteur_public.bonification_enfant.nombre_trimestres_par_enfant_bonification.after_2004_01_01
            nombre_enfants_nes_apres_2004 = individu('nombre_enfants', period) - nombre_enfants_nes_avant_2004
            bonification_cpcm = (
                bonification_par_enfant_av_2004 * nombre_enfants_nes_avant_2004
                + bonification_par_enfant_pr_2004 * nombre_enfants_nes_apres_2004
                )
            sexe = individu('sexe', period)
            return where(sexe, bonification_cpcm, 0)

        def formula_1949(individu, period, parameters):
            bonification_par_enfant_av_2004 = parameters(period).secteur_public.bonification_enfant.nombre_trimestres_par_enfant_bonification.before_2004_01_01
            nombre_enfants = individu('nombre_enfants', period)
            bonification_cpcm = bonification_par_enfant_av_2004 * nombre_enfants
            sexe = individu('sexe', period)
            return where(sexe, bonification_cpcm, 0)

    class majoration_duree_de_service(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Majoration de durée de service"

    class minimum_garanti(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Minimum garanti de la fonction publique"
        reference = "Loi 75-1242 du 27 décembre 1975"

        def formula_1976(individu, period, parameters):
            date_de_naissance = individu('date_de_naissance', period)
            liquidation_date = individu('regime_name_liquidation_date', period)
            annee_de_liquidation = individu('regime_name_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
            duree_de_service_effective = individu("fonction_publique_duree_de_service", period)
            annee_age_ouverture_droits = individu('regime_name_annee_age_ouverture_droits', period)
            decote = individu("regime_name_decote", period)

            service_public = parameters(period).regime_name
            minimum_garanti = service_public.minimum_garanti
            points_moins_40_ans = minimum_garanti.points_moins_40_ans.point_annee_supplementaire_moins_40_ans[liquidation_date]
            points_plus_15_ans = minimum_garanti.points_plus_15_ans.point_annee_supplementaire_plus_15_ans[liquidation_date]
            annee_moins_40_ans = minimum_garanti.annee_moins_40_ans.annee_supplementaire_moins_40_ans[liquidation_date]
            part_fixe = service_public.part_valeur_indice_majore.part_indice_majore_en_euros[liquidation_date]
            indice_majore = service_public.valeur_indice_maj.indice_majore_en_euros[liquidation_date]
            pt_indice = parameters(period).marche_travail.remuneration_dans_fonction_publique.indicefp.point_indice_en_euros
            duree_assurance_requise = service_public.trimtp.nombre_trimestres_cibles_taux_plein_par_generation[date_de_naissance]

            coefficient_moins_15_ans = duree_de_service_effective / duree_assurance_requise
            coefficient_plus_15_ans = (
                part_fixe
                + max_(duree_de_service_effective - 4 * 15, 0) * points_plus_15_ans
                )
            coefficient_plus_30_ans = (
                part_fixe
                + max_(annee_moins_40_ans - 4 * 15, 0) * points_plus_15_ans
                + max_(duree_de_service_effective - annee_moins_40_ans, 0) * points_moins_40_ans
                )
            coefficient_plus_40_ans = 1

            # Tiré de https://www.service-public.fr/particuliers/vosdroits/F13300#:~:text=Cas%20g%C3%A9n%C3%A9ral-,Le%20montant%20mensuel%20du%20minimum%20garanti%20qui%20vous%20est%20applicable,une%20retraite%20%C3%A0%20taux%20plein.
            # Vous justifiez du nombre de trimestres d'assurance requis pour bénéficier d'une retraite à taux plein
            # Vous avez atteint la limite d'âge
            # Vous avez atteint l'âge d'annulation de la décote
            # Vous êtes admis à la retraite pour invalidité
            # Vous êtes admis à la retraite anticipée en tant que parent d'un enfant invalide
            # Vous êtes admis à la retraite anticipée en tant que fonctionnaire handicapé à 50 %
            # Vous êtes admis à la retraite anticipée pour infirmité ou maladie incurable
            condition_absence_decote = decote == 0
            condition_duree = duree_de_service_effective > duree_assurance_requise
            condition_age_ouverture_des_droits = (annee_age_ouverture_droits < 2011) * (annee_de_liquidation >= 2011)
            post_condition = where(
                (annee_de_liquidation < 2011) + condition_age_ouverture_des_droits,  # + is OR
                True,
                condition_duree + condition_absence_decote,
                )

            return post_condition * indice_majore * pt_indice * select(
                [
                    duree_de_service_effective < 60,
                    duree_de_service_effective < annee_moins_40_ans,
                    duree_de_service_effective < 160,
                    duree_de_service_effective >= 160,
                    ],
                [
                    coefficient_moins_15_ans,
                    coefficient_plus_15_ans,
                    coefficient_plus_30_ans,
                    coefficient_plus_40_ans,
                    ]
                )

    class nombre_annees_actif(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Nombre d'années travaillant en tant qu'actif"

        def formula(individu, period):
            annee_de_liquidation = individu('regime_name_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
            if all(period.start.year > annee_de_liquidation):
                return individu.empty_array()
            last_year = period.start.period('year').offset(-1)
            nombre_annees_actif_annee_precedente = individu('regime_name_nombre_annees_actif', last_year)
            categorie_activite = individu('regime_name_categorie_activite', period)
            return nombre_annees_actif_annee_precedente + 1 * (categorie_activite == TypesCategorieActivite.actif)

    class nombre_enfants_nes_avant_2004(Variable):
        value_type = int
        entity = Person
        label = "Nombre d'enfants nés avant 2004"
        definition_period = ETERNITY

    class pension(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Pension"

        def formula(individu, period):
            pension_brute = individu('regime_name_pension_brute', period)
            majoration_pension = individu('regime_name_majoration_pension', period)
            pension_maximale = individu('regime_name_salaire_de_reference', period)
            return min_(pension_brute + majoration_pension, pension_maximale)

    class pension_brute(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = 'Pension brute'

        def formula(individu, period, parameters):
            pension_avant_minimum_et_plafonnement = individu("regime_name_pension_avant_minimum_et_plafonnement", period)
            minimum_garanti = individu("regime_name_minimum_garanti", period)
            return max_(pension_avant_minimum_et_plafonnement, minimum_garanti)

    class quotite_de_travail(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = 'Quotité de travail'
        default_value = 1.0

    class salaire_de_reference(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Traitement de référence"

        def formula(individu, period, parameters):
            dernier_indice_atteint = individu("regime_name_dernier_indice_atteint", period)
            try:
                valeur_point_indice = parameters(period).marche_travail.remuneration_dans_fonction_publique.indicefp.point_indice_en_euros
            except ParameterNotFound:  # TODO fix this hack
                valeur_point_indice = 0

            return dernier_indice_atteint * valeur_point_indice

    class surcote_trimestres(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Trimestres surcote avant application du minimum garanti"

        def formula_2004(individu, period, parameters):
            liquidation_date = individu('regime_name_liquidation_date', period)
            date_de_naissance = individu('date_de_naissance', period)
            # Âge d'ouverture des droits
            aod_sedentaire = parameters(period).regime_name.aod_s.age_ouverture_droits_fonction_publique_sedentaire_selon_annee_naissance
            if period.start.year <= 2011:
                aod_sedentaire_annee = aod_sedentaire.before_1951_07_01.annee
                aod_sedentaire_mois = 0
            else:
                aod_sedentaire_annee = aod_sedentaire[date_de_naissance].annee
                aod_sedentaire_mois = aod_sedentaire[date_de_naissance].mois

            age_en_mois_a_la_liquidation = (
                individu('regime_name_liquidation_date', period)
                - individu('date_de_naissance', period)
                ).astype("timedelta64[M]").astype(int)

            arrondi_trimestres_aod = np.ceil if period.start.year < 2009 else np.floor  # add link
            trimestres_apres_aod = max_(
                0,
                (
                    (
                        age_en_mois_a_la_liquidation - (12 * aod_sedentaire_annee + aod_sedentaire_mois)
                        ) / 3
                    )
                )
            duree_assurance_requise = parameters(period).regime_name.trimtp.nombre_trimestres_cibles_taux_plein_par_generation[date_de_naissance]
            trimestres_apres_instauration_surcote = ((individu('regime_name_liquidation_date', period) - np.datetime64("2004-01-01")).astype("timedelta64[M]").astype(int)) / 3
            duree_assurance_excedentaire = (
                individu('duree_assurance_tous_regimes', period)
                - duree_assurance_requise
                )
            trimestres_surcote = max_(
                0,
                arrondi_trimestres_aod(min_(
                    min_(trimestres_apres_instauration_surcote, trimestres_apres_aod),
                    duree_assurance_excedentaire
                    ))
                )
            # TODO correction réforme 2013 voir guide page 1937
            return where(
                liquidation_date < np.datetime64("2010-11-11"),
                min_(trimestres_surcote, 20),
                trimestres_surcote,
                )

    class surcote(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Surcote"

        def formula_2004(individu, period, parameters):
            surcote_trimestres = individu('regime_name_surcote_trimestres', period)
            actif_a_la_liquidation = individu('regime_name_actif_a_la_liquidation', period)
            taux_surcote = parameters(period).regime_name.surcote.taux_surcote_par_trimestre
            return where(actif_a_la_liquidation, 0, taux_surcote * surcote_trimestres)

    class taux_de_liquidation_proratise(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Taux de liquidation proratisé"

        def formula(individu, period):
            return (
                individu('regime_name_taux_de_liquidation', period)
                * individu('regime_name_coefficient_de_proratisation', period)
                )

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
