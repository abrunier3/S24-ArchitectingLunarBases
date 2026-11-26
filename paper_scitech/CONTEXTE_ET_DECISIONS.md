# Contexte et décisions pour le paper SciTech

Mise à jour du 18 novembre 2026.

## Consignes courantes et révision V4

Arthur valide globalement la structure et demande une V4 limitée aux points de ses nouvelles annotations vertes dans la V3. La V4 est construite à partir de la V3 annotée, sans reprendre les scripts de réécriture V3. Les 14 annotations vertes sont préservées, ainsi que les anciennes notes rouges. Les questions suivies de validations sont interprétées ensemble.

Abstract, Introduction et Motivation ne sont pas modifiés dans la V4. Pour leur rédaction ultérieure, réutiliser le paper existant et l’améliorer avec les apports de l’été et les notes déjà fournies, sans réécriture complète par défaut. Les structures Architecture et Implementation sont validées ; leur contenu sera peuplé à partir du paper précédent et des développements récents.

Les changements ciblés concernent la comparaison des études selon les critères pertinents, la séparation synthèse de littérature/research gap, l’objectif formulé en digital engineering ecosystem et evaluated, operational behavior dans RQ1, et les explications des contributions C1/C3. RQ2 et RQ3 restent inchangées. La responsabilité d’autorité des informations reste dans Architecture ; outils, formats et règles concrètes sont réservés à Implementation. Le schéma précoce et la chaîne critères → mécanismes → preuves sont confirmés. V.B rassemble site selection et démonstration du parcours ; les méthodes restent dans Implementation et les performances dans V.C.

Réutiliser les références scientifiques pertinentes déjà présentes. Les ajouts scientifiques doivent provenir de journaux reconnus et évalués par les pairs. Le préprint LUNAverse fourni sert au contexte de l’initiative et conserve explicitement son statut ; les documentations officielles servent aux mécanismes logiciels, pas à démontrer une nouveauté scientifique.

Arthur demande de mieux mettre en avant la généralisation opérationnelle jusqu’à la simulation. La V4 précise que le compilateur générique a exécuté des scénarios simples non-ISRU, et permet de construire des scénarios différents exprimables avec les rôles, comportements et équations pris en charge. Ne pas confondre cette capacité avec une couverture universelle de toute mission ou une validation non-ISRU jusqu’à Omniverse. Aucune grande campagne supplémentaire de généralisation n’est requise pour cette soumission ; des traces existantes peuvent être utilisées brièvement si disponibles. Le protocole chiffré de la petite campagne ISRU sera fourni avant les runs, avec la configuration de référence, les équations, hypothèses, paramètres et sorties attendues.

## Priorité de relecture après la critique de la V2

La V3 repart de la V1 annotée, et non des transformations de la V2. Arthur précise que ses notes sont un brouillon de raisonnement à interpréter globalement et chronologiquement, pas des consignes indépendantes. L’assistant doit exercer un jugement critique et expliquer les arbitrages plutôt qu’accepter automatiquement chaque suggestion.

N10 réinterprète N09 : l’objection de N09 venait d’une lecture des blocs comme des écrans. Le bloc fonctionnel Module Selection and Scenario Configuration peut définir sélection, multiplicités et instances logiques ; sa réalisation peut être répartie entre Step 2 et Step 4.2. La V3 conserve cette responsabilité logique et réserve le mapping UI à Implementation. Il ne fallait pas renommer/réduire le bloc sur la seule base de N09.

La V3 retient quatre axes de contribution et explicite les apports DES/CAD comme mécanismes techniques, sans ajouter mécaniquement deux axes qui se recouvrent. Elle conserve le budget convenu de 22 à 24 pages et le contexte LUNAverse. Les vingt notes rouges originales sont conservées avec des analyses regroupées et des décisions justifiées. La portée non validée d’un mécanisme ne doit être confondue ni avec son absence, ni avec une généralisation universelle démontrée.

## Historique V2 après relecture annotée

Cette mise à jour historique est à lire sous réserve des arbitrages V3 ci-dessus. Le 18 novembre, Arthur précise que les essais cargo relay, ice processing et water transfer étaient simples et n’avaient pas été validés de bout en bout jusqu’à Omniverse. Ils sont retirés des démonstrations de résultats ; la généralisation reste décrite comme mécanisme implémenté avec un périmètre à évaluer. La sous-partie de résultats sur la vérification intégrée d’exigences est également retirée, car ce développement n’avait pas été suffisamment testé.

La V2 rétablit les six thèmes d’exigences : interoperability, scalability, traceability, multi-user support, versioning et modularity. Les contributions centrales pipeline intégré, modularité, collaboration et visualisation restent explicites ; les apports DES et CAD s’y ajoutent. Step 2 active les types et permet de revoir les classes ; les instances fixes sont créées et placées en Step 4.2 Phase 1, les flottes/routes en Phase 2. Les blocs logiques ne correspondent pas nécessairement aux écrans.

Cible éditoriale convenue : 22 à 24 pages tout compris, avec un budget de travail de 24 pages. Répartition : titre/abstract 1 ; introduction 1 ; problem formulation et littérature 3 ; architecture 4 ; implementation 6 ; résultats 4 ; discussion 1,5 ; conclusion 0,5 ; remerciements/références 3. La FAQ générale SciTech consultée le 18 novembre indique une longueur courante de 12 à 24 pages et pas de limite générale ; des consignes de session peuvent différer. Le document de travail annoté n’est pas soumis à ce budget de manuscrit.

Le préprint fourni The Case for the LUNAverse sert au contexte, à la motivation et à l’orientation de la revue de littérature : coordination des systèmes indépendants, données spatiales partagées, modèle/évidence/décision et intégration des outils. Ses ambitions globales ne sont pas des résultats d’ECLIPSE. Le périmètre de la nouvelle équipe sera précisé après lecture de son PPT ; la continuation doctorale peut être évoquée comme travail prévu.

Les 20 annotations originales sont conservées en rouge dans SCITECH_Outline_v2.docx avec une réponse locale. Les questions complémentaires et le budget sont aussi tracés. La V1 annotée est conservée inchangée.

## Document de travail

L'outline courant est dans `SCITECH_Outline_v4.docx`, avec une version Markdown correspondante. Il conserve la V3 annotée et n’en modifie que les points ciblés dans les nouvelles notes et le message associé. Les protocoles d'évaluation proposés dans cet outline ne sont pas des expériences déjà exécutées.

## Sources et priorité

- Paper SciTech envoyé : `/Users/arthur/Desktop/SCITECH/ECLIPSE_PAPER.pdf`.
- Paper 8900 final envoyé : `/Users/arthur/Desktop/Cours/2025-2026/SUMMER 2026/AE8900/Deliverables/Final-Paper_Brunier_Arthur.pdf`.
- Outline historique : `/Users/arthur/Desktop/Cours/2025-2026/SUMMER 2026/AE8900/paper scitech/outline/Detailed Outline2.docx`.
- Trois photos annotées : `/private/tmp/IMG_8577.HEIC`, `/private/tmp/IMG_8578.HEIC`, `/private/tmp/IMG_8579.HEIC`.
- Instructions actuelles : fusionner les travaux dans le paper SciTech, commencer par l'outline, puis approfondir introduction, motivation et revue de littérature avant de remplir le reste.

Le paper prévaut sur l'ancien outline. Pour décrire l'état technique final, le paper 8900, les décisions ultérieures et le code actuel complètent le paper initial. Une proposition ancienne ou un message intermédiaire de diagnostic ne constitue pas une fonctionnalité finale.

## Discussions retrouvées

La conversation « Étudier intégration Omniverse » a été récupérée jusqu'à son début, sur 36 pages de lecture et 359 tours. Elle couvre le diagnostic initial, le manifest, le terrain, les modèles CAD, l'extension, la transformation ISRU, les scénarios génériques et la rédaction du rapport 8900.

La conversation « Expliquer la généralisation DES » a aussi été récupérée jusqu'à son début, sur 12 pages et 111 tours. Elle apporte des décisions complémentaires : classification par interfaces et flux, corrections des équations détaillées et coefficients SysML, mode sans contrainte d'énergie, utilisation des assets du scénario courant, suppression du chargeur actif, sauvegarde, comparaison avec baseline, courbes superposées, CAD par scénario, commandes de lecture et corrections d'orientation. Les plaques de fondation sous les modules ont été retirées à la demande d'Arthur.

La conversation « Rédiger l’abstract du projet » contient une décision éditoriale essentielle d'octobre : présenter directement l'outil final, sans raconter « avant puis mes améliorations ». Le message central est un environnement collaboratif de création, simulation et visualisation de mission, organisé en étapes où chaque spécialiste contribue à son domaine. Les standards et outils expliquent ensuite comment les contributions restent connectées.

La discussion TRC concerne l'intégration des améliorations de l'été demandée par Olivia Fischer et la préparation de la soumission SciTech. Aucun message externe n'a été envoyé dans ce travail.

## Travail technique à préserver

### Simulation et description de mission

- Deux modes explicites : contrôleurs ISRU configurables et compilation générique de la description du scénario.
- Scénario ISRU transparent : instances, connexions, routes, affectations, équations et paramètres visibles ; valeurs de référence SysML et surcharges de configuration identifiables.
- Chaîne détaillée de production et d'énergie exposée, variables intermédiaires comprises. Les coefficients technologiques auparavant anonymes sont nommés dans le SysML ; ils ne doivent pas être confondus avec des constantes physiques ou des mécanismes internes du simulateur.
- Multiples rovers et usines, stocks d'entrée par usine, logique de dispatch, aller et retour, distances et métriques de route.
- Puissance et batteries configurables, intégration des consommations de procédé et de stockage dans le bilan, modèles de demande moyenne/profil/équation, et mode explicite sans contrainte énergétique.
- Rôles génériques Source, Processor, Storage, Consumer, Transporter et PowerGenerator ; classification Passive lorsque pertinente ; correction manuelle des ambiguïtés.
- Équations analysées avec une grammaire restreinte et raccordées à des effets exécutables. Une équation arbitraire ou un nouveau phénomène physique ne sont pas automatiquement pris en charge.
- Exemples cargo relay, ice processing et water transfer : essais exploratoires simples au-delà de LOX/régolithe, sans contrôle complet jusqu’à Omniverse. Ils ne sont pas retenus comme résultats validés ni comme campagne à reproduire pour cette soumission ; la diversité des scénarios reste une évaluation future.

### CAD et données d'ingénierie

- STEP/STP, STL, OBJ et famille USD ; standardisation USD et aperçu navigateur.
- Métadonnées source séparées des métadonnées de visualisation ; provenance, unités, orientation et fiabilité des propriétés dérivées.
- Dimensions SysML conservées comme autorité ; adaptation géométrique et des propriétés dépendant de l'échelle ; écriture des métadonnées dans le SysML et les assets.
- Distinction up axis et front axis, orientation des modules statiques et mobiles, modèles CAD et choix sauvegardés par scénario, bibliothèque de modèles réutilisables.

### Scénarios et Omniverse

- Scénarios nommés, configuration et sorties conservées, rechargement et comparaison de scénarios terminés avec choix de baseline, différences relatives et historiques superposés.
- Manifest liant scène, waypoints, terrain, acteurs, résultats et log d'un scénario donné ; sélection du package dans l'extension.
- Repère métrique commun, terrain sampler, interpolation sur triangles, empreinte réelle des modules, plan de pose local, corrections verticales, projection et diagnostic des routes.
- Lecture synchronisée d'un log terminé, choix du temps et de la vitesse, caméras et télémétrie. Le moteur DES ne tourne pas nécessairement pendant cette lecture.

## Limites importantes à conserver

- Le simulateur générique reste limité par ses rôles, ses contrats d'équations et les comportements implémentés.
- Le DES utilise des métriques de route et des lois simplifiées, pas une dynamique complète du véhicule à chaque waypoint.
- Un terrain préparé peut être aligné et échantillonné ; cela n'établit pas automatiquement qu'il correspond exactement à la zone géographique sélectionnée. L'extraction automatique des patches reste à développer.
- La télémétrie Omniverse est synchronisée au playback enregistré ; son schéma et une partie de la logique restent plus complets pour ISRU.
- La collaboration est fondée sur les contributions aux étapes et les artefacts versionnés ; elle ne constitue pas une application d'édition simultanée avec garanties d'autorisation et de résolution de conflits.
- Le bilan de puissance est simplifié ; le chargeur rover a été retiré du moteur actif. Un mode sans contrainte énergétique ne démontre aucune faisabilité électrique.
- Une propriété extraite d'un CAD n'est pas automatiquement une propriété physique certifiée. Le centre géométrique calculé n'établit pas un centre de masse réel sans hypothèses de densité.

## Écarts repérés dans l'ancien outline

- La sauvegarde, la comparaison, le dashboard et les formats CAD supplémentaires ne sont plus seulement des pistes futures.
- La simulation n'est plus exclusivement limitée au cas ISRU initial, mais sa généralisation n'est pas universelle.
- Le paper SciTech contient un MCDM Omniverse à 4,55 comparé à Siemens NX, 3DEXPERIENCE et ANSYS Minerva. L'outline cite un autre ensemble de concurrents et 4,8 : reprendre les tableaux du paper si on les conserve. Le score OpenUSD du paper est 4,80.
- L'outline déplace trop de détails techniques vers Architecture. La nouvelle version réserve cette partie aux fonctions, interfaces logiques et règles d'autorité ; les outils, algorithmes et équations vont dans Implementation.
- Les affirmations « n'importe quelle mission », « optimisation généralisée », « aucune perte de métadonnées », « garantie de non-interférence », « protection de la propriété intellectuelle » et « des mois réduits à une session » nécessitent des preuves qui ne découlent pas simplement des standards ou de GitHub.

## Résultats à refaire

Le chiffre historique de 111,23 kg de LOX et l'interprétation « batterie toujours pleine, donc puissance suffisante » appartiennent à l'ancien cas. Le bilan énergétique a été modifié pour inclure des demandes auparavant mal raccordées. Les conclusions ne peuvent pas être reportées sans réexécution documentée.

Il faudra distinguer durée totale de simulation, durée d'activité de chaque usine, production, livraison et stocks finaux. Les 91 % cités dans l'ancien texte sont une fraction livrée sur la fenêtre simulée, pas une efficacité physique. Les valeurs par défaut ne constituent pas une justification des coefficients : provenance, unités et hypothèses doivent accompagner les nouvelles données.

La boucle de vérification d'exigences reste une contribution du paper initial à conserver. Pour décrire son automatisation exacte et illustrer les résultats, récupérer un exemple actuel avec expression, attribut, instants vérifiés, rapport et éventuelle correction. Une relation satisfy ne prouve pas à elle seule l'exécution d'un test.

## État du dépôt inspecté

Le dossier ouvert est sur `cleanup-branch`, au commit local `54beb25` du 20 octobre 2026 lors de la lecture. Le dossier `ECLIPSE_2.0`, créé ensuite pour transmettre une copie, existe aussi. Les fichiers du moteur générique, du contrôleur ISRU actif et du manifest builder comparés sont identiques entre les deux copies ; le HTML diffère notamment par des changements de configuration du dépôt. Aucun fetch, changement de branche, commit ou push n'a été exécuté pendant cette préparation.

Le document `docs/DES_DIAGNOSIS_REPORT.md` décrit des limitations historiques, comme le stock régolithe commun et des demandes énergétiques non raccordées. Il sert à comprendre l'évolution, pas à décrire automatiquement le code actuel. De même, certaines formulations de `docs/GENERIC_DES_ENGINE.md` divergent des défauts actuels de classification : décrire le chemin UI avec classes explicites, puis préciser les fallbacks du backend si nécessaire.

## Prochaine séquence de travail

1. Discuter et stabiliser l'outline intégré.
2. Construire une revue de littérature comparative par familles de méthodes, lire les sources primaires et préciser le gap.
3. Rédiger introduction et motivation, en justifiant d'abord le besoin de contributions de plusieurs spécialités et en explicitant la visualisation de la mission.
4. Réutiliser et harmoniser les contenus techniques des deux papers dans Architecture et Implementation.
5. Déclarer les cas et hypothèses, relancer la campagne, vérifier les résultats et collecter les preuves graphiques.
6. Finaliser Discussion, Conclusion et Abstract à partir des résultats obtenus.
