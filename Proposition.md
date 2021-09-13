# Proposition de changement de calculateur

## Etat des lieux

Le système de retraite français a été codé en s'inspirant de l'approche adoptée par Til-Pension et en utilisant le formalisme et les outils OpenFisca.

Cela permet d'obtenir un code modulaire et déclaratif accompagnés de tests unitaires.
Cela améliore sa découvrabilité, évite au mieux les redondances et permet de parcelliser le travail afin de faciliter le travail collectif asynchrone et la vitesse des itérations.

Les composantes du système de retraite codées sont limitées aux droits directs et ne concernent que les régimes suivants:
- le régime général de la CNAV,
- le régime de la FPE (hors actif),
- le régime complémentaire Agirc-Arrco.

Les pension de la catégorie active, les minimas de pensions ne sont pas codés ni les droits dérivés.

Les paramètres de la législation sont fournis par les barèmes IPP.
Les différentes composantes sont testées par des tests unitaires reprenant le précis de législation sur les retraites.

Il n'existe pour l'instant pas de tests sur une carrière complète car pas il n'existe pas de référence disponible.

Un test de branchement partiel avec des données "réelles" avec les données Destinie essentiellement pour tester la faisabilité et les performances.
Il a révélé que le branchement sur les données n'est pas particulièrement compliqué et qu'il n'y avait rien de dirimant côté performances et usage.

## Chemin critique

- Lister les composantes du système de retraite restant à coder pour avoir un MVP:
  - c'idéal serait de connaître exactement ce qui a été fait dans PENSIPP de le reproduire;
  - cela permettrait de chiffrer le temps pour reproduire;
  - une hiérarchisation des étapes serait également possible.

- Brancher les données EIR-EIC en les restreignant aux cas couverts par le MVP pour tester:
  - en effet, on ne dispose pas de base de cas type de carrières à tester;
  - on peut profiter que l'on peut utiliser des données hors CASD pour faire cela dans une CI et itérer rapidement.

- S'en servir pour les travaux sur les inégalités de pension (reproduire et compléter les travaux NBER).

- Ajouter une réforme type comptes notionnels

- Préparer le branchement sur les données de projection:
  - Brancher sur les données projections quand celles-ci seront de bonne qualité;
  - Comparer avec les résultats obtenus sur PENSIPP.

- Brancher sur le RGCU.

Les 4 voire 5 derniers points peuvent être menés en parallèle.


## Ressources qui seraient très utiles

- Un référent législation:
  - pour être capable de donner cas-type pour tout point de législation posant problème;
  - pour gérer les corrections proposés par DREES DSS;
  - élaborer un cadre de vérification;
  - pour améliorer le précis de législation (l'ouvrir à la collaboration ?).

- Des cas-types de carrière entière (DREES DSS ?)
