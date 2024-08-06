"""Régime de base de la fonction publique."""

import numpy as np

from openfisca_core.model_api import *
from openfisca_core.parameters import ParameterNotFound

from openfisca_france_pension.entities import Person
from openfisca_france_pension.regimes.regime import AbstractRegimeEnAnnuites
from openfisca_france_pension.tools import add_vectorial_timedelta, year_
from openfisca_france_pension.variables.hors_regime import TypesRaisonDepartTauxPleinAnticipe


class TypesCategorieActivite(Enum):
    __order__ = 'sedentaire actif super_actif'  # Needed to preserve the enum order in Python 2
    sedentaire = 'Sédentaire'
    actif = "Actif"
    super_actif = "Super actif"


class AbstractRegimeFonctionPublique(AbstractRegimeEnAnnuites):
    name = "Régime de base de la fonction publique"
    variable_prefix = "fonction_publique"
    parameters_prefix = "retraites.secteur_public.pension_civile"

    class ouverture_des_droits_date(Variable):
        value_type = date
        entity = Person
        definition_period = YEAR
        label = "Date à laquelle l'individu atteint l'âge d'ouverture des droits"
        default_value = date(2250, 12, 31)

        def formula_2006(individu, period):
            ouverture_des_droits_date_normale = individu("regime_name_ouverture_des_droits_date_normale", period)

            date_satisfaction_condition_depart_anticipe_parents_trois_enfants = individu("regime_name_date_satisfaction_condition_depart_anticipe_parents_trois_enfants", period)
            depart_anticipe_trois_enfants = individu("regime_name_depart_anticipe_trois_enfants", period)
            date_ouverture_droits_depart_anticipe_trois_enfants = min_(
                ouverture_des_droits_date_normale,
                date_satisfaction_condition_depart_anticipe_parents_trois_enfants
                )
            ouverture_des_droits_carriere_longue_date = min_(
                ouverture_des_droits_date_normale,
                individu('regime_name_ouverture_des_droits_carriere_longue_date', period),
                )

            carriere_longue = individu('regime_name_carriere_longue', period)
            return select(
                [
                    depart_anticipe_trois_enfants,
                    carriere_longue,
                    ],
                [
                    date_ouverture_droits_depart_anticipe_trois_enfants,
                    ouverture_des_droits_carriere_longue_date,
                    ],
                default = ouverture_des_droits_date_normale,
                )

    class actif_a_la_liquidation(Variable):
        value_type = bool
        entity = Person
        definition_period = YEAR
        label = "Est considéré comme actif à la liquiation (a atteint des quinze ans de service sur un emploi de civil actif"

        def formula(individu, period, parameters):
            date_quinze_ans_actif = individu('regime_name_date_quinze_ans_actif', period)
            actif_annee = parameters(period).regime_name.duree_seuil_actif.duree_service_minimale_considere_comme_actif[date_quinze_ans_actif]
            actif = individu('regime_name_nombre_annees_actif', period) >= actif_annee
            return actif

    class ouverture_des_droits_carriere_longue_date(Variable):
        value_type = date
        entity = Person
        definition_period = YEAR
        label = "Date de l'ouverture des droits pour les départs anticipés pour carrière longue"
        default_value = date(2250, 12, 31)

        def formula_2006(individu, period, parameters):
            carriere_longue_seuil_determine_aod = individu('regime_name_carriere_longue_seuil_determine_aod', period)
            date_de_naissance = individu('date_de_naissance', period)
            aod_carriere_longue_2_annee = parameters(period).regime_name.carriere_longue.aod_seuil_2[date_de_naissance].annee
            aod_carriere_longue_15_annee = parameters(period).regime_name.carriere_longue.aod_seuil_15[date_de_naissance].annee
            aod_carriere_longue_1_annee = parameters(period).regime_name.carriere_longue.aod_seuil_1[date_de_naissance].annee
            aod_carriere_longue_2_mois = parameters(period).regime_name.carriere_longue.aod_seuil_2[date_de_naissance].mois
            aod_carriere_longue_15_mois = parameters(period).regime_name.carriere_longue.aod_seuil_15[date_de_naissance].mois
            aod_carriere_longue_1_mois = parameters(period).regime_name.carriere_longue.aod_seuil_1[date_de_naissance].mois
            aod_carriere_longue_annee = select(
                [
                    carriere_longue_seuil_determine_aod == 1,
                    carriere_longue_seuil_determine_aod == 15,
                    carriere_longue_seuil_determine_aod == 2
                    ],
                [
                    aod_carriere_longue_1_annee,
                    aod_carriere_longue_15_annee,
                    aod_carriere_longue_2_annee
                    ],
                )
            aod_carriere_longue_mois = select(
                [
                    carriere_longue_seuil_determine_aod == 1,
                    carriere_longue_seuil_determine_aod == 15,
                    carriere_longue_seuil_determine_aod == 2
                    ],
                [
                    aod_carriere_longue_1_mois,
                    aod_carriere_longue_15_mois,
                    aod_carriere_longue_2_mois
                    ]
                )
            ouverture_des_droits_carriere_longue_date = add_vectorial_timedelta(
                date_de_naissance,
                aod_carriere_longue_annee,
                aod_carriere_longue_mois,
                )

            return ouverture_des_droits_carriere_longue_date

    class ouverture_des_droits_date_normale(Variable):
        value_type = date
        entity = Person
        definition_period = YEAR
        label = "Date de l'ouverture des droits selon l'âge"
        default_value = date(2250, 12, 31)

        def formula(individu, period, parameters):
            date_de_naissance = individu('date_de_naissance', period)
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
            aod_annee = select(
                [
                    actif_a_la_liquidation
                    ],
                [
                    aod_active_annee
                    ],
                default = aod_sedentaire_annee
                )
            aod_mois = select(
                [
                    actif_a_la_liquidation,
                    ],
                [
                    aod_active_mois
                    ],
                default = aod_sedentaire_mois
                )
            ouverture_des_droits_date = add_vectorial_timedelta(date_de_naissance, years = aod_annee, months = aod_mois)

            return ouverture_des_droits_date

    class aod(Variable):
        value_type = int
        entity = Person
        definition_period = YEAR
        label = "Äge d'ouvertue des droits"

        def formula(individu, period, parameters):
            date_de_naissance = individu('date_de_naissance', period)
            aod_active = parameters(period).regime_name.aod_a.age_ouverture_droits_fonction_publique_active_selon_annee_naissance[date_de_naissance]
            aod_sedentaire = parameters(period).regime_name.aod_s.age_ouverture_droits_fonction_publique_sedentaire_selon_annee_naissance[date_de_naissance]
            actif_a_la_liquidation = individu('regime_name_actif_a_la_liquidation', period)
            return where(actif_a_la_liquidation, aod_active, aod_sedentaire)

    class aod_egal_date_depart_anticipe_parent_trois_enfants(Variable):
        value_type = bool
        entity = Person
        definition_period = YEAR
        label = "Condition remplie pour que l'AOD soit égale à la date de satisfaction des conditions pour un départ anticipé au titre de parent de trois enfants"
        default_value = False

        def formula(individu, period):
            nombre_enfants = individu('nombre_enfants', period)
            duree_de_service_effective = individu("regime_name_duree_de_service_effective", period)
            liquidation_date = individu('regime_name_liquidation_date', period)
            annee_satisfaction_condition_depart_anticipe_parents_trois_enfants = individu('regime_name_date_satisfaction_condition_depart_anticipe_parents_trois_enfants', period).astype('datetime64[Y]').astype('int')
            condition_enfant = nombre_enfants >= 3
            condition_service = duree_de_service_effective >= 60
            condition_date = annee_satisfaction_condition_depart_anticipe_parents_trois_enfants < 2012
            condition_date_liquidation = liquidation_date < np.datetime64("2011-07-01")
            return condition_enfant * condition_service * condition_date_liquidation * condition_date

    class coefficient_de_proratisation(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Coefficient de proratisation"

        def formula(individu, period, parameters):
            date_de_naissance = individu('date_de_naissance', period)
            bonification_cpcm = individu('regime_name_bonification_cpcm', period)
            duree_de_service_effective = individu("regime_name_duree_de_service_effective", period)
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
                    (min_(duree_de_service_effective, duree_de_service_requise) + bonification_cpcm)
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
        label = "Date d'atteinte de la durée en tant qu'actif requise pour liquider sa pension en tant qu'actif"
        default_value = date(2250, 12, 31)

        def formula(individu, period):
            last_year = period.last_year
            nombre_annees_actif_annee_courante = individu('regime_name_nombre_annees_actif', period)
            date_actif_annee_precedente = individu('regime_name_date_quinze_ans_actif', last_year)
            date = select(
                [
                    date_actif_annee_precedente < np.datetime64("2250-12-31"),
                    (nombre_annees_actif_annee_courante >= 15) & (date_actif_annee_precedente == np.datetime64("2250-12-31")),
                    (nombre_annees_actif_annee_courante < 15) & (date_actif_annee_precedente == np.datetime64("2250-12-31"))
                    ],
                [
                    date_actif_annee_precedente,
                    np.datetime64(str(period.start)),
                    np.datetime64("2250-12-31")
                    ],
                default = np.datetime64("2250-12-31")
                )
            return date

    class date_quinze_ans_service(Variable):
        value_type = date
        entity = Person
        definition_period = YEAR
        label = "Date d'atteinte des quinze ans d'activité"
        default_value = date(2250, 12, 31)

        def formula(individu, period):
            last_year = period.last_year
            nombre_annees_service_annee_courante = individu('regime_name_duree_de_service_effective', period)
            date_service_annee_precedente = individu('regime_name_date_quinze_ans_service', last_year)
            date = select(
                [
                    date_service_annee_precedente < np.datetime64("2250-12-31"),
                    (nombre_annees_service_annee_courante >= 60) * (date_service_annee_precedente == np.datetime64("2250-12-31")),
                    (nombre_annees_service_annee_courante < 60) * (date_service_annee_precedente == np.datetime64("2250-12-31")),
                    ],
                [
                    date_service_annee_precedente,
                    np.datetime64(str(period.start)),
                    np.datetime64("2250-12-31"),
                    ],
                default = np.datetime64("2250-12-31")
                )
            return date

    class date_satisfaction_condition_depart_anticipe_parents_trois_enfants(Variable):
        value_type = date
        entity = Person
        definition_period = YEAR
        label = "Date à laquelle les deux conditions permettant un départ anticipé pour motif de parent de trois enfant sont satisfaites"
        default_value = date(2250, 12, 31)

        def formula(individu, period):
            date_naissance_enfant = individu('date_naissance_enfant', period)
            date_trois_enfants = date_naissance_enfant  # date de naissance du 3e enfant
            date_quinze_ans_service = individu('regime_name_date_quinze_ans_service', period)
            raison_depart_taux_plein_anticipe = individu('raison_depart_taux_plein_anticipe', period)
            liquidation_date = individu('regime_name_liquidation_date', period)
            return where(
                (raison_depart_taux_plein_anticipe == TypesRaisonDepartTauxPleinAnticipe.famille),
                liquidation_date,
                max_(date_trois_enfants, date_quinze_ans_service),
                )

    class decote_a_date_depart_anticipe_parent_trois_enfants(Variable):
        value_type = bool
        entity = Person
        definition_period = YEAR
        label = "Condition remplie pour que la décote dépende de la date où les condtions pour départ anticipé pour motif de parent de trois enfants sont remplies (et pas de la génération)"
        default_value = False

        def formula(individu, period):
            nombre_enfants = individu('nombre_enfants', period)
            duree_de_service_effective = individu("regime_name_duree_de_service_effective", period)
            ouverture_des_droits_date = individu('regime_name_ouverture_des_droits_date', period)
            liquidation_date = individu('regime_name_liquidation_date', period)
            date_satisfaction_condition_depart_anticipe_parents_trois_enfants = individu('regime_name_date_satisfaction_condition_depart_anticipe_parents_trois_enfants', period)
            condition_date = year_(date_satisfaction_condition_depart_anticipe_parents_trois_enfants) < 2012
            condition_enfant = nombre_enfants >= 3
            condition_service = duree_de_service_effective >= 60
            condition_aod = year_(ouverture_des_droits_date) < 2016
            condition_date_liquidation = liquidation_date < np.datetime64("2011-07-01")
            return condition_enfant * condition_service * condition_aod * condition_date_liquidation * condition_date

    class decote_trimestres(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "decote trimestres"

        def formula_2006(individu, period, parameters):
            date_de_naissance = individu('date_de_naissance', period)
            carriere_longue = individu('regime_name_carriere_longue', period)
            actif_a_la_liquidation = individu('regime_name_actif_a_la_liquidation', period)
            super_actif_a_la_liquidation = individu('regime_name_super_actif_a_la_liquidation', period)
            annee_age_ouverture_droits = year_(individu('regime_name_ouverture_des_droits_date', period))
            conditions_depart_anticipe_parent_trois_enfants = individu('regime_name_decote_a_date_depart_anticipe_parent_trois_enfants', period)
            aad_en_nombre_trimestres_par_rapport_limite_age = parameters(period).regime_name.aad.age_annulation_decote_selon_annee_ouverture_droits_en_nombre_trimestres_par_rapport_limite_age
            reduction_add_en_mois = where(
                # Double condition car cette réduction de l'AAD s'éteint en 2020 et vaut -1 en 2019
                (2019 >= annee_age_ouverture_droits) * (annee_age_ouverture_droits >= 2006),
                # aad_en_nombre_trimestres_par_rapport_limite_age est négatif et non renseigné en 2020 ni avant 2006 exclu
                # d'où le clip pour éviter l'erreur
                3 * aad_en_nombre_trimestres_par_rapport_limite_age[np.clip(annee_age_ouverture_droits, 2006, 2019)],
                0
                )
            aad_en_mois_general = individu("regime_name_limite_d_age", period) * 12 + reduction_add_en_mois
            aad_en_mois_parents_trois_enfants = 65 * 12 + reduction_add_en_mois  # les parents de 3 enfants béénficie de la limite d'âge en vigueur avant la réforme de 2010
            aad_en_mois = where(
                conditions_depart_anticipe_parent_trois_enfants,
                min_(aad_en_mois_parents_trois_enfants, aad_en_mois_general),
                aad_en_mois_general
                )
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
            duree_assurance_requise_super_actifs = duree_assurance_requise_actifs - 4 * 5
            duree_assurance_requise = select(
                [
                    super_actif_a_la_liquidation,
                    actif_a_la_liquidation & not_(super_actif_a_la_liquidation),
                    ],
                [
                    duree_assurance_requise_super_actifs,
                    duree_assurance_requise_actifs,
                    ],
                default = duree_assurance_requise_sedentaires,
                )
            duree_assurance_tous_regimes = individu('duree_assurance_tous_regimes', period)
            decote_trimestres = min_(
                max_(
                    0,
                    min_(
                        trimestres_avant_aad,
                        duree_assurance_requise - duree_assurance_tous_regimes
                        )
                    ),
                20,
                )
            return select(
                [
                    carriere_longue,
                    annee_age_ouverture_droits >= 2006
                    ],
                [
                    0,
                    min_(decote_trimestres, 20)
                    ],
                default = 0
                )

    class decote(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "annee_age_ouverture_droits"

        def formula_2006(individu, period, parameters):
            annee_age_ouverture_droits = year_(individu('regime_name_ouverture_des_droits_date', period))
            decote_trimestres = individu('regime_name_decote_trimestres', period)
            taux_decote = (
                (annee_age_ouverture_droits >= 2006)  # TODO check condtion on 2015 ?
                * parameters(period).regime_name.decote.taux_decote_selon_annee_age_ouverture_droits.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants[
                    np.clip(annee_age_ouverture_droits, 2006, 2015)
                    ]
                )
            return taux_decote * decote_trimestres

    class depart_anticipe_trois_enfants(Variable):
        value_type = bool
        entity = Person
        definition_period = ETERNITY
        label = "Demande de dépar anticipé pour 3 enfants"

        def formula(individu, period, parameters):
            aod_egal_date_depart_anticipe_parent_trois_enfants = individu('regime_name_aod_egal_date_depart_anticipe_parent_trois_enfants', period)
            annee_age_ouverture_droits = year_(individu('regime_name_ouverture_des_droits_date_normale', period))
            raison_depart_taux_plein_anticipe = individu("raison_depart_taux_plein_anticipe", period)
            date_satisfaction_condition_depart_anticipe_parents_trois_enfants = individu('regime_name_date_satisfaction_condition_depart_anticipe_parents_trois_enfants', period)
            condition_aod = annee_age_ouverture_droits < 2016
            condition_decote = year_(date_satisfaction_condition_depart_anticipe_parents_trois_enfants) < 2003

            return (
                aod_egal_date_depart_anticipe_parent_trois_enfants * (condition_aod + condition_decote)
                + (raison_depart_taux_plein_anticipe == TypesRaisonDepartTauxPleinAnticipe.famille)
                )

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
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Durée d'assurance (trimestres validés dans la fonction publique)"

        def formula(individu, period, parameters):
            duree_assurance_annuelle = individu("regime_name_duree_assurance_annuelle", period)
            duree_assurance_annee_precedente = individu("regime_name_duree_assurance_validee", period.last_year)
            # hack to avoid infinite recursion depth loop
            if all((duree_assurance_annuelle == 0.0) & (duree_assurance_annee_precedente == 0.0)):
                return individu.empty_array()

            annee_de_liquidation = individu('regime_name_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
            return where(
                annee_de_liquidation == period.start.year,
                round_(duree_assurance_annee_precedente + duree_assurance_annuelle),  # On arrondi l'année de la liquidation
                duree_assurance_annee_precedente + duree_assurance_annuelle,
                )

    class duree_de_service_effective(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Durée de service (trimestres cotisés dans la fonction publique) hors bonification obtenue à la liquidation"

        def formula(individu, period, parameters):
            duree_de_service_annuelle = individu("regime_name_duree_de_service_annuelle", period)
            duree_de_service_annee_precedente = individu("regime_name_duree_de_service_effective", period.last_year)
            # hack to avoid infinite recursion depth loop
            if all((duree_de_service_annuelle == 0.0) & (duree_de_service_annee_precedente == 0.0)):
                return individu.empty_array()

            annee_de_liquidation = individu('regime_name_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
            return where(
                annee_de_liquidation == period.start.year,
                round_(
                    duree_de_service_annee_precedente
                    + duree_de_service_annuelle
                    ),  # On arrondi l'année de la liquidation
                duree_de_service_annee_precedente + duree_de_service_annuelle
                )

    class duree_de_service_actif(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Durée de service en catégorie active (trimestres cotisés dans la fonction publique active)"

        def formula(individu, period, parameters):
            duree_de_service_actif_annuelle = individu("regime_name_duree_de_service_actif_annuelle", period)
            duree_de_service_actif_annee_precedente = individu("regime_name_duree_de_service_actif", period.last_year)
            # TODO: hack to avoid infinite recursion depth loop
            if all((duree_de_service_actif_annuelle == 0.0) & (duree_de_service_actif_annee_precedente == 0.0)):
                return individu.empty_array()

            annee_de_liquidation = individu('regime_name_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
            return where(
                annee_de_liquidation == period.start.year,
                round_(
                    duree_de_service_actif_annee_precedente
                    + duree_de_service_actif_annuelle
                    ),  # On arrondi l'année de la liquidation
                duree_de_service_actif_annee_precedente + duree_de_service_actif_annuelle
                )

    class duree_de_service_actif_annuelle(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Durée de service dans la fonction publique au service actif"

    class duree_de_service_annuelle(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Durée de service annuelle dans la fonction publique hors rachat et bonification non attribuable à une année"

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
        label = "Durée de service cotisée dans la fonction publique hors rachat et bonification dans l'année"

    class duree_de_service_rachetee_annuelle(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Durée de service rachetée (années d'études) dans la fonction publique hors rachat et bonification dans l'année"

    class duree_de_service_super_actif(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Durée de service en catégorie super active (trimestres cotisés dans la fonction publique active)"

        def formula(individu, period, parameters):
            duree_de_service_super_actif_annuelle = individu("regime_name_duree_de_service_super_actif_annuelle", period)
            duree_de_service_super_actif_annee_precedente = individu("regime_name_duree_de_service_super_actif", period.last_year)
            # TODO: hack to avoid infinite recursion depth loop
            if all((duree_de_service_super_actif_annuelle == 0.0) & (duree_de_service_super_actif_annee_precedente == 0.0)):
                return individu.empty_array()

            annee_de_liquidation = individu('regime_name_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
            return where(
                annee_de_liquidation == period.start.year,
                round_(
                    duree_de_service_super_actif_annee_precedente
                    + duree_de_service_super_actif_annuelle
                    ),  # On arrondi l'année de la liquidation
                duree_de_service_super_actif_annee_precedente + duree_de_service_super_actif_annuelle
                )

    class duree_de_service_super_actif_annuelle(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Durée de service dans la fonction publique en catégorie super actif"

    class duree_assurance_cotisee_seuil_bas(Variable):
        value_type = int
        entity = Person
        definition_period = ETERNITY
        label = "Durée d'assurance cotisée tous régimes (trimestres cotisés tous régimes confondus) avant le seuil minimum pour partir pour motif RACL"

        def formula_1994(individu, period, parameters):
            liquidation_date = individu('regime_name_liquidation_date', period)
            annee_de_naissance = (
                individu('date_de_naissance', period).astype('datetime64[Y]').astype(int) + 1970
                )
            annees_de_naissance_distinctes = np.unique(
                annee_de_naissance[liquidation_date >= np.datetime64(period.start)]
                )
            duree_assurance_cotisee_16 = individu.empty_array()
            for _annee_de_naissance in sorted(annees_de_naissance_distinctes):
                filter = annee_de_naissance == _annee_de_naissance
                duree_assurance_cotisee_16[filter] = individu('fonction_publique_duree_de_service_effective', str(_annee_de_naissance + 16))[filter]

            return duree_assurance_cotisee_16

    class duree_assurance_cotisee_seuil_haut(Variable):
        value_type = int
        entity = Person
        definition_period = ETERNITY
        label = "Durée d'assurance cotisée tous régimes (trimestres cotisés tous régimes confondus) avant le seuil maximum pour partir pour motif RACL"

        def formula_1994(individu, period, parameters):
            liquidation_date = individu('regime_name_liquidation_date', period)
            annee_de_naissance = (
                individu('date_de_naissance', period).astype('datetime64[Y]').astype(int) + 1970
                )
            annees_de_naissance_distinctes = np.unique(
                annee_de_naissance[liquidation_date >= np.datetime64(period.start)]
                )
            duree_assurance_cotisee_20 = individu.empty_array()
            for _annee_de_naissance in sorted(annees_de_naissance_distinctes):
                filter = annee_de_naissance == _annee_de_naissance
                duree_assurance_cotisee_20[filter] = individu('fonction_publique_duree_de_service_effective', str(_annee_de_naissance + 16))[filter]
            return duree_assurance_cotisee_20

    class limite_d_age(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Limite d'âge"

        def formula(individu, period, parameters):
            date_de_naissance = individu('date_de_naissance', period)
            actif_a_la_liquidation = individu('regime_name_actif_a_la_liquidation', period)
            super_actif_a_la_liquidation = individu('regime_name_super_actif_a_la_liquidation', period)

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
                actif_a_la_liquidation | super_actif_a_la_liquidation,
                limite_age_actif - 5 * super_actif_a_la_liquidation,
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
            nombre_enfants_nes_avant_2004 = individu('regime_name_nombre_enfants_nes_avant_2004', period)
            majoration_par_enfant_pr_2004 = parameters(period).regime_name.bonification_enfant.nombre_trimestres_par_enfant_bonification.after_2004_01_01
            nombre_enfants_nes_apres_2004 = individu('nombre_enfants', period) - nombre_enfants_nes_avant_2004
            majoration = majoration_par_enfant_pr_2004 * nombre_enfants_nes_apres_2004
            sexe = individu('sexe', period)
            est_a_la_fonction_publique = (
                individu('fonction_publique_liquidation_date', period)
                < individu('regime_general_cnav_liquidation_date', period)
                )
            return where(sexe * est_a_la_fonction_publique, majoration, 0)

    class majoration_duree_assurance(Variable):
        value_type = float
        entity = Person
        definition_period = ETERNITY
        label = "Majoration de duree d'assurance"
        definition_period = YEAR

        def formula(individu, period):
            return (
                individu('regime_name_majoration_duree_assurance_enfant', period)
                + individu('regime_name_majoration_duree_assurance_autre', period)
                + individu('regime_name_bonification_cpcm', period)
                )

    class bonification_cpcm_depaysement(Variable):
        value_type = float
        entity = Person
        definition_period = ETERNITY
        label = "Bonification du code des pensions civiles et militaires liée au dépaysement (compte pour la durée d'assurance et la durée de service/durée liquidable)"

    class bonification_cpcm_enfant(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Bonification du code des pensions civiles et militaires liée aux enfants (compte pour la durée d'assurance et la durée de service/durée liquidable)"

        def formula_2004(individu, period, parameters):
            bonification_par_enfant_av_2004 = parameters(period).regime_name.bonification_enfant.nombre_trimestres_par_enfant_bonification.before_2004_01_01
            nombre_enfants_nes_avant_2004 = individu('regime_name_nombre_enfants_nes_avant_2004', period)
            bonification_cpcm = bonification_par_enfant_av_2004 * nombre_enfants_nes_avant_2004
            sexe = individu('sexe', period)

            est_a_la_fonction_publique = (
                individu('regime_name_liquidation_date', period)
                < individu('regime_general_cnav_liquidation_date', period)
                )
            # TODO; père qui s'arrête au moins 2 mois
            return where(sexe * est_a_la_fonction_publique, bonification_cpcm, 0)

        def formula_1949(individu, period, parameters):
            bonification_par_enfant_av_2004 = parameters(period).regime_name.bonification_enfant.nombre_trimestres_par_enfant_bonification.before_2004_01_01
            nombre_enfants = individu('nombre_enfants', period)
            bonification_cpcm = bonification_par_enfant_av_2004 * nombre_enfants
            sexe = individu('sexe', period)
            return where(sexe, bonification_cpcm, 0)

    class bonification_cpcm(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Bonification du code des pensions civiles et militaires (compte pour la durée d'assurance et la durée de service/durée liquidable)"

        def formula_2004(individu, period):
            return individu('regime_name_bonification_cpcm_enfant', period) + individu('regime_name_bonification_cpcm_depaysement', period)

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
            duree_de_service_effective = individu("fonction_publique_duree_de_service_effective", period)
            annee_age_ouverture_droits = year_(individu('regime_name_ouverture_des_droits_date', period))
            decote = individu("regime_name_decote", period)

            service_public = parameters(period).regime_name
            minimum_garanti = service_public.minimum_garanti
            points_moins_40_ans = minimum_garanti.points_moins_40_ans[liquidation_date]
            points_plus_15_ans = minimum_garanti.points_plus_15_ans[liquidation_date]
            annee_moins_40_ans = minimum_garanti.annee_moins_40_ans[liquidation_date]
            part_fixe = service_public.minimum_garanti.part_valeur_indice_majore[liquidation_date]
            indice_majore = service_public.minimum_garanti.valeur_indice_maj[liquidation_date]
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
            last_year = period.last_year
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

            # TODO passer pr des dates
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

    class super_actif_a_la_liquidation(Variable):
        value_type = bool
        entity = Person
        definition_period = YEAR
        label = "Est considéré comme super actif à la liquiation (a atteint la durée de service requise sur un emploi de civil actif insalubre ou roulant"

        # TODO: missing variables date_vingt_cinq_ans_actif nombre_annees_super_actif
        # def formula(individu, period, parameters):
        #     date_vingt_cinq_ans_actif = individu('regime_name_date_vingt_cinq_ans_actif', period)
        #     super_actif_duree_requise = parameters(period).regime_name.duree_seuil_super_actif.duree_service_minimale_considere_comme_super_actif[date_vingt_cinq_ans_actif]
        #     super_actif = individu('regime_name_nombre_annees_super_actif', period) >= super_actif_duree_requise
        #     return actif

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

    class carriere_longue_seuil_determine_aod(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "L'âge d'ouverture des droit des personnes pouvant bénéficier du dispositif RACL dépend de l'âge de début de cotisation"

        # TODO: transformer en Enum
        def formula(individu, period, parameters):
            carriere_longue = parameters(period).regime_name.carriere_longue
            date_de_naissance = individu('date_de_naissance', period)
            naissance_mois = date_de_naissance.astype('datetime64[M]').astype(int) % 12 + 1
            duree_assurance_cotisee_avant_16_ans = individu('regime_name_duree_assurance_cotisee_seuil_bas', period)
            duree_assurance_cotisee_avant_20_ans = individu('regime_name_duree_assurance_cotisee_seuil_haut', period)
            duree_assurance_cotisee_tous_regimes = individu('duree_assurance_cotisee_tous_regimes', period)
            duree_assurance_seuil_1 = carriere_longue.duree_assurance_seuil_1[date_de_naissance]
            duree_assurance_seuil_15 = carriere_longue.duree_assurance_seuil_15[date_de_naissance]
            nbr_min_trimestres_debut_annee = carriere_longue.nbr_min_trimestres_debut_annee[date_de_naissance]
            nbr_min_trimestres_fin_annee = carriere_longue.nbr_min_trimestres_fin_annee[date_de_naissance]
            trims_requis_selon_mois_naissance = where(
                naissance_mois < 10,
                nbr_min_trimestres_debut_annee,
                nbr_min_trimestres_fin_annee
                )
            condition_duree_cotisee_minimale = select(
                [
                    (duree_assurance_cotisee_avant_16_ans >= trims_requis_selon_mois_naissance) * (duree_assurance_cotisee_tous_regimes > duree_assurance_seuil_1),
                    (duree_assurance_cotisee_avant_16_ans >= trims_requis_selon_mois_naissance) * (duree_assurance_cotisee_tous_regimes > duree_assurance_seuil_15),
                    duree_assurance_cotisee_avant_20_ans >= trims_requis_selon_mois_naissance
                    ],
                [
                    1,
                    15,
                    2
                    ],
                default = 0
                )
            return condition_duree_cotisee_minimale

    class carriere_longue(Variable):
        value_type = bool
        entity = Person
        definition_period = YEAR
        label = "Départ anticipé possible pour motif de carriere longue"

        def formula(individu, period, parameters):
            date_de_naissance = individu('date_de_naissance', period)
            carriere_longue = parameters(period).regime_name.carriere_longue
            duree_assurance_cotisee_tous_regimes = individu('duree_assurance_cotisee_tous_regimes', period)
            duree_assurance_seuil_1 = carriere_longue.duree_assurance_seuil_1[date_de_naissance]
            duree_assurance_seuil_15 = carriere_longue.duree_assurance_seuil_15[date_de_naissance]
            duree_assurance_seuil_2 = carriere_longue.duree_assurance_seuil_2[date_de_naissance]
            carriere_longue_seuil_determine_aod = individu('regime_name_carriere_longue_seuil_determine_aod', period)
            raison_depart_taux_plein_anticipe = individu('raison_depart_taux_plein_anticipe', period)
            condition_duree_minimale = select(
                [
                    carriere_longue_seuil_determine_aod == 2,
                    carriere_longue_seuil_determine_aod == 15,
                    carriere_longue_seuil_determine_aod == 1
                    ],
                [
                    duree_assurance_seuil_2,
                    duree_assurance_seuil_15,
                    duree_assurance_seuil_1
                    ],
                default = 1000
                )

            condition_assurance_total = duree_assurance_cotisee_tous_regimes > condition_duree_minimale
            return condition_assurance_total + (raison_depart_taux_plein_anticipe == TypesRaisonDepartTauxPleinAnticipe.carriere_longue)

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
    #     """ Calcul des cotisations passées par année"""
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


class RegimeFonctionPublique(AbstractRegimeFonctionPublique):
    name = "Régime de base de la fonction publique"
    variable_prefix = "fonction_publique"
    parameters_prefix = "retraites.secteur_public.pension_civile"


class RegimeCnracl(AbstractRegimeFonctionPublique):
    name = 'Régime de la Caisse nationale des agents des collectivités locales'
    variable_prefix = 'cnracl'
    parameters_prefix = 'retraites.secteur_public.pension_civile'
