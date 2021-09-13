# Proposition de changement de calculateur

## Etat des lieux

Le système de retraite français a été codé en s'inspirant de l'approche adoptée par Til-Pension et en utilisant le formalisme et les outils OpenFisca.

Le code est structuré autour de régimes abstraits, dont les régimes concrets héritent avec la possibilité de modifier certaines de leur caractéristiques. Par exemple, le régime général et celui de la fonction publique sont tous les deux des régimes en annuités. Ils héritent par conséquent tous les deux de la structure d'AbstractRegimeDeBase. Cela leur permet de profiter implicitement de leurs points communs avec ce type de régime, comme par exemple le calcul de la pension en fonction d'un salaire de reference multiplié par un taux de liquidation et un coefficient de proratisation. Certaines formules sont alors partagées. Là où chaque régime diverge du modèle de base, les formules sont adaptées. Ainsi, le calcul du salaire de référence dans le régime général divergera des autres régimes.

L'autre apport du cadre OpenFisca est l'objet Reform, qui viendra modifier, retirer ou ajouter, de façon sélective, certaines variables du système de retraite ou en modifier certains paramètres. Ainsi, on peut comparer plusieurs systèmes socio-fiscaux en modifiant les composants du code de manière minimale.

Le code est donc modulaire : les systèmes et régimes partagent tout ce qu'ils peuvent, mais sont indépendants. Cela permet à la fois d'éviter au mieux les redondances et de parcelliser les tâches afin de faciliter le travail collectif asynchrone et la vitesse des itérations.
Les composantes du système de retraite codées sont limitées aux droits directs et ne concernent que les régimes suivants:
- le régime général de la CNAV,
- le régime de la FPE (hors catégories actives),
- le régime complémentaire Agirc-Arrco.

Ni les minima, ni les majorations de pension ne sont codées. 

Les paramètres de la législation sont fournis par les barèmes IPP.
L'ensemble des composantes sont testées par des tests unitaires reprenant le précis de législation sur les retraites. (TODO INSERER ICI IMAGE)

Il n'existe pour l'instant pas de tests sur une carrière complète car il n'existe pas de référence disponible. Une priorité à court terme sera de créer des cas types.

Un test de branchement partiel avec des données "réelles" avec les données Destinie essentiellement pour tester la faisabilité et les performances.
Il a révélé que le branchement sur les données n'est pas particulièrement compliqué et qu'il n'y avait rien de dirimant côté performances et usage.

## Chemin critique

- Lister les composantes du système de retraite restant à coder pour avoir un MVP:
  - l'idéal serait de connaître exactement ce qui a été fait dans PENSIPP pour égaler la couverture atteinte;
  - cela permettrait de chiffrer le temps pour reproduire;
  - une hiérarchisation des étapes serait également possible.

- Brancher les données EIR-EIC en les restreignant aux cas couverts par le MVP pour tester:
  - en effet, on ne dispose pas de base de cas type de carrières à tester;
  - on peut profiter que l'on peut utiliser des données hors CASD pour faire cela dans une CI et itérer rapidement.

- S'en servir pour les travaux sur les inégalités de pension (reproduire et compléter les travaux NBER).

- Ajouter un Régime abstrait de type comptes notionnels pour élargir le cadre des Réformes possibles

- Préparer le branchement avec les données projetées par taxipp-life:
  - Brancher sur les données projetées quand celles-ci seront de bonne qualité;
  - Comparer avec les résultats obtenus avec PENSIPP.

- Brancher sur le RGCU.

Les 4 voire 5 derniers points peuvent être menés en parallèle.


## Ressources qui seraient très utiles

- Un référent législation:
  - pour être capable de donner cas-type pour tout point de législation posant problème;
  - pour gérer les corrections proposés par DREES DSS;
  - élaborer un cadre de vérification;
  - pour améliorer le précis de législation (l'ouvrir à la collaboration ?).

- Des cas-types de carrière entière (DREES DSS ?)
