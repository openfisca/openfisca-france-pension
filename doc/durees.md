# Les concepts de durées mobilisés

## Le régime général

### Durée de service (durée liquidable)

C'est la durée qui est au numérateur du coefficient de proratisation.
La durée de service (`duree_de_service`) es égale à la durée d'assurance.

### Durée d'assurance

C'est la durée d'assurance qui entre dans le calcul de la durée d'assurance tous régimes.


La durée d'assurance (sous entendue majorée) est égale à la somme de:

- la durée d'assurance validée (`duree_assurance_validee`)
- la majoration de durée d'assurance (`majoration_duree_assurance`)

#### Les durées d'assurance validées annuellement

La durée d'assurance validée (`duree_assurance_validee`) est la somme des
durées d'assurance annuelles (`duree_assurance_annuelle`) qui sont les sommes écrêtées à 4 trimestres par an:
- des durées d'assurance cotisées annuelles  (`duree_assurance_cotisee_annuelle)`
- et des périodes assimilées annuelles  (`duree_assurance_periode_assimilee_annuelle`)

La durée d'assurance cotisée est la somme de
la durée d'assurance personnellement cotisée (`duree_assurance_personnellement_cotisee_annuelle`)
et de
la durée d'assurance cotisée au titre de l'AVPF (`duree_assurance_avpf_annuelle`)

La durée d'assurance annuelle au tire des périodes assimilées est la somme des durées d'assurance validées au titre:
- du chômage (`duree_assurance_chomage_annuelle`)
- de la maladie (et de la maternité) (`duree_assurance_maladie_annuelle`)
- des accidents du travail (`duree_assurance_accident_du_travail_annuelle`)
- de l'invalidité (`duree_assurance_invalidite_annuelle`)
- du service national (`duree_assurance_service national_annuelle`)
- et des autres périodes (`duree_assurance_autre_annuelle`)                     ]

#### Les majoration de durées d'assurance

La majoration de durée d'assurance totale est la somme de la majoration de durée d'assurance lié à la présence d'enfants (`majoration_duree_assurance_enfant`) et les autres majorations de durées d'assurance (`majoration_duree_assurance_autre`)

## Le régime de la fonction publique

### La durée de service (ou durée liquidable)

La durée de service est la somme des durée de service annuelle (`duree_de_service_annuelle`) et de la majoration de durée de service (`majoration_duree_de_service`).

#### Les durées de service validées annuellement

La durée de service annuelle est la somme de

- la durée de service cotisée annuelle (`duree_de_service_cotisee_annuelle`)
- la durée de service rachetée annuelle (`duree_de_service_rachetee_annuelle`)
- et de la durée d'assurance du service national annuelle (`duree_assurance_service_national_annuelle`)

#### La majoration de durée de service

La durée de service effective est majorée par la bonification du cinquième pour les supers actifs
et de la bonification du code des pensions civiles et militaires `bonification_cpcm` (elles entrent toutes les deux dans le calcul du coefficient de proratisation).

### La durée d'assurance

La durée d'assurance est la somme de la durée d'assurance validée
(`duree_assurance_validee`) et de la majoration de durée d'assurance (`majoration_duree_assurance`).

#### Les durées d'assurance validées annuellement

La durée d'assurance validée (`duree_assurance_validee`) est la somme des
durées d'assurance annuelles (`duree_assurance_annuelle`) qui est la sommes écrêtées à 4 trimestres par an:

- de la durée d'assurance cotisée annuelle obtenue en divisant la durée de service par la quotité de travail
- de la durée d'assurance rachetée annuelle duree_assurance_rachetée_annuelle (prise égale à la durée de service rachetée annuelle)
- et de la durée d'assurance du service national annuelle (`duree_assurance_service_national_annuelle`)

En pratique on injecte directement la durée d'assurance annuelle dans la fonction publique.

#### La majoration de durée d'assurance

La majoration de durée d'assurance totale est la somme de la majoration de durée d'assurance lié à la présence d'enfants (`majoration_duree_assurance_enfant`) et les autres majorations de durées d'assurance (`majoration_duree_assurance_autre`).
