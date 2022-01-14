"""Variables communes à tout les régimes."""

from openfisca_core.model_api import *
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

class TypesRaisonDepartTauxPleinAnticipe(Enum):
    __order__ = 'non_concerne ancien_deporte inapte ancien_combattant travailleur_manuel'
    non_concerne = "Non concerné"
    ancien_deporte = "Ancien déporté ou interné politique"
    inapte = "Inapte"
    ancien_combattant = "Ancien combattant"
    travailleur_manuel = "Travailleur manuel ou mère de famille ouvrière"

class TypesStatutDuCotisant(Enum):
    # Guide EIC 2013 section 3.4.1 page 28
    __order__ = 'emploi independant avpf chomage maladie accident_du_travail invalidite service_national periode_assimilee_autre inactif non_pertinent'
    emploi = "Emploi salarié"
    independant = "Indépendant"
    avpf = "AVPF"   # CNAF seulement
    chomage = "Chômage, pré-retraite, reconversion et formation"
    maladie = "Maladie-maternité"  # TODO: sont séparés dans EIC donc peut-être qu'il faudrait lesséparer ici également
    accident_du_travail = "Accident du travail"
    invalidite = "Invalidite"
    service_national = "Service national"
    periode_assimilee_autre = "Autre période assimilée"
    inactif = "Inactif"
    non_pertinent = "Non pertinent"

class age_au_31_decembre(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = 'Age'

    def formula(individu, period):
        # https://stackoverflow.com/questions/13648774/get-year-month-or-day-from-numpy-datetime64
        annee_de_naissance = individu('date_de_naissance', period).astype('datetime64[Y]').astype(int) + 1970
        return period.start.year - annee_de_naissance

class avpf(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Salaire porté au compte au titre de l'assurance vieillesse des parents au foyer"


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


class duree_assurance_cotisee_tous_regimes(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance cotisée tous régimes (trimestres cotisés tous régimes confondus)"

    def formula(individu, period):
        regimes = ['regime_general_cnav', 'fonction_publique']
        return sum(
            individu(f'{regime}_duree_assurance_cotisee', period)
            for regime in regimes
            )


class duree_assurance_tous_regimes(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance tous régimes (trimestres validés tous régimes confondus)"

    def formula(individu, period):
        regimes = ['regime_general_cnav', 'fonction_publique']
        return sum(
            individu(f'{regime}_duree_assurance', period)
            for regime in regimes
            )


class nombre_enfants(Variable):
    value_type = int
    entity = Person
    definition_period = ETERNITY
    label = "Nombre d'enfants"


class nombre_enfants_a_charge(Variable):
    value_type = int
    entity = Person
    definition_period = ETERNITY
    label = "Nombre d'enfants à charge"


class salaire_de_base(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Salaire de base (salaire brut)'
    set_input = set_input_divide_by_period


class statut_du_cotisant(Variable):
    value_type = Enum
    possible_values = TypesStatutDuCotisant
    default_value = TypesStatutDuCotisant.non_pertinent
    entity = Person
    definition_period = YEAR
    label = 'Statut du cotisant'
    set_input = set_input_dispatch_by_period


class taux_de_prime(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Taux de prime dans la fonction publique'
    set_input = set_input_dispatch_by_period


class raison_depart_taux_plein_anticipe(Variable):
    value_type = Enum
    possible_values = TypesRaisonDepartTauxPleinAnticipe
    default_value = TypesRaisonDepartTauxPleinAnticipe.non_concerne
    entity = Person
    label = "Raison du départ anticipé au taux plein "
    definition_period = ETERNITY
