# Proposition de changement de calculateur

## Etat des lieux

Le système de retraite français a été codé en s'inspirant de l'approche adoptée par [Til-Pension et en utilisant le formalisme et les outils OpenFisca](./README.md).

Le code est structuré autour de régimes abstraits, dont les régimes concrets héritent avec la possibilité de modifier certaines de leur caractéristiques. Par exemple, le régime général et celui de la fonction publique sont tous les deux des régimes en annuités. Ils héritent par conséquent tous les deux de la structure d'AbstractRegimeDeBase. Cela leur permet de profiter implicitement de leurs points communs avec ce type de régime, comme par exemple le calcul de la pension en fonction d'un salaire de reference multiplié par un taux de liquidation et un coefficient de proratisation. Certaines formules sont alors partagées. Là où chaque régime diverge du modèle de base, les formules sont adaptées. Ainsi, le calcul du salaire de référence dans le régime général divergera des autres régimes.

L'autre apport du cadre OpenFisca est l'objet Reform, qui viendra modifier, retirer ou ajouter, de façon sélective, certaines variables du système de retraite ou en modifier certains paramètres. Ainsi, on peut comparer plusieurs systèmes socio-fiscaux en modifiant les composants du code de manière minimale.

Le code est donc modulaire : les systèmes et régimes partagent tout ce qu'ils peuvent, mais sont indépendants. Cela permet à la fois d'éviter au mieux les redondances et de parcelliser les tâches afin de faciliter le travail collectif asynchrone et la vitesse des itérations.
Les composantes du système de retraite codées sont limitées aux droits directs et ne concernent que les régimes suivants:
- le régime général de la CNAV,

- le régime de la FPE (hors catégories actives),

- le régime complémentaire Agirc-Arrco.

Ni les minima, ni les majorations de pension ne sont codées.

Les paramètres de la législation sont fournis par les barèmes IPP.
L'ensemble des composantes sont testées par des tests unitaires reprenant le précis de législation sur les retraites.
Les tests unitaires unitaires ont un triple intérêt:

- définir clairement l'objectif à atteindre,

- produire un test de non-régression,

- disposer d'un outil de débogage lors de la première écriture du code ou en cas de régression.

Un exemple de test et sa trace dans le débogueur sont disponibles en annexe, en bas du document. Si le résultat n'est pas celui qui est attendu, on a à disposition un arbre des valeurs calculées, qui permet de tracer la provenance de l'erreur.
En cas de bug informatique, on peut entrer directement dans le débogueur Python exactement à l'endroit où celui-ci s'est produit et explorer l'état du système, ce qui facilite considérablement la résolution des problèmes.

Il n'existe pour l'instant pas de tests sur une carrière complète car il n'existe pas de référence disponible. Une priorité à court terme sera de créer des cas types.

Un test de branchement partiel avec des données "réelles" avec les données Destinie essentiellement pour tester la faisabilité et les performances.
Il a révélé que le branchement sur les données n'est pas particulièrement compliqué et qu'il n'y avait rien de dirimant côté performances et usage.

## Chemin critique

- 1. Lister les composantes du système de retraite restant à coder pour avoir un MVP:

  - l'idéal serait de connaître exactement ce qui a été fait dans PENSIPP pour égaler la couverture atteinte;

  - cela permettrait de chiffrer le temps pour reproduire;

  - une hiérarchisation des étapes serait également possible.

- 2. Brancher les données EIR-EIC en les restreignant aux cas couverts par le MVP pour tester la législation:

  - en effet, on ne dispose pas de base de cas type de carrières à tester;

  - on peut profiter que l'on peut utiliser des données hors CASD pour faire cela dans une CI et itérer rapidement;

  - on disposera d'une mesure de la couverture de la législation sur les cas pertinents pour les chiffrages;

  - une CI fonctionnelle avec des données d'enquête nous permet de disposer d'un cas d'usage en état de marche facilement reproductible.

- 3. S'en servir pour les travaux sur les inégalités de pension (reproduire et compléter les travaux NBER).

- 4. Ajouter un Régime abstrait de type comptes notionnels pour élargir le cadre des Réformes possibles

- 5. Préparer le branchement avec les données projetées par taxipp-life:

  - Brancher sur les données projetées quand celles-ci seront de bonne qualité;

  - Comparer avec les résultats obtenus avec PENSIPP.

- 6. Brancher sur le RGCU.

Les 4 voire les 5 derniers points peuvent être menés en parallèle.

## Ressources qui seraient très utiles

- Un référent législation:
  - pour être capable de donner cas-type pour tout point de législation posant problème;
  - pour gérer les corrections proposés par DREES DSS;
  - élaborer un cadre de vérification;
  - pour améliorer le précis de législation (l'ouvrir à la collaboration ?).

- Des cas-types de carrière entière (DREES DSS ?)

## Annexe : extraits de débogueur

### Exemple de test de calcul de la pension d'un individu

```yaml
- name: Décote entre 2004 et 2010 pour une personne de 61 ans et 159 trimestres
  absolute_error_margin: .001
  period: 2008
  input:
    date_de_naissance: 1947-11-19
    regime_general_cnav_liquidation_date: 2008-11-18
    regime_general_cnav_duree_assurance: 159
    regime_general_cnav_salaire_de_reference: 1000
  output:
    regime_general_cnav_coefficient_de_proratisation: 1
    regime_general_cnav_surcote: 0
    regime_general_cnav_decote: (160 - 159) * 0.02
    regime_general_cnav_pension_brute: 1000 * .5 * (1 - (160 - 159) * 0.02)
```

### Arbre des valeurs calculées pour le test de calcul de pension

```shell
$ openfisca test openfisca_france_pension/tests/formulas/regime_general_cnav/decote.yml -v

...
.Computation log:
  regime_general_cnav_coefficient_de_proratisation<2008> >> [1.]
    date_de_naissance<2008> >> ['1947-11-19']
    regime_general_cnav_liquidation_date<2008> >> ['2008-11-18']
    date_de_naissance<2008> >> ['1947-11-19']
    regime_general_cnav_duree_assurance<2008> >> [159]
  regime_general_cnav_surcote<2008> >> [0.]
    date_de_naissance<2008> >> ['1947-11-19']
    regime_general_cnav_liquidation_date<2008> >> ['2008-11-18']
    date_de_naissance<2008> >> ['1947-11-19']
    regime_general_cnav_duree_assurance<2008> >> [159]
  regime_general_cnav_decote<2008> >> [0.02]
    date_de_naissance<2008> >> ['1947-11-19']
    regime_general_cnav_decote_trimestres<2008> >> [1.]
      date_de_naissance<2008> >> ['1947-11-19']
      regime_general_cnav_liquidation_date<2008> >> ['2008-11-18']
      date_de_naissance<2008> >> ['1947-11-19']
      regime_general_cnav_duree_assurance<2008> >> [159]
  regime_general_cnav_pension_brute<2008> >> [490.]
    regime_general_cnav_coefficient_de_proratisation<2008> >> [1.]
    regime_general_cnav_salaire_de_reference<2008> >> [1000.]
    regime_general_cnav_taux_de_liquidation<2008> >> [0.49]
      regime_general_cnav_decote<2008> >> [0.02]
      regime_general_cnav_surcote<2008> >> [0.]
...
```
