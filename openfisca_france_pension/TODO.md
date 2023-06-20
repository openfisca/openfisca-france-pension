# TODO

## Législation à coder

### Cotisations cet etc pour Agirc-Arrco

### RAFP

### Indépendants (voir Til-Pension)

### AVPF, MDA, Enfants


## Perfomance mémoire

### mask sur les vivants dans les getter et setter à chaque période


## Perfomance temps


## Législation: parameters à compléter

### Salaire validant un trimestre avant 1930 ?


## Erreurs à corriger

### Surcote et décote régime général

Problèmes de déclages de plus ou moins 1 trimestres

EIR
(regime == 'regime_general_cnav') & (target_regime_general_cnav_surcote_trimestres == 0) & (regime_general_cnav_surcote_trimestres > 0) & (nombre_enfants == 0)

Pb des surcoteurs qui ni travallent plus dans la période de référence de la surcote.
Construire un masque avec la période de référence sur laquelle on compte les trimestres cotisées.


Match EIR-EIC
(regime == 'regime_general_cnav') & (diff_regime_general_cnav_duree_assurance > 0) & (regime_general_cnav_duree_assurance >= 150) & (regime_general_cnav_majoration_duree_assurance == 0)

### Durée de service fonction publique

Très bruitée  diagnostic à la réunion du 2023-02-20


### Pourquoi coexistence duree_service et duree_assurance qui sont les mêmes pour le regime général ?
