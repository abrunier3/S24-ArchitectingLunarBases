# Lunar Spaceport — résultats comparatifs pour V.C et V.D

Deux simulations indépendantes de 168 h ont été exécutées avec le moteur ECLIPSE utilisé en V.B. Pour *Reduced LOX dispatch threshold*, les deux seuils passent de 15 à 10 kg. Les autres entrées physiques sont celles du cas de référence. Pour *Distributed LOX storage*, le seuil reste à 15 kg. Le dépôt initial de 250 kg devient deux dépôts de 125 kg. Le premier garde sa position et sa route. Le second est placé à (245, 760) m dans le repère local de Malapert. Le trajet de la navette 2 passe de 2,817 à 0,254 km en plan.

La configuration distribuée exécutée est exactement le payload exporté par le portail et archivé lors du contrôle préalable. Il contient une affectation LOX par usine et par navette. Les trois polylignes témoins, dont deux de régolithe, ont été comparées waypoint par waypoint. Les quatre routes auxiliaires sont aussi identiques. Les deux expériences sont passées par le dispatcher Python en local. Le script de campagne assemble l'expérience de seuil et archive les appels. Le workflow distant GitHub Actions n'a pas été déclenché. [Audit des routes](results/route_audit.json) · [Export du portail](../distributed_storage_preflight/portal_export.json)

## Tableau compact pour V.C

| Metric over 168 h | Lunar Spaceport case study | Reduced LOX dispatch threshold | Distributed LOX storage |
|---|---:|---:|---:|
| Dispatch threshold (kg) | 15 | 10 | 15 |
| Completed batches, plants 1 / 2 | 63 / 37 | 63 / 37 | 63 / 37 |
| LOX produced (kg) | 112.530 | 112.530 | 112.530 |
| First delivery, rovers 1 / 2 (h) | 25.529 / 27.650 | 17.863 / 19.984 | 25.529 / 25.087 |
| LOX at original depot site at 168 h (kg) | 90.171 | 110.328 | 60.130 |
| LOX at second depot at 168 h (kg) | — | — | 30.090 |
| Final plant buffers, total (kg) | 22.359 | 2.202 | 22.310 |
| Completed LOX deliveries, rovers 1 / 2 | 4 / 2 | 7 / 4 | 4 / 2 |
| Completed LOX fleet travel (km) | 16.836 | 32.280 | 6.584 |

Le LOX en transit à 168 h est nul dans les trois cas. Les distances cumulent tous les segments achevés des navettes LOX, allers chargés et retours à vide. Un tiret indique un dépôt absent. [Table LaTeX](table_vc.tex) · [Chiffres intégralement désagrégés](results/comparison.json)

### Disponibilité par site et par navette

| Stock au dépôt (kg) | 24 h | 48 h | 168 h |
|---|---:|---:|---:|
| Lunar Spaceport case study · site initial | 0.000 | 30.041 | 90.171 |
| Reduced LOX dispatch threshold · site initial | 20.060 | 40.119 | 110.328 |
| Distributed LOX storage · site initial | 0.000 | 15.020 | 60.130 |
| Distributed LOX storage · second site | 0.000 | 15.020 | 30.090 |

| Configuration | Charge moyenne navettes 1 / 2 (kg/livraison) | Distance navettes 1 / 2 (km) | Tampons usines 1 / 2 à 168 h (kg) |
|---|---:|---:|---:|
| Lunar Spaceport case study | 15.033 / 15.020 | 5.568 / 11.268 | 10.764 / 11.595 |
| Reduced LOX dispatch threshold | 10.030 / 10.030 | 9.744 / 22.536 | 0.685 / 1.517 |
| Distributed LOX storage | 15.033 / 15.045 | 5.568 / 1.016 | 10.764 / 11.547 |

Dans les deux premiers cas les navettes alimentent le même dépôt. Dans le cas distribué la navette 1 dessert le site initial et la navette 2 dessert le second site.

### Résultats et compromis

- **Seuil réduit.** Les premières livraisons surviennent 7,667 h plus tôt pour chaque navette. Le dépôt reçoit 20,060 kg dès 24 h et 20,158 kg de plus à 168 h, soit +22,4 %. Les livraisons passent de 6 à 11 et la flotte parcourt 15,444 km supplémentaires, soit +91,7 %. La quantité de LOX livrée par km de flotte passe de 5,36 à 3,42 kg/km sur la fenêtre.
- **Stockage distribué.** La navette 2 part à 24,833 h dans les deux architectures et arrive 2,563 h plus tôt avec la route courte. Sa distance cumulée baisse de 11,268 à 1,016 km, soit −91,0 %. La flotte passe de 16,836 à 6,584 km. La masse cumulée aux deux dépôts reste proche de celle du cas étalon, 90,220 contre 90,171 kg, avec seulement 60,130 kg au site initial. Les 30,090 kg du second site y demeurent. L'écart agrégé de 0,049 kg correspond à la masse supplémentaire chargée lors de la seconde livraison de la navette 2. Le calendrier de disponibilité est échantillonné aux vérifications de seuil de chaque véhicule.
- **Amont et bilans.** Chaque variante reproduit exactement la chronologie des lots, des rovers de régolithe et de la liquéfaction de référence. Les trémies manquent respectivement 35 et 61 démarrages de lots. Les rovers manquent au total 35 opportunités de livraison de régolithe et 42 opportunités d'enlèvement de résidus, en raison des missions en cours ou de la recharge. Le résidu stocké atteint 817,47 kg au total. Aucun délai d'attente positif au quai LOX n'est enregistré, et aucun dépôt n'atteint sa capacité. Le résidu maximal des bilans matière en cours d'événement vaut 8,53 × 10⁻¹³ kg dans les trois cas.
- **Limites.** Les kilomètres mesurent la charge de transport. La consommation des navettes LOX, la distribution vers la zone de lancement, le maintien cryogénique et les coûts du second dépôt restent hors modèle. La durée de roulage DES emploie la distance en plan à vitesse prescrite. Le maillage est utilisé pour le rejeu et présente des avertissements d'alignement de pente. Le trajet de 0,254 km est une hypothèse d'implantation. L'optimum et la traversabilité du site nécessiteraient des analyses distinctes.

**Figure proposée.** Le panneau (a) met en relation la première livraison et les kilomètres parcourus par chaque navette. Le panneau (b) localise le LOX à 168 h. [PDF vectoriel](lox_logistics_tradeoffs.pdf) · [PNG](lox_logistics_tradeoffs.png)

*Proposed caption.* Operational trade-offs across the Lunar Spaceport case study and two independent variants. (a) First LOX delivery time and completed travel distance over 168 h for each rover. The rover 1 observations coincide for the Lunar Spaceport case study and distributed storage. (b) Final LOX inventory by location. All configurations produced 112.53 kg, and no LOX remained in transit at the end of the runs.

## V.D — preuve de continuité

| Maillon | Cas de référence | Variante à deux dépôts |
|---|---|---|
| Définition et instanciation | Le SysML fournit le type `PropellantDepot` et les interfaces `ISRUPlantToRover` et `RoverToPropellantDepot`. Le graphe et le JSON système relient les types aux instances du cas. | Le même type alimente `PropellantDepot_1` et `PropellantDepot_2` dans le snapshot et le payload. L'implantation est définie dans l'export Urban Planning. |
| Spatial → DES → USD | La navette `LOXRover_2` part à 24,8333 h et livre 15,0203 kg à 27,6503 h. À 26 h, le tableau Kit affiche 31,6 kg produits, 15,0 kg au dépôt et 1,6 kg aux usines, avec les rovers et le terrain visibles selon l'observation utilisateur. | Même acteur et identifiant de trajet `LOX_1790955451209_1`. La route `ISRUPlant_2ToPropellantDepot_2_LOX` relie le payload de 0,254 km au prim de waypoints du même nom et au trajet du manifeste. Le départ à 24,8333 h conduit à une réception de 15,0203 kg à 25,0873 h. Le nouveau dépôt est composé sous `/World/PropellantDepot_2`. |
| Validation de la représentation | Le chargement et le rejeu dans Kit depuis GitHub sont confirmés par l'utilisateur. Les captures Overview, dashboard et télémétrie sont à intégrer au manuscrit. | OpenUSD résout les couches, les actifs et les textures. Les fonctions de l’extension ont aussi été testées sur une scène OpenUSD sans interface pour la découverte, la composition et le placement des deux dépôts, ainsi que la liaison entre le déplacement et l’instant DES. Les 54 déplacements et les 100 intervalles de traitement correspondent au même `request_id` que le DES. Le rejeu interactif de cette variante reste à confirmer dans Kit. |

Pour la variante à deux dépôts, l'instant commun de **26 h** est prévu à **30,041 kg dans les deux dépôts**, soit **15,020 kg par dépôt**, **0 kg en transit** et **1,566 kg aux usines** sur **31,606 kg produits**. À cet instant, la navette 1 revient vers l'usine 1 et la navette 2 attend déjà à l'usine 2. Le tableau de bord agrège le stock des destinations. Pour prouver sa localisation, conserver aussi la vue Overview avec les routes et rapprocher l'image des inventaires désagrégés du journal DES. [Paquet et contrôles OpenUSD](../../../outputs/scenarios/Distributed_LOX_storage) · [Résultat routé et télémétrie DES](results/distributed_storage/des_results.json)

**Interopérabilité et versioning.** Le commit `4e3888172badde2094e7fb55ca9725dc3130ec57` attribue l'ajout du CAD source de dépôt à `ivmalav-a11y`. Le commit `e87be9bc8ae5ffd8829b09ebee5a07a489e372b6` attribue sa copie dans le scénario ISRU à `abrunier3`. Les deux fichiers ont le même objet Git `0c702f318b99b54b5dd3af9b835554385a4a3e40` et la même empreinte SHA-256 `23bba7588ebdf0d23dd58662940ada104df3c6db7b62d18dfc6959dedd56c3fb`. Le rejeu public compose une copie portable enrichie de textures. L'ancienne vérification OpenUSD établit l'identité de l'actif géométrique de référence et le contrôle de préparation de la scène établit l'identité des points et de la topologie de son dérivé. La scène distribuée référence cette même copie portable pour les deux dépôts. Cette chaîne établit la réutilisation d'un CAD entre contributeurs. Le snapshot exporté établit la persistance de la configuration distribuée. [Provenance de la contribution](../README.md#contribution-provenance)

## Orientation de rédaction

- **V.C · C2, C4 et RQ1.** Présenter les deux variantes comme deux décisions indépendantes sur un cas de départ commun. Le seuil teste la politique d'exploitation. Le second dépôt teste l'instanciation, le placement et le routage. Utiliser la figure pour le compromis délai–distance–lieu, et citer les paramètres maintenus pour attribuer les écarts. En une phrase, ajouter le contrôle de l'éditeur d'équations. Une surcharge enregistrée et rechargée sur `ISRUPlant_1` a limité l'O₂ gazeux de son premier lot à 1,0000 kg, contre 1,1253 kg pour l'usine 2 qui héritait de la loi nominale. [Contrôle de l'éditeur](../equation_editor/evidence.json)
- **V.D · C1, C3, C4 et RQ2–RQ3.** Suivre une livraison de la navette 2 dans les deux architectures et relier le même événement au stock local et à la scène. Pour le cas de référence, préférer une capture Overview à 26 h avec les routes et le tableau de bord. Si le rejeu distribué est confirmé, ajouter une seconde vue au même instant ou une vue au moment de la réception. Lier les deux commits du CAD à l'actif employé dans la scène. Les traces disponibles étayent le réemploi d'artefacts et l'interopérabilité. Une reprise par deux collaborateurs de la variante distribuée demanderait leurs révisions et interventions attribuables.
- Le cas étaye **RQ1** pour l'instanciation et les comportements configurables des types pris en charge. Il étaye **RQ2** par un exemple de contribution CAD versionnée et réutilisée. Pour **RQ3**, l'état du stock par destination est la mesure qui donne un sens opérationnel à la comparaison visuelle. La portée à de nouveaux types SysML reste étayée séparément au niveau du moteur générique.

## Reproductibilité

Les dossiers [seuil réduit](results/reduced_dispatch_threshold) et [stockage distribué](results/distributed_storage) contiennent les entrées, les configurations résolues, la télémétrie standard, le journal complet compressé, les séries horaires, les livraisons et les empreintes. La révision et les hachés établissent que les fichiers du moteur et de la configuration par défaut sont identiques à ceux archivés pour le cas V.B.

Depuis la racine, avec SimPy et OpenUSD disponibles pour les commandes correspondantes.

```sh
python3 -m paper_scitech.engineering_evidence.scenario_comparison.run_comparison /tmp/lunar_spaceport_contrasts
python3 paper_scitech/engineering_evidence/scenario_comparison/plot_comparison.py
```

Le script `export_distributed_replay.py` réemploie le constructeur de manifeste et le générateur de waypoints d'ECLIPSE. Exécution avec un nouveau dossier de sortie sous `outputs/scenarios/` et le répertoire du run distribué pour produire une copie de contrôle. Le paquet livré est à l'emplacement attendu par le sélecteur **Distributed LOX storage**.
