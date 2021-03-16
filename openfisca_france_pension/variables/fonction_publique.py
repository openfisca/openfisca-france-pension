"""Abstract regimesdefinition."""
from openfisca_core.model_api import *
from openfisca_france_pension.entities import Household, Person
'Régime de base de la fonction publique.'
from openfisca_core.variables import Variable
from openfisca_core.model_api import *
from openfisca_france_pension.entities import Household, Person
from openfisca_france_pension.regimes.regime import AbstractRegimeDeBase

class fonction_publique_salaire_de_reference(Variable):
    value_type = float
    entity = Person
    definition_period = ETERNITY
    label = 'Salaire de référence'

class fonction_publique_trimestres(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = 'Trimestres'

class fonction_publique_majoration_pension(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH
    label = 'Majoration de pension'

class fonction_publique_decote(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Décote'

class fonction_publique_surcote(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Surcote'

class fonction_publique_pension_brute(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension brute'

    def formula(individu, period, parameters):
        coefficient_de_proratisation = individu('fonction_publique_coefficient_de_proratisation', period)
        salaire_de_reference = individu('fonction_publique_salaire_de_reference', period)
        taux_de_liquidation = individu('fonction_publique_taux_de_liquidation', period)
        return coefficient_de_proratisation * salaire_de_reference * taux_de_liquidation

class fonction_publique_pension(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension'

    def formula(individu, period):
        pension_brute = individu('fonction_publique_pension_brute', period)
        majoration_pension = individu('fonction_publique_majoration_pension', period)
        return pension_brute + majoration_pension

class fonction_publique_surcote_debut_date(Variable):
    value_type = date
    entity = Person
    definition_period = YEAR
    label = 'Date du début de la surcote'

class fonction_publique_decote_annulation_date(Variable):
    value_type = date
    entity = Person
    definition_period = YEAR
    label = "Date d'annulation de la décote'"

class fonction_publique_taux_plein_date(Variable):
    value_type = date
    entity = Person
    definition_period = YEAR
    label = 'Date du taux plein'

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

class fonction_publique_cotisation_retraite(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH
    label = 'cotisation retraite'

    def formula(individu, period, parameters):
        salaire_de_base = individu('salaire_de_base', period)
        taux = parameters(period).secteur_public.cotisation.taux
        return salaire_de_base * taux

class fonction_publique_trimestres(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = 'Trimestres validés dans la fonction publique'

class fonction_publique_coefficient_de_proratisation(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Coefficient de proratisation'

    def formula(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        duree_de_service_effective = individu('fonction_publique_trimestres', period)
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
    definition_period = YEAR
    label = "Limite d'âge"

    def formula(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        limite_age_sedentaire = parameters(period).secteur_public.la_s.age_limite_fonction_publique_sedentaire_selon_annee_naissance[date_de_naissance]
        limite_age_active = parameters(period).secteur_public.la_s.age_limite_fonction_publique_sedentaire_selon_annee_naissance[date_de_naissance]
        statut = individu('statut', period)
        return select([statut == 'fonction_publique_active', statut == 'fonction_publique_sedentaire'], [limite_age_active, limite_age_sedentaire, 99])

class fonction_publique_decote(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Décote'

    def formula_2006(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        aod_active = parameters(period).secteur_public.aod_a.age_ouverture_droits_fonction_publique_active_selon_annee_naissance[date_de_naissance]
        aod_sedentaire = parameters(period).secteur_public.aod_s.age_ouverture_droits_fonction_publique_sedentaire_selon_annee_naissance[date_de_naissance]
        statut = individu('statut', period)
        aod = select([statut == 'fonction_publique_active', statut == 'fonction_publique_sedentaire'], [aod_active, aod_sedentaire, 99])
        annee_age_ouverture_droits = (date_de_naissance.astype('datetime64[Y]') + aod).astype('int')
        decote = parameters(period).secteur_public.decote.taux_decote_selon_annee_age_ouverture_droits[annee_age_ouverture_droits]
        return decote