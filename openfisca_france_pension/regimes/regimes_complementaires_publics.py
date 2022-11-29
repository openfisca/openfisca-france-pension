"""Régimes complémentaires du secteur privé."""


from openfisca_core.model_api import *
from openfisca_core.variables import Variable

from openfisca_france_pension.entities import Person
from openfisca_france_pension.regimes.regime import AbstractRegimeComplementaire
from openfisca_france_pension.variables.hors_regime import TypesCategorieSalarie
from openfisca_france_pension.regimes.regime_general_cnav import conversion_parametre_en_euros


class RegimeIrcantec(AbstractRegimeComplementaire):
    name = "Régime complémentaire public Ircantec"
    variable_prefix = "ircantec"
    parameters_prefix = "secteur_public.regimes_complementaires.ircantec"

    class cotisation(Variable):
        value_type = float
        default_value = 0
        entity = Person
        definition_period = YEAR
        label = "Cotisation"

        def formula(individu, period, parameters):
            categorie_salarie = individu("categorie_salarie", period)
            salaire_de_base = individu("regime_general_cnav_salaire_de_base", period)
            plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel * conversion_parametre_en_euros(period.start.year)
            employeur = parameters(period).regime_name.prelevements_sociaux.employeur
            salarie = parameters(period).regime_name.prelevements_sociaux.salarie
            return (
                (categorie_salarie == TypesCategorieSalarie.public_non_titulaire)
                * (
                    employeur.ircantec.calc(salaire_de_base, factor = plafond_securite_sociale)
                    + salarie.ircantec.calc(salaire_de_base, factor = plafond_securite_sociale)
                    )
                )

    class points_annuels(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Points"

        def formula(individu, period, parameters):
            salaire_de_reference = parameters(period).regime_name.salaire_de_reference.salaire_reference_ircantec
            taux_appel = parameters(period).prelevements_sociaux.cotisations_secteur_public.ircantec.taux_appel
            cotisation = individu("regime_name_cotisation", period)
            return cotisation / taux_appel / salaire_de_reference
