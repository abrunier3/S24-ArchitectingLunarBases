# B0 · Lunar Spaceport à Malapert Massif

**Exécution B0-168h-01.** En 168 h, les deux usines ont traité 930,0 kg de régolithe et liquéfié **112,53 kg de LOX**. Le dépôt a reçu **90,17 kg** au cours de six livraisons. Les 22,36 kg restants sont dans les deux tampons d’usine. Le scénario a terminé à l’horizon prévu, avec les quatre rovers à l’arrêt et sans lot, liquéfaction ni cargaison en cours. [Configuration](runs/B0-168h-01/scenario.json) · [Analyse chiffrée](runs/B0-168h-01/analysis.json)

## Hypothèses et paramètres utilisables dans V.A

| Poste | Valeur dans B0 | Origine |
|---|---|---|
| Architecture | Une zone d’excavation, deux rovers de régolithe, deux usines, deux navettes LOX, un dépôt, une alimentation solaire et une zone d’atterrissage/lancement. L’habitation est exclue. La zone ne prélève pas de LOX sur la fenêtre. | Sept types du Lunar Spaceport, positions et orientations archivées de Malapert. |
| Site et horizon | 168 h éclairées. Les batteries des rovers de régolithe sont initialement pleines. Chaque trémie reçoit 130,2 kg au départ. Stocks d’oxygène, de LOX et de résidus vides. | Même convention de départ que le benchmark R. Éclairement uniforme choisi pour l’étude, sans profil solaire mesuré à Malapert. |
| Procédé | Deux lignes carbothermiques. 9,3 kg par lot, 100 min de service, 14 créneaux uniformes par 24 h. O₂ extrait = 0,121 × masse traitée, crédité à la fin du lot. Le résidu solide reçoit la masse traitée moins l’O₂ extrait. Un lot exige au moins 9,3 kg dans la trémie et le créneau est perdu si la charge manque. | Masse du lot, durée et rendement COMPASS, cas 2. Démarrage des lots par créneau, synchronisation et représentation agrégée de la chimie hérités du benchmark ECLIPSE. |
| Trémies et ravitaillement | 130,2 kg par usine. Créneaux à 0, 6, 12 et 18 h de chaque jour. Jusqu’à 35 kg selon la place libre. Chargement 3 min, déchargement 5 min. Un aller-retour prend 4,021 h vers U1 et 8,263 h vers U2, manutention incluse. | Capacités et durées COMPASS. Routes ECLIPSE, vitesse effective de 1 km/h, réservation d’un véhicule par ligne et calendrier déterministe. |
| Résidus solides | Opportunités à 3, 9 et 15 h. Charge utile 40 kg et chargement 5 min. Le rover rejoint d’abord son usine à vide, puis une décharge conceptuelle à 100 m. Retour estimé via l’usine. Les rotations demanderaient environ 4,171 h pour U1 et 8,413 h pour U2, repositionnement compris. | Cadence, charge et manutention COMPASS. Embranchements sans géométrie locale qualifiée. La capacité des stocks de résidus est supposée suffisante. |
| Recharge mobile | Batterie de 1 kWh, réserve 0,20 kWh, 71,59 W en déplacement et manutention. Recharge de 0,10 kW pendant 10 h, rendement de charge 80 %. À Malapert, le rover reporte la mission et se recharge si son départ compromet la réserve. | Batterie et recharge COMPASS. Puissance d’activité dérivée du budget de référence. Déclenchement à la demande adapté à Malapert. |
| Liquéfaction | Deux liquéfacteurs dédiés de 0,65 kg/h chacun, capacité agrégée 1,30 kg/h. Masse libérée par paquets ≤ 0,05 kg après le service. Tampon LOX de 35 kg par usine. | Même débit nominal agrégé que dans COMPASS, où un liquéfacteur commun partage toute la capacité. La distribution interdit d’emprunter la capacité inutilisée de l’autre usine. Le volume utile de stockage est fixé pour B0. |
| Livraison de LOX | Deux navettes dédiées, 18 kg chacune, seuil de 15 kg, vérification toutes les 5 min, vitesse 1 km/h, manutention de LOX instantanée. Un seul dépôt de 250 kg. Les pertes de LOX sont supposées nulles. | Hypothèses du Lunar Spaceport. COMPASS mesure au réservoir commun et reporte la logistique du client à une étude ultérieure. |
| Électricité | 15 kWe disponibles, 11,544 kWe de demande pour deux lignes actives, 2,678 kWe en veille avec interpolation pour une seule ligne. Ajouter le tirage des recharges de régolithe lorsque les chargeurs sont actifs. Surplus écrêté, aucun stockage électrique central crédité. | Mode ensoleillé et dimensionnement COMPASS. Veille courte et interpolation ECLIPSE. Les pertes du réseau, l’énergie des navettes LOX et le froid du dépôt distant sont hors de ce bilan partiel. |
| Chaleur directe | 11,1 kWth reçus par ligne active, avec deux collecteurs locaux supposés. L’intégrale thermique ne passe pas par le bus électrique. | Valeur au récepteur COMPASS. Le concentrateur commun de la NASA est remplacé par une fourniture locale supposée à Malapert. |

Sources des paramètres COMPASS et de leurs frontières. [Linne et al., NASA 2019, cas 2 et Powered Equipment List](https://ntrs.nasa.gov/citations/20190029197) · [Linne et al., ASCE 2021](https://doi.org/10.1061/%28ASCE%29AS.1943-5525.0001269)

## Résultats matière et chronologie

| Grandeur sur 168 h | Usine 1 | Usine 2 | Ensemble |
|---|---:|---:|---:|
| Régolithe livré à la trémie [kg] | 457,20 | 219,30 | 676,50 |
| Régolithe traité [kg] | 585,90 | 344,10 | 930,00 |
| Régolithe restant en trémie [kg] | 1,50 | 5,40 | 6,90 |
| Lots terminés / manqués | 63 / 35 | 37 / 61 | 100 / 96 |
| Première opportunité de lot manquée [h] | 42,857 | 25,714 | 25,714 |
| O₂ extrait [kg] | 70,894 | 41,636 | 112,530 |
| LOX liquéfié [kg] | 70,894 | 41,636 | 112,530 |
| Premier LOX disponible [h] | 1,742 | 1,742 | 1,742 |
| Premier LOX arrivé au dépôt [h] | 25,529 | 27,650 | 25,529 |
| LOX déposé [kg] | 60,130 | 30,041 | 90,171 |
| Tampon LOX final à l’usine [kg] | 10,764 | 11,595 | 22,359 |
| Maximum du tampon LOX [kg] | 15,069 | 15,020 | — |
| LOX en transit à 168 h [kg] | 0 | 0 | 0 |
| Résidu solide en stock [kg] | 515,006 | 302,464 | 817,470 |
| Chaleur reçue par les réacteurs [kWhth] | 1 165,5 | 684,5 | 1 850,0 |

Environ **80,1 %** du LOX produit a rejoint le dépôt. Le reste était disponible en tampon, sous le seuil de départ de 15 kg pour chaque navette. Les deux tampons LOX restent sous leur capacité de 35 kg. Le dépôt atteint 90,17 kg sur une capacité de 250 kg et ne provoque aucune attente de place. Les trémies de régolithe sont pleines au départ par construction. Les lots manqués surviennent lorsque la matière disponible est inférieure à 9,3 kg. Les stocks gazeux et les encours de liquéfaction sont nuls à l’horizon à la précision numérique.

| Véhicule | Livraisons | Distance achevée [km] | Conduite [h] | Manutention [h] | Recharge [h] | Attente ou inactivité [h] | Usage transport |
|---|---:|---:|---:|---:|---:|---:|---:|
| Régolithe 1 | 14 | 54,432 | 54,432 | 1,867 | 70,000 | 41,701 | 33,5 % |
| Régolithe 2 | 7 | 56,910 | 56,910 | 0,933 | 70,000 | 40,157 | 34,4 % |
| LOX 1 | 4 | 5,568 | 5,568 | 0 | — | 162,432 | 3,3 % |
| LOX 2 | 2 | 11,268 | 11,268 | 0 | — | 156,732 | 6,7 % |

L’usage transport inclut conduite et manutention. La colonne d’inactivité couvre notamment les attentes de créneau ou de seuil LOX. Les deux navettes franchissent leur seuil initial au même instant, à **24,833 h**. L’écart de **2,121 h** entre leurs premières livraisons découle des 2,121 km supplémentaires vers le dépôt à la vitesse prescrite. Ensuite, le rythme de production de chaque usine commande le remplissage des navettes.

### Interactions qui expliquent les résultats

1. **Le calendrier et la batterie amplifient l’effet de la distance.** Avec les trajets actuels, deux tours vers U1 consomment environ 0,576 kWh, alors qu’un seul vers U2 demande environ 0,592 kWh. La réserve de 0,20 kWh interdit respectivement un troisième ou un deuxième tour sans recharge. Le rover d’U2 parcourt donc légèrement plus de kilomètres que celui d’U1, tout en assurant la moitié de ses livraisons. Sur les 28 créneaux d’approvisionnement par véhicule, U1 en perd sept en déclenchant la recharge et sept pendant une occupation. U2 en perd 21 pendant une occupation. Ses sept recharges sont déclenchées par des tentatives de mission de résidus. Ce sont les effets conjoints des distances, des calendriers et de la stratégie de recharge.
2. **La collecte des résidus n’est jamais servie.** Les 21 créneaux d’U1 sont occupés par d’autres phases au moment prévu. Sur U2, 14 créneaux tombent pendant une occupation et sept déclenchent une recharge. Les 817,47 kg restent aux usines. L’espace de stockage supposé suffisant permet au DES de poursuivre. Ce résultat expose un conflit de planification. La capacité réelle des trémies de résidus et un blocage éventuel des réacteurs restent à établir.
3. **L’alimentation amont domine la perte de production.** Le nombre de lots et l’O₂ extrait baissent de 49,0 %. Le LOX liquéfié baisse de 48,0 %. B0 vide sa file de liquéfaction pendant les arrêts dus au manque de régolithe. Il serait donc erroné d’attribuer l’écart à la seule distribution des liquéfacteurs. La comparaison combine une implantation différente, une recharge adaptée aux missions et deux capacités aval dédiées. Les plafonds de 0,65 kg/h par ligne sont atteignables dans le modèle pendant les séquences alimentées.

## Comparaison COMPASS–B0 à frontières constantes

| Mesure | R-168h-01, COMPASS | B0-168h-01, Malapert | Écart B0/R |
|---|---:|---:|---:|
| Régolithe livré aux trémies [kg] | 1 671,60 | 676,50 | −59,53 % |
| Lots terminés | 196 | 100 | −48,98 % |
| Régolithe traité [kg] | 1 822,80 | 930,00 | −48,98 % |
| O₂ extrait [kg] | 220,559 | 112,530 | −48,98 % |
| LOX à la sortie de liquéfaction [kg] | 216,204 | 112,530 | −47,95 % |
| Débit moyen de LOX liquéfié sur l’horizon [kg/h] | 1,28693 | 0,66982 | −47,95 % |
| Électricité du noyau [kWh] | 1 898,017 | 1 188,737 | −37,37 % |
| Électricité tirée par les chargeurs de régolithe [kWh] | 2,000 | 14,000 | +600 % |
| Chaleur reçue aux réacteurs [kWhth] | 3 626,0 | 1 850,0 | −48,98 % |

Le réservoir commun de COMPASS est à la sortie du liquéfacteur. La livraison de 90,17 kg au dépôt distant est un résultat propre à B0. La baisse de **47,95 %** se compare donc à la sortie de liquéfaction. Les hauteurs de terrain projetées et la disponibilité annuelle solaire sortent du périmètre comparable.

**Énergie B0.** Sur 2 520,000 kWh disponibles, le bus demande **1 202,737 kWh** (noyau et chargeurs) et écrête **1 317,263 kWh**. Aucune demande électrique n’est non servie dans ce périmètre. La puissance de pointe modélisée avec deux chargeurs actifs vaut **11,744 kWe**. Les rovers de régolithe dépensent 4,030 et 4,141 kWh sur leurs batteries. Ces décharges ne sont pas additionnées une seconde fois à la demande du bus. Les navettes LOX, le froid des tampons déportés et du dépôt, et les pertes de transfert n’ont pas de budget énergétique caractérisé. Le rapport bus/LOX vaut **10,69 kWh électriques/kg** pour B0 et **8,79** pour R sur leur fenêtre respective. L’augmentation traduit dans ce modèle une plus grande part de veille par kilogramme de LOX. Elle ne mesure pas un changement d’efficacité des réacteurs.

## Routes et reconstruction spatiotemporelle

| Trajet opérationnel | Longueur en plan utilisée par le DES [km] | Longueur projetée sur le maillage [km] | Segments animés |
|---|---:|---:|---:|
| Excavation ↔ U1 | 1,944 | 1,995 | 28 |
| Excavation ↔ U2 | 4,065 | 4,174 | 14 |
| U1 ↔ dépôt | 0,696 | 0,717 | 8 |
| U2 ↔ dépôt | 2,817 | 2,897 | 4 |

Les longueurs DES coïncident au mètre près avec les polylignes archivées. Les projections 3D ont une couverture complète dans OpenUSD, avec des avertissements d’alignement et des pentes maximales locales de 36,5–40,9°. La vitesse constante et le cadre de la scène ne qualifient pas la traversabilité. Les embranchements de résidus restent des distances conceptuelles et aucune mission correspondante n’a commencé. Le paquet OpenUSD exploite les **54 intervalles exacts de déplacement** et les **100 intervalles de traitement**. Des textures de matériaux référencées dans les fichiers CAD historiques n’ont pas été résolues. Les maillages et les géométries de chemins ont été ouverts et contrôlés. Le rendu et le tableau de bord ont été raccordés au code de l’extension. Leur rendu interactif dans NVIDIA Kit reste à vérifier.

- [Manifest Omniverse et chronologies](runs/B0-168h-01/omniverse/manifest.json) · [Scène USDA](runs/B0-168h-01/omniverse/scene.usda) · [Waypoints USDA](runs/B0-168h-01/omniverse/waypoints.usda) · [Contrôles OpenUSD](runs/B0-168h-01/omniverse/checks.json)
- Les identifiants des instances et des trajets suivent l’architecture spatiale archivée. Le [système exporté](runs/B0-168h-01/system.json) associe la topologie, les poses et les routes aux lois carbothermiques réellement exécutées. Le SysML et le graphe archivés servent de référence pour les types, instances et interfaces. Les propriétés chimiques historiques présentes dans le SysML source n’alimentent pas cette exécution.
- Le portail accepte les paramètres de traitement par lots dans le panneau DES, continue d’utiliser son éditeur d’équations et ses routes opérationnelles, et sauvegarde les paramètres via le formulaire de scénario existant. Le workflow utilise le même format de résultats pour ses graphiques et ses comparaisons. Les [snapshots B0](runs/B0-168h-01/portal_snapshot.json) et [COMPASS R](runs/B0-168h-01/compass_portal_snapshot.json) s’importent dans **Saved configurations** et donnent deux entrées pour **Scenario Comparison**. Le snapshot R sert à la comparaison des résultats. Pour ce cas, la valeur zéro dans la colonne des livraisons désigne l’absence de navette vers un dépôt distant. Le LOX du réservoir commun se compare dans la colonne de production. Le workflow GitHub a été vérifié au niveau du code et de l’enveloppe de résultats locale.

## Reproductibilité

Deux lancements indépendants de 168 h ont livré des journaux compressés, CSV, analyses, exports DES et snapshots identiques octet pour octet. L’écart maximal d’un bilan matière sur les événements vaut **8,53 × 10⁻¹³ kg**. Le résidu de fermeture du bus électrique vaut **2,04 × 10⁻¹² kWh** en valeur absolue. Les intervalles des véhicules sont exclusifs, les distances de leurs trajets achevés concordent avec les compteurs DES et aucune phase ne reste ouverte à 168 h. Les sommes de contrôle de l’ancien B0 et de la référence COMPASS ont été préservées. **65 tests Python et 7 tests JavaScript** ont réussi. La révision Git de base est `c271a8cf5d86ca306c04d46e06b8f552e9e86c52`, avec copie exacte et SHA-256 des sources utilisées, y compris les adaptations encore locales.

```sh
python3 -m paper_scitech.COMPASS_B0.run_b0 paper_scitech/COMPASS_B0/runs/B0-168h-replay
python3 -m paper_scitech.COMPASS_B0.figures paper_scitech/COMPASS_B0/runs/B0-168h-replay
python3 paper_scitech/B0/visualize_b0.py paper_scitech/COMPASS_B0/runs/B0-168h-replay
```

Les figures requièrent Matplotlib, l’export 3D OpenUSD. [Provenance](runs/B0-168h-01/provenance.json) · [Résultats et journal complet](runs/B0-168h-01/results.json.gz) · [Séries horaires](runs/B0-168h-01/hourly.csv) · [Export standard DES](runs/B0-168h-01/des_results.json)

## Figures et résultats candidats pour la Section V

1. **Les deux usines ont le même procédé et des performances différentes.** La première pénurie survient à 25,7 h sur U2 et à 42,9 h sur U1. Les paliers des stocks expliquent les 37 contre 63 lots. C’est la preuve quantitative la plus directe du lien entre implantation, affectation des véhicules et performance de l’architecture. [Séries opérationnelles, PDF](runs/B0-168h-01/figures/operations.pdf)
2. **La production et la disponibilité au dépôt répondent à deux questions différentes.** Les courbes distinguent 112,53 kg liquéfiés et 90,17 kg livrés. Le premier trajet de chaque navette isole l’effet des distances de 0,696 et 2,817 km sur le délai de livraison. Les mêmes intervalles sont disponibles dans le paquet Omniverse. [Plan des routes, PDF](runs/B0-168h-01/figures/routes.pdf) · [Manifest et playback](runs/B0-168h-01/omniverse/manifest.json)
3. **La gestion des résidus révèle un conflit de ressources.** Aucun des 42 créneaux de résidus ne débouche sur une rotation. À mettre dans V.B si le calendrier opérationnel est montré, sinon à discuter avec l’hypothèse de stockage des résidus. Ce constat démontre l’intérêt d’un journal couplé des activités et des ressources, avec la capacité physique du stock à caractériser séparément.
