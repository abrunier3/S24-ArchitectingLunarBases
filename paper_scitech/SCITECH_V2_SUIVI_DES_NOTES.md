# Suivi des annotations de la V2

Les notes originales sont conservées en rouge dans la V2 Word. La V1 annotée reste inchangée.

## N01 Traité

Là je crois que je preferais l’ancienne formulation, qu’en penses tu?

Oui, l’ancienne formulation portait mieux l’ambition de modularité. RQ1 est rétablie autour d’un processus guidé par les exigences, modulaire et scalable. J’enlève seulement la promesse d’une optimisation universelle automatique : elle ne correspond pas à une capacité démontrée.

## N02 Traité

Là j’ai l’impression que tu as pas mal change les axes de contributioons proposes non. Avant c’était end to end pipline (donc ok pour integrated ecosysteme), modularity, collaboration, visualization. Là tu skip c’est 3 derniers alors qu’ils sont centraux pour le projet (fin surotut les deux derniers car je opense que configurable behavior modeling est inclus dans modularity mais modularity incluait d’autres choses). Pourquoi ne pas juste ajouter des axes de contributions comme ca on prend tout en compte?

Tu as raison : la V1 réduisait les axes du projet. La V2 rétablit les quatre contributions centrales — pipeline intégré, modularité/scalability, collaboration, visualisation — et ajoute deux axes techniques explicites pour la simulation configurable et le CAD. La sauvegarde et la comparaison renforcent ces axes au lieu de les remplacer.

## N03 Traité

l’interoperability ne concerne que le data exchange?

Non. L’interopérabilité concerne les outils, les modèles et leurs significations, les unités, les repères spatiaux, la géométrie et les échanges entre étapes. Un JSON lisible par deux outils ne suffit pas si ces outils interprètent différemment une grandeur, un identifiant ou un repère.

## N04 Traité

Tu as enlevé versioning: en, soi on a toiujours un versioning au niveau des scenarios et meme des cad ajoutés etc donc je pense qu’on peut le garde ren tant que req.

Versioning est rétabli comme thème d’exigences : modèles, code, assets CAD et configurations suivis dans le dépôt, ainsi que conservation des scénarios nommés. Je distingue le nom d’un scénario d’une révision : un scénario peut évoluer, tandis que l’historique Git permet de retrouver des versions lorsque les artefacts concernés y sont suivis.

## N05 Traité

En vrai j’aimais bien la facon de rédiger les requirements de l’ancien paper. On dit ok on a ces grands themes de reqiuirements qui ont engendré la creation de l’arhitecture. Apres pour chaque bloc on dit explicitement quelles sont les req et puis les criteres de résuiites comme tu dis, opn dit ce qu’est le bloc et on vérifie que ca valide le critere, ou bien ca ca vient apres?

Je reprends la logique de l’ancien paper : les grands thèmes d’exigences introduisent Architecture, puis chaque bloc est dérivé des besoins auxquels il répond. Le critère de réussite est défini à cet endroit ; le mécanisme concret est décrit dans Implementation ; la satisfaction effectivement observée est discutée avec les résultats disponibles, sans annoncer d’emblée que tout est vérifié.

## N06 Traité

Je ne pense ^pas qu’il y ait besoin de faire une soys partie pour ca, je pense que je preferais comme avant.

La sous-partie autonome sur les exigences est supprimée. Les six thèmes historiques ouvrent directement la section III, avant le schéma global et la dérivation des blocs.

## N07 Traité

Est ce que tu penses que je dois mettre ici le schema global de l’architectire (donc juste avant qu’on explique la decomposition des blocs) ou bien apres (comme ce que j’avais fait avant)? Je me demande si c’est pas mieux avant.

Je retiens le schéma avant la décomposition détaillée. Après le paragraphe sur les exigences, deux phrases présentent la vue d’ensemble et la figure donne au lecteur une carte des blocs. La suite justifie chaque bloc ; le dernier paragraphe fait la synthèse sans répéter la figure.

## N08 Traité

(que veut dire stabe identifiers?)

Je voulais dire les identifiants communs permettant de reconnaître un même système dans le SysML, ses exports, les routes, les résultats et la scène. Par exemple, un identifiant d’instance tel que ISRUPlant_1 permet de rattacher une production à la bonne usine. Je remplace « stable identifiers » par une formulation explicite ; cela ne suppose pas un identifiant universel qui résisterait automatiquement à tout renommage.

## N09 Traité

c’est pas la qu’on choisit les instances des modules mais dans la step4.2 phase 1 qui s’appelle d’ailleurs asset instancing et placement) ici on choisit juste leur type (leur classe) et si on veut les active ou non

Correction faite : Step 2 active les systèmes et permet de revoir leur classe opérationnelle. Le nombre d’instances fixes et leur placement sont définis en Step 4.2 Phase 1, Asset Instancing and Placement ; les flottes et affectations de rovers relèvent de la Phase 2. Le bloc logique est renommé Module Selection et le mapping est précisé dans Implementation.

## N10 Traité

Ah mais je viens de comprendre. En fait ces blocs logiques ne correspondent pas necessaire aux steps de l’interface c’est ca? en gros c’est juste l’architectire logique et dans implementation on va voir concretement comment ca a été implémenté donc on aure peut etre des blocs mélangés ou séparés en deux?

Exactement. Les blocs décrivent des responsabilités fonctionnelles, pas nécessairement des écrans. Une étape de l’interface peut réunir plusieurs responsabilités, et un bloc peut être réalisé à plusieurs étapes. La V2 ajoute le mapping explicite vers Step 2 et les phases de Step 4.2.

## N11 Traité

je ne comprends pas bien ce que tu veux dire avec cette phrase)(quelle est la diff entre resource relashionship et equations?)Ne parle t-on pas de scenario validation aussi ou ca ca viendra dans implementation?

La description opérationnelle précise quels systèmes participent, qui échange quelle ressource, sur quelle route, avec quelles lois et quels réglages. Une relation de ressource indique « qui fournit quoi à qui » ; une équation indique « combien, en combien de temps et avec quelle énergie ». La validation du scénario est mentionnée ici comme fonction ; ses contrôles sont détaillés en IV.D. Elle est distincte de la vérification des exigences après simulation.

## N12 Traité

On a aussi mtn la possibiité de chatgé des scenarios etc de faire du versioning de scenario entre les users etc, ce qui ajoute a la collaboration.

Oui : les scénarios sauvegardés, leur chargement par les contributeurs ayant accès au dépôt, la comparaison et le versioning font partie du support à la collaboration. Le bloc et IV.H le disent maintenant explicitement. Cela reste distinct d’une édition simultanée du même scénario par plusieurs utilisateurs.

## N13 Traité

 la je ne comprends pas bien, peux tu me donner plus de details?

Il s’agit de dire quelle donnée fait référence et qui a le droit de la remplacer dans le workflow. Les dimensions de conception proviennent du SysML ; une surcharge de scénario est une hypothèse locale à cet essai ; le CAD apporte une géométrie et une provenance ; le DES produit les résultats ; le manifest indique les fichiers à lire ensemble. Le CAD ne doit donc pas redéfinir silencieusement les dimensions SysML et un ancien résultat ne doit pas être associé à une nouvelle configuration.

## N14 Traité

(j’aime beaucoup cette phrase, elle claque). je ne comprends pas cette deuxieme partie de phrase, a quoi fais tu références?

Je conserve l’idée « a scenario binds these artifacts together ». La suite est réécrite concrètement : les entrées et sorties de deux scénarios nommés restent identifiables séparément, ce qui permet de revenir au scénario A après avoir exécuté B. Cela ne promet pas des snapshots immuables pour chaque run d’un même scénario ; une reproduction historique exacte requiert aussi la révision des fichiers et dépendances.

## N15 Traité

Ah donc tu penses que la figure on la laisse a la fin, oui c’est peut etre mieux possiblement mais en meme temps ca facilite peut etre la lecture si c’est au debut. En fait je pense que pour la lecture c’est mieux au début, mais pour la continuité logique c’est mieux a la fin.


La décision est prise en faveur de la lecture : figure en début de III, après les thèmes d’exigences et une courte présentation. La continuité logique est conservée en justifiant ensuite les blocs dans l’ordre du flux, puis en terminant par un paragraphe de synthèse.

## N16 Traité

Donc concretement pour update cette figure, tu penses a quoi? Qu’est ce qui doitetre ajouté a la figure actuelle?

Le brief de mise à jour est maintenant explicite : conserver les huit blocs ; montrer la définition de scénario avec instances, routes, équations et réglages ; ajouter sauvegarde/chargement/comparaison à la couche Collaboration ; représenter le retour des métadonnées CAD vers SysML ; et montrer le package de visualisation et la télémétrie enregistrée. Les rôles d’acteurs restent visibles. La figure principale reste fonctionnelle : les fichiers et les détails d’algorithmes vont dans le texte d’implémentation, sans multiplier les schémas.

## N17 Traité

 la tu as enlevé le mot collaboration d’ici alors que c’est un mot clé du projet.

Collaboration est rétabli dans le titre de IV.H et dans son contenu : contributions aux étapes, partage et chargement des scénarios, historique des modèles et CAD, comparaison et automatisation. Le multi-user support reste une exigence ; son niveau de réalisation est décrit précisément.

## N18 Traité

  ca on l’a pas vrm fait, je ne pense pas que ca serve a quelque chose de parler de ca. je pense la stratégie qu’on peut prendre c’est d’expliquer concretemtn ce qu’on peut faire, dire que de base ca a été consrutit sur un scenario ISRU mais qu’on a généralisé le process et que mtn ca peut etre faoit sur tou type de scenario mais ca n’a pas été encore testé sur des scenarios vrm tres different. Je evux dire ok tu m’avais généré d’autres scenarios et on les avait run mais concretemtn on n’avais pas regarder si tout marchait bien jusqu’a la visualization et c’était des scenarios tres simples.

Je retire la sous-partie de résultats consacrée aux trois exemples génériques et les demandes de les reproduire pour ce paper. Tu confirmes des essais simples exécutés, mais pas une validation de bout en bout jusqu’à Omniverse. La méthode explique la généralisation réellement implémentée ; la discussion précise qu’elle reste à évaluer sur des scénarios significativement différents. On peut exposer l’ambition de couvrir plusieurs types de scénarios, sans conclure que tous les scénarios sont déjà supportés ou validés.

## N19 Traité

 ca pareil je pense qu’on va l’enlever car cette partioe a été faite mais pas vrm testé.

Je retire la sous-partie V.F qui demandait une démonstration actuelle de vérification et de couverture. La boucle d’exigences reste décrite dans Architecture et Implementation comme un développement dont la validation intégrée n’est pas établie ici. Le paper ne présentera ni rapport pass/fail ni automatisation complète comme résultat sans preuve correspondante.

## N20 Pris en compte et à compléter

 une npuvelle team bosse sur le projet, on va les introduire je pense ici et je t’enverrai leur ppt le plus recent au niveau des points. On peut aussi dire que je vais contnuer la rechercher dessus dans le cadre de mon phd?

Oui, Future Work peut situer la poursuite du projet par une nouvelle équipe et par tes recherches doctorales prévues, en restant centré sur les questions scientifiques. Je prévois une phrase collective et sobre. Le périmètre précis de la nouvelle équipe sera intégré après lecture de son PPT ; je ne lui attribue pas à ce stade les tâches de la liste.

## N21 Traité

Tu parles souvent de generic démonstrations, a quoi tu fais ref?

Je faisais référence aux essais cargo relay, ice processing et water transfer cités dans les échanges précédents. Ta précision prévaut : des scénarios simples ont été générés et exécutés, mais leur chaîne complète jusqu’à la visualisation n’a pas été validée. Je retire leur statut de démonstrations et leurs résultats du plan scientifique.

## N22 Traité

j’ai l’impression que tu as remplacé certains mots clés: modularity par configurability, scalability par extensibilité, multi-user support par contribution from different specialties. Peux tu m’expliquer ce choix?

J’avais choisi des termes décrivant plus directement les mécanismes observables, mais cela réduisait les exigences au lieu de les préciser. Modularity concerne la composition et le remplacement de modules ; configurability concerne leurs réglages. Scalability concerne l’augmentation de systèmes, scénarios, données ou utilisateurs ; extensibility concerne l’ajout de fonctions. Multi-user support concerne l’usage par plusieurs personnes ; les contributions par spécialité en décrivent un mode, sans couvrir tout le besoin. Les mots-clés originaux sont rétablis, avec leur niveau de preuve.

## N23 Traité

Il y a aussi un point a prendre en compte, c’est la longueur du paper. Celui-ci ne peut pas être infini ; un conference paper fait généralement 15-20 pages ?

La FAQ générale SciTech indique l’absence de plafond général et une longueur courante de 12 à 24 pages, références comprises ; des règles spécifiques peuvent dépendre de la session. Pour ce paper, la V2 retient une cible éditoriale de 22 à 24 pages et un budget de travail de 24 pages, figures, tableaux et références inclus. La longueur du présent outline annoté n’est pas celle du manuscrit final.
