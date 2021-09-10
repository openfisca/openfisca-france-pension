# OpenFisca-France-Pension

## [EN] Introduction

OpenFisca is a versatile microsimulation free software. This repository contains the OpenFisca model of the French tax pension schemes inspired from [TiL-Pension](https://www.github.com/TaxIPP-Life/Til-Pension).
Therefore, the working language here is French. You can however check the [general OpenFisca documentation](https://openfisca.org/doc/) in English!

## [FR] Introduction

[OpenFisca](https://www.openfisca.fr/) est un logiciel libre de micro-simulation. Ce dépôt contient la modélisation des principaux régimes de retraite français inspiré par [TiL-Pension](https://www.github.com/TaxIPP-Life/Til-Pension). Pour plus d'information sur les fonctionnalités et la manière d'utiliser OpenFisca, vous pouvez consulter la [documentation générale](https://openfisca.org/doc/).

## [FR] Les principes de la modélisation

### Les concepts d'OpenFisca mobilisés

Le système de retraite français est composé de différents régimes qui sont modélisés en utilisant le [formalisme d'OpenFisca](https://openfisca.org/doc/key-concepts/index.html). Ainsi le système complet est un système socio-fiscal ([`TaxBenefitSystem`](https://openfisca.org/doc/key-concepts/tax_and_benefit_system.html)) comprenant les caractéristiques des individus sous forme de variables [`Variables`](https://openfisca.org/doc/key-concepts/variables.html) rattachées à des entités ([`Entities`](https://openfisca.org/doc/key-concepts/person,_entities,_role.html)). Dans le cas qui nous intéresse les entités utilisées sont l'individu et ses ayants-droits.

Les caractéristiques des individus sont celles de leur carrière [fournies par l'utilisateur](https://openfisca.org/doc/coding-the-legislation/20_input_variables.html) et [celles calculées](https://openfisca.org/doc/coding-the-legislation/10_basic_example.html) selon les règles du régime approprié (trimestres, décote, surcote, points, pension, majoration etc) à partir de formules faisant intervenir d'autres variables et des paramètres législatifs ([`Parameters`](https://openfisca.org/doc/key-concepts/parameters.html)). Les paramètres de la législation sont consommées directement depuis [les barèmes IPP](https://framagit.org/french-tax-and-benefit-tables/baremes-ipp-yaml/-/tree/master/parameters/retraites).

Une contrainte forte pesant sur l'écriture des formules des variables est l'utilisation d'opération sur des vecteurs car l'usage d'une boucle sur l'ensemble des individus est trop coûteux si leur nombre est grand alors qu'une opération vectorielle est quasiment indépendante de la taille des vecteurs qu'elle manipule (tant que ceux-ci sont stockables dans la RAM).

Afin de refléter l'évolution de la législation, les variables calculées s'appuient sur des formules qui peuvent évoluer dans le temps de deux façons:

- [l'évolution dans le temps des paramètres](https://openfisca.org/doc/coding-the-legislation/40_legislation_evolutions.html#parameter-evolution)
- [l'évolution dans le temps des formules](https://openfisca.org/doc/coding-the-legislation/40_legislation_evolutions.html#formula-evolution)

### L'utilisation de régimes "abstraits"

Afin d'éviter des redondances inutiles et de factoriser la création des variables intervenant dans les différents régimes, une innovation issue de [TiL-Pension](https://www.github.com/TaxIPP-Life/Til-Pension) a été rajoutée, le régime. Les [abstractions retenues](openfisca_france_pension/regimes/regime.py) sont:
- le régime le plus abstrait (ÀbstractRegime`) qui spécifie les variables communes à tous les régimes (sans nécessairement préciser leurs formules)
- le régime de base abstrait (`AbstractRegimeDeBase`) (TODO: envisager de renommer en régime en annuités)
- le régime complémentaire abstrait (`AbstractRegimeComplementaire`) (TODO: envisager de renommer en régime en points)

Les "vrais" régimes vont donc s'appuyer sur ces régimes pour la structure globale et ne définir que leurs variables propres.

Les variables crées seront préfixées par le nom du régime (par exemple `regime_genral_cnav_pension`).

### L'étude de potentielles réformes

L'étude des réformes du système de retraite peut être facilement conduite
en mobilisant l'objet idoine [`Reform`](https://openfisca.org/doc/coding-the-legislation/reforms.html#reforms) fourni par OpenFisca qui viendra modifier, retirer ou ajouter, de façon sélective, certaines variables du système de retraite ou en modifier certains paramètres.

## [FR] Les composantes des régimes modélisées

Les composantes des différents régimes ont été modélisés à partir du  travail déjà effectué dans [TiL-Pension](https://www.github.com/TaxIPP-Life/Til-Pension) et des informations trouvées dans le précis de législation de l'IPP intitulé "Le système de retraite
français : historique et législation". Notamment les exemples données dans le précis de législation ont servi de base pour écrire les tests unitaires des formules des différentes variables.

Le pas de temps retenu ici est l'année mais il peut-être modifié.

### Les régimes de base

#### Le régime abstrait de base (en annuités)

Il définit les éléments essentiels d'un régime en annuité (décote, surcote et taux de liquidation). Il permet de calculer la pension brute à partir d'un coefficient de proratisation, d'un taux de liquidation et d'un salaire de référence et la pension complète à partir de la pension brute et des majorations.

#### Le régime général de la sécurité sociale (héritant du régime abstrait de base)

Le régime général de la sécurité sociale [`RegimeGeneralCnav`](openfisca_france_pension/regimes/regime_general_cnav.py) a été modélisé avec les variables suivantes:
- `cotisation_employeur` et `cotisation_salarie`
- `salaire_de_reference`
- `trimestres`
- `majoration_duree_assurance_trimestres` (non implémentés)
- `coefficient_de_proratisation`
- `decote_trimestres`
- `decote`
- `surcote`
- `pension_minimale` (non implémentée)
- `pension_maximale`
- `pension_majoration` (non implémentée)

#### Le régime de la fonction publique (héritant du régime abstrait de base)

Le régime général de la sécurité sociale [`RegimeGeneralCnav`](openfisca_france_pension/regimes/fonction_publique.py) a été modélisé avec les variables suivantes (hors service actif):
- `trimetres` (non implémentés)
- `coefficient_de_proratisation`
- `aod`
- `limite_d_age`
- `decote`
- `surcote`
- `dernier_indice_atteint` et `salaire_de_reference`
- `majoration` (non implémentée)
- `bonification` (non implémentée)

### Les régimes complémentaires

#### Le régime abstrait complémentaire (en points)

Il définit les éléments essentiels d'un régime en points (points, coefficient de minoration, décote et taux de liquidation). Il permet de calculer la pension brute à partir des points et de leur valeurs, et la pension complète à partir de la pension brute éventuellement majorée à laquelle on applique une décote et un coefficient de minoration.

#### Le régime Arrco

Le régime de retraite complémentaire Arrco avec un traitement différents des cadres et des non-cadres a été modélisé avec les variables suivantes (sans points enfnats ni pensions de réversion):
- `coefficient_de_minoration`
- `cotisation_employeur`
- `cotisation_salarie`

#### Le régime Agirc

Le régime de retraite complémentaire Agirc est spécifique aux cadres a été modélisé avec les variables suivantes (sans points enfants ni pensions de réversion):
- `coefficient_de_minoration`
- `cotisation_employeur`
- `cotisation_salarie`

#### Le régime unifié Agirc-Arrco

Pour l'instant le régime unifié est la poursuite du régime Arrco pour les non-cadres et de l'Agirc pour les cadres mais il serait préférable de créer un nouveau régime.

## [FR] Les simulations avec des données

### Mise en oeuvre

Pour réaliser des simulations avec des données, on mobilise un `SurveyScenario` qui permet d'utiliser un système de retraite et éventuellement une réforme en initialisant les individus avec des tables contenant certaines de leurs caractéristiques par période.
Un test de faisabilité a été [conduit](openfisca_france_pension/scenario.py) avec les données Destinie.

Le premier problème potentiel identifié a été une chute de performance due au calcul du salaire de référence dans le cadre du régime général.
En effet, ce calcul implique de faire des tris longitudinaux sur de nombreuses années.
Une pure solution Python étant trop lente, la compilation de la fonction problématique avec [Numba](http://numba.pydata.org/) a permis de résoudre le problème.

### Problèmes à résoudre

#### La gestion des décès

OpenFisca garde des effectifs constants lors d'une simulation. Si l'on désire faire un calcul en une seule simulation, on est donc conduit à conserver tous les individus ayant participé à la simulation sur toutes la durée de la simulation. Cela peut-être problématique en terme de mémoire consommée.
Une solution possible est de recourir à une écriture disque régulièrement mais cela serait vraisemblablement très coûteux en temps.
Une autre solution serait de découper la simulation en quelques intervalles temporels pour éliminer les personnes décédées régulièrement.

#### Le pas de temps

On utilise un pas de temps annuel. On peut prendre plus petit mais cela augementera la taille des données mobilisées et le temps de calcul.

#### Les polypensionnés

A priori il n'y a pas de problèmes de traiter des polypensionnés tant qu'il n'ont qu'ils ne cotisent qu'à une seule caisse par an.

#### Les ayants droit et les "donnants" droit (conjoints, enfants)

A priori on peut créer des entités collectives pour rattacher les individus entre eux.
Mais on peut aussi conserver les informations pertinentes au niveaux des individus.
En effet, il faudra garder tous les individus que l'on veut faire participer à des entités collectives dans la simulation dans ce cas.
