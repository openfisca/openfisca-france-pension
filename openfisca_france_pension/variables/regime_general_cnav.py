"""Abstract regimes definition."""
from openfisca_core.model_api import *
from openfisca_core.errors.variable_not_found_error import VariableNotFoundError
from openfisca_france_pension.entities import Person

def revalorise(variable_31_decembre_annee_precedente, variable_originale, annee_de_liquidation, revalorisation, period):
    return select([annee_de_liquidation > period.start.year, annee_de_liquidation == period.start.year, annee_de_liquidation < period.start.year], [0, variable_originale, variable_31_decembre_annee_precedente * revalorisation])
'Régime de base du secteur privé: régime général de la CNAV.'
import functools
import numpy as np
from openfisca_core.model_api import *
from openfisca_core.parameters import ParameterNotFound
from openfisca_core.periods import YEAR
from openfisca_core.variables import Variable
from openfisca_france_pension.entities import Person
from openfisca_france_pension.regimes import REGIMES_DE_BASE
from openfisca_france_pension.regimes.regime import AbstractRegimeEnAnnuites
from openfisca_france_pension.tools import add_vectorial_timedelta, calendar_quarters_elapsed_this_year_asof, count_calendar_quarters, mean_over_k_nonzero_largest, next_calendar_quarter_start_date
from openfisca_france_pension.variables.hors_regime import TypesCategorieSalarie
from openfisca_france_pension.variables.hors_regime import TypesRaisonDepartTauxPleinAnticipe
OFFSET = 10
REVAL_S_YEAR_MIN = 1949

def conversion_en_monnaie_courante(period):
    year = period if isinstance(period, (int, float)) else period.start.year
    euro_en_francs = 6.55957
    if year < 1960:
        return 100 * euro_en_francs
    elif year < 2002:
        return euro_en_francs
    else:
        return 1

def conversion_parametre_en_euros(period):
    return 1 / conversion_en_monnaie_courante(period)

def compute_salaire_de_reference(mean_over_largest, arr, salaire_de_refererence, filter):
    salaire_de_refererence[filter] = np.apply_along_axis(mean_over_largest, axis=0, arr=arr)

def make_mean_over_largest(k):

    def mean_over_largest(vector):
        return mean_over_k_nonzero_largest(vector, k=int(k))
    return mean_over_largest

class TypesSalaireValidantTrimestre(Enum):
    __order__ = 'metropole guadeloupe_guyane_martinique reunion'
    metropole = 'Métropole'
    guadeloupe_guyane_martinique = 'Guadeloupe, Guyane et Martinique'
    reunion = 'Réunion'

def build_revalorisation_salaire_cummulee(parameters_regime_name, period, annee_de_naissance):
    """
    Construit le dictionnaire des revalorisations de salaire par année d'octroi.

    Args:
        parameters (Parameters): paramètre de la législation
        period (Period): period
        annee_initiale (int): première année de la revalorisation

    Returns:
        dict: le dictionnaire des revalorisations de salaire par année d'octroi
    """
    annees_de_naissance_distinctes = np.unique(annee_de_naissance)
    most_recent_revaloraisation_year = int(max(parameters_regime_name.revalorisation_salaire_cummulee._children.keys()))
    revalorisation = dict(((annee_salaire, parameters_regime_name.revalorisation_salaire_cummulee[str(np.clip(annee_salaire, REVAL_S_YEAR_MIN, most_recent_revaloraisation_year))]) for annee_salaire in range(max(min(annees_de_naissance_distinctes) + OFFSET if annees_de_naissance_distinctes.size > 0 else REVAL_S_YEAR_MIN, REVAL_S_YEAR_MIN), period.start.year)))
    return revalorisation

class regime_general_cnav_age_a_la_liquidation(Variable):
    value_type = float
    entity = Person
    definition_period = ETERNITY
    label = 'Âge à la liquidation'

    def formula(individu, period):
        liquidation_date = individu('regime_general_cnav_liquidation_date', period)
        age_en_mois_a_la_liquidation = (liquidation_date - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        return age_en_mois_a_la_liquidation / 12

class regime_general_cnav_age_annulation_decote(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Âge auquel un individu peut partir au taux plein (éventuellement de façon anticipée)'

    def formula_2004(individu, period, parameters):
        aad_anciens_deportes = parameters(period).retraites.secteur_prive.regime_general_cnav.aad.age_annulation_decote_anciens_deportes
        aad_handicape = parameters(period).retraites.secteur_prive.regime_general_cnav.aad.age_annulation_decote_handicape
        aad_inaptitude = parameters(period).retraites.secteur_prive.regime_general_cnav.aad.age_annulation_decote_inaptitude
        aad_anciens_anciens_combattants = parameters(period).retraites.secteur_prive.regime_general_cnav.aad.age_annulation_decote_anciens_combattants
        aad_anciens_travailleurs_manuels = parameters(period).retraites.secteur_prive.regime_general_cnav.aad.travailleurs_manuels.age_annulation_decote
        aad_droit_commun = individu('regime_general_cnav_age_annulation_decote_droit_commun', period)
        raison_depart_taux_plein_anticipe = individu('raison_depart_taux_plein_anticipe', period)
        aad = switch(raison_depart_taux_plein_anticipe, {TypesRaisonDepartTauxPleinAnticipe.non_concerne: aad_droit_commun, TypesRaisonDepartTauxPleinAnticipe.handicape: aad_handicape, TypesRaisonDepartTauxPleinAnticipe.ancien_deporte: aad_anciens_deportes, TypesRaisonDepartTauxPleinAnticipe.inapte: aad_inaptitude, TypesRaisonDepartTauxPleinAnticipe.ancien_combattant: aad_anciens_anciens_combattants, TypesRaisonDepartTauxPleinAnticipe.travailleur_manuel: aad_anciens_travailleurs_manuels})
        return aad

    def formula_1976_07_01(individu, period, parameters):
        aad_anciens_deportes = parameters(period).retraites.secteur_prive.regime_general_cnav.aad.age_annulation_decote_anciens_deportes
        aad_inaptitude = parameters(period).retraites.secteur_prive.regime_general_cnav.aad.age_annulation_decote_inaptitude
        aad_anciens_anciens_combattants = parameters(period).retraites.secteur_prive.regime_general_cnav.aad.age_annulation_decote_anciens_combattants
        aad_anciens_travailleurs_manuels = parameters(period).retraites.secteur_prive.regime_general_cnav.aad.travailleurs_manuels.age_annulation_decote
        aad_droit_commun = individu('regime_general_cnav_age_annulation_decote_droit_commun', period)
        raison_depart_taux_plein_anticipe = individu('raison_depart_taux_plein_anticipe', period)
        aad = switch(raison_depart_taux_plein_anticipe, {TypesRaisonDepartTauxPleinAnticipe.non_concerne: aad_droit_commun, TypesRaisonDepartTauxPleinAnticipe.ancien_deporte: aad_anciens_deportes, TypesRaisonDepartTauxPleinAnticipe.handicape: aad_inaptitude, TypesRaisonDepartTauxPleinAnticipe.inapte: aad_inaptitude, TypesRaisonDepartTauxPleinAnticipe.ancien_combattant: aad_anciens_anciens_combattants, TypesRaisonDepartTauxPleinAnticipe.travailleur_manuel: aad_anciens_travailleurs_manuels})
        return aad

    def formula_1974_01_01(individu, period, parameters):
        aad_droit_commun = individu('regime_general_cnav_age_annulation_decote_droit_commun', period)
        aad_anciens_deportes = parameters(period).retraites.secteur_prive.regime_general_cnav.aad.age_annulation_decote_anciens_deportes
        aad_inaptitude = parameters(period).retraites.secteur_prive.regime_general_cnav.aad.age_annulation_decote_inaptitude
        aad_anciens_anciens_combattants = parameters(period).retraites.secteur_prive.regime_general_cnav.aad.age_annulation_decote_anciens_combattants
        raison_depart_taux_plein_anticipe = individu('raison_depart_taux_plein_anticipe', period)
        aad = switch(raison_depart_taux_plein_anticipe, {TypesRaisonDepartTauxPleinAnticipe.non_concerne: aad_droit_commun, TypesRaisonDepartTauxPleinAnticipe.ancien_deporte: aad_anciens_deportes, TypesRaisonDepartTauxPleinAnticipe.inapte: aad_inaptitude, TypesRaisonDepartTauxPleinAnticipe.ancien_combattant: aad_anciens_anciens_combattants})
        return aad

    def formula_1972_01_01(individu, period, parameters):
        aad_droit_commun = individu('regime_general_cnav_age_annulation_decote_droit_commun', period)
        aad_anciens_deportes = parameters(period).retraites.secteur_prive.regime_general_cnav.aad.age_annulation_decote_anciens_deportes
        aad_inaptitude = parameters(period).retraites.secteur_prive.regime_general_cnav.aad.age_annulation_decote_inaptitude
        raison_depart_taux_plein_anticipe = individu('raison_depart_taux_plein_anticipe', period)
        aad = switch(raison_depart_taux_plein_anticipe, {TypesRaisonDepartTauxPleinAnticipe.non_concerne: aad_droit_commun, TypesRaisonDepartTauxPleinAnticipe.ancien_deporte: aad_anciens_deportes, TypesRaisonDepartTauxPleinAnticipe.inapte: aad_inaptitude})
        return aad

    def formula_1965_05_01(individu, period, parameters):
        aad_droit_commun = individu('regime_general_cnav_age_annulation_decote_droit_commun', period)
        aad_anciens_deportes = parameters(period).retraites.secteur_prive.regime_general_cnav.aad.age_annulation_decote_anciens_deportes
        raison_depart_taux_plein_anticipe = individu('raison_depart_taux_plein_anticipe', period)
        aad = switch(raison_depart_taux_plein_anticipe, {TypesRaisonDepartTauxPleinAnticipe.non_concerne: aad_droit_commun, TypesRaisonDepartTauxPleinAnticipe.ancien_deporte: aad_anciens_deportes})
        return aad

    def formula_1945(individu, period, parameters):
        aad_droit_commun = individu('regime_general_cnav_age_annulation_decote_droit_commun', period)
        return aad_droit_commun

class regime_general_cnav_age_annulation_decote_droit_commun(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Âge auquel un individu peut partir au taux plein hors départ anticipé'

    def formula_2011_07_01(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        aad_annee = parameters(period).retraites.secteur_prive.regime_general_cnav.aad.age_annulation_decote_en_fonction_date_naissance[date_de_naissance].annee
        aad_mois = parameters(period).retraites.secteur_prive.regime_general_cnav.aad.age_annulation_decote_en_fonction_date_naissance[date_de_naissance].mois
        return aad_annee + aad_mois / 12

    def formula_1945(individu, period, parameters):
        return parameters(period).retraites.secteur_prive.regime_general_cnav.aad.age_annulation_decote_en_fonction_date_naissance.before_1951_07_01.annee

class regime_general_cnav_avpf(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Salaire porté au compte au titre de l'assurance vieillesse des parents au foyer"

class regime_general_cnav_coefficient_de_proratisation(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Coefficient de proratisation'

    def formula_2011_07_01(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        duree_de_proratisation = parameters(period).retraites.secteur_prive.regime_general_cnav.prorat.nombre_trimestres_maximal_pris_en_compte_proratisation_par_generation[date_de_naissance]
        aad = individu('regime_general_cnav_age_annulation_decote', period)
        coefficient_minoration_par_trimestre = parameters(period).retraites.secteur_prive.regime_general_cnav.decote.coefficient_minoration_par_trimestres_manquants.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants[date_de_naissance]
        liquidation_date = individu('regime_general_cnav_liquidation_date', period)
        age_en_mois_a_la_liquidation = (liquidation_date - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        trimestres_apres_aad = max_(0, np.floor((age_en_mois_a_la_liquidation - aad * 12) / 3))
        trimestres = individu('regime_general_cnav_duree_de_service', period)
        duree_assurance_corrigee = min_(duree_de_proratisation, trimestres * (1 + trimestres_apres_aad * coefficient_minoration_par_trimestre))
        coefficient = min_(1, duree_assurance_corrigee / duree_de_proratisation)
        return coefficient

    def formula_1983_04_01(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        duree_de_proratisation = parameters(period).retraites.secteur_prive.regime_general_cnav.prorat.nombre_trimestres_maximal_pris_en_compte_proratisation_par_generation[date_de_naissance]
        aad = individu('regime_general_cnav_age_annulation_decote', period)
        coefficient_minoration_par_trimestre = parameters(period).retraites.secteur_prive.regime_general_cnav.decote.coefficient_minoration_par_trimestres_manquants.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants[date_de_naissance]
        liquidation_date = individu('regime_general_cnav_liquidation_date', period)
        age_en_mois_a_la_liquidation = (liquidation_date - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        trimestres_apres_aad = max_(0, np.floor((age_en_mois_a_la_liquidation - aad * 12) / 3))
        trimestres = individu('regime_general_cnav_duree_assurance', period)
        duree_assurance_corrigee = min_(duree_de_proratisation, trimestres * (1 + trimestres_apres_aad * coefficient_minoration_par_trimestre))
        coefficient = min_(1, duree_assurance_corrigee / duree_de_proratisation)
        return coefficient

    def formula_1948(individu, period, parameters):
        trimestres = individu('regime_general_cnav_duree_assurance', period)
        duree_de_proratisation = parameters(period).retraites.secteur_prive.regime_general_cnav.prorat.nombre_trimestres_maximal_pris_en_compte_proratisation_par_generation.before_1944_01_01
        duree_assurance_corrigee = trimestres + (duree_de_proratisation - trimestres) / 2
        coefficient = min_(1, duree_assurance_corrigee / duree_de_proratisation)
        return coefficient

    def formula_1946(individu, period, parameters):
        duree_de_proratisation = parameters(period).retraites.secteur_prive.regime_general_cnav.prorat.nombre_trimestres_maximal_pris_en_compte_proratisation_par_generation.before_1944_01_01
        trimestres = individu('regime_general_cnav_duree_assurance', period)
        coefficient = min_(1, trimestres / duree_de_proratisation)
        return coefficient

class regime_general_cnav_cotisation(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'cotisation retraite employeur'

    def formula(individu, period, parameters):
        NotImplementedError

class regime_general_cnav_cotisation_employeur(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Cotisation employeur'

    def formula(individu, period, parameters):
        categorie_salarie = individu('categorie_salarie', period)
        salaire_de_base = individu('regime_general_cnav_salaire_de_base', period)
        plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel * conversion_parametre_en_euros(period.start.year)
        employeur = parameters(period).retraites.secteur_prive.regime_general_cnav.prelevements_sociaux.employeur
        salarie_concerne = (categorie_salarie == TypesCategorieSalarie.prive_non_cadre) + (categorie_salarie == TypesCategorieSalarie.prive_cadre) + (categorie_salarie == TypesCategorieSalarie.public_non_titulaire)
        return salarie_concerne * (employeur.vieillesse_deplafonnee.calc(salaire_de_base, factor=plafond_securite_sociale) + employeur.vieillesse_plafonnee.calc(salaire_de_base, factor=plafond_securite_sociale))

class regime_general_cnav_cotisation_salarie(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Cotisation salarié'

    def formula(individu, period, parameters):
        categorie_salarie = individu('categorie_salarie', period)
        salaire_de_base = individu('regime_general_cnav_salaire_de_base', period)
        plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel * conversion_parametre_en_euros(period.start.year)
        salarie = parameters(period).retraites.secteur_prive.regime_general_cnav.prelevements_sociaux.salarie
        salarie_concerne = (categorie_salarie == TypesCategorieSalarie.prive_non_cadre) + (categorie_salarie == TypesCategorieSalarie.prive_cadre) + (categorie_salarie == TypesCategorieSalarie.public_non_titulaire)
        return salarie_concerne * (salarie.vieillesse_deplafonnee.calc(salaire_de_base, factor=plafond_securite_sociale) + salarie.vieillesse_plafonnee.calc(salaire_de_base, factor=plafond_securite_sociale))

class regime_general_cnav_decote(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Décote'

    def formula_1983_04_01(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        coefficient_minoration_par_trimestre = parameters(period).retraites.secteur_prive.regime_general_cnav.decote.coefficient_minoration_par_trimestres_manquants.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants[date_de_naissance]
        decote_trimestres = individu('regime_general_cnav_decote_trimestres', period)
        decote = coefficient_minoration_par_trimestre * decote_trimestres
        return decote

    def formula_1945(individu, period, parameters):
        decote_trimestres = individu('regime_general_cnav_decote_trimestres', period)
        coefficient_minoration_par_trimestre = parameters(period).retraites.secteur_prive.regime_general_cnav.decote.coefficient_minoration_par_trimestres_manquants.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants.before_1944_01_01
        return coefficient_minoration_par_trimestre * decote_trimestres

class regime_general_cnav_decote_trimestres(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Trimestres de décote'

    def formula_2011_07_01(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        aad = individu('regime_general_cnav_age_annulation_decote', period)
        duree_assurance_cible_taux_plein = parameters(period).retraites.secteur_prive.regime_general_cnav.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]
        age_en_mois_a_la_liquidation = (individu('regime_general_cnav_liquidation_date', period) - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        trimestres_avant_aad = np.ceil((aad * 12 - age_en_mois_a_la_liquidation) / 3)
        duree_assurance_tous_regimes = individu('duree_assurance_tous_regimes', period)
        decote_trimestres = max_(0, min_(duree_assurance_cible_taux_plein - duree_assurance_tous_regimes, trimestres_avant_aad))
        return decote_trimestres

    def formula_1983_04_01(individu, period, parameters):
        aad = individu('regime_general_cnav_age_annulation_decote', period)
        date_de_naissance = individu('date_de_naissance', period)
        duree_assurance_cible_taux_plein = parameters(period).retraites.secteur_prive.regime_general_cnav.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]
        age_en_mois_a_la_liquidation = (individu('regime_general_cnav_liquidation_date', period) - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        trimestres_avant_aad = np.ceil((aad * 12 - age_en_mois_a_la_liquidation) / 3)
        duree_assurance_tous_regimes = individu('duree_assurance_tous_regimes', period)
        decote_trimestres = max_(0, min_(duree_assurance_cible_taux_plein - duree_assurance_tous_regimes, trimestres_avant_aad))
        return decote_trimestres

    def formula_1945(individu, period, parameters):
        aad = individu('regime_general_cnav_age_annulation_decote', period)
        liquidation_date = individu('regime_general_cnav_liquidation_date', period)
        age_en_mois_a_la_liquidation = (liquidation_date - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        decote_trimestres = max_(0, np.ceil((aad * 12 - age_en_mois_a_la_liquidation) / 3))
        return decote_trimestres

class regime_general_cnav_duree_assurance(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance (trimestres validés au régime général)"

    def formula(individu, period):
        duree_assurance_validee = individu('regime_general_cnav_duree_assurance_validee', period)
        annee_de_liquidation = individu('regime_general_cnav_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        liquidation = annee_de_liquidation == period.start.year
        majoration_duree_assurance = individu('regime_general_cnav_majoration_duree_assurance', period)
        return duree_assurance_validee + majoration_duree_assurance * liquidation

class regime_general_cnav_duree_assurance_accident_du_travail_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance au titre des accidents du travail (en trimestres validés l'année considérée)"

class regime_general_cnav_duree_assurance_annuelle(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance (trimestres validés au régime général)"

    def formula(individu, period):
        liquidation_date = individu('regime_general_cnav_liquidation_date', period)
        trimestres_validables = where(liquidation_date.astype('datetime64[Y]').astype(int) + 1970 == period.start.year, calendar_quarters_elapsed_this_year_asof(liquidation_date), 4)
        return np.clip(individu('regime_general_cnav_duree_assurance_cotisee_annuelle', period) + individu('regime_general_cnav_duree_assurance_periode_assimilee_annuelle', period), 0, trimestres_validables)

class regime_general_cnav_duree_assurance_autre_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance au titre des autres périodes assimilées (en trimestres validés l'année considérée)"

class regime_general_cnav_duree_assurance_avpf_annuelle(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance cotisée au titre de l'avpf (en trimestres cotisés l'année considérée)"

    def formula_1972(individu, period, parameters):
        avpf = individu('regime_general_cnav_avpf', period)
        smic_trimestriel = parameters(period).marche_travail.salaire_minimum.smic.smic_b_mensuel * 3.0
        avpf = avpf * conversion_en_monnaie_courante(period)
        return np.clip((avpf / smic_trimestriel).astype(int), 0, 4)

class regime_general_cnav_duree_assurance_chomage_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance au titre du chômage (en trimestres cotisés jusqu'à l'année considérée)"

class regime_general_cnav_duree_assurance_cotisee(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance en emploi cummulée (trimestres cotisés en emploi au régime général depuis l'entrée dans le régme)"

    def formula(individu, period, parameters):
        duree_assurance_cotisee_annuelle = individu('regime_general_cnav_duree_assurance_cotisee_annuelle', period)
        duree_assurance_cotisee_annee_precedente = individu('regime_general_cnav_duree_assurance_cotisee', period.last_year)
        if all((duree_assurance_cotisee_annuelle == 0) & (duree_assurance_cotisee_annee_precedente == 0)):
            return individu.empty_array()
        return duree_assurance_cotisee_annee_precedente + duree_assurance_cotisee_annuelle

class regime_general_cnav_duree_assurance_cotisee_annuelle(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance cotisée donc hors majoration de durée d'assurance (en trimestres cotisés l'année considérée)"

    def formula(individu, period, parameters):
        duree_assurance_personnellement_cotisee_annuelle = individu('regime_general_cnav_duree_assurance_personnellement_cotisee_annuelle', period)
        duree_assurance_avpf_annuelle = individu('regime_general_cnav_duree_assurance_avpf_annuelle', period)
        liquidation_date = individu('regime_general_cnav_liquidation_date', period)
        trimestres_validables = where(liquidation_date.astype('datetime64[Y]').astype(int) + 1970 == period.start.year, calendar_quarters_elapsed_this_year_asof(liquidation_date), 4)
        return np.clip(duree_assurance_personnellement_cotisee_annuelle + duree_assurance_avpf_annuelle, 0, trimestres_validables)

class regime_general_cnav_duree_assurance_emploi_annuelle(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance cotisée en emploi (en trimestres cotisés l'année considérée)"

    def formula_1930(individu, period, parameters):
        salaire_de_base = individu('regime_general_cnav_salaire_de_base', period)
        salaire_validant_trimestre = individu('regime_general_cnav_salaire_validant_trimestre', period)
        try:
            salaire_validant_un_trimestre = parameters(period).retraites.secteur_prive.regime_general_cnav.salval.salaire_validant_trimestre[salaire_validant_trimestre]
        except ParameterNotFound:
            import openfisca_core.periods as periods
            salaire_validant_un_trimestre = parameters(periods.period(1930)).retraites.secteur_prive.regime_general_cnav.salval.salaire_validant_trimestre[salaire_validant_trimestre]
        return np.clip((salaire_de_base * conversion_en_monnaie_courante(period) / salaire_validant_un_trimestre).astype(int), 0, 4)

class regime_general_cnav_duree_assurance_equivalente(Variable):
    value_type = int
    entity = Person
    definition_period = ETERNITY
    label = "Durée d'assurance considérée équivalente tous régimes"

class regime_general_cnav_duree_assurance_etranger(Variable):
    value_type = int
    entity = Person
    definition_period = ETERNITY
    label = "Durée d'assurance acquise à l'étranger"

class regime_general_cnav_duree_assurance_invalidite_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance au titre de l'invalidté (en trimestres validés l'année considérée)"

class regime_general_cnav_duree_assurance_maladie_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance au titre de la maladie (en trimestres validés l'année considérée)"

class regime_general_cnav_duree_assurance_periode_assimilee(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance pour période assimilée cumullée "

class regime_general_cnav_duree_assurance_periode_assimilee_annuelle(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance pour période assimilée annuelle"

    def formula(individu, period, parameters):
        duree_assurance_periodes_assimilees_annuelles = sum((individu(f'regime_general_cnav_duree_assurance_{periode_assimilee}_annuelle', period) for periode_assimilee in ['chomage', 'maladie', 'accident_du_travail', 'invalidite', 'service_national', 'autre']))
        liquidation_date = individu('regime_general_cnav_liquidation_date', period)
        trimestres_validables = where(liquidation_date.astype('datetime64[Y]').astype(int) + 1970 == period.start.year, calendar_quarters_elapsed_this_year_asof(liquidation_date), 4)
        duree_assurance_periode_assimilee_annuelle = np.clip(duree_assurance_periodes_assimilees_annuelles, 0, trimestres_validables)
        return duree_assurance_periode_assimilee_annuelle

class regime_general_cnav_duree_assurance_personnellement_cotisee(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance en emploi cummulée (trimestres cotisés en emploi au régime général depuis l'entrée dans le régme)"

    def formula(individu, period, parameters):
        duree_assurance_personnellement_cotisee_annuelle = individu('regime_general_cnav_duree_assurance_personnellement_cotisee_annuelle', period)
        duree_assurance_personnellement_cotisee_annee_precedente = individu('regime_general_cnav_duree_assurance_personnellement_cotisee', period.last_year)
        if all((duree_assurance_personnellement_cotisee_annuelle == 0) & (duree_assurance_personnellement_cotisee_annee_precedente == 0)):
            return individu.empty_array()
        return duree_assurance_personnellement_cotisee_annuelle + duree_assurance_personnellement_cotisee_annee_precedente

class regime_general_cnav_duree_assurance_personnellement_cotisee_annuelle(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance cotisée donc hors majoration de durée d'assurance (en trimestres cotisés l'année considérée)"

    def formula(individu, period, parameters):
        duree_assurance_emploi_annuelle = individu('regime_general_cnav_duree_assurance_emploi_annuelle', period)
        duree_assurance_rachetee_annuelle = individu('regime_general_cnav_duree_assurance_rachetee_annuelle', period)
        liquidation_date = individu('regime_general_cnav_liquidation_date', period)
        trimestres_validables = where(liquidation_date.astype('datetime64[Y]').astype(int) + 1970 == period.start.year, calendar_quarters_elapsed_this_year_asof(liquidation_date), 4)
        return np.clip(duree_assurance_emploi_annuelle + duree_assurance_rachetee_annuelle, 0, trimestres_validables)

class regime_general_cnav_duree_assurance_rachetee_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance rachetée l'année considérée)"

class regime_general_cnav_duree_assurance_service_national_annuelle(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance au titre du service national (en trimestres validés l'année considérée)"

class regime_general_cnav_duree_assurance_validee(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance validée cummulée (trimestres validés au régime général depuis l'entrée dans le régme hors majoration et bonification)"

    def formula(individu, period, parameters):
        duree_assurance_annuelle = individu('regime_general_cnav_duree_assurance_annuelle', period)
        duree_assurance_annee_precedente = individu('regime_general_cnav_duree_assurance_validee', period.last_year)
        if all((duree_assurance_annuelle == 0) & (duree_assurance_annee_precedente == 0)):
            return individu.empty_array()
        return duree_assurance_annee_precedente + duree_assurance_annuelle

class regime_general_cnav_duree_de_service(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = 'Durée de service'

    def formula(individu, period):
        duree_assurance_validee = individu('regime_general_cnav_duree_assurance_validee', period)
        annee_de_liquidation = individu('regime_general_cnav_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        liquidation = annee_de_liquidation == period.start.year
        majoration_duree_assurance = individu('regime_general_cnav_majoration_duree_assurance', period)
        return duree_assurance_validee + majoration_duree_assurance * liquidation

class regime_general_cnav_liquidation_date(Variable):
    value_type = date
    entity = Person
    definition_period = ETERNITY
    label = 'Date de liquidation'
    default_value = date(2250, 12, 31)

class regime_general_cnav_majoration_duree_assurance(Variable):
    value_type = float
    entity = Person
    definition_period = ETERNITY
    label = "Majoration de durée d'assurance"

    def formula(individu, period):
        return individu('regime_general_cnav_majoration_duree_assurance_enfant', period) + individu('regime_general_cnav_majoration_duree_assurance_autre', period)

class regime_general_cnav_majoration_duree_assurance_autre(Variable):
    value_type = float
    entity = Person
    definition_period = ETERNITY
    label = "Majoration de durée d'assurance autre que celle attribuée au motif des enfants"

class regime_general_cnav_majoration_duree_assurance_enfant(Variable):
    value_type = float
    entity = Person
    definition_period = ETERNITY
    label = "Majoration de durée d'assurance pour présence d'enfants"
    reference = 'https://www.cairn.info/revue-retraite-et-societe1-2012-1-page-183.htm'

    def formula_1974_07(individu, period):
        n_est_pas_a_la_fonction_publique = individu('fonction_publique_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970 >= 2250
        sexe = individu('sexe', period)
        return where(sexe * n_est_pas_a_la_fonction_publique, individu('nombre_enfants', period) * 8, 0)

    def formula_1972(individu, period):
        n_est_pas_a_la_fonction_publique = individu('fonction_publique_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970 >= 2250
        sexe = individu('sexe', period)
        return where(sexe * n_est_pas_a_la_fonction_publique * (individu('nombre_enfants', period) >= 2), individu('nombre_enfants', period) * 4, 0)

class regime_general_cnav_majoration_pension(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Majoration de pension'

    def formula(individu, period, parameters):
        nombre_enfants = individu('nombre_enfants', period)
        pension_brute = individu('regime_general_cnav_pension_brute', period)
        return 0.1 * pension_brute * (nombre_enfants >= 3)

class regime_general_cnav_majoration_pension_au_31_decembre(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Majoration de pension au 31 décembre'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('regime_general_cnav_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(annee_de_liquidation > period.start.year):
            return individu.empty_array()
        last_year = period.last_year
        majoration_pension_au_31_decembre_annee_precedente = individu('regime_general_cnav_majoration_pension_au_31_decembre', last_year)
        revalorisation = parameters(period).retraites.secteur_prive.regime_general_cnav.revalorisation_pension_au_31_decembre
        majoration_pension = individu('regime_general_cnav_majoration_pension', period)
        return revalorise(majoration_pension_au_31_decembre_annee_precedente, majoration_pension, annee_de_liquidation, revalorisation, period)

class regime_general_cnav_ouverture_des_droits_date(Variable):
    value_type = date
    entity = Person
    definition_period = YEAR
    label = "Date de l'ouverture des droits selon l'âge"
    default_value = date(2250, 12, 31)

    def formula_2009_04_01(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        if date(period.start.year, period.start.month, period.start.day) < date(2011, 7, 1):
            aod_annee = parameters(period).retraites.secteur_prive.regime_general_cnav.aod.age_ouverture_droits_age_legal_en_fonction_date_naissance.before_1951_07_01.annee
            aod_mois = 0
        else:
            aod_annee = parameters(period).retraites.secteur_prive.regime_general_cnav.aod.age_ouverture_droits_age_legal_en_fonction_date_naissance[date_de_naissance].annee
            aod_mois = parameters(period).retraites.secteur_prive.regime_general_cnav.aod.age_ouverture_droits_age_legal_en_fonction_date_naissance[date_de_naissance].mois
        ouverture_des_droits_date = add_vectorial_timedelta(date_de_naissance, years=aod_annee, months=aod_mois)
        return ouverture_des_droits_date

    def formula_2004_01_01(individu, period, parameters):
        aod = parameters(period).retraites.secteur_prive.regime_general_cnav.aod.age_ouverture_droits_age_legal_en_fonction_date_naissance.before_1951_07_01.annee
        date_de_naissance = individu('date_de_naissance', period)
        ouverture_des_droits_date = add_vectorial_timedelta(date_de_naissance, years=aod)
        return ouverture_des_droits_date

class regime_general_cnav_pension(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension'

    def formula(individu, period):
        pension_brute = individu('regime_general_cnav_pension_brute', period)
        majoration_pension = individu('regime_general_cnav_majoration_pension', period)
        return pension_brute + majoration_pension

class regime_general_cnav_pension_au_31_decembre(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension'

    def formula(individu, period):
        pension_brute_au_31_decembre = individu('regime_general_cnav_pension_brute_au_31_decembre', period)
        majoration_pension_au_31_decembre = individu('regime_general_cnav_majoration_pension_au_31_decembre', period)
        return pension_brute_au_31_decembre + majoration_pension_au_31_decembre

class regime_general_cnav_pension_avant_minimum_et_plafonnement(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension brute'

    def formula(individu, period):
        coefficient_de_proratisation = individu('regime_general_cnav_coefficient_de_proratisation', period)
        salaire_de_reference = individu('regime_general_cnav_salaire_de_reference', period)
        taux_de_liquidation = individu('regime_general_cnav_taux_de_liquidation', period)
        return coefficient_de_proratisation * salaire_de_reference * taux_de_liquidation

class regime_general_cnav_pension_brute(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension'

    def formula_2012_01_01(individu, period, parameters):
        pension_avant_minimum_et_plafonnement = individu('regime_general_cnav_pension_avant_minimum_et_plafonnement', period)
        minimum_contributif = individu('regime_general_cnav_pension_minimale', period)
        taux_de_liquidation = individu('regime_general_cnav_taux_de_liquidation', period)
        minimum_contributif_plafond_annuel = 12 * parameters(period).retraites.secteur_prive.regime_general_cnav.plafond_mico.minimum_contributif_plafond_mensuel
        plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel * conversion_parametre_en_euros(period.start.year)
        taux_plein = parameters(period).retraites.secteur_prive.regime_general_cnav.taux_plein.taux_plein
        a_atteint_taux_plein = taux_de_liquidation >= taux_plein
        pension_avant_minimum_et_plafonnement_a_taux_plein = where(taux_de_liquidation > 0, taux_plein * pension_avant_minimum_et_plafonnement / (taux_de_liquidation + (taux_de_liquidation <= 0)), 0)
        pension_avant_minimum = min_(taux_plein * plafond_securite_sociale, pension_avant_minimum_et_plafonnement_a_taux_plein) + (pension_avant_minimum_et_plafonnement - pension_avant_minimum_et_plafonnement_a_taux_plein)
        autres_pensions = individu('arrco_pension_au_31_decembre', period) + individu('agirc_pension_au_31_decembre', period) + individu('fonction_publique_pension_au_31_decembre', period)
        pension_tous_regime_avant_minimum = pension_avant_minimum + autres_pensions
        pension_apres_minimum = where((pension_avant_minimum > 0) * a_atteint_taux_plein * (pension_tous_regime_avant_minimum < minimum_contributif_plafond_annuel), max_(minimum_contributif, pension_avant_minimum), pension_avant_minimum)
        pension_tous_regime_apres_minimum = pension_apres_minimum + autres_pensions
        pension_brute = where((pension_avant_minimum > 0) * a_atteint_taux_plein * (pension_tous_regime_apres_minimum > minimum_contributif_plafond_annuel) * (pension_apres_minimum <= minimum_contributif), min_(max_(minimum_contributif_plafond_annuel - autres_pensions, 0), pension_apres_minimum), pension_apres_minimum)
        return pension_brute

    def formula_2004_01_01(individu, period, parameters):
        pension_avant_minimum_et_plafonnement = individu('regime_general_cnav_pension_avant_minimum_et_plafonnement', period)
        minimum_contributif = individu('regime_general_cnav_pension_minimale', period)
        taux_de_liquidation = individu('regime_general_cnav_taux_de_liquidation', period)
        plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel * conversion_parametre_en_euros(period.start.year)
        taux_plein = parameters(period).retraites.secteur_prive.regime_general_cnav.taux_plein.taux_plein
        pension_avant_minimum_et_plafonnement_a_taux_plein = where(taux_de_liquidation > 0, taux_plein * pension_avant_minimum_et_plafonnement / (taux_de_liquidation + (taux_de_liquidation <= 0)), 0)
        pension_avant_minimum = min_(taux_plein * plafond_securite_sociale, pension_avant_minimum_et_plafonnement_a_taux_plein) + (pension_avant_minimum_et_plafonnement - pension_avant_minimum_et_plafonnement_a_taux_plein)
        a_atteint_taux_plein = taux_de_liquidation >= taux_plein
        pension_brute = where((pension_avant_minimum > 0) * a_atteint_taux_plein, max_(minimum_contributif, pension_avant_minimum), pension_avant_minimum)
        return pension_brute

    def formula_1984(individu, period, parameters):
        pension_avant_minimum_et_plafonnement = individu('regime_general_cnav_pension_avant_minimum_et_plafonnement', period)
        minimum_contributif = individu('regime_general_cnav_pension_minimale', period)
        taux_plein = parameters(period).retraites.secteur_prive.regime_general_cnav.taux_plein.taux_plein
        taux_de_liquidation = individu('regime_general_cnav_taux_de_liquidation', period)
        a_atteint_taux_plein = taux_de_liquidation >= taux_plein
        plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel * conversion_parametre_en_euros(period.start.year)
        pension_avant_minimum_et_plafonnement_a_taux_plein = where(taux_de_liquidation > 0, taux_plein * pension_avant_minimum_et_plafonnement / (taux_de_liquidation + (taux_de_liquidation <= 0)), 0)
        pension_avant_minimum = min_(taux_plein * plafond_securite_sociale, pension_avant_minimum_et_plafonnement_a_taux_plein) + (pension_avant_minimum_et_plafonnement - pension_avant_minimum_et_plafonnement_a_taux_plein)
        pension_brute = where((pension_avant_minimum > 0) * a_atteint_taux_plein, max_(minimum_contributif, pension_avant_minimum), pension_avant_minimum)
        return pension_brute

class regime_general_cnav_pension_brute_au_31_decembre(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension brute au 31 décembre'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('regime_general_cnav_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(period.start.year < annee_de_liquidation):
            return individu.empty_array()
        last_year = period.last_year
        pension_brute_au_31_decembre_annee_precedente = individu('regime_general_cnav_pension_brute_au_31_decembre', last_year)
        revalorisation = parameters(period).retraites.secteur_prive.regime_general_cnav.revalorisation_pension_au_31_decembre
        pension_brute = individu('regime_general_cnav_pension_brute', period)
        return revalorise(pension_brute_au_31_decembre_annee_precedente, pension_brute, annee_de_liquidation, revalorisation, period)

class regime_general_cnav_pension_maximale(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension maximale'

    def formula(individu, period, parameters):
        plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel * conversion_parametre_en_euros(period.start.year)
        taux_plein = parameters(period).retraites.secteur_prive.regime_general_cnav.taux_plein.taux_plein
        pension_plafond_hors_surcote = taux_plein * plafond_securite_sociale
        pension_brute = individu('regime_general_cnav_pension_brute', period)
        taux_de_liquidation = individu('regime_general_cnav_taux_de_liquidation', period)
        surcote = individu('regime_general_cnav_surcote', period)
        pension_surcote = pension_brute / taux_de_liquidation * taux_plein * surcote
        return min_(pension_brute - pension_surcote, pension_plafond_hors_surcote) + pension_surcote

class regime_general_cnav_pension_minimale(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension minimale (minimum contributif du régime général)'

    def formula_2009_01_01(individu, period, parameters):
        """
                Introdcution d'un seuil de trimestres cotisées et de la surcote après minimum contributif.
                La réforme entre en vigueur pour les pensions liquidées au mois d'avril.
                On date la formule du mois de janvier car on travaille en annuel.
                On intègre la condition sur la date de liquidation explicitement.
            """
        regime_general_cnav = parameters(period).retraites.secteur_prive.regime_general_cnav
        minimum_contributif = regime_general_cnav.montant_mico
        mico = minimum_contributif.minimum_contributif.annuel
        mico_majoration = minimum_contributif.minimum_contributif_majore.annuel - mico
        date_de_naissance = individu('date_de_naissance', period)
        duree_de_proratisation = regime_general_cnav.prorat.nombre_trimestres_maximal_pris_en_compte_proratisation_par_generation[date_de_naissance]
        duree_assurance_cible_taux_plein = regime_general_cnav.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]
        duree_assurance_regime_general = individu('regime_general_cnav_duree_assurance', period)
        duree_assurance_personnellement_cotisee_regime_general = individu('regime_general_cnav_duree_assurance_personnellement_cotisee', period)
        duree_assurance_tous_regimes = individu('duree_assurance_tous_regimes', period)
        duree_assurance_cotisee_tous_regimes = individu('duree_assurance_cotisee_tous_regimes', period)
        mono_pensionne_regime_general_ou_polypensionne_carriere_incomplete = (duree_assurance_tous_regimes == duree_assurance_regime_general + individu('regime_general_cnav_duree_assurance_etranger', period)) + (duree_assurance_tous_regimes < duree_assurance_cible_taux_plein)
        polypensionne_cotisant_carriere_complete = not_(mono_pensionne_regime_general_ou_polypensionne_carriere_incomplete)
        numerateur_montant_de_base = select([mono_pensionne_regime_general_ou_polypensionne_carriere_incomplete, polypensionne_cotisant_carriere_complete], [duree_assurance_regime_general, duree_assurance_regime_general])
        denominateur_montant_de_base = select([mono_pensionne_regime_general_ou_polypensionne_carriere_incomplete, polypensionne_cotisant_carriere_complete], [duree_de_proratisation, duree_assurance_tous_regimes])
        coefficient_de_proratisation_montant_de_base = min_(1, numerateur_montant_de_base / denominateur_montant_de_base)
        numerateur_majoration = select([mono_pensionne_regime_general_ou_polypensionne_carriere_incomplete, polypensionne_cotisant_carriere_complete], [duree_assurance_personnellement_cotisee_regime_general, duree_assurance_cotisee_tous_regimes])
        denominateur_majoration = duree_de_proratisation
        liquidation_date = individu('regime_general_cnav_liquidation_date', period)
        condition_de_duree = (duree_assurance_personnellement_cotisee_regime_general >= 120) | (liquidation_date < date(2009, 4, 1))
        coefficient_de_proratisation_majoration = condition_de_duree * min_(1, numerateur_majoration / denominateur_majoration) * min_(1, duree_assurance_regime_general / duree_assurance_tous_regimes)
        surcote = individu('regime_general_cnav_surcote', period)
        return (coefficient_de_proratisation_montant_de_base * mico + coefficient_de_proratisation_majoration * mico_majoration) * (1 + surcote)

    def formula_2004_01_01(individu, period, parameters):
        """Introduction de la majoration du minimum contributif."""
        regime_general_cnav = parameters(period).retraites.secteur_prive.regime_general_cnav
        minimum_contributif = regime_general_cnav.montant_mico
        mico = minimum_contributif.minimum_contributif.annuel
        mico_majoration = minimum_contributif.minimum_contributif_majore.annuel - mico
        date_de_naissance = individu('date_de_naissance', period)
        duree_de_proratisation = regime_general_cnav.prorat.nombre_trimestres_maximal_pris_en_compte_proratisation_par_generation[date_de_naissance]
        duree_assurance_cible_taux_plein = regime_general_cnav.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]
        duree_assurance_regime_general = individu('regime_general_cnav_duree_assurance', period)
        duree_assurance_personnellement_cotisee_regime_general = individu('regime_general_cnav_duree_assurance_personnellement_cotisee', period)
        duree_assurance_tous_regimes_non_ecretee = duree_assurance_regime_general + individu('fonction_publique_duree_assurance', period) + individu('regime_general_cnav_duree_assurance_etranger', period)
        majoration = min_(1, duree_assurance_personnellement_cotisee_regime_general / duree_de_proratisation) * mico_majoration
        mono_pensionne_regime_general_ou_polypensionne_carriere_incomplete = (duree_assurance_tous_regimes_non_ecretee == duree_assurance_regime_general + individu('regime_general_cnav_duree_assurance_etranger', period)) + (duree_assurance_tous_regimes_non_ecretee < duree_assurance_cible_taux_plein)
        return where(mono_pensionne_regime_general_ou_polypensionne_carriere_incomplete, min_(1, duree_assurance_regime_general / duree_de_proratisation), min_(1, duree_assurance_regime_general / duree_assurance_tous_regimes_non_ecretee)) * mico + majoration

    def formula_1983_04_01(individu, period, parameters):
        regime_general_cnav = parameters(period).retraites.secteur_prive.regime_general_cnav
        minimum_contributif = regime_general_cnav.montant_mico
        mico = minimum_contributif.minimum_contributif.annuel
        duree_assurance = individu('regime_general_cnav_duree_assurance', period)
        date_de_naissance = individu('date_de_naissance', period)
        duree_de_proratisation = parameters(period).retraites.secteur_prive.regime_general_cnav.prorat.nombre_trimestres_maximal_pris_en_compte_proratisation_par_generation[date_de_naissance]
        coefficient_de_proratisation = min_(1, duree_assurance / duree_de_proratisation)
        return coefficient_de_proratisation * mico * conversion_parametre_en_euros(period)

    def formula_1941_01_01(indiivdu, period, parameters):
        avts = parameters(period).prestations_sociales.solidarite_insertion.minimum_vieillesse_droits_non_contributifs_de_retraite.avts_av_1961
        return avts * conversion_parametre_en_euros(period)

class regime_general_cnav_pension_servie(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension servie'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('regime_general_cnav_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(annee_de_liquidation > period.start.year):
            return individu.empty_array()
        last_year = period.last_year
        pension_au_31_decembre_annee_precedente = individu('regime_general_cnav_pension_au_31_decembre', last_year)
        revalorisation = parameters(period).retraites.secteur_prive.regime_general_cnav.revalarisation_pension_servie
        pension = individu('regime_general_cnav_pension_au_31_decembre', period)
        return revalorise(pension_au_31_decembre_annee_precedente, pension, annee_de_liquidation, revalorisation, period)

class regime_general_cnav_salaire_de_base(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Salaire de base (salaire brut)'
    set_input = set_input_divide_by_period

class regime_general_cnav_salaire_de_reference(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Salaire annuel moyen de base dit salaire de référence'
    reference = 'https://www.cor-retraites.fr/sites/default/files/2019-06/doc-1554.pdf'

    def formula_1994(individu, period, parameters):
        liquidation_date = individu('regime_general_cnav_liquidation_date', period)
        annee_de_naissance = individu('date_de_naissance', period).astype('datetime64[Y]').astype(int) + 1970
        annees_de_naissance_distinctes = np.unique(annee_de_naissance[liquidation_date >= np.datetime64(period.start)])
        salaire_de_reference = individu.empty_array()
        revalorisation = build_revalorisation_salaire_cummulee(parameters(period).retraites.secteur_prive.regime_general_cnav, period, annee_de_naissance)
        plafond_securite_sociale_annuel_first_year = 1931
        for _annee_de_naissance in sorted(annees_de_naissance_distinctes):
            if _annee_de_naissance + OFFSET >= period.start.year:
                break
            k = int(parameters(period).retraites.secteur_prive.regime_general_cnav.sam.nombre_annees_carriere_entrant_en_jeu_dans_determination_salaire_annuel_moyen[np.array(str(_annee_de_naissance), dtype='datetime64[Y]')])
            mean_over_largest = make_mean_over_largest(k)
            filter = annee_de_naissance == _annee_de_naissance
            first_year = min(_annee_de_naissance + OFFSET, period.start.year - 2)
            arr = np.vstack([min_(((individu('regime_general_cnav_salaire_de_base', period=year) + individu('regime_general_cnav_avpf', period=year)) * ((period.start.year < 2004) | (individu('regime_general_cnav_salaire_de_base', period=year) + individu('regime_general_cnav_avpf', period=year) >= parameters(max(year, 1930)).retraites.secteur_prive.regime_general_cnav.salval.salaire_validant_trimestre[individu('regime_general_cnav_salaire_validant_trimestre', year)] * conversion_parametre_en_euros(year))))[filter], parameters(max(year, plafond_securite_sociale_annuel_first_year)).prelevements_sociaux.pss.plafond_securite_sociale_annuel * conversion_parametre_en_euros(year)) * revalorisation.get(year, revalorisation[min(revalorisation.keys())]) for year in range(period.start.year - 1, first_year, -1)])
            compute_salaire_de_reference(mean_over_largest, arr, salaire_de_reference, filter)
        return salaire_de_reference

    def formula_1972(individu, period, parameters):
        """L'avpf n'existe pas avant 1972."""
        n = parameters(period).retraites.secteur_prive.regime_general_cnav.sam.nombre_annees_carriere_entrant_en_jeu_dans_determination_salaire_annuel_moyen.before_1934_01_01
        mean_over_largest = functools.partial(mean_over_k_nonzero_largest, k=n)
        annee_initiale = (individu('date_de_naissance', period).astype('datetime64[Y]').astype(int) + 1970).min()
        annee_de_naissance = individu('date_de_naissance', period).astype('datetime64[Y]').astype(int) + 1970
        revalorisation = build_revalorisation_salaire_cummulee(parameters(period).retraites.secteur_prive.regime_general_cnav, period, annee_de_naissance)
        plafond_securite_sociale_annuel_first_year = 1931
        salaire_de_refererence = np.apply_along_axis(mean_over_largest, axis=0, arr=np.vstack([min_(individu('regime_general_cnav_salaire_de_base', period=year) + individu('regime_general_cnav_avpf', period=year), parameters(max(year, plafond_securite_sociale_annuel_first_year)).prelevements_sociaux.pss.plafond_securite_sociale_annuel * conversion_parametre_en_euros(year)) * revalorisation.get(year, revalorisation[min(revalorisation.keys())]) for year in range(period.start.year - 1, annee_initiale + OFFSET, -1)]))
        return salaire_de_refererence

    def formula(individu, period, parameters):
        n = parameters(1972).retraites.secteur_prive.regime_general_cnav.sam.nombre_annees_carriere_entrant_en_jeu_dans_determination_salaire_annuel_moyen.before_1934_01_01
        mean_over_largest = functools.partial(mean_over_k_nonzero_largest, k=n)
        annee_initiale = (individu('date_de_naissance', period).astype('datetime64[Y]').astype(int) + 1970).min()
        annee_de_naissance = individu('date_de_naissance', period).astype('datetime64[Y]').astype(int) + 1970
        revalorisation = build_revalorisation_salaire_cummulee(parameters(period).retraites.secteur_prive.regime_general_cnav, period, annee_de_naissance)
        plafond_securite_sociale_annuel_first_year = 1931
        salaire_de_refererence = np.apply_along_axis(mean_over_largest, axis=0, arr=np.vstack([min_(individu('regime_general_cnav_salaire_de_base', period=year), parameters(max(year, plafond_securite_sociale_annuel_first_year)).prelevements_sociaux.pss.plafond_securite_sociale_annuel * conversion_parametre_en_euros(year)) * revalorisation.get(year, revalorisation[min(revalorisation.keys())]) for year in range(period.start.year - 1, annee_initiale + OFFSET, -1)]))
        return salaire_de_refererence

class regime_general_cnav_salaire_validant_trimestre(Variable):
    value_type = Enum
    possible_values = TypesSalaireValidantTrimestre
    default_value = TypesSalaireValidantTrimestre.metropole
    entity = Person
    label = 'Salaire validant un trimestre utilisé'
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

class regime_general_cnav_surcote(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Surcote'

    def formula_2009_04_01(individu, period, parameters):
        taux_surcote = parameters(period).retraites.secteur_prive.regime_general_cnav.surcote.taux_surcote_par_trimestre_cotise_selon_date_cotisation.apres_01_01_2004['partir_65_ans']
        surcote_trimestres = individu('regime_general_cnav_surcote_trimestres', period)
        return taux_surcote * surcote_trimestres

    def formula_2007_01_01(individu, period, parameters):
        taux_surcote_par_trimestre = parameters(period).retraites.secteur_prive.regime_general_cnav.surcote.taux_surcote_par_trimestre_cotise_selon_date_cotisation.apres_01_01_2004
        taux_surcote_par_trimestre_moins_de_4_trimestres = taux_surcote_par_trimestre['moins_de_4_trimestres']
        taux_surcote_par_trimestre_plus_de_5_trimestres = taux_surcote_par_trimestre['plus_de_5_trimestres']
        taux_surcote_par_trimestre_partir_65_ans = taux_surcote_par_trimestre['partir_65_ans']
        date_de_naissance = individu('date_de_naissance', period)
        liquidation_date = individu('regime_general_cnav_liquidation_date', period)
        age_en_mois_a_la_liquidation = (liquidation_date - date_de_naissance).astype('timedelta64[M]').astype(int)
        trimestres_surcote = individu('regime_general_cnav_surcote_trimestres', period)
        trimestres_surcote_au_dela_de_65_ans = min_(trimestres_surcote, max_(0, np.floor((age_en_mois_a_la_liquidation - 65 * 12) / 3)))
        trimestres_surcote_en_deca_de_65_ans = max_(0, trimestres_surcote - trimestres_surcote_au_dela_de_65_ans)
        surcote = taux_surcote_par_trimestre_moins_de_4_trimestres * min_(4, trimestres_surcote_en_deca_de_65_ans) + taux_surcote_par_trimestre_plus_de_5_trimestres * max_(0, trimestres_surcote_en_deca_de_65_ans - 4) + taux_surcote_par_trimestre_partir_65_ans * trimestres_surcote_au_dela_de_65_ans
        return surcote

    def formula_2004_01_01(individu, period, parameters):
        taux_surcote_par_trimestre_moins_de_4_trimestres = parameters(period).retraites.secteur_prive.regime_general_cnav.surcote.taux_surcote_par_trimestre_cotise_selon_date_cotisation.apres_01_01_2004['moins_de_4_trimestres']
        surcote_trimestres = individu('regime_general_cnav_surcote_trimestres', period)
        return taux_surcote_par_trimestre_moins_de_4_trimestres * surcote_trimestres

    def formula_1983_04_01(individu, period):
        return individu.empty_array()

    def formula_1945(individu, period):
        coefficient_majoration_par_trimestre = 0.1 / 4
        surcote_trimestres = individu('regime_general_cnav_surcote_trimestres', period)
        return coefficient_majoration_par_trimestre * surcote_trimestres

class regime_general_cnav_surcote_trimestres(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = 'Trimestres de surcote'

    def formula_2004_01_01(individu, period, parameters):
        liquidation_date = individu('regime_general_cnav_liquidation_date', period)
        ouverture_des_droits_date = individu('regime_general_cnav_ouverture_des_droits_date', period)
        ouverture_des_droits_date_surcote = next_calendar_quarter_start_date(ouverture_des_droits_date)
        duree_assurance_cotisee_annuelle = individu('regime_general_cnav_duree_assurance_cotisee_annuelle', period) + sum((individu(f'{regime}_duree_de_service_cotisee_annuelle', period) for regime in REGIMES_DE_BASE if regime != 'regime_general_cnav'))
        surcote_trimestres_periode_precedente = individu('regime_general_cnav_surcote_trimestres', period.last_year)
        surcote_trimestres_max = np.clip(count_calendar_quarters(start_date=max_(ouverture_des_droits_date_surcote, np.datetime64(period.start)), stop_date=liquidation_date), 0, 4)
        surcote_trimestres_periode_actuelle = where((liquidation_date >= ouverture_des_droits_date_surcote) & (ouverture_des_droits_date_surcote <= np.datetime64(period.start)), np.clip(duree_assurance_cotisee_annuelle, 0, surcote_trimestres_max), 0)
        trimestres_apres_aod = surcote_trimestres_periode_precedente + surcote_trimestres_periode_actuelle
        majoration_duree_assurance_avant_liquidation = sum(((liquidation_date >= np.datetime64(period.offset(1, 'year').start)) * individu(f'{regime}_majoration_duree_assurance', period) for regime in REGIMES_DE_BASE))
        duree_assurance_tous_regimes = individu('duree_assurance_tous_regimes', period) + majoration_duree_assurance_avant_liquidation
        date_de_naissance = individu('date_de_naissance', period)
        duree_assurance_cible_taux_plein = parameters(period).retraites.secteur_prive.regime_general_cnav.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]
        surcote_trimestres = max_(0, min_(trimestres_apres_aod, duree_assurance_tous_regimes - duree_assurance_cible_taux_plein))
        return surcote_trimestres

    def formula_1983_04_01(individu, period):
        return individu.empty_array()

    def formula_1945(individu, period):
        aad = 65
        liquidation_date = individu('regime_general_cnav_liquidation_date', period)
        age_en_mois_a_la_liquidation = (liquidation_date - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        surcote_trimestres = max_(0, np.floor((age_en_mois_a_la_liquidation - aad * 12) / 3))
        return surcote_trimestres

class regime_general_cnav_surcote_trimestres_effectifs(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = 'Trimestres de surcote effectifs'

    def formula_2009(individu, period):
        return individu('regime_general_cnav_surcote_trimestres', period)

    def formula_2004(individu, period):
        return individu('regime_general_cnav_surcote_trimestres', period) * (individu('regime_general_cnav_pension_brute', period) > individu('regime_general_cnav_pension_minimale', period))

    def formula_1945(individu, period):
        return individu('regime_general_cnav_surcote_trimestres', period)

class regime_general_cnav_taux_de_liquidation(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Taux de liquidation de la pension'

    def formula(individu, period, parameters):
        decote = individu('regime_general_cnav_decote', period)
        surcote = individu('regime_general_cnav_surcote', period)
        taux_plein = parameters(period).retraites.secteur_prive.regime_general_cnav.taux_plein.taux_plein
        return taux_plein * (1 - decote + surcote)

class regime_general_cnav_taux_de_liquidation_effectif(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Taux de liquidation de la pension'

    def formula(individu, period, parameters):
        decote = individu('regime_general_cnav_decote', period)
        surcote = individu('regime_general_cnav_surcote', period) * (individu('regime_general_cnav_surcote_trimestres_effectifs', period) > 0)
        taux_plein = parameters(period).retraites.secteur_prive.regime_general_cnav.taux_plein.taux_plein
        return taux_plein * (1 - decote + surcote)