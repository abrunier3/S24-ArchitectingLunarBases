# Lunar Spaceport B0 — configuration, résultats et portée scientifique

**Exécution canonique** `B0-983d9d8cac414f8b8d0973324d42684b`, 26 novembre 2026. Le DES a exécuté 60 h avec sept types opérationnels, deux usines et quatre rovers. Un rejeu indépendant de la même configuration a reproduit exactement les 61 instantanés horaires, les huit indicateurs et les résultats de chaque sous-système. Les archives ISRU restent dans leur dossier d’origine. [Identité et sources](run/provenance.json) · [Contrôle de reproduction](run/reproduction.json) · [Sortie DES originale de B0](run/des_results.json).

**Décision pour le paper.** Ce run peut servir de référence numérique pour discuter des routes, de la cadence des livraisons et de l’accumulation des stocks. Trois choix doivent être explicités avant de figer une référence physique pour la production et l’énergie : le moment où un lot devient disponible, l’unité temporelle du coefficient cryogénique et le régime d’alimentation électrique. Une modification ultérieure de ces conventions justifierait une nouvelle exécution identifiée. Les résultats ci-dessous appartiennent tous à la configuration héritée. [Comparaison des hypothèses avec les sources primaires](PARAMETRES_ET_LITTERATURE.md).

## Configuration utilisable dans V.A

| Parameter | Executed B0 value | Equation, provenance or scope |
|---|---|---|
| Site and layout | Malapert Massif, nominal centre 85.9° S, 0.5° W | Historical layout and orientations. Four existing road segments retained. One new segment routed between the plants following removal of the habitat. |
| Active infrastructure | 1 excavation site, 2 ISRU plants, 1 depot, 1 solar system, 1 landing/launch zone, 2 regolith rovers and 2 LOX rovers | Ten operational instances, seven types. Each regolith rover serves its own plant. Each LOX rover serves the same depot from its own plant. Landing zone receives no LOX in B0. |
| Horizon and sampling | 60 h, hourly state log, power and storage accounting at 1 h | 61 state records. SimPy stops before events scheduled at exactly 60 h. The power manager executed 59 hourly updates. |
| Feed logistics | 4,000 kg/load and per raw-feed batch, 20,000 kg inlet capacity per plant | Dedicated assignments, 0.1 h dispatch retry. Nominal least-fill policy applies within the eligible destinations. Excavation supplies requests without an independently timed digging cycle. |
| Conversion and service | 1,600 kg raw feed/h per plant, 0.002527902017 kg LOX/kg feed | Per batch, service time = feed/rate = 2.5 h. Credited LOX = feed × yield = 10.111608 kg. The model makes this LOX available at batch admission. |
| Mobility | Payload limit 4,000 kg for either rover type, flat speed 2 km/h, battery initially 100 kWh per rover | Active equations: travel time [h] = distance [km] × 0.5 h/km; traction energy [kWh] = distance × cargo mass × 0.00034 kWh/(kg·km). Empty returns consume time with zero traction energy in this model. |
| LOX logistics | 100 kg dispatch threshold per plant, 1 h polling, empty initial LOX stocks | Ship available stock up to vehicle capacity. Depot accumulates deliveries. No customer withdrawals, transfer duration or boil-off mass loss. |
| Process energy per 4,000 kg admitted | 237.241 kWh | Sum of excavation, nominal haul, beneficiation, reduction, electrolysis and liquefaction, excluding subsequent storage. See parameter dossier for the different mass bases. |
| Cryogenic storage | 0.31 kWh/(kg·h) on plant inventory | Each accounting step charges 0.31 × stored LOX × elapsed hours. Depot power law is zero. Operation therefore transfers the accounting boundary as well as the material. |
| Electrical supply and loads | 100,000 kW constant generation, battery 500,000 kWh, initially 49,950 kWh | Illustrative ample-power regime. Landing-zone baseline 3 kW and a 50 kWh event at 25 h. Mobile traction draws on separate onboard batteries. |

[Configuration d’entrée](run/scenario.json) · [Configuration effective, y compris les valeurs par défaut](run/resolved.json) · [Équations par type et instance](run/scenario.json) · [Géométrie, positions et affectations](run/routing.json).

## Vérification avant calcul

- Le sous-graphe SysML a été régénéré depuis une copie du modèle de référence, avec une seule inversion locale : la sortie LOX de l’usine alimente le port bidirectionnel du rover dans `ISRUPlantToRover`. Le parseur n’a signalé aucune erreur de direction après correction. Huit interfaces actives : excavation → rover régolithe → usine, usine → rover LOX → dépôt, et quatre interfaces électriques. Les quatre affectations opérationnelles d’instances sont ajoutées séparément. Le parseur historique émet des avertissements sur les littéraux booléens de métadonnées CAD ; le DES utilise les fiches d’actifs archivées pour ses propriétés numériques. [Source SysML corrigée](run/reference.sysml) · [Graphe actif](run/graph.json) · [Système publié](run/system.json).
- Le SysML complet reste une **bibliothèque de référence**. L’habitation est absente des sept types sélectionnés, des fiches actives, du graphe, des instances, des consommateurs, des arrêts, des sorties et de la scène. Le chargeur commun conserve des clés de valeurs par défaut pour des modules désactivés. Le moteur spécialisé affiche cinq drapeaux de classes DES ; il construit aussi l’excavation et le dépôt à partir des définitions et affectations du scénario. Tous deux sont présents dans le journal. [Entrées effectives et journal](run/des_results.json).
- Le correctif de chemin est présent à la révision auditée. Les deux tests de `tests/test_rover_route_payload.js` ont réussi. Le calcul utilise directement les fonctions de `ScenarioIndex.html` pour Prim, A*, l’assemblage des polylignes et le calcul des pentes. Quatre tronçons existants ont conservé leurs waypoints modifiés. A* a fourni le seul nouveau tronçon requis. Aucun trajet opérationnel ne contient d’arrêt de service intermédiaire. Une route peut passer par un autre module sans y effectuer un transfert. [Calcul reproductible](routes.js) · [Provenance de chaque tronçon](run/routing.json).

| Rover | Origine → destination | Chemin DES et scène 2D, km | Pente grille moyenne / max., ° | Durée aller DES, h | Chemin projeté 3D, km | Pente locale max. maillage, ° |
|---|---|---:|---:|---:|---:|---:|
| Régolithe 1 | Excavation → usine 1 | 1.944 | 12.782 / 13.819 | 0.9720 | 1.995 | 36.525 |
| Régolithe 2 | Excavation → usine 2 | 4.065 | 12.280 / 14.730 | 2.0325 | 4.174 | 40.879 |
| LOX 1 | Usine 1 → dépôt | 0.696 | 12.620 / 13.819 | 0.3480 | 0.717 | 36.525 |
| LOX 2 | Usine 2 → dépôt | 2.817 | 12.027 / 14.730 | 1.4085 | 2.897 | 40.879 |

Chaque distance DES reproduit la longueur XY de la polyligne publiée à l’arrondi de 1 m. La pente est transmise au moteur. Dans **ces** lois, `TravelTime = Distance * hoursPerKm` remplace le temps par défaut qui dépend de la pente. Les durées imprimées aux premières livraisons le confirment. Le diagnostic 3D échantillonne le maillage recalé : couverture complète sur les quatre trajets et quatre avertissements au seuil de 15°. La grille embarquée est donnée pour 80 × 80 cellules à 12,5 m, soit environ 1 km, tandis que le cadre historique les étire sur 2,79 km. Les distances du paper sont des distances dans le plan du scénario. Une conclusion de traversabilité réelle à Malapert demanderait un recalage métrique et altimétrique indépendant. [Vérifications OpenUSD](run/omniverse/checks.json).

## Mesures pour V.B

[Figure exploratoire des stocks et livraisons (PDF)](run/operations.pdf). Les courbes usine et trémies suivent les instantanés horaires. Les sauts du stock au dépôt utilisent les heures de livraison du journal d’événements.

| Grandeur sur 60 h | Usine 1 | Usine 2 | Ensemble |
|---|---:|---:|---:|
| Régolithe livré aux trémies, kg | 116 000 | 60 000 | 176 000 |
| Régolithe admis en traitement, kg | 96 000 | 60 000 | 156 000 |
| Stock final de régolithe en trémie, kg | 20 000 | 0 | 20 000 |
| Lots engagés / lots terminés | 24 / 23 | 15 / 14 | 39 / 37 |
| LOX crédité par le DES, kg | 242,68 | 151,67 | 394,35 |
| LOX livré au dépôt par origine, kg | 202,23 | 101,12 | 303,35 |
| LOX restant en usine, kg | 40,45 | 50,56 | 91,00 |
| Énergie comptée en usine, kWh | 6 508,77 | 4 295,24 | 10 804,01 |

**Bilan matière.** Les 176 t de livraisons proviennent de 44 déchargements observés. Le compteur `Total_Regolith_Received_kg` augmente lorsque l’usine prend un lot dans sa trémie : son libellé masquerait 20 t si on l’utilisait pour le transport. À 60 h, 176 = 156 + 20 t. Sur chacun des 61 états, le LOX crédité égale la somme des stocks usine, dépôt, zone et cargaisons à une tolérance de 10⁻⁷ kg. En fin de run, 394,35 = 303,35 + 91,00 kg, sans LOX en transit ni dans la zone de lancement. [États horaires](run/hourly.csv) · [Événements aux temps du DES](run/events.csv).

**Convention de production.** `ISRUPlant.processRegolith` comptabilise la masse, l’énergie et les 2,5 h de service **avant** l’attente SimPy. À la coupure, deux lots sont en cours. Les 37 lots achevés représentent 374,13 kg à leur rendement nominal, soit 6,24 kg/h sur l’horizon. Le crédit DES est de 6,57 kg/h et le dépôt a reçu 5,06 kg/h. Les 374,13 kg sont une conversion du nombre de fins de cycle observées ; ce chiffre ne remplace pas le stock utilisé par le contrôleur. De même, 60 et 37,5 h sont des durées de service **engagées**. [Résumé des contrôles](run/summary.json) · [Événements natifs](run/events.txt).

**Cadence et limite de débit observable.** Le trajet aller-retour du rover régolithe 2 dure 4,065 h, contre 2,5 h pour traiter sa cargaison. Les 15 livraisons et sa trémie vide après chaque remise sont cohérentes avec une usine 2 limitée par l’alimentation dans cette affectation. Côté usine 1, l’aller-retour dure 1,944 h. Sa trémie atteint 20 t et le dispatch attend de la place. Ces tendances opposées émergent dans le même scénario à rendements égaux. Les départs LOX ont lieu à 24,00, 39,00 et 48,70 h. Les réceptions au dépôt ont lieu à **24,35, 40,41 et 49,04 h**, chacune d’environ 101,12 kg. Le premier rover LOX n’utilise qu’environ 2,53 % de sa capacité à chaque envoi. Le seuil et l’horizon expliquent la présence d’un stock final sans impliquer un manque de capacité de transport LOX. [Événements](run/events.csv).

**Bilan énergétique.** Le bus enregistre **5 900 000 kWh générés**, **11 032,16 kWh demandés**, **450 050 kWh ajoutés à la batterie**, aucun soutirage et **5 438 917,84 kWh d’excédent non stocké** inférés par différence. L’énergie non servie est nulle sur les 59 intervalles calculés : la génération dépasse la demande dans chacun. Le maximum de demande est de 527,66 kWh en une heure ; il s’agit d’une moyenne sur cet intervalle. Les batteries mobiles dépensent séparément **159,60 kWh** (régolithe) et **0,14 kWh** (LOX). Le bus intègre aussi l’énergie des usines ; l’addition « bus + usines » la compterait deux fois. Le modèle usine inclut déjà l’excavation et un transport de référence de 1 km. Ajouter la traction mobile et le coût d’excavation sans réconcilier les frontières introduirait un recouvrement. Le bilan de comparaison publie séparément procédé, usine, bus et traction. [Série énergétique par intervalle](run/bus.csv) · [Indicateurs calculés sans arrondi intermédiaire](run/summary.json).

## Ce que montre la visualisation

Le paquet natif a été généré depuis le JSON actif et le DES de **cette** exécution. Les couches scène et waypoints s’ouvrent avec OpenUSD 25.11. Les sept types ont une géométrie maillée résolue, les quatre acteurs ont leur route et toutes les positions des routes sont couvertes sur le maillage. Onze références JPEG de matériaux restent non résolues dans les CAD sources ; leur apparence texturée reste à confirmer. La lecture interactive dans Omniverse Kit n’a pas été exécutée. [Scène](run/omniverse/scene.usda) · [Waypoints](run/omniverse/waypoints.usda) · [Manifeste natif](run/omniverse/manifest.json) · [Dépendances et diagnostics](run/omniverse/checks.json).

Le générateur natif reconstitue les mouvements à partir d’états horaires. La première livraison LOX entière tombe entre deux captures. Elle figure dans le stock du dépôt et dans le journal DES, mais son aller-retour est absent de la chronologie native. Pour les rovers régolithe, l’animation native enchaîne les tronçons et peut masquer une attente devant la trémie. Un **second manifeste de visualisation pour le même run** utilise les livraisons et retours consignés dans le flux d’événements à 0,01 h. Il conserve géométries, positions et télémétrie. Les départs régolithe sont déduits de l’heure de livraison et de la loi de trajet active ; la fin des deux retours encore en cours à 60 h est extrapolée par cette loi. Les trois expéditions LOX y figurent. Contrôles hors Kit : 58 et 30 tronçons régolithe, 4 et 2 tronçons LOX, et distance cumulée de chaque acteur conforme au compteur du DES (qui crédite sa distance dès le départ). Pour une figure illustrant **le workflow standard**, utiliser la deuxième livraison et signaler l’intervalle reconstruit. Pour une figure chronométrée sur événements, préciser le post-traitement spécifique à B0. [Manifeste synchronisé sur événements](run/omniverse/manifest_events.json) · [Script de rapprochement](event_playback.py).

## Reproduire

Révision du moteur et du portail : `c271a8cf5d86ca306c04d46e06b8f552e9e86c52`. Les scripts de ce dossier orchestrent la simulation et l’extraction. Garder ce dossier et le checkout indiqué pour résoudre les références CAD et terrain relatives. Le jeu de résultats canonique est sous `run/`. Les commandes ci-dessous créent une autre copie de **B0** dans un répertoire neuf. Employer l’environnement du DES pour la première commande et celui d’OpenUSD pour la troisième. Sur la machine de l’étude, les interpréteurs sont respectivement `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3` et `/Users/arthur/miniforge3/envs/s24-usd/bin/python`.

```sh
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 paper_scitech/B0/run_b0.py paper_scitech/B0/replay
python3 paper_scitech/B0/analyze_b0.py paper_scitech/B0/replay
/Users/arthur/miniforge3/envs/s24-usd/bin/python paper_scitech/B0/visualize_b0.py paper_scitech/B0/replay
python3 paper_scitech/B0/event_playback.py paper_scitech/B0/replay
```

Le run écrit son journal natif dans un dossier temporaire neuf. Seules les entrées enchâssées de l’archive historique sont lues pour le DES. Les sorties, le journal et les chronologies sont générés à nouveau. Le temps de calcul, le chemin du dossier et l’identifiant changent lors d’un rejeu. Les empreintes du paquet sont dans [SHA256SUMS](SHA256SUMS).
