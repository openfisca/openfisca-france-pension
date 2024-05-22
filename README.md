# OpenFisca-France-Pension

Ce paquet est en cours de développement

## [EN] Introduction

OpenFisca is a versatile microsimulation free software. This repository contains the OpenFisca model of the French tax pension schemes inspired from [TiL-Pension](https://www.github.com/TaxIPP-Life/Til-Pension).
Therefore, the working language here is French. You can however check the [general OpenFisca documentation](https://openfisca.org/doc/) in English!

## [FR] Introduction

[OpenFisca](https://www.openfisca.fr/) est un logiciel libre de micro-simulation. Ce dépôt contient la modélisation des principaux régimes de retraite français inspiré par [TiL-Pension](https://www.github.com/TaxIPP-Life/Til-Pension). Pour plus d'information sur les fonctionnalités et la manière d'utiliser OpenFisca, vous pouvez consulter la [documentation générale](https://openfisca.org/doc/).

## [FR] Installation

### [FR] Installation avec `pip`

Si vous êtes familier de `pip`, le commande suivante devrait suffire
```shell
pip install -e .
```
Vous pouvez tester si tout a bien fonctionné :
```shell
openfisca test openfisca_france_pension/tests/
```

Si vous travaillez sous Microsoft Windows et que vous n e maîtrisez pas l'installation avec pip sur cette infrastructure,
il vaut mieux suivre la procédure d'installation avec `conda`.

### [FR] Installation avec `conda` (et `pip` ...)

Les étapes à suivre sont les suivantes:
- installer une distribution `conda` comme [`anaconda`](https://www.anaconda.com/)
- procéder à l'installation via des dépendances via le fichier `environment.yml` :
```shell
conda env create -f environment.yml
```
- activer l'environnement que l'on vient de créer
```shell
conda activate openfisca-france-pension
```
- procéder à l'installation du paquet :
```shell
pip install -e .
```
- tester si tout a bien fonctionné :
```shell
openfisca test openfisca_france_pension/tests/
```

La modélisation à proprement parler est décrite [ici](./doc/modelisation.md).
