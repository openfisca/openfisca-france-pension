"""Abstract regimes definition."""
import numpy as np
from openfisca_core.model_api import *
from openfisca_core.errors.variable_not_found_error import VariableNotFoundError
from openfisca_france_pension.entities import Person

def revalorise(variable_31_decembre_annee_precedente, variable_originale, annee_de_liquidation, revalorisation, period):
    return select([annee_de_liquidation > period.start.year, annee_de_liquidation == period.start.year, annee_de_liquidation < period.start.year], [0, variable_originale, variable_31_decembre_annee_precedente * revalorisation])
'Régimes complémentaires du secteur privé.'
from openfisca_core.model_api import *
from openfisca_core.variables import Variable
from openfisca_france_pension.entities import Person
from openfisca_france_pension.regimes.regime import AbstractRegimeComplementaire
from openfisca_france_pension.variables.hors_regime import TypesCategorieSalarie
from openfisca_france_pension.regimes.regime_general_cnav import conversion_parametre_en_euros

class Ircantec(AbstractRegimeComplementaire):
    name = 'Régime complémentaire public Ircantec'
    variable_prefix = 'ircantec'
    parameters_prefix = 'secteur_public.ircantec'

    class cotisation(Variable):
        value_type = float
        default_value = 0
        entity = Person
        definition_period = YEAR
        label = 'Cotisation'

        def formula_2019(individu, period, parameters):
            categorie_salarie = individu('categorie_salarie', period)
            salaire_de_base = individu('regime_general_cnav_salaire_de_base', period)
            plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel * conversion_parametre_en_euros(period.start.year)
            employeur = parameters(period).regime_name.prelevements_sociaux.ircantec.taux_cotisations_appeles.employeur
            salarie = parameters(period).regime_name.prelevements_sociaux.ircantec.taux_cotisations_appeles.salarie
            return (categorie_salarie == TypesCategorieSalarie.prive_non_titulaire) * (employeur.ircantec.calc(salaire_de_base, factor=plafond_securite_sociale) + salarie.ircantec.calc(salaire_de_base, factor=plafond_securite_sociale))

    class points_annuels(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = 'Points'

        def formula_1962(individu, period, parameters):
            salaire_de_reference = parameters(period).regime_name.salaire_de_reference.salaire_reference_en_euros
            taux_appel = parameters(period).regime_name.prelevements_sociaux.taux_appel
            cotisation = individu('regime_name_cotisation', period)
            return cotisation / salaire_de_reference / taux_appel