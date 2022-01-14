"""Abstract regimes definition."""
from datetime import datetime
import numpy as np
from openfisca_core.model_api import *
from openfisca_core.errors.variable_not_found_error import VariableNotFoundError
from openfisca_france_pension.entities import Person

def revalorise(variable_servie_annee_precedente, variable_originale, annee_de_liquidation, revalorisation, period):
    return select([annee_de_liquidation > period.start.year, annee_de_liquidation == period.start.year, annee_de_liquidation < period.start.year], [0, variable_originale, variable_servie_annee_precedente * revalorisation])
'Régime de base du secteur privé: régime général de la CNAV.'
import functools
import numpy as np
from openfisca_core.model_api import *
from openfisca_core.parameters import ParameterNotFound
from openfisca_core.periods import YEAR
from openfisca_core.variables import Variable
from openfisca_france_pension.entities import Person
from openfisca_france_pension.regimes.regime import AbstractRegimeDeBase
from openfisca_france_pension.tools import mean_over_k_nonzero_largest
from openfisca_france_pension.variables.hors_regime import TypesCategorieSalarie, TypesStatutDuCotisant
from openfisca_france_pension.variables.hors_regime import TypesRaisonDepartTauxPleinAnticipe
REVAL_S_YEAR_MIN = 1949
EURO_EN_FRANCS = 6.55957

def compute_salaire_de_reference(mean_over_largest, arr, salaire_de_refererence, filter):
    salaire_de_refererence[filter] = np.apply_along_axis(mean_over_largest, axis=0, arr=arr)

def make_mean_over_largest(k):

    def mean_over_largest(vector):
        return mean_over_k_nonzero_largest(vector, k=int(k))
    return mean_over_largest

class regime_general_cnav_age_annulation_decote(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Âge auquel un individu peut partir au taux plein (éventuellement de façon anticipée)'

    def formula_1976_07_01(individu, period, parameters):
        aad_anciens_deportes = parameters(period).secteur_prive.regime_general_cnav.aad.age_annulation_decote_anciens_deportes
        aad_inaptitude = parameters(period).secteur_prive.regime_general_cnav.aad.age_annulation_decote_inaptitude
        aad_anciens_anciens_combattants = parameters(period).secteur_prive.regime_general_cnav.aad.age_annulation_decote_anciens_combattants
        aad_anciens_travailleurs_manuels = parameters(period).secteur_prive.regime_general_cnav.aad.travailleurs_manuels.age_annulation_decote
        aad_droit_commun = individu('regime_general_cnav_age_annulation_decote_droit_commun', period)
        raison_depart_taux_plein_anticipe = individu('raison_depart_taux_plein_anticipe', period)
        aad = switch(raison_depart_taux_plein_anticipe, {TypesRaisonDepartTauxPleinAnticipe.non_concerne: aad_droit_commun, TypesRaisonDepartTauxPleinAnticipe.ancien_deporte: aad_anciens_deportes, TypesRaisonDepartTauxPleinAnticipe.inapte: aad_inaptitude, TypesRaisonDepartTauxPleinAnticipe.ancien_combattant: aad_anciens_anciens_combattants, TypesRaisonDepartTauxPleinAnticipe.travailleur_manuel: aad_anciens_travailleurs_manuels})
        return aad

    def formula_1974_01_01(individu, period, parameters):
        aad_droit_commun = 65
        aad_anciens_deportes = parameters(period).secteur_prive.regime_general_cnav.aad.age_annulation_decote_anciens_deportes
        aad_inaptitude = parameters(period).secteur_prive.regime_general_cnav.aad.age_annulation_decote_inaptitude
        aad_anciens_anciens_combattants = parameters(period).secteur_prive.regime_general_cnav.aad.age_annulation_decote_anciens_combattants
        raison_depart_taux_plein_anticipe = individu('raison_depart_taux_plein_anticipe', period)
        aad = switch(raison_depart_taux_plein_anticipe, {TypesRaisonDepartTauxPleinAnticipe.non_concerne: aad_droit_commun, TypesRaisonDepartTauxPleinAnticipe.ancien_deporte: aad_anciens_deportes, TypesRaisonDepartTauxPleinAnticipe.inapte: aad_inaptitude, TypesRaisonDepartTauxPleinAnticipe.ancien_combattant: aad_anciens_anciens_combattants})
        return aad

    def formula_1972_01_01(individu, period, parameters):
        aad_droit_commun = 65
        aad_anciens_deportes = parameters(period).secteur_prive.regime_general_cnav.aad.age_annulation_decote_anciens_deportes
        aad_inaptitude = parameters(period).secteur_prive.regime_general_cnav.aad.age_annulation_decote_inaptitude
        raison_depart_taux_plein_anticipe = individu('raison_depart_taux_plein_anticipe', period)
        aad = switch(raison_depart_taux_plein_anticipe, {TypesRaisonDepartTauxPleinAnticipe.non_concerne: aad_droit_commun, TypesRaisonDepartTauxPleinAnticipe.ancien_deporte: aad_anciens_deportes, TypesRaisonDepartTauxPleinAnticipe.inapte: aad_inaptitude})
        return aad

    def formula_1965_05_01(individu, period, parameters):
        aad_droit_commun = 65
        aad_anciens_deportes = parameters(period).secteur_prive.regime_general_cnav.aad.age_annulation_decote_anciens_deportes
        raison_depart_taux_plein_anticipe = individu('raison_depart_taux_plein_anticipe', period)
        aad = switch(raison_depart_taux_plein_anticipe, {TypesRaisonDepartTauxPleinAnticipe.non_concerne: aad_droit_commun, TypesRaisonDepartTauxPleinAnticipe.ancien_deporte: aad_anciens_deportes})
        return aad

    def formula_1945(individu, period, parameters):
        aad_droit_commun = 65
        return aad_droit_commun

class regime_general_cnav_age_annulation_decote_droit_commun(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Âge auquel un individu peut partir au taux plein hors départ anticipé'

    def formula_2011_07_01(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        aad_annee = parameters(period).secteur_prive.regime_general_cnav.aad.age_annulation_decote_en_fonction_date_naissance[date_de_naissance].annee
        aad_mois = parameters(period).secteur_prive.regime_general_cnav.aad.age_annulation_decote_en_fonction_date_naissance[date_de_naissance].mois
        return aad_annee + aad_mois / 12

    def formula_1945(individu, period, parameters):
        return parameters(period).secteur_prive.regime_general_cnav.aad.age_annulation_decote_en_fonction_date_naissance.before_1951_07_01.annee

class regime_general_cnav_coefficient_de_proratisation(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Coefficient de proratisation'

    def formula_2011_07_01(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        duree_de_proratisation = parameters(period).secteur_prive.regime_general_cnav.prorat.nombre_trimestres_maximal_pris_en_compte_proratisation_par_generation[date_de_naissance]
        aad = individu('regime_general_cnav_age_annulation_decote', period)
        coefficient_minoration_par_trimestre = parameters(period).secteur_prive.regime_general_cnav.decote.coefficient_minoration_par_trimestres_manquants.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants[date_de_naissance]
        liquidation_date = individu('regime_general_cnav_liquidation_date', period)
        age_en_mois_a_la_liquidation = (liquidation_date - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        trimestres_apres_aad = max_(0, np.trunc((age_en_mois_a_la_liquidation - aad * 12) / 3))
        trimestres = individu('regime_general_cnav_duree_assurance', period)
        duree_assurance_corrigee = min_(duree_de_proratisation, trimestres * (1 + trimestres_apres_aad * coefficient_minoration_par_trimestre))
        coefficient = min_(1, duree_assurance_corrigee / duree_de_proratisation)
        return coefficient

    def formula_1983_04_01(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        duree_de_proratisation = parameters(period).secteur_prive.regime_general_cnav.prorat.nombre_trimestres_maximal_pris_en_compte_proratisation_par_generation[date_de_naissance]
        aad = individu('regime_general_cnav_age_annulation_decote', period)
        coefficient_minoration_par_trimestre = parameters(period).secteur_prive.regime_general_cnav.decote.coefficient_minoration_par_trimestres_manquants.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants[date_de_naissance]
        liquidation_date = individu('regime_general_cnav_liquidation_date', period)
        age_en_mois_a_la_liquidation = (liquidation_date - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        trimestres_apres_aad = max_(0, np.trunc((age_en_mois_a_la_liquidation - aad * 12) / 3))
        trimestres = individu('regime_general_cnav_duree_assurance', period)
        duree_assurance_corrigee = min_(duree_de_proratisation, trimestres * (1 + trimestres_apres_aad * coefficient_minoration_par_trimestre))
        coefficient = min_(1, duree_assurance_corrigee / duree_de_proratisation)
        return coefficient

    def formula_1948(individu, period, parameters):
        trimestres = individu('regime_general_cnav_duree_assurance', period)
        duree_de_proratisation = parameters(period).secteur_prive.regime_general_cnav.prorat.nombre_trimestres_maximal_pris_en_compte_proratisation_par_generation.before_1944_01_01
        duree_assurance_corrigee = trimestres + (duree_de_proratisation - trimestres) / 2
        coefficient = min_(1, duree_assurance_corrigee / duree_de_proratisation)
        return coefficient

    def formula_1946(individu, period, parameters):
        duree_de_proratisation = parameters(period).secteur_prive.regime_general_cnav.prorat.nombre_trimestres_maximal_pris_en_compte_proratisation_par_generation.before_1944_01_01
        trimestres = individu('regime_general_cnav_duree_assurance', period)
        coefficient = min_(1, trimestres / duree_de_proratisation)
        return coefficient

class regime_general_cnav_cotisation(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'cotisation retraite employeur'

    def formula(individu, period):
        return individu('regime_general_cnav_cotisation_employeur', period) + individu('regime_general_cnav_cotisation_salarie', period)

class regime_general_cnav_cotisation_employeur(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Cotisation employeur'

    def formula(individu, period, parameters):
        categorie_salarie = individu('categorie_salarie', period)
        salaire_de_base = individu('salaire_de_base', period)
        plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel
        employeur = parameters(period).secteur_prive.regime_general_cnav.prelevements_sociaux.employeur
        salarie_concerne = (categorie_salarie == TypesCategorieSalarie.prive_non_cadre) + (categorie_salarie == TypesCategorieSalarie.prive_cadre) + (categorie_salarie == TypesCategorieSalarie.public_non_titulaire)
        return salarie_concerne * (employeur.vieillesse_deplafonnee.calc(salaire_de_base, factor=plafond_securite_sociale) + employeur.vieillesse_plafonnee.calc(salaire_de_base, factor=plafond_securite_sociale))

class regime_general_cnav_cotisation_salarie(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Cotisation salarié'

    def formula(individu, period, parameters):
        categorie_salarie = individu('categorie_salarie', period)
        salaire_de_base = individu('salaire_de_base', period)
        plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel
        salarie = parameters(period).secteur_prive.regime_general_cnav.prelevements_sociaux.salarie
        salarie_concerne = (categorie_salarie == TypesCategorieSalarie.prive_non_cadre) + (categorie_salarie == TypesCategorieSalarie.prive_cadre) + (categorie_salarie == TypesCategorieSalarie.public_non_titulaire)
        return salarie_concerne * (salarie.vieillesse_deplafonnee.calc(salaire_de_base, factor=plafond_securite_sociale) + salarie.vieillesse_plafonnee.calc(salaire_de_base, factor=plafond_securite_sociale))

class regime_general_cnav_decote(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Décote'

    def formula_1983_04_01(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        coefficient_minoration_par_trimestre = parameters(period).secteur_prive.regime_general_cnav.decote.coefficient_minoration_par_trimestres_manquants.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants[date_de_naissance]
        decote_trimestres = individu('regime_general_cnav_decote_trimestres', period)
        decote = coefficient_minoration_par_trimestre * decote_trimestres
        return decote

    def formula_1945(individu, period, parameters):
        decote_trimestres = individu('regime_general_cnav_decote_trimestres', period)
        coefficient_minoration_par_trimestre = parameters(period).secteur_prive.regime_general_cnav.decote.coefficient_minoration_par_trimestres_manquants.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants.before_1944_01_01
        return coefficient_minoration_par_trimestre * decote_trimestres

class regime_general_cnav_decote_trimestres(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Trimestres de décote'

    def formula_2011_07_01(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        aad = individu('regime_general_cnav_age_annulation_decote', period)
        duree_assurance_cible_taux_plein = parameters(period).secteur_prive.regime_general_cnav.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]
        age_en_mois_a_la_liquidation = (individu('regime_general_cnav_liquidation_date', period) - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        trimestres_avant_aad = np.trunc((aad * 12 - age_en_mois_a_la_liquidation) / 3)
        duree_assurance_tous_regimes = individu('duree_assurance_tous_regimes', period)
        decote_trimestres = max_(0, min_(duree_assurance_cible_taux_plein - duree_assurance_tous_regimes, trimestres_avant_aad))
        return decote_trimestres

    def formula_1983_04_01(individu, period, parameters):
        aad = individu('regime_general_cnav_age_annulation_decote', period)
        date_de_naissance = individu('date_de_naissance', period)
        duree_assurance_cible_taux_plein = parameters(period).secteur_prive.regime_general_cnav.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]
        age_en_mois_a_la_liquidation = (individu('regime_general_cnav_liquidation_date', period) - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        trimestres_avant_aad = np.trunc((aad * 12 - age_en_mois_a_la_liquidation) / 3)
        duree_assurance_tous_regimes = individu('duree_assurance_tous_regimes', period)
        decote_trimestres = max_(0, min_(duree_assurance_cible_taux_plein - duree_assurance_tous_regimes, trimestres_avant_aad))
        return decote_trimestres

    def formula_1945(individu, period, parameters):
        aad = individu('regime_general_cnav_age_annulation_decote', period)
        liquidation_date = individu('regime_general_cnav_liquidation_date', period)
        age_en_mois_a_la_liquidation = (liquidation_date - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        decote_trimestres = max_(0, np.trunc((aad * 12 - age_en_mois_a_la_liquidation) / 3))
        return decote_trimestres

class regime_general_cnav_duree_assurance(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance (trimestres validés au régime général)"

    def formula(individu, period, parameters):
        duree_assurance_cotisee = individu('regime_general_cnav_duree_assurance_cotisee', period)
        majoration_duree_assurance = individu('regime_general_cnav_majoration_duree_assurance', period)
        return duree_assurance_cotisee + majoration_duree_assurance

class regime_general_cnav_duree_assurance_assimilee_annuelle(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance validée au titre des périodes assimilées (en trimestres cotisés seulement l'année considérée)"

class regime_general_cnav_duree_assurance_cotisee(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance cotisée cummulée (trimestres cotisés au régime général depuis l'entrée dans le régme)"

    def formula(individu, period, parameters):
        duree_assurance_travail_annuelle = individu('regime_general_cnav_duree_assurance_travail_annuelle', period)
        duree_assurance_periodes_assimilees_annuelles = sum((individu(f'regime_general_cnav_duree_assurance_periode_assimilee_{periode_assimilee}_annuelle', period) for periode_assimilee in ['chomage', 'maladie', 'accident_du_travail', 'invalidite', 'service_national', 'autre']))
        duree_assurance_annuelle = min_(duree_assurance_travail_annuelle + duree_assurance_periodes_assimilees_annuelles, 4)
        duree_assurance_cotisee_annee_precedente = individu('regime_general_cnav_duree_assurance_cotisee', period.last_year)
        if all((duree_assurance_annuelle == 0) & (duree_assurance_cotisee_annee_precedente == 0)):
            return individu.empty_array()
        return individu('regime_general_cnav_duree_assurance_cotisee', period.last_year) + duree_assurance_annuelle

class regime_general_cnav_duree_assurance_periode_assimilee_accident_du_travail_annuelle(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance au titre des accidents du travail (en trimestres cotisés l'année considérée)"

class regime_general_cnav_duree_assurance_periode_assimilee_autre_annuelle(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance au titre des autres périodes assimilées (en trimestres cotisés l'année considérée)"

class regime_general_cnav_duree_assurance_periode_assimilee_chomage_annuelle(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance au titre du chômage (en trimestres cotisés jusqu'à l'année considérée)"

class regime_general_cnav_duree_assurance_periode_assimilee_invalidite_annuelle(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance au titre de l'invalidté (en trimestres cotisés l'année considérée)"

class regime_general_cnav_duree_assurance_periode_assimilee_maladie_annuelle(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance au titre de la maladie (en trimestres cotisés l'année considérée)"

class regime_general_cnav_duree_assurance_periode_assimilee_service_national_annuelle(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance au titre du service national (en trimestres cotisés l'année considérée)"

class regime_general_cnav_duree_assurance_travail_annuelle(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance cotisée donc hors majoration de durée d'assurance (en trimestres cotisés l'année considérée)"

    def formula(individu, period, parameters):
        statut_du_cotisant = individu('statut_du_cotisant', period)
        duree_assurance_travail_emploi_annuelle = individu('regime_general_cnav_duree_assurance_travail_emploi_annuelle', period)
        duree_assurance_travail_avpf_annuelle = individu('regime_general_cnav_duree_assurance_travail_avpf_annuelle', period)
        return where((statut_du_cotisant == TypesStatutDuCotisant.emploi) | (statut_du_cotisant == TypesStatutDuCotisant.avpf), min_(duree_assurance_travail_emploi_annuelle + duree_assurance_travail_avpf_annuelle, 4), 0)

class regime_general_cnav_duree_assurance_travail_avpf_annuelle(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance cotisée avpf (en trimestres cotisés jusqu'à l'année considérée)"

    def formula_1972(individu, period, parameters):
        avpf = individu('avpf', period)
        smic_trimestriel = parameters(period).marche_travail.salaire_minimum.smic.smic_brut_mensuel * 3
        conversion_en_euros = 1 / EURO_EN_FRANCS if period.start.year < 2002 else 1
        avpf = avpf * conversion_en_euros
        return min_((avpf / smic_trimestriel).astype(int), 4)

class regime_general_cnav_duree_assurance_travail_emploi_annuelle(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance cotisée en emploi (en trimestres cotisés jusqu'à l'année considérée)"

    def formula(individu, period, parameters):
        salaire_de_base = individu('salaire_de_base', period)
        try:
            salaire_validant_un_trimestre = parameters(period).secteur_prive.regime_general_cnav.salval.salaire_validant_trimestre.metropole
        except ParameterNotFound:
            import openfisca_core.periods as periods
            salaire_validant_un_trimestre = parameters(periods.period(1930)).secteur_prive.regime_general_cnav.salval.salaire_validant_trimestre.metropole
        conversion_en_euros = 1 / EURO_EN_FRANCS if period.start.year < 2002 else 1
        salaire_validant_un_trimestre = salaire_validant_un_trimestre * conversion_en_euros
        return min_((salaire_de_base / salaire_validant_un_trimestre).astype(int), 4)

class regime_general_cnav_liquidation_date(Variable):
    value_type = date
    entity = Person
    definition_period = ETERNITY
    label = 'Date de liquidation'
    default_value = datetime.max.date()

class regime_general_cnav_majoration_duree_assurance(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Majoration de durée d'assurance (trimestres augmentant la durée d'assurance au régime général)"

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('regime_general_cnav_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        liquidation = annee_de_liquidation == period.start.year
        majoration_duree_assurance_enfant = individu('nombre_enfants', period) * 8
        return liquidation * majoration_duree_assurance_enfant

class regime_general_cnav_majoration_pension(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Majoration de pension'

    def formula(individu, period, parameters):
        nombre_enfants = individu('nombre_enfants', period)
        pension_brute = individu('regime_general_cnav_pension_brute', period)
        return 0.1 * pension_brute * (nombre_enfants >= 3)

class regime_general_cnav_majoration_pension_servie(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Majoration de pension servie'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('regime_general_cnav_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(annee_de_liquidation > period.start.year):
            return individu.empty_array()
        last_year = period.start.period('year').offset(-1)
        majoration_pension_servie_annee_precedente = individu('regime_general_cnav_majoration_pension_servie', last_year)
        revalorisation = parameters(period).secteur_prive.regime_general_cnav.reval_p.coefficient
        majoration_pension = individu('regime_general_cnav_majoration_pension', period)
        return revalorise(majoration_pension_servie_annee_precedente, majoration_pension, annee_de_liquidation, revalorisation, period)

class regime_general_cnav_pension(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension'

    def formula(individu, period):
        pension_brute = individu('regime_general_cnav_pension_brute', period)
        majoration_pension = individu('regime_general_cnav_majoration_pension', period)
        return pension_brute + majoration_pension

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

    def formula_2012(individu, period, parameters):
        pension_avant_minimum_et_plafonnement = individu('regime_general_cnav_pension_avant_minimum_et_plafonnement', period)
        minimum_contributif = individu('regime_general_cnav_pension_minimale', period)
        taux_de_liquidation = individu('regime_general_cnav_taux_de_liquidation', period)
        minimum_contributif_plafond_annuel = 12 * parameters(period).secteur_prive.regime_general_cnav.plafond_mico.minimum_contributif_plafond_mensuel
        plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel
        taux_plein = parameters(period).secteur_prive.regime_general_cnav.taux_plein.taux_plein
        a_atteint_taux_plein = taux_de_liquidation >= taux_plein
        pension_avant_minimum_et_plafonnement_a_taux_plein = where(taux_de_liquidation > 0, taux_plein * pension_avant_minimum_et_plafonnement / (taux_de_liquidation + (taux_de_liquidation <= 0)), 0)
        pension_avant_minimum = min_(taux_plein * plafond_securite_sociale, pension_avant_minimum_et_plafonnement_a_taux_plein) + (pension_avant_minimum_et_plafonnement - pension_avant_minimum_et_plafonnement_a_taux_plein)
        autres_pensions = individu('arrco_pension_servie', period) + individu('agirc_pension_servie', period) + individu('fonction_publique_pension_servie', period)
        pension_tous_regime_avant_minimum = pension_avant_minimum + autres_pensions
        pension_apres_minimum = where((pension_avant_minimum > 0) * a_atteint_taux_plein * (pension_tous_regime_avant_minimum < minimum_contributif_plafond_annuel), max_(minimum_contributif, pension_avant_minimum), pension_avant_minimum)
        pension_tous_regime_apres_minimum = pension_apres_minimum + autres_pensions
        pension_brute = where((pension_tous_regime_apres_minimum > minimum_contributif_plafond_annuel) * (pension_apres_minimum <= minimum_contributif), minimum_contributif_plafond_annuel - autres_pensions, pension_apres_minimum)
        return pension_brute

    def formula_1984(individu, period, parameters):
        pension_avant_minimum_et_plafonnement = individu('regime_general_cnav_pension_avant_minimum_et_plafonnement', period)
        minimum_contributif = individu('regime_general_cnav_pension_minimale', period)
        taux_plein = parameters(period).secteur_prive.regime_general_cnav.taux_plein.taux_plein
        taux_de_liquidation = individu('regime_general_cnav_taux_de_liquidation', period)
        a_atteint_taux_plein = taux_de_liquidation >= taux_plein
        plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel
        pension_avant_minimum_et_plafonnement_a_taux_plein = where(taux_de_liquidation > 0, taux_plein * pension_avant_minimum_et_plafonnement / (taux_de_liquidation + (taux_de_liquidation <= 0)), 0)
        pension_avant_minimum = min_(taux_plein * plafond_securite_sociale, pension_avant_minimum_et_plafonnement_a_taux_plein) + (pension_avant_minimum_et_plafonnement - pension_avant_minimum_et_plafonnement_a_taux_plein)
        pension_brute = where((pension_avant_minimum > 0) * a_atteint_taux_plein, max_(minimum_contributif, pension_avant_minimum), pension_avant_minimum)
        return pension_brute

class regime_general_cnav_pension_brute_servie(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension servie'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('regime_general_cnav_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(annee_de_liquidation > period.start.year):
            return individu.empty_array()
        last_year = period.start.period('year').offset(-1)
        pension_brute_servie_annee_precedente = individu('regime_general_cnav_pension_brute_servie', last_year)
        revalorisation = parameters(period).secteur_prive.regime_general_cnav.reval_p.coefficient
        pension_brute = individu('regime_general_cnav_pension_brute', period)
        return revalorise(pension_brute_servie_annee_precedente, pension_brute, annee_de_liquidation, revalorisation, period)

class regime_general_cnav_pension_maximale(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension maximale'

    def formula(individu, period, parameters):
        plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel
        taux_plein = parameters(period).secteur_prive.regime_general_cnav.taux_plein.taux_plein
        pension_plafond_hors_sucote = taux_plein * plafond_securite_sociale
        pension_brute = individu('regime_general_cnav_pension_brute', period)
        taux_de_liquidation = individu('regime_general_cnav_taux_de_liquidation', period)
        surcote = individu('regime_general_cnav_surcote', period)
        pension_surcote = pension_brute / taux_de_liquidation * taux_plein * surcote
        return min_(pension_brute - pension_surcote, pension_plafond_hors_sucote) + pension_surcote

class regime_general_cnav_pension_minimale(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension minimale (minimum contributif du régime général)'

    def formula_2004_01_01(individu, period, parameters):
        regime_general_cnav = parameters(period).secteur_prive.regime_general_cnav
        minimum_contributif = regime_general_cnav.montant_mico
        mico = minimum_contributif.minimum_contributif.annuel
        mico_majoration = minimum_contributif.minimum_contributif_majore.annuel - mico
        date_de_naissance = individu('date_de_naissance', period)
        duree_de_proratisation = regime_general_cnav.prorat.nombre_trimestres_maximal_pris_en_compte_proratisation_par_generation[date_de_naissance]
        duree_assurance_cible_taux_plein = regime_general_cnav.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]
        duree_assurance_regime_general = individu('regime_general_cnav_duree_assurance', period)
        duree_assurance_cotisee_regime_general = individu('regime_general_cnav_duree_assurance_cotisee', period)
        duree_assurance_tous_regimes = individu('duree_assurance_tous_regimes', period)
        duree_assurance_cotisee_tous_regimes = individu('duree_assurance_cotisee_tous_regimes', period)
        mono_pensionne_regime_general_ou_polypensionne_carriere_incomplete = (duree_assurance_tous_regimes == duree_assurance_regime_general) + (duree_assurance_tous_regimes < duree_assurance_cible_taux_plein)
        polypensionne_cotisant_moins_que_duree_requise = not_(mono_pensionne_regime_general_ou_polypensionne_carriere_incomplete) + (duree_assurance_cotisee_tous_regimes < duree_de_proratisation)
        polypensionne_cotisant_moins_plus_duree_requise = not_(mono_pensionne_regime_general_ou_polypensionne_carriere_incomplete) + (duree_assurance_cotisee_tous_regimes >= duree_de_proratisation)
        numerateur_montant_de_base = select([mono_pensionne_regime_general_ou_polypensionne_carriere_incomplete, polypensionne_cotisant_moins_que_duree_requise, polypensionne_cotisant_moins_plus_duree_requise], [duree_assurance_regime_general, duree_assurance_regime_general, duree_assurance_regime_general])
        denominateur_montant_de_base = select([mono_pensionne_regime_general_ou_polypensionne_carriere_incomplete, polypensionne_cotisant_moins_que_duree_requise, polypensionne_cotisant_moins_plus_duree_requise], [duree_de_proratisation, duree_assurance_tous_regimes, duree_assurance_tous_regimes])
        numerateur_majoration = select([mono_pensionne_regime_general_ou_polypensionne_carriere_incomplete, polypensionne_cotisant_moins_que_duree_requise, polypensionne_cotisant_moins_plus_duree_requise], [duree_assurance_cotisee_regime_general, duree_assurance_cotisee_tous_regimes, duree_assurance_regime_general])
        denominateur_majoration = select([mono_pensionne_regime_general_ou_polypensionne_carriere_incomplete, polypensionne_cotisant_moins_que_duree_requise, polypensionne_cotisant_moins_plus_duree_requise], [duree_de_proratisation, duree_de_proratisation, duree_assurance_tous_regimes])
        coefficient_de_proratisation_montant_de_base = min_(1, numerateur_montant_de_base / denominateur_montant_de_base)
        coefficient_de_proratisation_majoration = min_(1, numerateur_majoration / denominateur_majoration)
        return coefficient_de_proratisation_montant_de_base * mico + coefficient_de_proratisation_majoration * mico_majoration

    def formula_1984_01_01(individu, period, parameters):
        regime_general_cnav = parameters(period).secteur_prive.regime_general_cnav
        minimum_contributif = regime_general_cnav.montant_mico
        mico = minimum_contributif.minimum_contributif.annuel
        trimestres_regime = individu('regime_general_cnav_duree_assurance', period)
        date_de_naissance = individu('date_de_naissance', period)
        duree_de_proratisation = parameters(period).secteur_prive.regime_general_cnav.prorat.nombre_trimestres_maximal_pris_en_compte_proratisation_par_generation[date_de_naissance]
        coefficient_de_proratisation = min_(1, trimestres_regime / duree_de_proratisation)
        conversion_en_euros = 1 / EURO_EN_FRANCS if period.start.year < 2002 else 1
        return coefficient_de_proratisation * mico * conversion_en_euros

    def formula_1941_01_01(indiivdu, period, parameters):
        avts = parameters(period).prestations_sociales.solidarite_insertion.minimum_vieillesse_droits_non_contributifs_de_retraite.avts_av_1961
        conversion_en_euros = 1 / EURO_EN_FRANCS if period.start.year < 2002 else 1
        return avts * conversion_en_euros

class regime_general_cnav_pension_servie(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension servie'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('regime_general_cnav_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(annee_de_liquidation > period.start.year):
            return individu.empty_array()
        last_year = period.start.period('year').offset(-1)
        pension_servie_annee_precedente = individu('regime_general_cnav_pension_servie', last_year)
        revalorisation = parameters(period).secteur_prive.regime_general_cnav.reval_p.coefficient
        pension = individu('regime_general_cnav_pension', period)
        return revalorise(pension_servie_annee_precedente, pension, annee_de_liquidation, revalorisation, period)

class regime_general_cnav_salaire_de_reference(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Salaire annuel moyen de base dit salaire de référence'

    def formula_1994(individu, period, parameters):
        OFFSET = 10
        liquidation_date = individu('regime_general_cnav_liquidation_date', period)
        annee_de_naissance = individu('date_de_naissance', period).astype('datetime64[Y]').astype(int) + 1970
        annees_de_naissance_distinctes = np.unique(annee_de_naissance[liquidation_date >= np.datetime64(period.start)])
        salaire_de_reference = individu.empty_array()
        for _annee_de_naissance in sorted(annees_de_naissance_distinctes):
            if _annee_de_naissance + OFFSET >= period.start.year:
                break
            k = int(parameters(period).secteur_prive.regime_general_cnav.sam.nombre_annees_carriere_entrant_en_jeu_dans_determination_salaire_annuel_moyen[np.array(str(_annee_de_naissance), dtype='datetime64[Y]')])
            mean_over_largest = make_mean_over_largest(k)
            revalorisation = dict()
            revalorisation[period.start.year] = 1
            for annee_salaire in range(max(_annee_de_naissance + OFFSET, REVAL_S_YEAR_MIN), period.start.year + 1):
                revalorisation[annee_salaire] = np.prod(np.array([parameters(_annee).secteur_prive.regime_general_cnav.reval_s.coefficient for _annee in range(annee_salaire + 1, period.start.year + 1)]))
            filter = (annee_de_naissance == _annee_de_naissance,)
            arr = np.vstack([min_(individu('salaire_de_base', period=year)[filter], parameters(year).prelevements_sociaux.pss.plafond_securite_sociale_annuel) * revalorisation[year] for year in range(period.start.year, _annee_de_naissance + OFFSET, -1)])
            compute_salaire_de_reference(mean_over_largest, arr, salaire_de_reference, filter)
        return salaire_de_reference

    def formula_1972(individu, period, parameters):
        OFFSET = 10
        n = parameters(period).secteur_prive.regime_general_cnav.sam.nombre_annees_carriere_entrant_en_jeu_dans_determination_salaire_annuel_moyen.before_1934_01_01
        mean_over_largest = functools.partial(mean_over_k_nonzero_largest, k=n)
        annee_initiale = (individu('date_de_naissance', period).astype('datetime64[Y]').astype(int) + 1970).min()
        revalorisation = dict()
        revalorisation[period.start.year] = 1
        for annee_salaire in range(max(annee_initiale + OFFSET, REVAL_S_YEAR_MIN), period.start.year + 1):
            revalorisation[annee_salaire] = np.prod(np.array([parameters(_annee).secteur_prive.regime_general_cnav.reval_s.coefficient for _annee in range(annee_salaire + 1, period.start.year + 1)]))
        salaire_de_refererence = np.apply_along_axis(mean_over_largest, axis=0, arr=np.vstack([min_(individu('salaire_de_base', period=year), parameters(year).prelevements_sociaux.pss.plafond_securite_sociale_annuel) * revalorisation[annee_salaire] for year in range(period.start.year, max(annee_initiale + OFFSET, REVAL_S_YEAR_MIN), -1)]))
        return salaire_de_refererence

class regime_general_cnav_surcote(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Surcote'

    def formula_2009_04_01(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        if date(period.start.year, period.start.month, period.start.day) < date(2011, 7, 1):
            aod_annee = parameters(period).secteur_prive.regime_general_cnav.aod.age_ouverture_droits_age_legal_en_fonction_date_naissance.before_1951_07_01.annee
            aod_mois = 0
        else:
            aod_annee = parameters(period).secteur_prive.regime_general_cnav.aod.age_ouverture_droits_age_legal_en_fonction_date_naissance[date_de_naissance].annee
            aod_mois = parameters(period).secteur_prive.regime_general_cnav.aod.age_ouverture_droits_age_legal_en_fonction_date_naissance[date_de_naissance].mois
        taux_surcote = parameters(period).secteur_prive.regime_general_cnav.surcote.taux_surcote_par_trimestre_cotise_selon_date_cotisation.apres_01_01_2004['partir_65_ans']
        date_de_naissance = individu('date_de_naissance', period)
        liquidation_date = individu('regime_general_cnav_liquidation_date', period)
        age_en_mois_a_la_liquidation = (liquidation_date - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        trimestres_apres_aod = max_(0, np.trunc((age_en_mois_a_la_liquidation - (12 * aod_annee + aod_mois)) / 3))
        distance_a_2004_en_trimestres = max_(0, np.trunc((liquidation_date - np.datetime64('2004-01-01')).astype('timedelta64[M]').astype(int) / 3))
        duree_assurance_tous_regimes = individu('duree_assurance_tous_regimes', period)
        duree_assurance_cible_taux_plein = parameters(period).secteur_prive.regime_general_cnav.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]
        trimestres_surcote = max_(0, min_(min_(distance_a_2004_en_trimestres, trimestres_apres_aod), duree_assurance_tous_regimes - duree_assurance_cible_taux_plein))
        return taux_surcote * trimestres_surcote

    def formula_2007_01_01(individu, period, parameters):
        aod = parameters(period).secteur_prive.regime_general_cnav.aod.age_ouverture_droits_age_legal_en_fonction_date_naissance.before_1951_07_01.annee
        taux_surcote_par_trimestre = parameters(period).secteur_prive.regime_general_cnav.surcote.taux_surcote_par_trimestre_cotise_selon_date_cotisation.apres_01_01_2004
        taux_surcote_par_trimestre_moins_de_4_trimestres = taux_surcote_par_trimestre['moins_de_4_trimestres']
        taux_surcote_par_trimestre_plus_de_5_trimestres = taux_surcote_par_trimestre['plus_de_5_trimestres']
        taux_surcote_par_trimestre_partir_65_ans = taux_surcote_par_trimestre['partir_65_ans']
        date_de_naissance = individu('date_de_naissance', period)
        liquidation_date = individu('regime_general_cnav_liquidation_date', period)
        age_en_mois_a_la_liquidation = (liquidation_date - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        trimestres_apres_aod = max_(0, np.trunc((age_en_mois_a_la_liquidation - 12 * aod) / 3))
        distance_a_2004_en_trimestres = max_(0, np.trunc((liquidation_date - np.datetime64('2004-01-01')).astype('timedelta64[M]').astype(int) / 3))
        duree_assurance_tous_regimes = individu('duree_assurance_tous_regimes', period)
        duree_assurance_cible_taux_plein = parameters(period).secteur_prive.regime_general_cnav.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]
        trimestres_surcote = max_(0, min_(min_(distance_a_2004_en_trimestres, trimestres_apres_aod), duree_assurance_tous_regimes - duree_assurance_cible_taux_plein))
        trimestres_surcote_au_dela_de_65_ans = min_(trimestres_surcote, max_(0, np.trunc((age_en_mois_a_la_liquidation - 65 * 12) / 3)))
        trimestres_surcote_en_deca_de_65_ans = max_(0, trimestres_surcote - trimestres_surcote_au_dela_de_65_ans)
        surcote = taux_surcote_par_trimestre_moins_de_4_trimestres * min_(4, trimestres_surcote_en_deca_de_65_ans) + taux_surcote_par_trimestre_plus_de_5_trimestres * max_(0, trimestres_surcote_en_deca_de_65_ans - 4) + taux_surcote_par_trimestre_partir_65_ans * trimestres_surcote_au_dela_de_65_ans
        return surcote

    def formula_2004_01_01(individu, period, parameters):
        aod = parameters(period).secteur_prive.regime_general_cnav.aod.age_ouverture_droits_age_legal_en_fonction_date_naissance.before_1951_07_01.annee
        taux_surcote_par_trimestre_moins_de_4_trimestres = parameters(period).secteur_prive.regime_general_cnav.surcote.taux_surcote_par_trimestre_cotise_selon_date_cotisation.apres_01_01_2004['moins_de_4_trimestres']
        date_de_naissance = individu('date_de_naissance', period)
        liquidation_date = individu('regime_general_cnav_liquidation_date', period)
        age_en_mois_a_la_liquidation = (liquidation_date - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        trimestres_apres_aod = max_(0, np.trunc((age_en_mois_a_la_liquidation - 12 * aod) / 3))
        distance_a_2004_en_trimestres = max_(0, np.trunc((liquidation_date - np.datetime64('2004-01-01')).astype('timedelta64[M]').astype(int) / 3))
        duree_assurance_tous_regimes = individu('duree_assurance_tous_regimes', period)
        duree_assurance_cible_taux_plein = parameters(period).secteur_prive.regime_general_cnav.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]
        trimestres_surcote = max_(0, min_(min_(distance_a_2004_en_trimestres, trimestres_apres_aod), duree_assurance_tous_regimes - duree_assurance_cible_taux_plein))
        return taux_surcote_par_trimestre_moins_de_4_trimestres * trimestres_surcote

    def formula_1983_04_01(individu, period):
        return individu.empty_array()

    def formula_1945(individu, period):
        coefficient_majoration_par_trimestre = 0.1 / 4
        aad = 65
        liquidation_date = individu('regime_general_cnav_liquidation_date', period)
        age_en_mois_a_la_liquidation = (liquidation_date - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        trimestres_apres_aad = max_(0, np.trunc((age_en_mois_a_la_liquidation - aad * 12) / 3))
        return coefficient_majoration_par_trimestre * trimestres_apres_aad

class regime_general_cnav_taux_de_liquidation(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Taux de liquidation de la pension'

    def formula(individu, period, parameters):
        decote = individu('regime_general_cnav_decote', period)
        surcote = individu('regime_general_cnav_surcote', period)
        taux_plein = parameters(period).secteur_prive.regime_general_cnav.taux_plein.taux_plein
        return taux_plein * (1 - decote + surcote)