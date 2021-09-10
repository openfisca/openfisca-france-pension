"""Variables communes à tout les régimes."""

from openfisca_core.model_api import *
# from openfisca_core.periods import ETERNITY, MONTH, YEAR
# from openfisca_core.variables import Variable
from openfisca_france_pension.entities import Person


class TypesCategorieSalarie(Enum):
    __order__ = 'prive_non_cadre prive_cadre public_titulaire_etat public_titulaire_militaire public_titulaire_territoriale public_titulaire_hospitaliere public_non_titulaire non_pertinent'  # Needed to preserve the enum order in Python 2
    prive_non_cadre = 'prive_non_cadre'
    prive_cadre = 'prive_cadre'
    public_titulaire_etat = 'public_titulaire_etat'
    public_titulaire_militaire = 'public_titulaire_militaire'
    public_titulaire_territoriale = 'public_titulaire_territoriale'
    public_titulaire_hospitaliere = 'public_titulaire_hospitaliere'
    public_non_titulaire = 'public_non_titulaire'
    non_pertinent = 'non_pertinent'


class age_au_31_decembre(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Age'

    def formula(individu, period):
        # https://stackoverflow.com/questions/13648774/get-year-month-or-day-from-numpy-datetime64
        annee_de_naissance = individu('date_de_naissance', period).astype('datetime64[Y]').astype(int) + 1970
        return period.start.year - annee_de_naissance


class categorie_salarie(Variable):
    value_type = Enum
    possible_values = TypesCategorieSalarie
    default_value = TypesCategorieSalarie.prive_non_cadre
    entity = Person
    label = "Catégorie de salarié"
    definition_period = YEAR
    set_input = set_input_dispatch_by_period


class date_de_naissance(Variable):
    value_type = date
    entity = Person
    definition_period = ETERNITY
    label = 'Date de naissance'


class salaire_de_base(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Salaire de base (salaire brut)'
    set_input = set_input_divide_by_period


class taux_de_prime(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Taux de prime dans la fonction publique'
    set_input = set_input_dispatch_by_period


class trimestres_tous_regimes(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = 'Trimestres accumulés tous régimes confondus'

    def formula(individu, period):
        regimes = ['regime_general_cnav', 'fonction_publique']
        return sum(
            individu(f'{regime}_trimestres', period)
            for regime in regimes
            )
