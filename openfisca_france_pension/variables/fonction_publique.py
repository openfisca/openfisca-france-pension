"""Abstract regimes definition."""
from datetime import datetime
from openfisca_core.model_api import *
from openfisca_core.errors.variable_not_found_error import VariableNotFoundError
from openfisca_france_pension.entities import Person
'Régime de base de la fonction publique.'
import numpy as np
from openfisca_core.model_api import *
from openfisca_france_pension.entities import Person
from openfisca_france_pension.regimes.regime import AbstractRegimeDeBase

class fonction_publique_cotisation(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'cotisation retraite employeur'

    def formula(individu, period):
        return individu('fonction_publique_cotisation_employeur', period) + individu('fonction_publique_cotisation_salarie', period)

class fonction_publique_liquidation_date(Variable):
    value_type = date
    entity = Person
    definition_period = ETERNITY
    label = 'Date de liquidation'
    default_value = datetime.max.date()

class fonction_publique_cotisation_employeur(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'cotisation retraite employeur'

    def formula(individu, period, parameters):
        NotImplementedError

class fonction_publique_cotisation_salarie(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'cotisation retraite employeur'

    def formula(individu, period, parameters):
        NotImplementedError

class fonction_publique_majoration_pension(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Majoration de pension'

class fonction_publique_pension(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension'

    def formula(individu, period):
        pension_brute = individu('fonction_publique_pension_brute', period)
        majoration_pension = individu('fonction_publique_majoration_pension', period)
        return pension_brute + majoration_pension

class fonction_publique_pension_brute(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension brute'

    def formula(individu, period):
        coefficient_de_proratisation = individu('fonction_publique_coefficient_de_proratisation', period)
        salaire_de_reference = individu('fonction_publique_salaire_de_reference', period)
        taux_de_liquidation = individu('fonction_publique_taux_de_liquidation', period)
        return coefficient_de_proratisation * salaire_de_reference * taux_de_liquidation

class fonction_publique_pension_servie(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension servie'

    def formula(individu, period, parameters):
        revalorisation = parameters(period).secteur_public.reval_p.coefficient
        pension = individu('fonction_publique_pension', period)
        pension_servie_annee_precedente = individu('fonction_publique_pension_servie', period.offset(-1))
        annee_de_liquidation = individu('fonction_publique_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        pension_servie = select([annee_de_liquidation < period.start.year, annee_de_liquidation == period.start.year, annee_de_liquidation > period.start.year], [0, pension, pension_servie_annee_precedente * revalorisation])
        return pension_servie

class fonction_publique_salaire_de_reference(Variable):
    value_type = float
    entity = Person
    definition_period = ETERNITY
    label = 'Salaire de référence'

class fonction_publique_surcote(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Surcote'

class fonction_publique_taux_de_liquidation(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Taux de liquidation de la pension'

    def formula(individu, period, parameters):
        decote = individu('fonction_publique_decote', period)
        surcote = individu('fonction_publique_surcote', period)
        taux_plein = parameters(period).secteur_public.taux_plein.taux_plein
        return taux_plein * (1 - decote + surcote)

class fonction_publique_duree_assurance(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance (trimestres validés dans la fonction publique)"

class fonction_publique_duree_assurance_cotisee(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance (trimestres cotisés dans la fonction publique)"

class fonction_publique_coefficient_de_proratisation(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Coefficient de proratisation'

    def formula(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        duree_de_service_effective = individu('fonction_publique_duree_assurance', period)
        bonification_cpcm = 0
        super_actif = False
        bonification_du_cinquieme = super_actif * min_(duree_de_service_effective / 5, 5)
        duree_assurance_requise = parameters(period).secteur_public.trimtp.nombre_trimestres_cibles_taux_plein_par_generation[date_de_naissance]
        coefficient_de_proratisation = max_(min_(1, (duree_de_service_effective + bonification_du_cinquieme) / duree_assurance_requise), min_(80 / 75, (min_(duree_de_service_effective, duree_assurance_requise) + bonification_cpcm) / duree_assurance_requise))
        return coefficient_de_proratisation

class fonction_publique_aod(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Äge d'ouvertue des droits"

    def formula(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        aod_active = parameters(period).secteur_public.aod_a.age_ouverture_droits_fonction_publique_active_selon_annee_naissance[date_de_naissance]
        aod_sedentaire = parameters(period).secteur_public.aod_s.age_ouverture_droits_fonction_publique_sedentaire_selon_annee_naissance[date_de_naissance]
        statut = individu('statut', period)
        return select([statut == 'fonction_publique_active', statut == 'fonction_publique_sedentaire'], [aod_active, aod_sedentaire, 99])

class fonction_publique_limite_d_age(Variable):
    value_type = int
    entity = Person
    definition_period = ETERNITY
    label = "Limite d'âge"

    def formula(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        limite_age_sedentaire = parameters(period).secteur_public.la_s.age_limite_fonction_publique_sedentaire_selon_annee_naissance
        if period.start.year <= 2011:
            limite_age_sedentaire_annee = limite_age_sedentaire.ne_avant_1951_07_01.annee
            limite_age_sedentaire_mois = 0
        else:
            limite_age_sedentaire_annee = limite_age_sedentaire[date_de_naissance].annee
            limite_age_sedentaire_mois = limite_age_sedentaire[date_de_naissance].mois
        return limite_age_sedentaire_annee + limite_age_sedentaire_mois / 4

class fonction_publique_decote(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Décote'

    def formula_2006(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        aod_sedentaire = parameters(period).secteur_public.aod_s.age_ouverture_droits_fonction_publique_sedentaire_selon_annee_naissance
        if period.start.year <= 2011:
            aod_sedentaire_annee = aod_sedentaire.ne_avant_1951_07_01.annee
            aod_sedentaire_mois = 0
        else:
            aod_sedentaire_annee = aod_sedentaire[date_de_naissance].annee
            aod_sedentaire_mois = aod_sedentaire[date_de_naissance].mois
        aad_en_nombre_trimestres_par_rapport_limite_age = parameters(period).secteur_public.aad.age_annulation_decote_selon_annee_ouverture_droits_en_nombre_trimestres_par_rapport_limite_age
        aod_annee = aod_sedentaire_annee
        aod_mois = aod_sedentaire_mois
        annee_age_ouverture_droits = np.trunc(date_de_naissance.astype('datetime64[Y]').astype('int') + 1970 + aod_annee + ((date_de_naissance.astype('datetime64[M]') - date_de_naissance.astype('datetime64[Y]')).astype('int') + aod_mois) / 12).astype(int)
        aad_en_mois = individu('fonction_publique_limite_d_age', period) * 12 + (annee_age_ouverture_droits >= 2006) * aad_en_nombre_trimestres_par_rapport_limite_age[max_(2006, annee_age_ouverture_droits)] * 3
        age_en_mois_a_la_liquidation = (individu('fonction_publique_liquidation_date', period) - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        trimestres_avant_aad = max_(0, np.trunc((aad_en_mois - age_en_mois_a_la_liquidation) / 3))
        duree_assurance_requise = parameters(period).secteur_public.trimtp.nombre_trimestres_cibles_taux_plein_par_generation[date_de_naissance]
        trimestres = individu('duree_assurance_tous_regimes', period)
        decote_trimestres = max_(0, min_(trimestres_avant_aad, duree_assurance_requise - trimestres))
        taux_decote = (annee_age_ouverture_droits >= 2006) * parameters(period).secteur_public.decote.taux_decote_selon_annee_age_ouverture_droits.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants[max_(2006, annee_age_ouverture_droits)]
        return taux_decote * decote_trimestres

class fonction_publique_surcote(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Surcote'

    def formula_2004(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        aod_sedentaire = parameters(period).secteur_public.aod_s.age_ouverture_droits_fonction_publique_sedentaire_selon_annee_naissance
        if period.start.year <= 2011:
            aod_sedentaire_annee = aod_sedentaire.ne_avant_1951_07_01.annee
            aod_sedentaire_mois = 0
        else:
            aod_sedentaire_annee = aod_sedentaire[date_de_naissance].annee
            aod_sedentaire_mois = aod_sedentaire[date_de_naissance].mois
        aod_annee = aod_sedentaire_annee
        aod_mois = aod_sedentaire_mois
        age_en_mois_a_la_liquidation = (individu('fonction_publique_liquidation_date', period) - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        trimestres_apres_aod = max_(0, np.trunc((age_en_mois_a_la_liquidation - 12 * aod_annee + aod_mois) / 3))
        duree_assurance_requise = parameters(period).secteur_public.trimtp.nombre_trimestres_cibles_taux_plein_par_generation[date_de_naissance]
        duree_assurance_excedentaire = individu('duree_assurance_tous_regimes', period) - duree_assurance_requise
        trimestres_surcote = max_(0, min_(trimestres_apres_aod, duree_assurance_excedentaire))
        taux_surcote = parameters(period).secteur_public.surcote.taux_surcote_par_trimestre
        return taux_surcote * trimestres_surcote

class fonction_publique_dernier_indice_atteint(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Dernier indice connu dans la fonction publique'

    def formula(individu, period, parameters):
        salaire_de_base = individu('salaire_de_base', period)
        taux_de_prime = individu('taux_de_prime', period)
        valeur_point_indice = parameters(period).marche_travail.remuneration_dans_fonction_publique.indicefp.point_indice_en_euros
        dernier_indice = where(salaire_de_base > 0, salaire_de_base / (1 + taux_de_prime) / valeur_point_indice, individu('fonction_publique_dernier_indice_atteint', period.last_year))
        return dernier_indice

class fonction_publique_salaire_de_reference(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Traitement de référence'

    def formula(individu, period, parameters):
        dernier_indice_atteint = individu('fonction_publique_dernier_indice_atteint', period)
        valeur_point_indice = parameters(period).marche_travail.remuneration_dans_fonction_publique.indicefp.point_indice_en_euros
        return dernier_indice_atteint * valeur_point_indice