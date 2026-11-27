# Reproduction du cas NASA COMPASS à 7 t/an

**Exécution R-168h-01.** Deux lignes carbothermiques ont traité **1 822,8 kg de régolithe** en 196 lots. Le réservoir commun contient **216,204 kg de LOX** après 168 h. Le débit mesuré vaut **1,28693 kg/h** sur toute la fenêtre et **1,29983 kg/h** à partir de la première extraction. Les 7 t/an désignent la capacité annuelle de conception publiée pour les deux lignes au site de la NASA. L’expérience ECLIPSE couvre une semaine éclairée.

## Sources et périmètre

- Linne et al., *Oxygen Production System for Refueling Human Landing System Elements*, juin 2019, cas 2 CD-2018-162. Les planches 2, 6, 8, 10, 12, 16 et 22–23 décrivent la frontière du système, les rotations, les phases, le rendement et le dimensionnement énergétique. Le tableau *Powered Equipment List* donne le mode 3 avant marge. Les valeurs de régime alimentent la comparaison. [Présentation technique NASA](https://ntrs.nasa.gov/api/citations/20190029197/downloads/20190029197.pdf?attachment=true)
- Linne et al., *Lunar Production System for Extracting Oxygen from Regolith*, *Journal of Aerospace Engineering*, 34(4), 2021. L’article distingue les dimensionnements à 7 t/an et 10,5 t/an. Les données opérationnelles employées ici sont celles de la présentation technique du cas à deux lignes. [Article ASCE](https://doi.org/10.1061/%28ASCE%29AS.1943-5525.0001269)

La mesure de référence se termine **au réservoir de l’étage de descente**, immédiatement après la liquéfaction. Les rotations amont incluent les résidus solides et la recharge des excavateurs. Le transfert de LOX au client, les opérations hors période éclairée et la caractérisation cryogénique du dépôt distant relèvent d’autres frontières.

## Configuration et conventions

| Poste | Valeurs et mode d’application | Provenance |
|---|---|---|
| Production | Deux lignes synchronisées, 9,3 kg de charge par lot, 100 min de traitement, 14 créneaux de démarrage par période de 24 h, soit 40 min/j sans traitement en régime nominal. Un créneau manqué faute de charge est journalisé. | Valeurs COMPASS, planche 10. L’espacement uniforme des créneaux et la synchronisation sont des conventions ECLIPSE. |
| Matière | Régolithe sec accepté après tri nominal de 2 cm. Loi de rendement agrégée de 0,121 kg O₂/kg traité. Le résidu vaut la masse de charge moins la masse d’O₂ extraite. | Planche 10 pour le tri, planche 16 pour le rendement à 1 800 °C. Absence de mesure locale de composition et de taux de refus dans le modèle. Les étapes de méthanation, d’électrolyse et de recyclage sont agrégées. |
| État initial | 130,2 kg en trémie par ligne, pleine au départ, avec O₂ gazeux, LOX et résidus à zéro. Deux rovers à l’excavation, batteries pleines. | Planche 10, dimensionnement d’une journée de charge. Conditions initiales de l’expérience, choisies pour comparer une installation prête à opérer. |
| Ravitaillement | Trajets mine–usine de 100 m. Quatre créneaux par rover à 0, 6, 12 et 18 h. Jusqu’à 35 kg selon l’espace en trémie. 3 min de chargement, 6 min d’aller, 5 min de déchargement, 6 min de retour. | Planche 8. Adaptation avec prélèvement partiel, vitesse effective de 1 km/h et calendrier déterministe. |
| Résidus | Trois créneaux par rover à 3, 9 et 15 h, jusqu’à 40 kg. 5 min de chargement à l’usine, 6 min jusqu’à la décharge, puis 6 min pour revenir à la mine. Le rover ajoute 6 min pour rejoindre l’usine depuis la mine avant cette mission. | Planches 8 et 12. Les 17 min NASA correspondent à l’opération après positionnement. Le repositionnement est explicite dans le journal. |
| Recharge | 1 kWh nominal par rover, réserve de 0,20 kWh. Charge à 100 W pendant 10 h à partir de 108 h. Une mission dont l’énergie estimée compromet la réserve est écartée. | Planche 8. Puissance moyenne de travail de 71,59 W déduite de 0,8 kWh pour 4,5 jours de missions nominales, repositionnement inclus. Rendement de charge supposé de 80 %. Cette estimation regroupe déplacement et manutention. |
| Liquéfaction | O₂ accessible au service de liquéfaction après fin de traitement. Un service FIFO partagé à 1,30 kg/h. Sortie par paquets au plus égaux à 0,05 kg, crédités après leur passage au service. Cuve de semaine de 250 kg avec maintien idéal du stock. | Planche 10 pour le débit et la cuve commune. Le découpage en paquets, le stockage gazeux agrégé, la capacité sur la semaine et le zéro boil-off sont des hypothèses de simulation. |
| Électricité | 15 kWe disponibles et constants pendant 168 h. Charge du noyau de 2,678 kW en veille à 11,544 kW pour deux lignes actives, interpolation par nombre de lignes actives. Ajouter la recharge de 0,1 kW par rover connecté. Surplus écrêté. | Planche 23 et tableau de puissance, modes 3 et 4. L’usage de la veille ensoleillée pendant les intercycles courts et la charge concomitante sont des conventions de scénario. |
| Thermique | 11,1 kWth reçus par réacteur en traitement, soit 22,2 kWth si les deux sont actifs. Intégrale séparée du bus électrique. | Planches 22–23. Les 32,3 kWth à la sortie du concentrateur correspondent à un autre point de mesure. |

Les rotations, le procédé et les budgets effectivement lus sont dans [reference.json](reference.json), sous `batch_operations`, `simulation` et `scenario_builder`. Le [fichier résolu](runs/R-168h-01/resolved.json) garde aussi les valeurs par défaut du chargeur commun. Les blocs propres au preset historique, notamment ses coefficients de froid et sa chimie à hydrogène, sont inactifs dans ce mode.

## Comparaison quantitative

| Indicateur | NASA ou dérivation directe | DES | Écart relatif |
|---|---:|---:|---:|
| Lots terminés par jour et par ligne | 14 | 14,00 | 0 % |
| Régolithe traité, deux lignes | 260,4 kg/j | 260,4 kg/j | 0 % |
| Rendement d’extraction O₂ | 12,10 % | 12,10 % | 0 % |
| Débit liquéfié sur 168 h | 1,30 kg/h nominal | 1,28693 kg/h | −1,005 % |
| Débit liquéfié à partir de la première extraction | 1,30 kg/h nominal | 1,29983 kg/h | −0,0134 % |
| Rotations de régolithe par véhicule et par jour | 4 | 3,714 | −7,14 % |
| Temps d’une rotation de régolithe | 20 min | 20 min | 0 % |
| Rotations de résidus par véhicule et par jour | 3 | 2,714 | −9,52 % |
| Temps d’une rotation de résidus après positionnement | 17 min | 17 min | 0 % |
| Puissance électrique maximale du noyau | 11,544 kWe | 11,544 kWe | 0 % |
| Puissance thermique maximale reçue aux réacteurs | 22,2 kWth | 22,2 kWth | 0 % |

**Le rendement, les temps de service, le plafond de liquéfaction et les deux puissances de pointe sont des entrées de configuration.** L’accord numérique vérifie leur application par le DES. Les lots effectivement achevés, les missions manquées et les stocks disponibles au fil des événements sont des résultats de la coordination des processus.

- **Démarrage et disponibilité du LOX.** Première extraction à 1 h 40 min et premier LOX liquide à 1 h 42 min 15,5 s. Le manque par rapport à 218,4 kg sur sept jours continus est de 2,196 kg. Il se décompose en 2,167 kg dus à la mise en route et 0,029 kg attribuables au reliquat de la discrétisation au terme de la fenêtre. Les matières se ferment avec 220,559 kg d’O₂ extrait, 216,204 kg au réservoir, 4,305 kg gazeux en file et 0,049 kg en liquéfaction. La capacité nominale est légèrement inférieure aux 31,5084 kg/j d’O₂ issus des lots paramétrés. L’écart entre les deux capacités, environ 0,308 kg/j, reste visible dans la file. L’extrapolation annuelle exigerait un modèle de disponibilité et une décision sur cet encours.
- **Logistique et trémies.** Les deux excavateurs ont livré 1 671,6 kg en 52 rotations. Pour chaque rover, la recharge de 108 à 118 h recouvre deux créneaux d’approvisionnement et un créneau de résidus. La réserve minimale écarte un autre créneau de résidus à 105 h. Les deux trémies passent ensemble de 260,4 à 109,2 kg, donc fournissent 151,2 kg du brut effectivement traité. Aucun des 196 créneaux de traitement n’est perdu. Au terme de la semaine, 1 377,47 kg de résidus sont en décharge et 224,77 kg en trémie de résidus. Leur capacité est supposée suffisante dans cette expérience.
- **Électricité et chaleur.** Le bus dispose de 2 520,000 kWh. Le noyau demande 1 898,017 kWh et les chargeurs 2,000 kWh. Le surplus de 619,983 kWh est écrêté et le déficit est nul. Le pic simultané, chargeurs inclus, est de 11,744 kWe. Les réacteurs reçoivent 3 626,000 kWh thermiques dans leur propre bilan. Le noyau produit à 8,779 kWh électriques/kg LOX sur la fenêtre. Les 8,88 kWh électriques/kg dérivés de 11,544/1,30 correspondent au point nominal. L’intégrale sur la fenêtre inclut les périodes de veille et le transitoire de démarrage.

## Code, limites et vérifications

- Le DES spécialisé sélectionne le mode par la présence du bloc `batch_operations`. Le chargement de configuration et la validation utilisent les points d’entrée existants. Les scénarios déjà enregistrés sans ce bloc continuent de passer par leur contrôleur existant. Le contrôleur par lots accepte des équations de scénario pour la durée et le rendement, utilise les contrats de transport de `LunarRover` et associe ses trajets aux identifiants de `resource_routes`. [Moteur spécialisé](../../S24/DES_pipeline_version/ISRU_DES_Model_V5_2_PV.py) · [Validation et dispatch](../../S24/DES_pipeline_version/scenario_runner.py) · [Opérations par lots](../../S24/DES_pipeline_version/batch_isru.py)
- Les stocks, la file de liquéfaction, la charge embarquée et le temps d’occupation des véhicules évoluent par événements SimPy. Le contrôle de masse intervient à chaque événement instrumenté. L’erreur maximale cumulée en valeur absolue est de **1,51 × 10⁻¹¹ kg** sur les trois bilans de cette exécution. Le budget de puissance est intégré aux transitions. Un déficit est signalé dans le bilan. La suspension de production en cas de déficit et la gestion hivernale nécessiteraient un couplage supplémentaire.
- Le modèle COMPASS utilise la configuration JSON du DES. L’édition dédiée de ces paramètres dans le portail et l’export Omniverse de ce nouveau journal nécessitent encore un raccordement. Il n’y a pas de nouvelle validation SysML ni de visualisation du cas R dans cette livraison.
- **64 tests Python et 5 tests JavaScript réussis.** Six tests Python ciblent ce mode. Ils exercent la chronologie du LOX, l’exclusivité du liquéfacteur et des phases rover, la continuité de position, le temps de recharge, la conservation des masses et de l’énergie, le stockage saturé, la récupération après manque d’alimentation, la configuration des lois et la validation des trajets. Deux exécutions dans des processus Python séparés donnent exactement le même journal compressé et le même CSV. [Tests ciblés](../../tests/test_batch_isru.py)

Reproduction depuis la racine du dépôt avec un répertoire de sortie neuf.

```sh
python3 -m paper_scitech.COMPASS.run_reference paper_scitech/COMPASS/runs/R-168h-replay
python3 -m unittest discover -s tests
node --test tests/*.js
```

[Résultats et comparaison](runs/R-168h-01/summary.json) · [Séries horaires](runs/R-168h-01/hourly.csv) · [Journal et états compressés](runs/R-168h-01/results.json.gz) · [Provenance et SHA-256](runs/R-168h-01/provenance.json). Révision Git de base `c271a8cf5d86ca306c04d46e06b8f552e9e86c52`, avec le code exact exécuté archivé dans `runs/R-168h-01/source/`. La révision de base seule ne contient pas l’implémentation de cette livraison.

## Configuration B0 à Malapert

La [configuration proposée](malapert_b0.proposed.json) a passé la validation structurelle. **B0 attend son exécution.** Elle conserve deux usines, deux rovers de régolithe, deux navettes LOX, une excavation, un dépôt, le solaire et la zone de lancement/atterrissage. Les paramètres de traitement et le budget électrique de référence sont conservés. La liquéfaction est distribuée à 0,65 kg/h et le flux thermique local est fixé à 11,1 kWth par ligne. Les navettes de 18 kg partent à partir de 15 kg disponibles. Chaque tampon usine contient jusqu’à 35 kg, le dépôt jusqu’à 250 kg. Les manœuvres et la chaîne du froid en aval sont idéalisées, et le budget électrique ne quantifie pas les navettes LOX ni le refroidissement déporté.

Les distances archivées en plan sont **1,944 et 4,065 km** entre excavation et usines, puis **0,696 et 2,817 km** entre usines et dépôt. Les polylignes portent les mêmes identifiants dans l’archive spatiale. Les trajets de résidus utilisent un point de décharge conceptuel à 100 m de chaque usine et un retour par le corridor mine–usine. Ces embranchements ne disposent pas encore d’un tracé local qualifié. La vitesse effective reste 1 km/h afin d’isoler les distances des effets de pente. Les rovers de régolithe préservent la même batterie et la même réserve, mais se rechargent à la demande lorsque la mission suivante compromet la réserve. [Archive de routes et distances](../B0/run/routing.json)

Sur la seconde liaison, la borne sans résidus ni recharge est de **101,7 kg/j** pour un rover, contre 130,2 kg/j demandés par l’usine. Le temps jusqu’à la première pénurie et la livraison réelle au dépôt sont les indicateurs à mesurer lors de l’exécution autorisée de B0. La fenêtre éclairée de 168 h et la fourniture thermique à Malapert restent des hypothèses d’architecture.
