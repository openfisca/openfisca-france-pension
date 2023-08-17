"""Abstract regimes definition."""
from openfisca_core.model_api import *
from openfisca_core.errors.variable_not_found_error import VariableNotFoundError
from openfisca_france_pension.entities import Person

def revalorise(variable_31_decembre_annee_precedente, variable_originale, annee_de_liquidation, revalorisation, period):
    return select([annee_de_liquidation > period.start.year, annee_de_liquidation == period.start.year, annee_de_liquidation < period.start.year], [0, variable_originale, variable_31_decembre_annee_precedente * revalorisation])
'Régime de base de la fonction publique.'
import numpy as np
from openfisca_core.model_api import *
from openfisca_core.parameters import ParameterNotFound
from openfisca_france_pension.entities import Person
from openfisca_france_pension.regimes.regime import AbstractRegimeEnAnnuites
from openfisca_france_pension.tools import add_vectorial_timedelta, year_
from openfisca_france_pension.variables.hors_regime import TypesRaisonDepartTauxPleinAnticipe

class TypesCategorieActivite(Enum):
    __order__ = 'sedentaire actif super_actif'
    sedentaire = 'Sédentaire'
    actif = 'Actif'
    super_actif = 'Super actif'

class cnracl_actif_a_la_liquidation(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = 'Est considéré comme actif à la liquiation (a atteint des quinze ans de service sur un emploi de civil actif'

    def formula(individu, period, parameters):
        date_quinze_ans_actif = individu('cnracl_date_quinze_ans_actif', period)
        actif_annee = parameters(period).retraites.secteur_public.pension_civile.duree_seuil_actif.duree_service_minimale_considere_comme_actif[date_quinze_ans_actif]
        actif = individu('cnracl_nombre_annees_actif', period) >= actif_annee
        return actif

class cnracl_aod(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Äge d'ouvertue des droits"

    def formula(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        aod_active = parameters(period).retraites.secteur_public.pension_civile.aod_a.age_ouverture_droits_fonction_publique_active_selon_annee_naissance[date_de_naissance]
        aod_sedentaire = parameters(period).retraites.secteur_public.pension_civile.aod_s.age_ouverture_droits_fonction_publique_sedentaire_selon_annee_naissance[date_de_naissance]
        actif_a_la_liquidation = individu('cnracl_actif_a_la_liquidation', period)
        return where(actif_a_la_liquidation, aod_active, aod_sedentaire)

class cnracl_aod_egal_date_depart_anticipe_parent_trois_enfants(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "Condition remplie pour que l'AOD soit égale à la date de satisfaction des conditions pour un départ anticipé au titre de parent de trois enfants"
    default_value = False

    def formula(individu, period):
        nombre_enfants = individu('nombre_enfants', period)
        duree_de_service_effective = individu('cnracl_duree_de_service_effective', period)
        liquidation_date = individu('cnracl_liquidation_date', period)
        annee_satisfaction_condition_depart_anticipe_parents_trois_enfants = individu('cnracl_date_satisfaction_condition_depart_anticipe_parents_trois_enfants', period).astype('datetime64[Y]').astype('int')
        condition_enfant = nombre_enfants >= 3
        condition_service = duree_de_service_effective >= 60
        condition_date = annee_satisfaction_condition_depart_anticipe_parents_trois_enfants < 2012
        condition_date_liquidation = liquidation_date < np.datetime64('2011-07-01')
        return condition_enfant * condition_service * condition_date_liquidation * condition_date

class cnracl_bonification_cpcm(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Bonification du code des pensions civiles et militaires (compte pour la durée d'assurance et la durée de service/durée liquidable)"

    def formula_2004(individu, period):
        return individu('cnracl_bonification_cpcm_enfant', period) + individu('cnracl_bonification_cpcm_depaysement', period)

class cnracl_bonification_cpcm_depaysement(Variable):
    value_type = float
    entity = Person
    definition_period = ETERNITY
    label = "Bonification du code des pensions civiles et militaires liée au dépaysement (compte pour la durée d'assurance et la durée de service/durée liquidable)"

class cnracl_bonification_cpcm_enfant(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Bonification du code des pensions civiles et militaires liée aux enfants (compte pour la durée d'assurance et la durée de service/durée liquidable)"

    def formula_2004(individu, period, parameters):
        bonification_par_enfant_av_2004 = parameters(period).retraites.secteur_public.pension_civile.bonification_enfant.nombre_trimestres_par_enfant_bonification.before_2004_01_01
        nombre_enfants_nes_avant_2004 = individu('cnracl_nombre_enfants_nes_avant_2004', period)
        bonification_cpcm = bonification_par_enfant_av_2004 * nombre_enfants_nes_avant_2004
        sexe = individu('sexe', period)
        est_a_la_fonction_publique = individu('cnracl_liquidation_date', period) < individu('regime_general_cnav_liquidation_date', period)
        return where(sexe * est_a_la_fonction_publique, bonification_cpcm, 0)

    def formula_1949(individu, period, parameters):
        bonification_par_enfant_av_2004 = parameters(period).retraites.secteur_public.pension_civile.bonification_enfant.nombre_trimestres_par_enfant_bonification.before_2004_01_01
        nombre_enfants = individu('nombre_enfants', period)
        bonification_cpcm = bonification_par_enfant_av_2004 * nombre_enfants
        sexe = individu('sexe', period)
        return where(sexe, bonification_cpcm, 0)

class cnracl_carriere_longue(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = 'Départ anticipé possible pour motif de carriere longue'

    def formula(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        carriere_longue = parameters(period).retraites.secteur_public.pension_civile.carriere_longue
        duree_assurance_cotisee_tous_regimes = individu('duree_assurance_cotisee_tous_regimes', period)
        duree_assurance_seuil_1 = carriere_longue.duree_assurance_seuil_1[date_de_naissance]
        duree_assurance_seuil_15 = carriere_longue.duree_assurance_seuil_15[date_de_naissance]
        duree_assurance_seuil_2 = carriere_longue.duree_assurance_seuil_2[date_de_naissance]
        carriere_longue_seuil_determine_aod = individu('cnracl_carriere_longue_seuil_determine_aod', period)
        raison_depart_taux_plein_anticipe = individu('raison_depart_taux_plein_anticipe', period)
        condition_duree_minimale = select([carriere_longue_seuil_determine_aod == 2, carriere_longue_seuil_determine_aod == 15, carriere_longue_seuil_determine_aod == 1], [duree_assurance_seuil_2, duree_assurance_seuil_15, duree_assurance_seuil_1], default=1000)
        condition_assurance_total = duree_assurance_cotisee_tous_regimes > condition_duree_minimale
        return condition_assurance_total + (raison_depart_taux_plein_anticipe == TypesRaisonDepartTauxPleinAnticipe.carriere_longue)

class cnracl_carriere_longue_seuil_determine_aod(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "L'âge d'ouverture des droit des personnes pouvant bénéficier du dispositif RACL dépend de l'âge de début de cotisation"

    def formula(individu, period, parameters):
        carriere_longue = parameters(period).retraites.secteur_public.pension_civile.carriere_longue
        date_de_naissance = individu('date_de_naissance', period)
        naissance_mois = date_de_naissance.astype('datetime64[M]').astype(int) % 12 + 1
        duree_assurance_cotisee_avant_16_ans = individu('cnracl_duree_assurance_cotisee_seuil_bas', period)
        duree_assurance_cotisee_avant_20_ans = individu('cnracl_duree_assurance_cotisee_seuil_haut', period)
        duree_assurance_cotisee_tous_regimes = individu('duree_assurance_cotisee_tous_regimes', period)
        duree_assurance_seuil_1 = carriere_longue.duree_assurance_seuil_1[date_de_naissance]
        duree_assurance_seuil_15 = carriere_longue.duree_assurance_seuil_15[date_de_naissance]
        nbr_min_trimestres_debut_annee = carriere_longue.nbr_min_trimestres_debut_annee[date_de_naissance]
        nbr_min_trimestres_fin_annee = carriere_longue.nbr_min_trimestres_fin_annee[date_de_naissance]
        trims_requis_selon_mois_naissance = where(naissance_mois < 10, nbr_min_trimestres_debut_annee, nbr_min_trimestres_fin_annee)
        condition_duree_cotisee_minimale = select([(duree_assurance_cotisee_avant_16_ans >= trims_requis_selon_mois_naissance) * (duree_assurance_cotisee_tous_regimes > duree_assurance_seuil_1), (duree_assurance_cotisee_avant_16_ans >= trims_requis_selon_mois_naissance) * (duree_assurance_cotisee_tous_regimes > duree_assurance_seuil_15), duree_assurance_cotisee_avant_20_ans >= trims_requis_selon_mois_naissance], [1, 15, 2], default=0)
        return condition_duree_cotisee_minimale

class cnracl_categorie_activite(Variable):
    value_type = Enum
    possible_values = TypesCategorieActivite
    default_value = TypesCategorieActivite.sedentaire
    entity = Person
    label = "Catégorie d'activité des emplois publics"
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

class cnracl_coefficient_de_proratisation(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Coefficient de proratisation'

    def formula(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        bonification_cpcm = individu('cnracl_bonification_cpcm', period)
        duree_de_service_effective = individu('cnracl_duree_de_service_effective', period)
        super_actif = False
        bonification_du_cinquieme = super_actif * min_(duree_de_service_effective / 5, 5)
        duree_de_service_requise = parameters(period).retraites.secteur_public.pension_civile.trimtp.nombre_trimestres_cibles_taux_plein_par_generation[date_de_naissance]
        coefficient_de_proratisation = max_(min_(1, (duree_de_service_effective + bonification_du_cinquieme) / duree_de_service_requise), min_(80 / 75, (min_(duree_de_service_effective, duree_de_service_requise) + bonification_cpcm) / duree_de_service_requise))
        return coefficient_de_proratisation

class cnracl_cotisation(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'cotisation retraite employeur'

    def formula(individu, period, parameters):
        NotImplementedError

class cnracl_date_quinze_ans_actif(Variable):
    value_type = date
    entity = Person
    definition_period = YEAR
    label = "Date d'atteinte de la durée en tant qu'actif requise pour liquider sa pension en tant qu'actif"
    default_value = date(2250, 12, 31)

    def formula(individu, period):
        last_year = period.last_year
        nombre_annees_actif_annee_courante = individu('cnracl_nombre_annees_actif', period)
        date_actif_annee_precedente = individu('cnracl_date_quinze_ans_actif', last_year)
        date = select([date_actif_annee_precedente < np.datetime64('2250-12-31'), (nombre_annees_actif_annee_courante >= 15) & (date_actif_annee_precedente == np.datetime64('2250-12-31')), (nombre_annees_actif_annee_courante < 15) & (date_actif_annee_precedente == np.datetime64('2250-12-31'))], [date_actif_annee_precedente, np.datetime64(str(period.start)), np.datetime64('2250-12-31')], default=np.datetime64('2250-12-31'))
        return date

class cnracl_date_quinze_ans_service(Variable):
    value_type = date
    entity = Person
    definition_period = YEAR
    label = "Date d'atteinte des quinze ans d'activité"
    default_value = date(2250, 12, 31)

    def formula(individu, period):
        last_year = period.last_year
        nombre_annees_service_annee_courante = individu('cnracl_duree_de_service_effective', period)
        date_service_annee_precedente = individu('cnracl_date_quinze_ans_service', last_year)
        date = select([date_service_annee_precedente < np.datetime64('2250-12-31'), (nombre_annees_service_annee_courante >= 60) * (date_service_annee_precedente == np.datetime64('2250-12-31')), (nombre_annees_service_annee_courante < 60) * (date_service_annee_precedente == np.datetime64('2250-12-31'))], [date_service_annee_precedente, np.datetime64(str(period.start)), np.datetime64('2250-12-31')], default=np.datetime64('2250-12-31'))
        return date

class cnracl_date_satisfaction_condition_depart_anticipe_parents_trois_enfants(Variable):
    value_type = date
    entity = Person
    definition_period = YEAR
    label = 'Date à laquelle les deux conditions permettant un départ anticipé pour motif de parent de trois enfant sont satisfaites'
    default_value = date(2250, 12, 31)

    def formula(individu, period):
        date_naissance_enfant = individu('date_naissance_enfant', period)
        date_trois_enfants = date_naissance_enfant
        date_quinze_ans_service = individu('cnracl_date_quinze_ans_service', period)
        raison_depart_taux_plein_anticipe = individu('raison_depart_taux_plein_anticipe', period)
        liquidation_date = individu('cnracl_liquidation_date', period)
        return where(raison_depart_taux_plein_anticipe == TypesRaisonDepartTauxPleinAnticipe.famille, liquidation_date, max_(date_trois_enfants, date_quinze_ans_service))

class cnracl_decote(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'annee_age_ouverture_droits'

    def formula_2006(individu, period, parameters):
        annee_age_ouverture_droits = year_(individu('cnracl_ouverture_des_droits_date', period))
        decote_trimestres = individu('cnracl_decote_trimestres', period)
        taux_decote = (annee_age_ouverture_droits >= 2006) * parameters(period).retraites.secteur_public.pension_civile.decote.taux_decote_selon_annee_age_ouverture_droits.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants[np.clip(annee_age_ouverture_droits, 2006, 2015)]
        return taux_decote * decote_trimestres

class cnracl_decote_a_date_depart_anticipe_parent_trois_enfants(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = 'Condition remplie pour que la décote dépende de la date où les condtions pour départ anticipé pour motif de parent de trois enfants sont remplies (et pas de la génération)'
    default_value = False

    def formula(individu, period):
        nombre_enfants = individu('nombre_enfants', period)
        duree_de_service_effective = individu('cnracl_duree_de_service_effective', period)
        ouverture_des_droits_date = individu('cnracl_ouverture_des_droits_date', period)
        liquidation_date = individu('cnracl_liquidation_date', period)
        date_satisfaction_condition_depart_anticipe_parents_trois_enfants = individu('cnracl_date_satisfaction_condition_depart_anticipe_parents_trois_enfants', period)
        condition_date = year_(date_satisfaction_condition_depart_anticipe_parents_trois_enfants) < 2012
        condition_enfant = nombre_enfants >= 3
        condition_service = duree_de_service_effective >= 60
        condition_aod = year_(ouverture_des_droits_date) < 2016
        condition_date_liquidation = liquidation_date < np.datetime64('2011-07-01')
        return condition_enfant * condition_service * condition_aod * condition_date_liquidation * condition_date

class cnracl_decote_trimestres(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'decote trimestres'

    def formula_2006(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        carriere_longue = individu('cnracl_carriere_longue', period)
        actif_a_la_liquidation = individu('cnracl_actif_a_la_liquidation', period)
        super_actif_a_la_liquidation = individu('cnracl_super_actif_a_la_liquidation', period)
        annee_age_ouverture_droits = year_(individu('cnracl_ouverture_des_droits_date', period))
        conditions_depart_anticipe_parent_trois_enfants = individu('cnracl_decote_a_date_depart_anticipe_parent_trois_enfants', period)
        aad_en_nombre_trimestres_par_rapport_limite_age = parameters(period).retraites.secteur_public.pension_civile.aad.age_annulation_decote_selon_annee_ouverture_droits_en_nombre_trimestres_par_rapport_limite_age
        reduction_add_en_mois = where((2019 >= annee_age_ouverture_droits) * (annee_age_ouverture_droits >= 2006), 3 * aad_en_nombre_trimestres_par_rapport_limite_age[np.clip(annee_age_ouverture_droits, 2006, 2019)], 0)
        aad_en_mois_general = individu('cnracl_limite_d_age', period) * 12 + reduction_add_en_mois
        aad_en_mois_parents_trois_enfants = 65 * 12 + reduction_add_en_mois
        aad_en_mois = where(conditions_depart_anticipe_parent_trois_enfants, min_(aad_en_mois_parents_trois_enfants, aad_en_mois_general), aad_en_mois_general)
        age_en_mois_a_la_liquidation = (individu('cnracl_liquidation_date', period) - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        trimestres_avant_aad = max_(0, np.ceil((aad_en_mois - age_en_mois_a_la_liquidation) / 3))
        duree_assurance_requise_sedentaires = parameters(period).retraites.secteur_public.pension_civile.trimtp.nombre_trimestres_cibles_taux_plein_par_generation[date_de_naissance]
        duree_assurance_requise_actifs = parameters(period).retraites.secteur_public.pension_civile.trimtp_a.nombre_trimestres_cibles_taux_plein_par_generation_actifs[date_de_naissance]
        duree_assurance_requise_super_actifs = duree_assurance_requise_actifs - 4 * 5
        duree_assurance_requise = select([super_actif_a_la_liquidation, actif_a_la_liquidation & not_(super_actif_a_la_liquidation)], [duree_assurance_requise_super_actifs, duree_assurance_requise_actifs], default=duree_assurance_requise_sedentaires)
        duree_assurance_tous_regimes = individu('duree_assurance_tous_regimes', period)
        decote_trimestres = min_(max_(0, min_(trimestres_avant_aad, duree_assurance_requise - duree_assurance_tous_regimes)), 20)
        return select([carriere_longue, annee_age_ouverture_droits >= 2006], [0, min_(decote_trimestres, 20)], default=0)

class cnracl_depart_anticipe_trois_enfants(Variable):
    value_type = bool
    entity = Person
    definition_period = ETERNITY
    label = 'Demande de dépar anticipé pour 3 enfants'

    def formula(individu, period, parameters):
        aod_egal_date_depart_anticipe_parent_trois_enfants = individu('cnracl_aod_egal_date_depart_anticipe_parent_trois_enfants', period)
        annee_age_ouverture_droits = year_(individu('cnracl_ouverture_des_droits_date_normale', period))
        raison_depart_taux_plein_anticipe = individu('raison_depart_taux_plein_anticipe', period)
        date_satisfaction_condition_depart_anticipe_parents_trois_enfants = individu('cnracl_date_satisfaction_condition_depart_anticipe_parents_trois_enfants', period)
        condition_aod = annee_age_ouverture_droits < 2016
        condition_decote = year_(date_satisfaction_condition_depart_anticipe_parents_trois_enfants) < 2003
        return aod_egal_date_depart_anticipe_parent_trois_enfants * (condition_aod + condition_decote) + (raison_depart_taux_plein_anticipe == TypesRaisonDepartTauxPleinAnticipe.famille)

class cnracl_dernier_indice_atteint(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Dernier indice connu dans la fonction publique'

    def formula_1970(individu, period, parameters):
        salaire_de_base = individu('cnracl_salaire_de_base', period)
        taux_de_prime = individu('taux_de_prime', period)
        valeur_point_indice = parameters(period).marche_travail.remuneration_dans_fonction_publique.indicefp.point_indice_en_euros
        dernier_indice = where(salaire_de_base > 0, salaire_de_base / (1 + taux_de_prime) / valeur_point_indice, individu('cnracl_dernier_indice_atteint', period.last_year))
        return dernier_indice

class cnracl_duree_assurance(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance (trimestres validés dans la fonction publique)"

    def formula(individu, period, parameters):
        duree_assurance_validee = individu('cnracl_duree_assurance_validee', period)
        annee_de_liquidation = individu('cnracl_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        majoration_duree_assurance = individu('cnracl_majoration_duree_assurance', period)
        return where(annee_de_liquidation == period.start.year, round_(duree_assurance_validee + majoration_duree_assurance), duree_assurance_validee)

class cnracl_duree_assurance_accident_du_travail_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance au titre des accidents du travail (en trimestres validés l'année considérée)"

class cnracl_duree_assurance_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance annuelle (trimestres validés dans la fonction publique hors majoration)"

    def formula(individu, period, parameters):
        quotite_de_travail = np.clip(individu('cnracl_quotite_de_travail', period), 0.0, 1.0)
        duree_de_service_cotisee_annuelle = individu('cnracl_duree_de_service_cotisee_annuelle', period)
        duree_de_service_cotisee_annuelle = where(quotite_de_travail == 0, 0, duree_de_service_cotisee_annuelle)
        duree_assurance_cotisee_annuelle = duree_de_service_cotisee_annuelle / (quotite_de_travail + (quotite_de_travail == 0))
        duree_assurance_rachetee_annuelle = individu('cnracl_duree_de_service_rachetee_annuelle', period)
        duree_assurance_service_national_annuelle = individu('cnracl_duree_assurance_service_national_annuelle', period)
        return np.clip(duree_assurance_cotisee_annuelle + duree_assurance_rachetee_annuelle + duree_assurance_service_national_annuelle, 0, 4)

class cnracl_duree_assurance_autre_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance au titre des autres périodes assimilées (en trimestres validés l'année considérée)"

class cnracl_duree_assurance_chomage_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance au titre du chômage (en trimestres cotisés jusqu'à l'année considérée)"

class cnracl_duree_assurance_cotisee_seuil_bas(Variable):
    value_type = int
    entity = Person
    definition_period = ETERNITY
    label = "Durée d'assurance cotisée tous régimes (trimestres cotisés tous régimes confondus) avant le seuil minimum pour partir pour motif RACL"

    def formula_1994(individu, period, parameters):
        liquidation_date = individu('cnracl_liquidation_date', period)
        annee_de_naissance = individu('date_de_naissance', period).astype('datetime64[Y]').astype(int) + 1970
        annees_de_naissance_distinctes = np.unique(annee_de_naissance[liquidation_date >= np.datetime64(period.start)])
        duree_assurance_cotisee_16 = individu.empty_array()
        for _annee_de_naissance in sorted(annees_de_naissance_distinctes):
            filter = annee_de_naissance == _annee_de_naissance
            duree_assurance_cotisee_16[filter] = individu('fonction_publique_duree_de_service_effective', str(_annee_de_naissance + 16))[filter]
        return duree_assurance_cotisee_16

class cnracl_duree_assurance_cotisee_seuil_haut(Variable):
    value_type = int
    entity = Person
    definition_period = ETERNITY
    label = "Durée d'assurance cotisée tous régimes (trimestres cotisés tous régimes confondus) avant le seuil maximum pour partir pour motif RACL"

    def formula_1994(individu, period, parameters):
        liquidation_date = individu('cnracl_liquidation_date', period)
        annee_de_naissance = individu('date_de_naissance', period).astype('datetime64[Y]').astype(int) + 1970
        annees_de_naissance_distinctes = np.unique(annee_de_naissance[liquidation_date >= np.datetime64(period.start)])
        duree_assurance_cotisee_20 = individu.empty_array()
        for _annee_de_naissance in sorted(annees_de_naissance_distinctes):
            filter = annee_de_naissance == _annee_de_naissance
            duree_assurance_cotisee_20[filter] = individu('fonction_publique_duree_de_service_effective', str(_annee_de_naissance + 16))[filter]
        return duree_assurance_cotisee_20

class cnracl_duree_assurance_invalidite_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance au titre de l'invalidté (en trimestres validés l'année considérée)"

class cnracl_duree_assurance_maladie_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance au titre de la maladie (en trimestres validés l'année considérée)"

class cnracl_duree_assurance_periode_assimilee(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance pour période assimilée cumullée "

class cnracl_duree_assurance_rachetee_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance rachetée l'année considérée)"

class cnracl_duree_assurance_service_national_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance au titre du service national (en trimestres validés l'année considérée)"

class cnracl_duree_assurance_validee(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance (trimestres validés dans la fonction publique)"

    def formula(individu, period, parameters):
        duree_assurance_annuelle = individu('cnracl_duree_assurance_annuelle', period)
        duree_assurance_annee_precedente = individu('cnracl_duree_assurance_validee', period.last_year)
        if all((duree_assurance_annuelle == 0.0) & (duree_assurance_annee_precedente == 0.0)):
            return individu.empty_array()
        annee_de_liquidation = individu('cnracl_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        return where(annee_de_liquidation == period.start.year, round_(duree_assurance_annee_precedente + duree_assurance_annuelle), duree_assurance_annee_precedente + duree_assurance_annuelle)

class cnracl_duree_de_service_actif(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Durée de service en catégorie active (trimestres cotisés dans la fonction publique active)'

    def formula(individu, period, parameters):
        duree_de_service_actif_annuelle = individu('cnracl_duree_de_service_actif_annuelle', period)
        duree_de_service_actif_annee_precedente = individu('cnracl_duree_de_service_actif', period.last_year)
        if all((duree_de_service_actif_annuelle == 0.0) & (duree_de_service_actif_annee_precedente == 0.0)):
            return individu.empty_array()
        annee_de_liquidation = individu('cnracl_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        return where(annee_de_liquidation == period.start.year, round_(duree_de_service_actif_annee_precedente + duree_de_service_actif_annuelle), duree_de_service_actif_annee_precedente + duree_de_service_actif_annuelle)

class cnracl_duree_de_service_actif_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Durée de service dans la fonction publique au service actif'

class cnracl_duree_de_service_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Durée de service annuelle dans la fonction publique hors rachat et bonification non attribuable à une année'

    def formula(individu, period, parameters):
        return np.clip(individu('cnracl_duree_de_service_cotisee_annuelle', period) + individu('cnracl_duree_de_service_rachetee_annuelle', period) + individu('cnracl_duree_assurance_service_national_annuelle', period), 0, 4)

class cnracl_duree_de_service_cotisee_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée de service cotisée dans la fonction publique hors rachat et bonification dans l'année"

class cnracl_duree_de_service_effective(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Durée de service (trimestres cotisés dans la fonction publique) hors bonification obtenue à la liquidation'

    def formula(individu, period, parameters):
        duree_de_service_annuelle = individu('cnracl_duree_de_service_annuelle', period)
        duree_de_service_annee_precedente = individu('cnracl_duree_de_service_effective', period.last_year)
        if all((duree_de_service_annuelle == 0.0) & (duree_de_service_annee_precedente == 0.0)):
            return individu.empty_array()
        annee_de_liquidation = individu('cnracl_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        return where(annee_de_liquidation == period.start.year, round_(duree_de_service_annee_precedente + duree_de_service_annuelle), duree_de_service_annee_precedente + duree_de_service_annuelle)

class cnracl_duree_de_service_rachetee_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée de service rachetée (années d'études) dans la fonction publique hors rachat et bonification dans l'année"

class cnracl_duree_de_service_super_actif(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Durée de service en catégorie super active (trimestres cotisés dans la fonction publique active)'

    def formula(individu, period, parameters):
        duree_de_service_super_actif_annuelle = individu('cnracl_duree_de_service_super_actif_annuelle', period)
        duree_de_service_super_actif_annee_precedente = individu('cnracl_duree_de_service_super_actif', period.last_year)
        if all((duree_de_service_super_actif_annuelle == 0.0) & (duree_de_service_super_actif_annee_precedente == 0.0)):
            return individu.empty_array()
        annee_de_liquidation = individu('cnracl_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        return where(annee_de_liquidation == period.start.year, round_(duree_de_service_super_actif_annee_precedente + duree_de_service_super_actif_annuelle), duree_de_service_super_actif_annee_precedente + duree_de_service_super_actif_annuelle)

class cnracl_duree_de_service_super_actif_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Durée de service dans la fonction publique en catégorie super actif'

class cnracl_limite_d_age(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Limite d'âge"

    def formula(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        actif_a_la_liquidation = individu('cnracl_actif_a_la_liquidation', period)
        super_actif_a_la_liquidation = individu('cnracl_super_actif_a_la_liquidation', period)
        limite_age_active = parameters(period).retraites.secteur_public.pension_civile.la_a.age_limite_fonction_publique_active_selon_annee_naissance
        limite_age_sedentaire = parameters(period).retraites.secteur_public.pension_civile.la_s.age_limite_fonction_publique_sedentaire_selon_annee_naissance
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
        return where(actif_a_la_liquidation | super_actif_a_la_liquidation, limite_age_actif - 5 * super_actif_a_la_liquidation, limite_age_sedentaire)

class cnracl_liquidation_date(Variable):
    value_type = date
    entity = Person
    definition_period = ETERNITY
    label = 'Date de liquidation'
    default_value = date(2250, 12, 31)

class cnracl_majoration_duree_assurance(Variable):
    value_type = float
    entity = Person
    definition_period = ETERNITY
    label = "Majoration de duree d'assurance"
    definition_period = YEAR

    def formula(individu, period):
        return individu('cnracl_majoration_duree_assurance_enfant', period) + individu('cnracl_majoration_duree_assurance_autre', period) + individu('cnracl_bonification_cpcm', period)

class cnracl_majoration_duree_assurance_autre(Variable):
    value_type = float
    entity = Person
    definition_period = ETERNITY
    label = "Majoration de durée d'assurance autre que celle attribuée au motif des enfants"

class cnracl_majoration_duree_assurance_enfant(Variable):
    value_type = float
    entity = Person
    definition_period = ETERNITY
    label = 'Bonification pour enfants selon le code des pensions civiles et militaires'
    definition_period = YEAR

    def formula_2004(individu, period, parameters):
        nombre_enfants_nes_avant_2004 = individu('cnracl_nombre_enfants_nes_avant_2004', period)
        majoration_par_enfant_pr_2004 = parameters(period).retraites.secteur_public.pension_civile.bonification_enfant.nombre_trimestres_par_enfant_bonification.after_2004_01_01
        nombre_enfants_nes_apres_2004 = individu('nombre_enfants', period) - nombre_enfants_nes_avant_2004
        majoration = majoration_par_enfant_pr_2004 * nombre_enfants_nes_apres_2004
        sexe = individu('sexe', period)
        est_a_la_fonction_publique = individu('fonction_publique_liquidation_date', period) < individu('regime_general_cnav_liquidation_date', period)
        return where(sexe * est_a_la_fonction_publique, majoration, 0)

class cnracl_majoration_pension(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Majoration de pension'
    reference = ['https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000025076852/', 'https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI000006400888/']

    def formula_1965(individu, period):
        nombre_enfants = individu('nombre_enfants', period)
        pension_brute = individu('cnracl_pension_brute', period)
        return pension_brute * (0.1 * (nombre_enfants >= 3) + 0.05 * max_(nombre_enfants - 3, 0))

class cnracl_majoration_pension_au_31_decembre(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Majoration de pension au 31 décembre'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('cnracl_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(annee_de_liquidation > period.start.year):
            return individu.empty_array()
        last_year = period.last_year
        majoration_pension_au_31_decembre_annee_precedente = individu('cnracl_majoration_pension_au_31_decembre', last_year)
        revalorisation = parameters(period).retraites.secteur_public.pension_civile.revalorisation_pension_au_31_decembre
        majoration_pension = individu('cnracl_majoration_pension', period)
        return revalorise(majoration_pension_au_31_decembre_annee_precedente, majoration_pension, annee_de_liquidation, revalorisation, period)

class cnracl_minimum_garanti(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Minimum garanti de la fonction publique'
    reference = 'Loi 75-1242 du 27 décembre 1975'

    def formula_1976(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        liquidation_date = individu('cnracl_liquidation_date', period)
        annee_de_liquidation = individu('cnracl_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        duree_de_service_effective = individu('fonction_publique_duree_de_service_effective', period)
        annee_age_ouverture_droits = year_(individu('cnracl_ouverture_des_droits_date', period))
        decote = individu('cnracl_decote', period)
        service_public = parameters(period).retraites.secteur_public.pension_civile
        minimum_garanti = service_public.minimum_garanti
        points_moins_40_ans = minimum_garanti.points_moins_40_ans[liquidation_date]
        points_plus_15_ans = minimum_garanti.points_plus_15_ans[liquidation_date]
        annee_moins_40_ans = minimum_garanti.annee_moins_40_ans[liquidation_date]
        part_fixe = service_public.minimum_garanti.part_valeur_indice_majore[liquidation_date]
        indice_majore = service_public.minimum_garanti.valeur_indice_maj[liquidation_date]
        pt_indice = parameters(period).marche_travail.remuneration_dans_fonction_publique.indicefp.point_indice_en_euros
        duree_assurance_requise = service_public.trimtp.nombre_trimestres_cibles_taux_plein_par_generation[date_de_naissance]
        coefficient_moins_15_ans = duree_de_service_effective / duree_assurance_requise
        coefficient_plus_15_ans = part_fixe + max_(duree_de_service_effective - 4 * 15, 0) * points_plus_15_ans
        coefficient_plus_30_ans = part_fixe + max_(annee_moins_40_ans - 4 * 15, 0) * points_plus_15_ans + max_(duree_de_service_effective - annee_moins_40_ans, 0) * points_moins_40_ans
        coefficient_plus_40_ans = 1
        condition_absence_decote = decote == 0
        condition_duree = duree_de_service_effective > duree_assurance_requise
        condition_age_ouverture_des_droits = (annee_age_ouverture_droits < 2011) * (annee_de_liquidation >= 2011)
        post_condition = where((annee_de_liquidation < 2011) + condition_age_ouverture_des_droits, True, condition_duree + condition_absence_decote)
        return post_condition * indice_majore * pt_indice * select([duree_de_service_effective < 60, duree_de_service_effective < annee_moins_40_ans, duree_de_service_effective < 160, duree_de_service_effective >= 160], [coefficient_moins_15_ans, coefficient_plus_15_ans, coefficient_plus_30_ans, coefficient_plus_40_ans])

class cnracl_nombre_annees_actif(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Nombre d'années travaillant en tant qu'actif"

    def formula(individu, period):
        annee_de_liquidation = individu('cnracl_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(period.start.year > annee_de_liquidation):
            return individu.empty_array()
        last_year = period.last_year
        nombre_annees_actif_annee_precedente = individu('cnracl_nombre_annees_actif', last_year)
        categorie_activite = individu('cnracl_categorie_activite', period)
        return nombre_annees_actif_annee_precedente + 1 * (categorie_activite == TypesCategorieActivite.actif)

class cnracl_nombre_enfants_nes_avant_2004(Variable):
    value_type = int
    entity = Person
    label = "Nombre d'enfants nés avant 2004"
    definition_period = ETERNITY

class cnracl_ouverture_des_droits_carriere_longue_date(Variable):
    value_type = date
    entity = Person
    definition_period = YEAR
    label = "Date de l'ouverture des droits pour les départs anticipés pour carrière longue"
    default_value = date(2250, 12, 31)

    def formula_2006(individu, period, parameters):
        carriere_longue_seuil_determine_aod = individu('cnracl_carriere_longue_seuil_determine_aod', period)
        date_de_naissance = individu('date_de_naissance', period)
        aod_carriere_longue_2_annee = parameters(period).retraites.secteur_public.pension_civile.carriere_longue.aod_seuil_2[date_de_naissance].annee
        aod_carriere_longue_15_annee = parameters(period).retraites.secteur_public.pension_civile.carriere_longue.aod_seuil_15[date_de_naissance].annee
        aod_carriere_longue_1_annee = parameters(period).retraites.secteur_public.pension_civile.carriere_longue.aod_seuil_1[date_de_naissance].annee
        aod_carriere_longue_2_mois = parameters(period).retraites.secteur_public.pension_civile.carriere_longue.aod_seuil_2[date_de_naissance].mois
        aod_carriere_longue_15_mois = parameters(period).retraites.secteur_public.pension_civile.carriere_longue.aod_seuil_15[date_de_naissance].mois
        aod_carriere_longue_1_mois = parameters(period).retraites.secteur_public.pension_civile.carriere_longue.aod_seuil_1[date_de_naissance].mois
        aod_carriere_longue_annee = select([carriere_longue_seuil_determine_aod == 1, carriere_longue_seuil_determine_aod == 15, carriere_longue_seuil_determine_aod == 2], [aod_carriere_longue_1_annee, aod_carriere_longue_15_annee, aod_carriere_longue_2_annee])
        aod_carriere_longue_mois = select([carriere_longue_seuil_determine_aod == 1, carriere_longue_seuil_determine_aod == 15, carriere_longue_seuil_determine_aod == 2], [aod_carriere_longue_1_mois, aod_carriere_longue_15_mois, aod_carriere_longue_2_mois])
        ouverture_des_droits_carriere_longue_date = add_vectorial_timedelta(date_de_naissance, aod_carriere_longue_annee, aod_carriere_longue_mois)
        return ouverture_des_droits_carriere_longue_date

class cnracl_ouverture_des_droits_date(Variable):
    value_type = date
    entity = Person
    definition_period = YEAR
    label = "Date à laquelle l'individu atteint l'âge d'ouverture des droits"
    default_value = date(2250, 12, 31)

    def formula_2006(individu, period):
        ouverture_des_droits_date_normale = individu('cnracl_ouverture_des_droits_date_normale', period)
        date_satisfaction_condition_depart_anticipe_parents_trois_enfants = individu('cnracl_date_satisfaction_condition_depart_anticipe_parents_trois_enfants', period)
        depart_anticipe_trois_enfants = individu('cnracl_depart_anticipe_trois_enfants', period)
        date_ouverture_droits_depart_anticipe_trois_enfants = min_(ouverture_des_droits_date_normale, date_satisfaction_condition_depart_anticipe_parents_trois_enfants)
        ouverture_des_droits_carriere_longue_date = min_(ouverture_des_droits_date_normale, individu('cnracl_ouverture_des_droits_carriere_longue_date', period))
        carriere_longue = individu('cnracl_carriere_longue', period)
        return select([depart_anticipe_trois_enfants, carriere_longue], [date_ouverture_droits_depart_anticipe_trois_enfants, ouverture_des_droits_carriere_longue_date], default=ouverture_des_droits_date_normale)

class cnracl_ouverture_des_droits_date_normale(Variable):
    value_type = date
    entity = Person
    definition_period = YEAR
    label = "Date de l'ouverture des droits selon l'âge"
    default_value = date(2250, 12, 31)

    def formula(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        aod_active = parameters(period).retraites.secteur_public.pension_civile.aod_a.age_ouverture_droits_fonction_publique_active_selon_annee_naissance
        aod_sedentaire = parameters(period).retraites.secteur_public.pension_civile.aod_s.age_ouverture_droits_fonction_publique_sedentaire_selon_annee_naissance
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
        actif_a_la_liquidation = individu('cnracl_actif_a_la_liquidation', period)
        aod_annee = select([actif_a_la_liquidation], [aod_active_annee], default=aod_sedentaire_annee)
        aod_mois = select([actif_a_la_liquidation], [aod_active_mois], default=aod_sedentaire_mois)
        ouverture_des_droits_date = add_vectorial_timedelta(date_de_naissance, years=aod_annee, months=aod_mois)
        return ouverture_des_droits_date

class cnracl_pension(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension'

    def formula(individu, period):
        pension_brute = individu('cnracl_pension_brute', period)
        majoration_pension = individu('cnracl_majoration_pension', period)
        pension_maximale = individu('cnracl_salaire_de_reference', period)
        return min_(pension_brute + majoration_pension, pension_maximale)

class cnracl_pension_au_31_decembre(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension'

    def formula(individu, period):
        pension_brute_au_31_decembre = individu('cnracl_pension_brute_au_31_decembre', period)
        majoration_pension_au_31_decembre = individu('cnracl_majoration_pension_au_31_decembre', period)
        return pension_brute_au_31_decembre + majoration_pension_au_31_decembre

class cnracl_pension_avant_minimum_et_plafonnement(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension brute'

    def formula(individu, period):
        coefficient_de_proratisation = individu('cnracl_coefficient_de_proratisation', period)
        salaire_de_reference = individu('cnracl_salaire_de_reference', period)
        taux_de_liquidation = individu('cnracl_taux_de_liquidation', period)
        return coefficient_de_proratisation * salaire_de_reference * taux_de_liquidation

class cnracl_pension_brute(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension brute'

    def formula(individu, period, parameters):
        pension_avant_minimum_et_plafonnement = individu('cnracl_pension_avant_minimum_et_plafonnement', period)
        minimum_garanti = individu('cnracl_minimum_garanti', period)
        return max_(pension_avant_minimum_et_plafonnement, minimum_garanti)

class cnracl_pension_brute_au_31_decembre(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension brute au 31 décembre'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('cnracl_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(period.start.year < annee_de_liquidation):
            return individu.empty_array()
        last_year = period.last_year
        pension_brute_au_31_decembre_annee_precedente = individu('cnracl_pension_brute_au_31_decembre', last_year)
        revalorisation = parameters(period).retraites.secteur_public.pension_civile.revalorisation_pension_au_31_decembre
        pension_brute = individu('cnracl_pension_brute', period)
        return revalorise(pension_brute_au_31_decembre_annee_precedente, pension_brute, annee_de_liquidation, revalorisation, period)

class cnracl_pension_servie(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension servie'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('cnracl_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(annee_de_liquidation > period.start.year):
            return individu.empty_array()
        last_year = period.last_year
        pension_au_31_decembre_annee_precedente = individu('cnracl_pension_au_31_decembre', last_year)
        revalorisation = parameters(period).retraites.secteur_public.pension_civile.revalarisation_pension_servie
        pension = individu('cnracl_pension_au_31_decembre', period)
        return revalorise(pension_au_31_decembre_annee_precedente, pension, annee_de_liquidation, revalorisation, period)

class cnracl_quotite_de_travail(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Quotité de travail'
    default_value = 1.0

class cnracl_salaire_de_base(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Salaire de base (salaire brut)'
    set_input = set_input_divide_by_period

class cnracl_salaire_de_reference(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Traitement de référence'

    def formula(individu, period, parameters):
        dernier_indice_atteint = individu('cnracl_dernier_indice_atteint', period)
        try:
            valeur_point_indice = parameters(period).marche_travail.remuneration_dans_fonction_publique.indicefp.point_indice_en_euros
        except ParameterNotFound:
            valeur_point_indice = 0
        return dernier_indice_atteint * valeur_point_indice

class cnracl_super_actif_a_la_liquidation(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = 'Est considéré comme super actif à la liquiation (a atteint la durée de service requise sur un emploi de civil actif insalubre ou roulant'

class cnracl_surcote(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Surcote'

    def formula_2004(individu, period, parameters):
        surcote_trimestres = individu('cnracl_surcote_trimestres', period)
        actif_a_la_liquidation = individu('cnracl_actif_a_la_liquidation', period)
        taux_surcote = parameters(period).retraites.secteur_public.pension_civile.surcote.taux_surcote_par_trimestre
        return where(actif_a_la_liquidation, 0, taux_surcote * surcote_trimestres)

class cnracl_surcote_trimestres(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Trimestres surcote avant application du minimum garanti'

    def formula_2004(individu, period, parameters):
        liquidation_date = individu('cnracl_liquidation_date', period)
        date_de_naissance = individu('date_de_naissance', period)
        aod_sedentaire = parameters(period).retraites.secteur_public.pension_civile.aod_s.age_ouverture_droits_fonction_publique_sedentaire_selon_annee_naissance
        if period.start.year <= 2011:
            aod_sedentaire_annee = aod_sedentaire.before_1951_07_01.annee
            aod_sedentaire_mois = 0
        else:
            aod_sedentaire_annee = aod_sedentaire[date_de_naissance].annee
            aod_sedentaire_mois = aod_sedentaire[date_de_naissance].mois
        age_en_mois_a_la_liquidation = (individu('cnracl_liquidation_date', period) - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        arrondi_trimestres_aod = np.ceil if period.start.year < 2009 else np.floor
        trimestres_apres_aod = max_(0, (age_en_mois_a_la_liquidation - (12 * aod_sedentaire_annee + aod_sedentaire_mois)) / 3)
        duree_assurance_requise = parameters(period).retraites.secteur_public.pension_civile.trimtp.nombre_trimestres_cibles_taux_plein_par_generation[date_de_naissance]
        trimestres_apres_instauration_surcote = (individu('cnracl_liquidation_date', period) - np.datetime64('2004-01-01')).astype('timedelta64[M]').astype(int) / 3
        duree_assurance_excedentaire = individu('duree_assurance_tous_regimes', period) - duree_assurance_requise
        trimestres_surcote = max_(0, arrondi_trimestres_aod(min_(min_(trimestres_apres_instauration_surcote, trimestres_apres_aod), duree_assurance_excedentaire)))
        return where(liquidation_date < np.datetime64('2010-11-11'), min_(trimestres_surcote, 20), trimestres_surcote)

class cnracl_taux_de_liquidation(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Taux de liquidation de la pension'

    def formula(individu, period, parameters):
        decote = individu('cnracl_decote', period)
        surcote = individu('cnracl_surcote', period)
        taux_plein = parameters(period).retraites.secteur_public.pension_civile.taux_plein.taux_plein
        return taux_plein * (1 - decote + surcote)

class cnracl_taux_de_liquidation_proratise(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Taux de liquidation proratisé'

    def formula(individu, period):
        return individu('cnracl_taux_de_liquidation', period) * individu('cnracl_coefficient_de_proratisation', period)

class fonction_publique_actif_a_la_liquidation(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = 'Est considéré comme actif à la liquiation (a atteint des quinze ans de service sur un emploi de civil actif'

    def formula(individu, period, parameters):
        date_quinze_ans_actif = individu('fonction_publique_date_quinze_ans_actif', period)
        actif_annee = parameters(period).retraites.secteur_public.pension_civile.duree_seuil_actif.duree_service_minimale_considere_comme_actif[date_quinze_ans_actif]
        actif = individu('fonction_publique_nombre_annees_actif', period) >= actif_annee
        return actif

class fonction_publique_aod(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Äge d'ouvertue des droits"

    def formula(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        aod_active = parameters(period).retraites.secteur_public.pension_civile.aod_a.age_ouverture_droits_fonction_publique_active_selon_annee_naissance[date_de_naissance]
        aod_sedentaire = parameters(period).retraites.secteur_public.pension_civile.aod_s.age_ouverture_droits_fonction_publique_sedentaire_selon_annee_naissance[date_de_naissance]
        actif_a_la_liquidation = individu('fonction_publique_actif_a_la_liquidation', period)
        return where(actif_a_la_liquidation, aod_active, aod_sedentaire)

class fonction_publique_aod_egal_date_depart_anticipe_parent_trois_enfants(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "Condition remplie pour que l'AOD soit égale à la date de satisfaction des conditions pour un départ anticipé au titre de parent de trois enfants"
    default_value = False

    def formula(individu, period):
        nombre_enfants = individu('nombre_enfants', period)
        duree_de_service_effective = individu('fonction_publique_duree_de_service_effective', period)
        liquidation_date = individu('fonction_publique_liquidation_date', period)
        annee_satisfaction_condition_depart_anticipe_parents_trois_enfants = individu('fonction_publique_date_satisfaction_condition_depart_anticipe_parents_trois_enfants', period).astype('datetime64[Y]').astype('int')
        condition_enfant = nombre_enfants >= 3
        condition_service = duree_de_service_effective >= 60
        condition_date = annee_satisfaction_condition_depart_anticipe_parents_trois_enfants < 2012
        condition_date_liquidation = liquidation_date < np.datetime64('2011-07-01')
        return condition_enfant * condition_service * condition_date_liquidation * condition_date

class fonction_publique_bonification_cpcm(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Bonification du code des pensions civiles et militaires (compte pour la durée d'assurance et la durée de service/durée liquidable)"

    def formula_2004(individu, period):
        return individu('fonction_publique_bonification_cpcm_enfant', period) + individu('fonction_publique_bonification_cpcm_depaysement', period)

class fonction_publique_bonification_cpcm_depaysement(Variable):
    value_type = float
    entity = Person
    definition_period = ETERNITY
    label = "Bonification du code des pensions civiles et militaires liée au dépaysement (compte pour la durée d'assurance et la durée de service/durée liquidable)"

class fonction_publique_bonification_cpcm_enfant(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Bonification du code des pensions civiles et militaires liée aux enfants (compte pour la durée d'assurance et la durée de service/durée liquidable)"

    def formula_2004(individu, period, parameters):
        bonification_par_enfant_av_2004 = parameters(period).retraites.secteur_public.pension_civile.bonification_enfant.nombre_trimestres_par_enfant_bonification.before_2004_01_01
        nombre_enfants_nes_avant_2004 = individu('fonction_publique_nombre_enfants_nes_avant_2004', period)
        bonification_cpcm = bonification_par_enfant_av_2004 * nombre_enfants_nes_avant_2004
        sexe = individu('sexe', period)
        est_a_la_fonction_publique = individu('fonction_publique_liquidation_date', period) < individu('regime_general_cnav_liquidation_date', period)
        return where(sexe * est_a_la_fonction_publique, bonification_cpcm, 0)

    def formula_1949(individu, period, parameters):
        bonification_par_enfant_av_2004 = parameters(period).retraites.secteur_public.pension_civile.bonification_enfant.nombre_trimestres_par_enfant_bonification.before_2004_01_01
        nombre_enfants = individu('nombre_enfants', period)
        bonification_cpcm = bonification_par_enfant_av_2004 * nombre_enfants
        sexe = individu('sexe', period)
        return where(sexe, bonification_cpcm, 0)

class fonction_publique_carriere_longue(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = 'Départ anticipé possible pour motif de carriere longue'

    def formula(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        carriere_longue = parameters(period).retraites.secteur_public.pension_civile.carriere_longue
        duree_assurance_cotisee_tous_regimes = individu('duree_assurance_cotisee_tous_regimes', period)
        duree_assurance_seuil_1 = carriere_longue.duree_assurance_seuil_1[date_de_naissance]
        duree_assurance_seuil_15 = carriere_longue.duree_assurance_seuil_15[date_de_naissance]
        duree_assurance_seuil_2 = carriere_longue.duree_assurance_seuil_2[date_de_naissance]
        carriere_longue_seuil_determine_aod = individu('fonction_publique_carriere_longue_seuil_determine_aod', period)
        raison_depart_taux_plein_anticipe = individu('raison_depart_taux_plein_anticipe', period)
        condition_duree_minimale = select([carriere_longue_seuil_determine_aod == 2, carriere_longue_seuil_determine_aod == 15, carriere_longue_seuil_determine_aod == 1], [duree_assurance_seuil_2, duree_assurance_seuil_15, duree_assurance_seuil_1], default=1000)
        condition_assurance_total = duree_assurance_cotisee_tous_regimes > condition_duree_minimale
        return condition_assurance_total + (raison_depart_taux_plein_anticipe == TypesRaisonDepartTauxPleinAnticipe.carriere_longue)

class fonction_publique_carriere_longue_seuil_determine_aod(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "L'âge d'ouverture des droit des personnes pouvant bénéficier du dispositif RACL dépend de l'âge de début de cotisation"

    def formula(individu, period, parameters):
        carriere_longue = parameters(period).retraites.secteur_public.pension_civile.carriere_longue
        date_de_naissance = individu('date_de_naissance', period)
        naissance_mois = date_de_naissance.astype('datetime64[M]').astype(int) % 12 + 1
        duree_assurance_cotisee_avant_16_ans = individu('fonction_publique_duree_assurance_cotisee_seuil_bas', period)
        duree_assurance_cotisee_avant_20_ans = individu('fonction_publique_duree_assurance_cotisee_seuil_haut', period)
        duree_assurance_cotisee_tous_regimes = individu('duree_assurance_cotisee_tous_regimes', period)
        duree_assurance_seuil_1 = carriere_longue.duree_assurance_seuil_1[date_de_naissance]
        duree_assurance_seuil_15 = carriere_longue.duree_assurance_seuil_15[date_de_naissance]
        nbr_min_trimestres_debut_annee = carriere_longue.nbr_min_trimestres_debut_annee[date_de_naissance]
        nbr_min_trimestres_fin_annee = carriere_longue.nbr_min_trimestres_fin_annee[date_de_naissance]
        trims_requis_selon_mois_naissance = where(naissance_mois < 10, nbr_min_trimestres_debut_annee, nbr_min_trimestres_fin_annee)
        condition_duree_cotisee_minimale = select([(duree_assurance_cotisee_avant_16_ans >= trims_requis_selon_mois_naissance) * (duree_assurance_cotisee_tous_regimes > duree_assurance_seuil_1), (duree_assurance_cotisee_avant_16_ans >= trims_requis_selon_mois_naissance) * (duree_assurance_cotisee_tous_regimes > duree_assurance_seuil_15), duree_assurance_cotisee_avant_20_ans >= trims_requis_selon_mois_naissance], [1, 15, 2], default=0)
        return condition_duree_cotisee_minimale

class fonction_publique_categorie_activite(Variable):
    value_type = Enum
    possible_values = TypesCategorieActivite
    default_value = TypesCategorieActivite.sedentaire
    entity = Person
    label = "Catégorie d'activité des emplois publics"
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

class fonction_publique_coefficient_de_proratisation(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Coefficient de proratisation'

    def formula(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        bonification_cpcm = individu('fonction_publique_bonification_cpcm', period)
        duree_de_service_effective = individu('fonction_publique_duree_de_service_effective', period)
        super_actif = False
        bonification_du_cinquieme = super_actif * min_(duree_de_service_effective / 5, 5)
        duree_de_service_requise = parameters(period).retraites.secteur_public.pension_civile.trimtp.nombre_trimestres_cibles_taux_plein_par_generation[date_de_naissance]
        coefficient_de_proratisation = max_(min_(1, (duree_de_service_effective + bonification_du_cinquieme) / duree_de_service_requise), min_(80 / 75, (min_(duree_de_service_effective, duree_de_service_requise) + bonification_cpcm) / duree_de_service_requise))
        return coefficient_de_proratisation

class fonction_publique_cotisation(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'cotisation retraite employeur'

    def formula(individu, period, parameters):
        NotImplementedError

class fonction_publique_date_quinze_ans_actif(Variable):
    value_type = date
    entity = Person
    definition_period = YEAR
    label = "Date d'atteinte de la durée en tant qu'actif requise pour liquider sa pension en tant qu'actif"
    default_value = date(2250, 12, 31)

    def formula(individu, period):
        last_year = period.last_year
        nombre_annees_actif_annee_courante = individu('fonction_publique_nombre_annees_actif', period)
        date_actif_annee_precedente = individu('fonction_publique_date_quinze_ans_actif', last_year)
        date = select([date_actif_annee_precedente < np.datetime64('2250-12-31'), (nombre_annees_actif_annee_courante >= 15) & (date_actif_annee_precedente == np.datetime64('2250-12-31')), (nombre_annees_actif_annee_courante < 15) & (date_actif_annee_precedente == np.datetime64('2250-12-31'))], [date_actif_annee_precedente, np.datetime64(str(period.start)), np.datetime64('2250-12-31')], default=np.datetime64('2250-12-31'))
        return date

class fonction_publique_date_quinze_ans_service(Variable):
    value_type = date
    entity = Person
    definition_period = YEAR
    label = "Date d'atteinte des quinze ans d'activité"
    default_value = date(2250, 12, 31)

    def formula(individu, period):
        last_year = period.last_year
        nombre_annees_service_annee_courante = individu('fonction_publique_duree_de_service_effective', period)
        date_service_annee_precedente = individu('fonction_publique_date_quinze_ans_service', last_year)
        date = select([date_service_annee_precedente < np.datetime64('2250-12-31'), (nombre_annees_service_annee_courante >= 60) * (date_service_annee_precedente == np.datetime64('2250-12-31')), (nombre_annees_service_annee_courante < 60) * (date_service_annee_precedente == np.datetime64('2250-12-31'))], [date_service_annee_precedente, np.datetime64(str(period.start)), np.datetime64('2250-12-31')], default=np.datetime64('2250-12-31'))
        return date

class fonction_publique_date_satisfaction_condition_depart_anticipe_parents_trois_enfants(Variable):
    value_type = date
    entity = Person
    definition_period = YEAR
    label = 'Date à laquelle les deux conditions permettant un départ anticipé pour motif de parent de trois enfant sont satisfaites'
    default_value = date(2250, 12, 31)

    def formula(individu, period):
        date_naissance_enfant = individu('date_naissance_enfant', period)
        date_trois_enfants = date_naissance_enfant
        date_quinze_ans_service = individu('fonction_publique_date_quinze_ans_service', period)
        raison_depart_taux_plein_anticipe = individu('raison_depart_taux_plein_anticipe', period)
        liquidation_date = individu('fonction_publique_liquidation_date', period)
        return where(raison_depart_taux_plein_anticipe == TypesRaisonDepartTauxPleinAnticipe.famille, liquidation_date, max_(date_trois_enfants, date_quinze_ans_service))

class fonction_publique_decote(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'annee_age_ouverture_droits'

    def formula_2006(individu, period, parameters):
        annee_age_ouverture_droits = year_(individu('fonction_publique_ouverture_des_droits_date', period))
        decote_trimestres = individu('fonction_publique_decote_trimestres', period)
        taux_decote = (annee_age_ouverture_droits >= 2006) * parameters(period).retraites.secteur_public.pension_civile.decote.taux_decote_selon_annee_age_ouverture_droits.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants[np.clip(annee_age_ouverture_droits, 2006, 2015)]
        return taux_decote * decote_trimestres

class fonction_publique_decote_a_date_depart_anticipe_parent_trois_enfants(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = 'Condition remplie pour que la décote dépende de la date où les condtions pour départ anticipé pour motif de parent de trois enfants sont remplies (et pas de la génération)'
    default_value = False

    def formula(individu, period):
        nombre_enfants = individu('nombre_enfants', period)
        duree_de_service_effective = individu('fonction_publique_duree_de_service_effective', period)
        ouverture_des_droits_date = individu('fonction_publique_ouverture_des_droits_date', period)
        liquidation_date = individu('fonction_publique_liquidation_date', period)
        date_satisfaction_condition_depart_anticipe_parents_trois_enfants = individu('fonction_publique_date_satisfaction_condition_depart_anticipe_parents_trois_enfants', period)
        condition_date = year_(date_satisfaction_condition_depart_anticipe_parents_trois_enfants) < 2012
        condition_enfant = nombre_enfants >= 3
        condition_service = duree_de_service_effective >= 60
        condition_aod = year_(ouverture_des_droits_date) < 2016
        condition_date_liquidation = liquidation_date < np.datetime64('2011-07-01')
        return condition_enfant * condition_service * condition_aod * condition_date_liquidation * condition_date

class fonction_publique_decote_trimestres(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'decote trimestres'

    def formula_2006(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        carriere_longue = individu('fonction_publique_carriere_longue', period)
        actif_a_la_liquidation = individu('fonction_publique_actif_a_la_liquidation', period)
        super_actif_a_la_liquidation = individu('fonction_publique_super_actif_a_la_liquidation', period)
        annee_age_ouverture_droits = year_(individu('fonction_publique_ouverture_des_droits_date', period))
        conditions_depart_anticipe_parent_trois_enfants = individu('fonction_publique_decote_a_date_depart_anticipe_parent_trois_enfants', period)
        aad_en_nombre_trimestres_par_rapport_limite_age = parameters(period).retraites.secteur_public.pension_civile.aad.age_annulation_decote_selon_annee_ouverture_droits_en_nombre_trimestres_par_rapport_limite_age
        reduction_add_en_mois = where((2019 >= annee_age_ouverture_droits) * (annee_age_ouverture_droits >= 2006), 3 * aad_en_nombre_trimestres_par_rapport_limite_age[np.clip(annee_age_ouverture_droits, 2006, 2019)], 0)
        aad_en_mois_general = individu('fonction_publique_limite_d_age', period) * 12 + reduction_add_en_mois
        aad_en_mois_parents_trois_enfants = 65 * 12 + reduction_add_en_mois
        aad_en_mois = where(conditions_depart_anticipe_parent_trois_enfants, min_(aad_en_mois_parents_trois_enfants, aad_en_mois_general), aad_en_mois_general)
        age_en_mois_a_la_liquidation = (individu('fonction_publique_liquidation_date', period) - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        trimestres_avant_aad = max_(0, np.ceil((aad_en_mois - age_en_mois_a_la_liquidation) / 3))
        duree_assurance_requise_sedentaires = parameters(period).retraites.secteur_public.pension_civile.trimtp.nombre_trimestres_cibles_taux_plein_par_generation[date_de_naissance]
        duree_assurance_requise_actifs = parameters(period).retraites.secteur_public.pension_civile.trimtp_a.nombre_trimestres_cibles_taux_plein_par_generation_actifs[date_de_naissance]
        duree_assurance_requise_super_actifs = duree_assurance_requise_actifs - 4 * 5
        duree_assurance_requise = select([super_actif_a_la_liquidation, actif_a_la_liquidation & not_(super_actif_a_la_liquidation)], [duree_assurance_requise_super_actifs, duree_assurance_requise_actifs], default=duree_assurance_requise_sedentaires)
        duree_assurance_tous_regimes = individu('duree_assurance_tous_regimes', period)
        decote_trimestres = min_(max_(0, min_(trimestres_avant_aad, duree_assurance_requise - duree_assurance_tous_regimes)), 20)
        return select([carriere_longue, annee_age_ouverture_droits >= 2006], [0, min_(decote_trimestres, 20)], default=0)

class fonction_publique_depart_anticipe_trois_enfants(Variable):
    value_type = bool
    entity = Person
    definition_period = ETERNITY
    label = 'Demande de dépar anticipé pour 3 enfants'

    def formula(individu, period, parameters):
        aod_egal_date_depart_anticipe_parent_trois_enfants = individu('fonction_publique_aod_egal_date_depart_anticipe_parent_trois_enfants', period)
        annee_age_ouverture_droits = year_(individu('fonction_publique_ouverture_des_droits_date_normale', period))
        raison_depart_taux_plein_anticipe = individu('raison_depart_taux_plein_anticipe', period)
        date_satisfaction_condition_depart_anticipe_parents_trois_enfants = individu('fonction_publique_date_satisfaction_condition_depart_anticipe_parents_trois_enfants', period)
        condition_aod = annee_age_ouverture_droits < 2016
        condition_decote = year_(date_satisfaction_condition_depart_anticipe_parents_trois_enfants) < 2003
        return aod_egal_date_depart_anticipe_parent_trois_enfants * (condition_aod + condition_decote) + (raison_depart_taux_plein_anticipe == TypesRaisonDepartTauxPleinAnticipe.famille)

class fonction_publique_dernier_indice_atteint(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Dernier indice connu dans la fonction publique'

    def formula_1970(individu, period, parameters):
        salaire_de_base = individu('fonction_publique_salaire_de_base', period)
        taux_de_prime = individu('taux_de_prime', period)
        valeur_point_indice = parameters(period).marche_travail.remuneration_dans_fonction_publique.indicefp.point_indice_en_euros
        dernier_indice = where(salaire_de_base > 0, salaire_de_base / (1 + taux_de_prime) / valeur_point_indice, individu('fonction_publique_dernier_indice_atteint', period.last_year))
        return dernier_indice

class fonction_publique_duree_assurance(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance (trimestres validés dans la fonction publique)"

    def formula(individu, period, parameters):
        duree_assurance_validee = individu('fonction_publique_duree_assurance_validee', period)
        annee_de_liquidation = individu('fonction_publique_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        majoration_duree_assurance = individu('fonction_publique_majoration_duree_assurance', period)
        return where(annee_de_liquidation == period.start.year, round_(duree_assurance_validee + majoration_duree_assurance), duree_assurance_validee)

class fonction_publique_duree_assurance_accident_du_travail_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance au titre des accidents du travail (en trimestres validés l'année considérée)"

class fonction_publique_duree_assurance_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance annuelle (trimestres validés dans la fonction publique hors majoration)"

    def formula(individu, period, parameters):
        quotite_de_travail = np.clip(individu('fonction_publique_quotite_de_travail', period), 0.0, 1.0)
        duree_de_service_cotisee_annuelle = individu('fonction_publique_duree_de_service_cotisee_annuelle', period)
        duree_de_service_cotisee_annuelle = where(quotite_de_travail == 0, 0, duree_de_service_cotisee_annuelle)
        duree_assurance_cotisee_annuelle = duree_de_service_cotisee_annuelle / (quotite_de_travail + (quotite_de_travail == 0))
        duree_assurance_rachetee_annuelle = individu('fonction_publique_duree_de_service_rachetee_annuelle', period)
        duree_assurance_service_national_annuelle = individu('fonction_publique_duree_assurance_service_national_annuelle', period)
        return np.clip(duree_assurance_cotisee_annuelle + duree_assurance_rachetee_annuelle + duree_assurance_service_national_annuelle, 0, 4)

class fonction_publique_duree_assurance_autre_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance au titre des autres périodes assimilées (en trimestres validés l'année considérée)"

class fonction_publique_duree_assurance_chomage_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance au titre du chômage (en trimestres cotisés jusqu'à l'année considérée)"

class fonction_publique_duree_assurance_cotisee_seuil_bas(Variable):
    value_type = int
    entity = Person
    definition_period = ETERNITY
    label = "Durée d'assurance cotisée tous régimes (trimestres cotisés tous régimes confondus) avant le seuil minimum pour partir pour motif RACL"

    def formula_1994(individu, period, parameters):
        liquidation_date = individu('fonction_publique_liquidation_date', period)
        annee_de_naissance = individu('date_de_naissance', period).astype('datetime64[Y]').astype(int) + 1970
        annees_de_naissance_distinctes = np.unique(annee_de_naissance[liquidation_date >= np.datetime64(period.start)])
        duree_assurance_cotisee_16 = individu.empty_array()
        for _annee_de_naissance in sorted(annees_de_naissance_distinctes):
            filter = annee_de_naissance == _annee_de_naissance
            duree_assurance_cotisee_16[filter] = individu('fonction_publique_duree_de_service_effective', str(_annee_de_naissance + 16))[filter]
        return duree_assurance_cotisee_16

class fonction_publique_duree_assurance_cotisee_seuil_haut(Variable):
    value_type = int
    entity = Person
    definition_period = ETERNITY
    label = "Durée d'assurance cotisée tous régimes (trimestres cotisés tous régimes confondus) avant le seuil maximum pour partir pour motif RACL"

    def formula_1994(individu, period, parameters):
        liquidation_date = individu('fonction_publique_liquidation_date', period)
        annee_de_naissance = individu('date_de_naissance', period).astype('datetime64[Y]').astype(int) + 1970
        annees_de_naissance_distinctes = np.unique(annee_de_naissance[liquidation_date >= np.datetime64(period.start)])
        duree_assurance_cotisee_20 = individu.empty_array()
        for _annee_de_naissance in sorted(annees_de_naissance_distinctes):
            filter = annee_de_naissance == _annee_de_naissance
            duree_assurance_cotisee_20[filter] = individu('fonction_publique_duree_de_service_effective', str(_annee_de_naissance + 16))[filter]
        return duree_assurance_cotisee_20

class fonction_publique_duree_assurance_invalidite_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance au titre de l'invalidté (en trimestres validés l'année considérée)"

class fonction_publique_duree_assurance_maladie_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance au titre de la maladie (en trimestres validés l'année considérée)"

class fonction_publique_duree_assurance_periode_assimilee(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance pour période assimilée cumullée "

class fonction_publique_duree_assurance_rachetee_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance rachetée l'année considérée)"

class fonction_publique_duree_assurance_service_national_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance au titre du service national (en trimestres validés l'année considérée)"

class fonction_publique_duree_assurance_validee(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance (trimestres validés dans la fonction publique)"

    def formula(individu, period, parameters):
        duree_assurance_annuelle = individu('fonction_publique_duree_assurance_annuelle', period)
        duree_assurance_annee_precedente = individu('fonction_publique_duree_assurance_validee', period.last_year)
        if all((duree_assurance_annuelle == 0.0) & (duree_assurance_annee_precedente == 0.0)):
            return individu.empty_array()
        annee_de_liquidation = individu('fonction_publique_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        return where(annee_de_liquidation == period.start.year, round_(duree_assurance_annee_precedente + duree_assurance_annuelle), duree_assurance_annee_precedente + duree_assurance_annuelle)

class fonction_publique_duree_de_service_actif(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Durée de service en catégorie active (trimestres cotisés dans la fonction publique active)'

    def formula(individu, period, parameters):
        duree_de_service_actif_annuelle = individu('fonction_publique_duree_de_service_actif_annuelle', period)
        duree_de_service_actif_annee_precedente = individu('fonction_publique_duree_de_service_actif', period.last_year)
        if all((duree_de_service_actif_annuelle == 0.0) & (duree_de_service_actif_annee_precedente == 0.0)):
            return individu.empty_array()
        annee_de_liquidation = individu('fonction_publique_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        return where(annee_de_liquidation == period.start.year, round_(duree_de_service_actif_annee_precedente + duree_de_service_actif_annuelle), duree_de_service_actif_annee_precedente + duree_de_service_actif_annuelle)

class fonction_publique_duree_de_service_actif_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Durée de service dans la fonction publique au service actif'

class fonction_publique_duree_de_service_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Durée de service annuelle dans la fonction publique hors rachat et bonification non attribuable à une année'

    def formula(individu, period, parameters):
        return np.clip(individu('fonction_publique_duree_de_service_cotisee_annuelle', period) + individu('fonction_publique_duree_de_service_rachetee_annuelle', period) + individu('fonction_publique_duree_assurance_service_national_annuelle', period), 0, 4)

class fonction_publique_duree_de_service_cotisee_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée de service cotisée dans la fonction publique hors rachat et bonification dans l'année"

class fonction_publique_duree_de_service_effective(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Durée de service (trimestres cotisés dans la fonction publique) hors bonification obtenue à la liquidation'

    def formula(individu, period, parameters):
        duree_de_service_annuelle = individu('fonction_publique_duree_de_service_annuelle', period)
        duree_de_service_annee_precedente = individu('fonction_publique_duree_de_service_effective', period.last_year)
        if all((duree_de_service_annuelle == 0.0) & (duree_de_service_annee_precedente == 0.0)):
            return individu.empty_array()
        annee_de_liquidation = individu('fonction_publique_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        return where(annee_de_liquidation == period.start.year, round_(duree_de_service_annee_precedente + duree_de_service_annuelle), duree_de_service_annee_precedente + duree_de_service_annuelle)

class fonction_publique_duree_de_service_rachetee_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée de service rachetée (années d'études) dans la fonction publique hors rachat et bonification dans l'année"

class fonction_publique_duree_de_service_super_actif(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Durée de service en catégorie super active (trimestres cotisés dans la fonction publique active)'

    def formula(individu, period, parameters):
        duree_de_service_super_actif_annuelle = individu('fonction_publique_duree_de_service_super_actif_annuelle', period)
        duree_de_service_super_actif_annee_precedente = individu('fonction_publique_duree_de_service_super_actif', period.last_year)
        if all((duree_de_service_super_actif_annuelle == 0.0) & (duree_de_service_super_actif_annee_precedente == 0.0)):
            return individu.empty_array()
        annee_de_liquidation = individu('fonction_publique_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        return where(annee_de_liquidation == period.start.year, round_(duree_de_service_super_actif_annee_precedente + duree_de_service_super_actif_annuelle), duree_de_service_super_actif_annee_precedente + duree_de_service_super_actif_annuelle)

class fonction_publique_duree_de_service_super_actif_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Durée de service dans la fonction publique en catégorie super actif'

class fonction_publique_limite_d_age(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Limite d'âge"

    def formula(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        actif_a_la_liquidation = individu('fonction_publique_actif_a_la_liquidation', period)
        super_actif_a_la_liquidation = individu('fonction_publique_super_actif_a_la_liquidation', period)
        limite_age_active = parameters(period).retraites.secteur_public.pension_civile.la_a.age_limite_fonction_publique_active_selon_annee_naissance
        limite_age_sedentaire = parameters(period).retraites.secteur_public.pension_civile.la_s.age_limite_fonction_publique_sedentaire_selon_annee_naissance
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
        return where(actif_a_la_liquidation | super_actif_a_la_liquidation, limite_age_actif - 5 * super_actif_a_la_liquidation, limite_age_sedentaire)

class fonction_publique_liquidation_date(Variable):
    value_type = date
    entity = Person
    definition_period = ETERNITY
    label = 'Date de liquidation'
    default_value = date(2250, 12, 31)

class fonction_publique_majoration_duree_assurance(Variable):
    value_type = float
    entity = Person
    definition_period = ETERNITY
    label = "Majoration de duree d'assurance"
    definition_period = YEAR

    def formula(individu, period):
        return individu('fonction_publique_majoration_duree_assurance_enfant', period) + individu('fonction_publique_majoration_duree_assurance_autre', period) + individu('fonction_publique_bonification_cpcm', period)

class fonction_publique_majoration_duree_assurance_autre(Variable):
    value_type = float
    entity = Person
    definition_period = ETERNITY
    label = "Majoration de durée d'assurance autre que celle attribuée au motif des enfants"

class fonction_publique_majoration_duree_assurance_enfant(Variable):
    value_type = float
    entity = Person
    definition_period = ETERNITY
    label = 'Bonification pour enfants selon le code des pensions civiles et militaires'
    definition_period = YEAR

    def formula_2004(individu, period, parameters):
        nombre_enfants_nes_avant_2004 = individu('fonction_publique_nombre_enfants_nes_avant_2004', period)
        majoration_par_enfant_pr_2004 = parameters(period).retraites.secteur_public.pension_civile.bonification_enfant.nombre_trimestres_par_enfant_bonification.after_2004_01_01
        nombre_enfants_nes_apres_2004 = individu('nombre_enfants', period) - nombre_enfants_nes_avant_2004
        majoration = majoration_par_enfant_pr_2004 * nombre_enfants_nes_apres_2004
        sexe = individu('sexe', period)
        est_a_la_fonction_publique = individu('fonction_publique_liquidation_date', period) < individu('regime_general_cnav_liquidation_date', period)
        return where(sexe * est_a_la_fonction_publique, majoration, 0)

class fonction_publique_majoration_pension(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Majoration de pension'
    reference = ['https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000025076852/', 'https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI000006400888/']

    def formula_1965(individu, period):
        nombre_enfants = individu('nombre_enfants', period)
        pension_brute = individu('fonction_publique_pension_brute', period)
        return pension_brute * (0.1 * (nombre_enfants >= 3) + 0.05 * max_(nombre_enfants - 3, 0))

class fonction_publique_majoration_pension_au_31_decembre(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Majoration de pension au 31 décembre'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('fonction_publique_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(annee_de_liquidation > period.start.year):
            return individu.empty_array()
        last_year = period.last_year
        majoration_pension_au_31_decembre_annee_precedente = individu('fonction_publique_majoration_pension_au_31_decembre', last_year)
        revalorisation = parameters(period).retraites.secteur_public.pension_civile.revalorisation_pension_au_31_decembre
        majoration_pension = individu('fonction_publique_majoration_pension', period)
        return revalorise(majoration_pension_au_31_decembre_annee_precedente, majoration_pension, annee_de_liquidation, revalorisation, period)

class fonction_publique_minimum_garanti(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Minimum garanti de la fonction publique'
    reference = 'Loi 75-1242 du 27 décembre 1975'

    def formula_1976(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        liquidation_date = individu('fonction_publique_liquidation_date', period)
        annee_de_liquidation = individu('fonction_publique_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        duree_de_service_effective = individu('fonction_publique_duree_de_service_effective', period)
        annee_age_ouverture_droits = year_(individu('fonction_publique_ouverture_des_droits_date', period))
        decote = individu('fonction_publique_decote', period)
        service_public = parameters(period).retraites.secteur_public.pension_civile
        minimum_garanti = service_public.minimum_garanti
        points_moins_40_ans = minimum_garanti.points_moins_40_ans[liquidation_date]
        points_plus_15_ans = minimum_garanti.points_plus_15_ans[liquidation_date]
        annee_moins_40_ans = minimum_garanti.annee_moins_40_ans[liquidation_date]
        part_fixe = service_public.minimum_garanti.part_valeur_indice_majore[liquidation_date]
        indice_majore = service_public.minimum_garanti.valeur_indice_maj[liquidation_date]
        pt_indice = parameters(period).marche_travail.remuneration_dans_fonction_publique.indicefp.point_indice_en_euros
        duree_assurance_requise = service_public.trimtp.nombre_trimestres_cibles_taux_plein_par_generation[date_de_naissance]
        coefficient_moins_15_ans = duree_de_service_effective / duree_assurance_requise
        coefficient_plus_15_ans = part_fixe + max_(duree_de_service_effective - 4 * 15, 0) * points_plus_15_ans
        coefficient_plus_30_ans = part_fixe + max_(annee_moins_40_ans - 4 * 15, 0) * points_plus_15_ans + max_(duree_de_service_effective - annee_moins_40_ans, 0) * points_moins_40_ans
        coefficient_plus_40_ans = 1
        condition_absence_decote = decote == 0
        condition_duree = duree_de_service_effective > duree_assurance_requise
        condition_age_ouverture_des_droits = (annee_age_ouverture_droits < 2011) * (annee_de_liquidation >= 2011)
        post_condition = where((annee_de_liquidation < 2011) + condition_age_ouverture_des_droits, True, condition_duree + condition_absence_decote)
        return post_condition * indice_majore * pt_indice * select([duree_de_service_effective < 60, duree_de_service_effective < annee_moins_40_ans, duree_de_service_effective < 160, duree_de_service_effective >= 160], [coefficient_moins_15_ans, coefficient_plus_15_ans, coefficient_plus_30_ans, coefficient_plus_40_ans])

class fonction_publique_nombre_annees_actif(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Nombre d'années travaillant en tant qu'actif"

    def formula(individu, period):
        annee_de_liquidation = individu('fonction_publique_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(period.start.year > annee_de_liquidation):
            return individu.empty_array()
        last_year = period.last_year
        nombre_annees_actif_annee_precedente = individu('fonction_publique_nombre_annees_actif', last_year)
        categorie_activite = individu('fonction_publique_categorie_activite', period)
        return nombre_annees_actif_annee_precedente + 1 * (categorie_activite == TypesCategorieActivite.actif)

class fonction_publique_nombre_enfants_nes_avant_2004(Variable):
    value_type = int
    entity = Person
    label = "Nombre d'enfants nés avant 2004"
    definition_period = ETERNITY

class fonction_publique_ouverture_des_droits_carriere_longue_date(Variable):
    value_type = date
    entity = Person
    definition_period = YEAR
    label = "Date de l'ouverture des droits pour les départs anticipés pour carrière longue"
    default_value = date(2250, 12, 31)

    def formula_2006(individu, period, parameters):
        carriere_longue_seuil_determine_aod = individu('fonction_publique_carriere_longue_seuil_determine_aod', period)
        date_de_naissance = individu('date_de_naissance', period)
        aod_carriere_longue_2_annee = parameters(period).retraites.secteur_public.pension_civile.carriere_longue.aod_seuil_2[date_de_naissance].annee
        aod_carriere_longue_15_annee = parameters(period).retraites.secteur_public.pension_civile.carriere_longue.aod_seuil_15[date_de_naissance].annee
        aod_carriere_longue_1_annee = parameters(period).retraites.secteur_public.pension_civile.carriere_longue.aod_seuil_1[date_de_naissance].annee
        aod_carriere_longue_2_mois = parameters(period).retraites.secteur_public.pension_civile.carriere_longue.aod_seuil_2[date_de_naissance].mois
        aod_carriere_longue_15_mois = parameters(period).retraites.secteur_public.pension_civile.carriere_longue.aod_seuil_15[date_de_naissance].mois
        aod_carriere_longue_1_mois = parameters(period).retraites.secteur_public.pension_civile.carriere_longue.aod_seuil_1[date_de_naissance].mois
        aod_carriere_longue_annee = select([carriere_longue_seuil_determine_aod == 1, carriere_longue_seuil_determine_aod == 15, carriere_longue_seuil_determine_aod == 2], [aod_carriere_longue_1_annee, aod_carriere_longue_15_annee, aod_carriere_longue_2_annee])
        aod_carriere_longue_mois = select([carriere_longue_seuil_determine_aod == 1, carriere_longue_seuil_determine_aod == 15, carriere_longue_seuil_determine_aod == 2], [aod_carriere_longue_1_mois, aod_carriere_longue_15_mois, aod_carriere_longue_2_mois])
        ouverture_des_droits_carriere_longue_date = add_vectorial_timedelta(date_de_naissance, aod_carriere_longue_annee, aod_carriere_longue_mois)
        return ouverture_des_droits_carriere_longue_date

class fonction_publique_ouverture_des_droits_date(Variable):
    value_type = date
    entity = Person
    definition_period = YEAR
    label = "Date à laquelle l'individu atteint l'âge d'ouverture des droits"
    default_value = date(2250, 12, 31)

    def formula_2006(individu, period):
        ouverture_des_droits_date_normale = individu('fonction_publique_ouverture_des_droits_date_normale', period)
        date_satisfaction_condition_depart_anticipe_parents_trois_enfants = individu('fonction_publique_date_satisfaction_condition_depart_anticipe_parents_trois_enfants', period)
        depart_anticipe_trois_enfants = individu('fonction_publique_depart_anticipe_trois_enfants', period)
        date_ouverture_droits_depart_anticipe_trois_enfants = min_(ouverture_des_droits_date_normale, date_satisfaction_condition_depart_anticipe_parents_trois_enfants)
        ouverture_des_droits_carriere_longue_date = min_(ouverture_des_droits_date_normale, individu('fonction_publique_ouverture_des_droits_carriere_longue_date', period))
        carriere_longue = individu('fonction_publique_carriere_longue', period)
        return select([depart_anticipe_trois_enfants, carriere_longue], [date_ouverture_droits_depart_anticipe_trois_enfants, ouverture_des_droits_carriere_longue_date], default=ouverture_des_droits_date_normale)

class fonction_publique_ouverture_des_droits_date_normale(Variable):
    value_type = date
    entity = Person
    definition_period = YEAR
    label = "Date de l'ouverture des droits selon l'âge"
    default_value = date(2250, 12, 31)

    def formula(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        aod_active = parameters(period).retraites.secteur_public.pension_civile.aod_a.age_ouverture_droits_fonction_publique_active_selon_annee_naissance
        aod_sedentaire = parameters(period).retraites.secteur_public.pension_civile.aod_s.age_ouverture_droits_fonction_publique_sedentaire_selon_annee_naissance
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
        actif_a_la_liquidation = individu('fonction_publique_actif_a_la_liquidation', period)
        aod_annee = select([actif_a_la_liquidation], [aod_active_annee], default=aod_sedentaire_annee)
        aod_mois = select([actif_a_la_liquidation], [aod_active_mois], default=aod_sedentaire_mois)
        ouverture_des_droits_date = add_vectorial_timedelta(date_de_naissance, years=aod_annee, months=aod_mois)
        return ouverture_des_droits_date

class fonction_publique_pension(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension'

    def formula(individu, period):
        pension_brute = individu('fonction_publique_pension_brute', period)
        majoration_pension = individu('fonction_publique_majoration_pension', period)
        pension_maximale = individu('fonction_publique_salaire_de_reference', period)
        return min_(pension_brute + majoration_pension, pension_maximale)

class fonction_publique_pension_au_31_decembre(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension'

    def formula(individu, period):
        pension_brute_au_31_decembre = individu('fonction_publique_pension_brute_au_31_decembre', period)
        majoration_pension_au_31_decembre = individu('fonction_publique_majoration_pension_au_31_decembre', period)
        return pension_brute_au_31_decembre + majoration_pension_au_31_decembre

class fonction_publique_pension_avant_minimum_et_plafonnement(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension brute'

    def formula(individu, period):
        coefficient_de_proratisation = individu('fonction_publique_coefficient_de_proratisation', period)
        salaire_de_reference = individu('fonction_publique_salaire_de_reference', period)
        taux_de_liquidation = individu('fonction_publique_taux_de_liquidation', period)
        return coefficient_de_proratisation * salaire_de_reference * taux_de_liquidation

class fonction_publique_pension_brute(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension brute'

    def formula(individu, period, parameters):
        pension_avant_minimum_et_plafonnement = individu('fonction_publique_pension_avant_minimum_et_plafonnement', period)
        minimum_garanti = individu('fonction_publique_minimum_garanti', period)
        return max_(pension_avant_minimum_et_plafonnement, minimum_garanti)

class fonction_publique_pension_brute_au_31_decembre(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension brute au 31 décembre'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('fonction_publique_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(period.start.year < annee_de_liquidation):
            return individu.empty_array()
        last_year = period.last_year
        pension_brute_au_31_decembre_annee_precedente = individu('fonction_publique_pension_brute_au_31_decembre', last_year)
        revalorisation = parameters(period).retraites.secteur_public.pension_civile.revalorisation_pension_au_31_decembre
        pension_brute = individu('fonction_publique_pension_brute', period)
        return revalorise(pension_brute_au_31_decembre_annee_precedente, pension_brute, annee_de_liquidation, revalorisation, period)

class fonction_publique_pension_servie(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension servie'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('fonction_publique_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(annee_de_liquidation > period.start.year):
            return individu.empty_array()
        last_year = period.last_year
        pension_au_31_decembre_annee_precedente = individu('fonction_publique_pension_au_31_decembre', last_year)
        revalorisation = parameters(period).retraites.secteur_public.pension_civile.revalarisation_pension_servie
        pension = individu('fonction_publique_pension_au_31_decembre', period)
        return revalorise(pension_au_31_decembre_annee_precedente, pension, annee_de_liquidation, revalorisation, period)

class fonction_publique_quotite_de_travail(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Quotité de travail'
    default_value = 1.0

class fonction_publique_salaire_de_base(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Salaire de base (salaire brut)'
    set_input = set_input_divide_by_period

class fonction_publique_salaire_de_reference(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Traitement de référence'

    def formula(individu, period, parameters):
        dernier_indice_atteint = individu('fonction_publique_dernier_indice_atteint', period)
        try:
            valeur_point_indice = parameters(period).marche_travail.remuneration_dans_fonction_publique.indicefp.point_indice_en_euros
        except ParameterNotFound:
            valeur_point_indice = 0
        return dernier_indice_atteint * valeur_point_indice

class fonction_publique_super_actif_a_la_liquidation(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = 'Est considéré comme super actif à la liquiation (a atteint la durée de service requise sur un emploi de civil actif insalubre ou roulant'

class fonction_publique_surcote(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Surcote'

    def formula_2004(individu, period, parameters):
        surcote_trimestres = individu('fonction_publique_surcote_trimestres', period)
        actif_a_la_liquidation = individu('fonction_publique_actif_a_la_liquidation', period)
        taux_surcote = parameters(period).retraites.secteur_public.pension_civile.surcote.taux_surcote_par_trimestre
        return where(actif_a_la_liquidation, 0, taux_surcote * surcote_trimestres)

class fonction_publique_surcote_trimestres(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Trimestres surcote avant application du minimum garanti'

    def formula_2004(individu, period, parameters):
        liquidation_date = individu('fonction_publique_liquidation_date', period)
        date_de_naissance = individu('date_de_naissance', period)
        aod_sedentaire = parameters(period).retraites.secteur_public.pension_civile.aod_s.age_ouverture_droits_fonction_publique_sedentaire_selon_annee_naissance
        if period.start.year <= 2011:
            aod_sedentaire_annee = aod_sedentaire.before_1951_07_01.annee
            aod_sedentaire_mois = 0
        else:
            aod_sedentaire_annee = aod_sedentaire[date_de_naissance].annee
            aod_sedentaire_mois = aod_sedentaire[date_de_naissance].mois
        age_en_mois_a_la_liquidation = (individu('fonction_publique_liquidation_date', period) - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        arrondi_trimestres_aod = np.ceil if period.start.year < 2009 else np.floor
        trimestres_apres_aod = max_(0, (age_en_mois_a_la_liquidation - (12 * aod_sedentaire_annee + aod_sedentaire_mois)) / 3)
        duree_assurance_requise = parameters(period).retraites.secteur_public.pension_civile.trimtp.nombre_trimestres_cibles_taux_plein_par_generation[date_de_naissance]
        trimestres_apres_instauration_surcote = (individu('fonction_publique_liquidation_date', period) - np.datetime64('2004-01-01')).astype('timedelta64[M]').astype(int) / 3
        duree_assurance_excedentaire = individu('duree_assurance_tous_regimes', period) - duree_assurance_requise
        trimestres_surcote = max_(0, arrondi_trimestres_aod(min_(min_(trimestres_apres_instauration_surcote, trimestres_apres_aod), duree_assurance_excedentaire)))
        return where(liquidation_date < np.datetime64('2010-11-11'), min_(trimestres_surcote, 20), trimestres_surcote)

class fonction_publique_taux_de_liquidation(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Taux de liquidation de la pension'

    def formula(individu, period, parameters):
        decote = individu('fonction_publique_decote', period)
        surcote = individu('fonction_publique_surcote', period)
        taux_plein = parameters(period).retraites.secteur_public.pension_civile.taux_plein.taux_plein
        return taux_plein * (1 - decote + surcote)

class fonction_publique_taux_de_liquidation_proratise(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Taux de liquidation proratisé'

    def formula(individu, period):
        return individu('fonction_publique_taux_de_liquidation', period) * individu('fonction_publique_coefficient_de_proratisation', period)