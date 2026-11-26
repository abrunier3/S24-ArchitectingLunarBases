# ECLIPSE SciTech paper outline V2

Integrated scenario definition simulation and visualization

Version 2 | 18 November 2026

The paper presents the complete ECLIPSE environment for collaborative lunar base architecting within the broader LUNAverse initiative. Its central contributions connect an end-to-end pipeline, modularity and scalability, collaboration, and spatial and temporal mission evaluation. The AE 8900 work strengthens those contributions through transparent simulation, reusable scenario descriptions, CAD interoperability, and synchronized visualization.

Retain the seven main sections of the ECLIPSE paper. Preserve its central vocabulary: interoperability, scalability, traceability, multi-user support, versioning, and modularity. Explain the delivered mechanisms and their evidence separately from the wider objectives. The paper presents the integrated tool; the technical account can briefly explain why a mechanism was generalized from the ISRU starting point.

Note Arthur N23  Il y a aussi un point a prendre en compte, c’est la longueur du paper. Celui-ci ne peut pas être infini ; un conference paper fait généralement 15-20 pages ?

Réponse V2 N23  Traité. La FAQ générale SciTech indique l’absence de plafond général et une longueur courante de 12 à 24 pages, références comprises ; des règles spécifiques peuvent dépendre de la session. Pour ce paper, la V2 retient une cible éditoriale de 22 à 24 pages et un budget de travail de 24 pages, figures, tableaux et références inclus. La longueur du présent outline annoté n’est pas celle du manuscrit final.

## Paper length and editorial priorities

Target 22 to 24 pages, using a 24-page working budget including title, abstract, figures, tables, acknowledgments, and references. This is an editorial target, not a verified track-specific rule. AIAA’s general SciTech FAQ reports no overall manuscript limit and a typical range of 12 to 24 pages including citations. Technical Presenter Resources, checked 18 November 2026: https://scitech.aiaa.org/call-for-content/technical-presenter-resources/

Page allocation totaling 24 pages. Title and abstract 1; Introduction 1; Problem formulation and literature review 3; Architecture 4; Implementation 6; Results 4; Discussion 1.5; Conclusions 0.5; acknowledgments and references 3. Figure and table space is already included. Aim for a complete manuscript within 22 to 24 pages; the allocation gives room to explain the architecture and technical mechanisms without requiring every section to fill its budget.

Content hierarchy. Explain each mechanism once. Give most technical space to scenario definition/DES, CAD authority, and the manifest/terrain link. Keep established SysML, GIS and workflow descriptions concise. Remove the generic-case result section and the untested integrated-verification result section. Describe the latter’s development briefly in the method and its maturity in Discussion.

Visual budget. Aim for 6 to 8 figures and 3 to 4 tables: an integrated architecture; an ISRU layout; a role/equation mechanism; a CAD metadata workflow; quantitative comparison plots; and Omniverse playback. Add a separate manifest or orientation view only if it earns its space. Prefer a compact rationale in the text to two full MCDM tables; retain the detailed scoring in working material for traceability.

Reading this V2. The outline remains in English. Arthur’s original notes are retained in red and labeled N01 to N20; each has a local French response and status. N21 to N23 record the additional questions about generic demonstrations, terminology, and length. Black text is the revised outline or a labeled response. The new team’s detailed scope remains to be completed when its presentation is available.

## Abstract

- Establish the engineering problem: interdependent lunar infrastructure must be designed by specialists using heterogeneous models and tools.

- Introduce ECLIPSE as a contribution to the LUNAverse vision of coordinated lunar and cislunar systems. Connect system definition, requirements, site planning, operational simulation, CAD integration, and visualization; describe the verification loop according to its current validation status.

- Explain modular architecture and scenario definition, the configurable ISRU behavior engine, the implemented role-based generalization mechanism, CAD metadata propagation, saved-scenario collaboration, comparison, and scenario-specific Omniverse playback.

- Summarize the demonstrations and include numerical findings only after the current simulation campaign has been completed and checked.

- End with the demonstrated ISRU-centered scope. Present generic behavior as an implemented approach whose broader end-to-end applicability remains to be evaluated; omit the small experimental examples from the abstract.

## I Introduction

### A Background

- Introduce sustained lunar infrastructure as a system of interdependent habitats, power, communications, processing facilities, storage, and transport assets.

- Explain why independently developed and managed systems must coordinate interfaces, service availability, operating assumptions, and timing. Use the LUNAverse position paper, especially Sections 2 and 5, to frame the systems-of-systems coordination problem; support detailed technical claims with the underlying primary studies.

- Use the lunar spaceport as the concrete design problem. Establish the coupled effects of placement, terrain, resource access, logistics, and power.

- Position within LUNAverse. Introduce LUNAverse as the wider initiative seeking coordination among independently managed lunar and cislunar systems. Position ECLIPSE as a lunar infrastructure design, simulation, and visualization contribution within that effort. Use The Case for the LUNAverse, Sections 1, 2 and 5, for the motivation; avoid implying that the preprint documents a measured deployment or validates every capability of ECLIPSE.

- Keep lunar program context brief and supported by current primary sources. Replace broad judgments about Apollo-era engineering with a precise description of the present integration problem.

### B Motivation

- Paragraph 1: carry forward the collaboration need from Background. Independent power, transport, processing, communications, and infrastructure contributions must operate together. Explain heterogeneous tools, data meanings, model versions, and coordination of assumptions; motivate controlled sharing without implying that all governance mechanisms are implemented.

- Paragraph 2: establish variation in mission objectives, active systems, instance counts, interfaces, routes, equations, and power assumptions. Derive modularity and scalability needs. Explain configurability as one means of achieving modularity, and extensibility as a separate ability to add supported behaviors.

- Paragraph 3: motivate explicit visualization of the simulated mission through time. Explain what spatial placement, rover movement, resource histories, and synchronized telemetry help stakeholders inspect alongside numerical measures of effectiveness.

- Paragraph 4: introduce digital engineering and situate ECLIPSE within LUNAverse. Use the preprint to motivate shared design-time coordination and iterative links between data, models, simulation, evidence, and decisions. Its economy-wide, governance, AI, and operational-twin ambitions are context, not ECLIPSE results.

## II Problem formulation

### A Literature review

Organize the review by engineering approach. Within each group, compare the problem addressed, representation used, demonstrated strengths, integration boundary, and implications for the present work. Synthesize relationships between studies rather than allocating one descriptive paragraph to each reference.

Group 1 Lunar system architecture and multidisciplinary trade studies. Review system-of-systems studies and parametric or MBSE-linked sizing methods. Candidate starting points in the supplied bibliography include the Cislunar Architecture Study and the ISRU and power-system studies by Boyer, Ramkumar, and Mehta. Assess how they connect architectural decisions to performance, what they demonstrate about trade exploration, and which operational or integration questions remain outside their reported scope.

Group 2 Operational modeling and scenario construction. Review lunar logistics and surface-operations environments, followed by configurable or composable simulation approaches. The tabletop study and MORPH, DELOS, and PIONEER are starting points whose actual reports must be inspected. Compare event logic, resource contention, scenario input languages, user responsibility, and the effort required to express a different resource chain. SimPy documentation explains the implementation framework; it cannot establish novelty relative to other simulation environments.

Group 3 Digital engineering integration and collaboration. Review authoritative models, digital threads, semantic and tool interoperability, versioning, and support for multiple contributors. Position The Case for the LUNAverse as a contextual preprint, not an independent validation of ECLIPSE. Its Sections 8 and 10 support discussion of iterative model/evidence links and integration of specialist tools; follow its references to the actual studies being compared.

Group 4 Spatial planning and simulation visualization. Review GIS-informed planning, simulation-linked 3D environments, shared frames, terrain provenance, scene interoperability, and recorded-time synchronization. LUNAverse Section 6 motivates a common environmental reference; the paper must distinguish that objective from the prepared terrain asset actually used in ECLIPSE. Review application evidence for claimed engineering benefits.

Cross-cutting comparison criteria. Compare modularity, scalability, interoperability across tools and data meanings, traceability, versioning, multi-user support, scenario preservation, and visual evaluation. Identify the kind of multi-user support described by each source. Distinguish a capability demonstrated in an inspected study from one simply not discussed there.

Review output. Build a compact comparison matrix and a synthesis paragraph explaining how the approaches complement one another. Use that synthesis to derive the specific integration problem addressed by ECLIPSE. Audit the supplied references for accurate titles, identifiers, dates, and relevance; expand the review beyond the existing Georgia Tech examples where the evidence warrants it.

LUNAverse source use. Draw on Sections 2 and 5 for the coordination problem, Section 6 for shared spatial assumptions, Sections 7 and 8 for model-based integration and the iterative digital thread, and Section 10 for specialist-tool integration. Read and verify the underlying references before using them as state-of-the-art evidence. The source is explicitly a preprint; do not import its AI, cybersecurity, market, training, or real-time operations objectives as implemented ECLIPSE capabilities.

### B Research gap

- Formulate a bounded integration gap: preserving a consistent, inspectable scenario definition across architecture, spatial planning, configurable operations, heterogeneous geometry, and quantitative and visual assessment.

- Separate limitations documented in prior publications from limitations observed in the original ECLIPSE prototype. A prototype limitation alone does not establish a field-wide research gap.

- Scope the novelty claim to the combination and implementation demonstrated in this paper. Finalize its wording after the comparative literature assessment.

### C Objectives and research questions

Objective. Develop ECLIPSE as a collaborative platform for lunar mission generation, simulation, and evaluation, guided by mission requirements and organized as a modular, scalable digital engineering workflow. Explain how its shared models and scenarios support contributions from different specialties, operational configuration, and quantitative and visual assessment.

RQ1 Modularity and scalability. How can a requirements-driven lunar scenario generation pipeline be designed to be modular and scalable, so that system configurations can be assembled, simulated, and evaluated through a common workflow without rebuilding the process for each scenario?

Note Arthur N01  Là je crois que je preferais l’ancienne formulation, qu’en penses tu?

Réponse V2 N01  Traité. Oui, l’ancienne formulation portait mieux l’ambition de modularité. RQ1 est rétablie autour d’un processus guidé par les exigences, modulaire et scalable. J’enlève seulement la promesse d’une optimisation universelle automatique : elle ne correspond pas à une capacité démontrée.

RQ2 Collaboration and interoperability. How can independent stakeholders contribute systems, models, geometry, and scenario data within a shared workflow while maintaining interoperability, traceability, and versioning across contributions?

RQ3 Visualization-based mission evaluation. How can quantitative measures of effectiveness be complemented by a coherent spatial and temporal representation of mission behavior that supports shared inspection and comparison of lunar architectures?

### D Contributions and evaluation strategy

- C1 End-to-end pipeline: connect requirements and system definition, selection, GIS planning, simulation, CAD, and visualization in a common digital thread; describe the requirements-verification branch according to its tested maturity.

- C2 Modularity and scalability: preserve a configurable set of system types, activation choices, module instances, interfaces, and scenario assumptions; separate reusable pipeline responsibilities from mission-specific content. Distinguish scalable composition from measured computational scaling.

- C3 Collaboration and multi-user support: organize specialist contributions around shared standards, versioned models and CAD, saved scenarios that can be loaded and discussed, and comparison against a selected baseline. State the current asynchronous mode and the limits on simultaneous editing.

- C4 Visualization-based mission evaluation: connect terrain-aware placement and routes to recorded-time mission playback and telemetry. Associate the selected visual scene with the same scenario definition and results used for quantitative assessment.

- C5 Transparent and generalized operational modeling: expose the ISRU scenario equations, numerical assumptions, module multiplicities, routing and power settings, and describe the implemented role-based compiler as a route to broader scenario construction whose end-to-end evaluation remains open.

- C6 CAD interoperability and authoritative metadata: accept supported engineering formats, preserve source and visualization metadata, align geometry with modeled dimensions, and write controlled engineering metadata back into the SysML model.

Link RQ1 to the architecture, scenario definition, and behavior engine; RQ2 to Collaboration, authoritative data, scenario versioning, and CAD integration; and RQ3 to GIS, quantitative comparisons, and Omniverse playback. Use the current ISRU case for demonstrated outcomes. The generic engine is an implemented generalization mechanism whose application to substantially different scenarios still requires integrated evaluation.

Note Arthur N02  Là j’ai l’impression que tu as pas mal change les axes de contributioons proposes non. Avant c’était end to end pipline (donc ok pour integrated ecosysteme), modularity, collaboration, visualization. Là tu skip c’est 3 derniers alors qu’ils sont centraux pour le projet (fin surotut les deux derniers car je opense que configurable behavior modeling est inclus dans modularity mais modularity incluait d’autres choses). Pourquoi ne pas juste ajouter des axes de contributions comme ca on prend tout en compte?

Réponse V2 N02  Traité. Tu as raison : la V1 réduisait les axes du projet. La V2 rétablit les quatre contributions centrales — pipeline intégré, modularité/scalability, collaboration, visualisation — et ajoute deux axes techniques explicites pour la simulation configurable et le CAD. La sauvegarde et la comparaison renforcent ces axes au lieu de les remplacer.

### Editorial rules for the merged paper

- Present the final tool directly. Retain a short historical comparison only when it clarifies a measured capability or a design rationale.

- Describe requirements as guiding architecture and evaluation. Do not imply automatic synthesis of arbitrary mission architectures or a global optimization process unless such a process is demonstrated.

- Use collaboration to describe connected specialist contributions and the implemented versioned workflow. Claims about access control, intellectual-property protection, conflict prevention, and simultaneous editing require separate evidence.

- Describe visualization as complementary to quantitative analysis. Do not claim universal stakeholder comprehension or improved decision quality without an evaluation of those outcomes.

## III Architecture

The original six requirement themes drive the architecture. Derive the functional blocks from these needs, then use the implementation and selected results to establish what is realized. This follows the original paper’s requirements-to-blocks logic without adding a separate requirements subsection.

- Introduce the six requirement themes retained from the original paper: interoperability, scalability, traceability, multi-user support, versioning, and modularity. Interoperability spans tools, model meaning, units, coordinate frames, geometry, and process handoffs. Configurability, extensibility, and spatial/temporal consistency refine these themes; they do not replace them.

Note Arthur N22  j’ai l’impression que tu as remplacé certains mots clés: modularity par configurability, scalability par extensibilité, multi-user support par contribution from different specialties. Peux tu m’expliquer ce choix?

Réponse V2 N22  Traité. J’avais choisi des termes décrivant plus directement les mécanismes observables, mais cela réduisait les exigences au lieu de les préciser. Modularity concerne la composition et le remplacement de modules ; configurability concerne leurs réglages. Scalability concerne l’augmentation de systèmes, scénarios, données ou utilisateurs ; extensibility concerne l’ajout de fonctions. Multi-user support concerne l’usage par plusieurs personnes ; les contributions par spécialité en décrivent un mode, sans couvrir tout le besoin. Les mots-clés originaux sont rétablis, avec leur niveau de preuve.

Note Arthur N03  l’interoperability ne concerne que le data exchange?

Réponse V2 N03  Traité. Non. L’interopérabilité concerne les outils, les modèles et leurs significations, les unités, les repères spatiaux, la géométrie et les échanges entre étapes. Un JSON lisible par deux outils ne suffit pas si ces outils interprètent différemment une grandeur, un identifiant ou un repère.

Note Arthur N04  Tu as enlevé versioning: en, soi on a toiujours un versioning au niveau des scenarios et meme des cad ajoutés etc donc je pense qu’on peut le garde ren tant que req.

Réponse V2 N04  Traité. Versioning est rétabli comme thème d’exigences : modèles, code, assets CAD et configurations suivis dans le dépôt, ainsi que conservation des scénarios nommés. Je distingue le nom d’un scénario d’une révision : un scénario peut évoluer, tandis que l’historique Git permet de retrouver des versions lorsque les artefacts concernés y sont suivis.

- Derive the blocks from these themes. For each block, explain which needs motivate it, its purpose, inputs and outputs, and an observable success criterion. Define the criterion here, describe its implementation in IV, and assess it only against evidence available in V and VI.

Note Arthur N05  En vrai j’aimais bien la facon de rédiger les requirements de l’ancien paper. On dit ok on a ces grands themes de reqiuirements qui ont engendré la creation de l’arhitecture. Apres pour chaque bloc on dit explicitement quelles sont les req et puis les criteres de résuiites comme tu dis, opn dit ce qu’est le bloc et on vérifie que ca valide le critere, ou bien ca ca vient apres?

Réponse V2 N05  Traité. Je reprends la logique de l’ancien paper : les grands thèmes d’exigences introduisent Architecture, puis chaque bloc est dérivé des besoins auxquels il répond. Le critère de réussite est défini à cet endroit ; le mécanisme concret est décrit dans Implementation ; la satisfaction effectivement observée est discutée avec les résultats disponibles, sans annoncer d’emblée que tout est vérifié.

Note Arthur N06  Je ne pense ^pas qu’il y ait besoin de faire une soys partie pour ca, je pense que je preferais comme avant.

Réponse V2 N06  Traité. La sous-partie autonome sur les exigences est supprimée. Les six thèmes historiques ouvrent directement la section III, avant le schéma global et la dérivation des blocs.

- Multi-user support includes contributions at specialist steps, shared repository artifacts, and loading or revisiting saved scenarios. Concurrent editing, application-level authorization, and conflict resolution remain separate implementation objectives.

Note Arthur N07  Est ce que tu penses que je dois mettre ici le schema global de l’architectire (donc juste avant qu’on explique la decomposition des blocs) ou bien apres (comme ce que j’avais fait avant)? Je me demande si c’est pas mieux avant.

Réponse V2 N07  Traité. Je retiens le schéma avant la décomposition détaillée. Après le paragraphe sur les exigences, deux phrases présentent la vue d’ensemble et la figure donne au lecteur une carte des blocs. La suite justifie chaque bloc ; le dernier paragraphe fait la synthèse sans répéter la figure.

Overview figure placement. Introduce the eight-block ecosystem after the requirement themes, then place the updated global architecture figure here, before the detailed block derivation. Use it as a map while explaining the blocks and conclude the section with one short synthesis paragraph.

### A Derivation of the main building blocks

For each block, follow the same short chain: motivating requirements, functional purpose, inputs and outputs, then intended success criterion. The diagram above is a reading guide, not evidence that every requirement has already been verified. Logical blocks need not correspond one-to-one with user-interface steps.

- Authoritative Source of Truth: responds to traceability, versioning, and interoperability needs by defining systems, reference properties, requirements, typed interfaces, and common system/instance identifiers across exported artifacts. The success criterion is an identifiable link from a downstream item to the corresponding modeled element.

Note Arthur N08  (que veut dire stabe identifiers?)

Réponse V2 N08  Traité. Je voulais dire les identifiants communs permettant de reconnaître un même système dans le SysML, ses exports, les routes, les résultats et la scène. Par exemple, un identifiant d’instance tel que ISRUPlant_1 permet de rattacher une production à la bonne usine. Je remplace « stable identifiers » par une formulation explicite ; cela ne suppose pas un identifiant universel qui résisterait automatiquement à tout renommage.

- Module Selection: responds to modularity and scalability needs by activating available system types and preserving their relevant interfaces. Operational classes can be reviewed in the interface. Instance creation and placement are separate responsibilities realized later in the mission builder.

Note Arthur N09  c’est pas la qu’on choisit les instances des modules mais dans la step4.2 phase 1 qui s’appelle d’ailleurs asset instancing et placement) ici on choisit juste leur type (leur classe) et si on veut les active ou non

Réponse V2 N09  Traité. Correction faite : Step 2 active les systèmes et permet de revoir leur classe opérationnelle. Le nombre d’instances fixes et leur placement sont définis en Step 4.2 Phase 1, Asset Instancing and Placement ; les flottes et affectations de rovers relèvent de la Phase 2. Le bloc logique est renommé Module Selection et le mapping est précisé dans Implementation.

Note Arthur N10  Ah mais je viens de comprendre. En fait ces blocs logiques ne correspondent pas necessaire aux steps de l’interface c’est ca? en gros c’est juste l’architectire logique et dans implementation on va voir concretement comment ca a été implémenté donc on aure peut etre des blocs mélangés ou séparés en deux?

Réponse V2 N10  Traité. Exactement. Les blocs décrivent des responsabilités fonctionnelles, pas nécessairement des écrans. Une étape de l’interface peut réunir plusieurs responsabilités, et un bloc peut être réalisé à plusieurs étapes. La V2 ajoute le mapping explicite vers Step 2 et les phases de Step 4.2.

- Urban Planning: responds to spatial interoperability and scalable scenario composition needs through site assessment, instance creation and placement, orientations, and operational routes. The intended criterion is consistent spatial information that the behavior and visualization blocks can consume for the chosen scenario.

- Behavior Engine: responds to operational evaluation and modularity needs by simulating who supplies or receives each resource, along which assigned route, under the selected quantity, timing, and energy equations. Check scenario consistency before execution, then generate time histories and final metrics. Post-simulation mission-requirement verification is a separate block.

Note Arthur N11  je ne comprends pas bien ce que tu veux dire avec cette phrase)(quelle est la diff entre resource relashionship et equations?)Ne parle t-on pas de scenario validation aussi ou ca ca viendra dans implementation?

Réponse V2 N11  Traité. La description opérationnelle précise quels systèmes participent, qui échange quelle ressource, sur quelle route, avec quelles lois et quels réglages. Une relation de ressource indique « qui fournit quoi à qui » ; une équation indique « combien, en combien de temps et avec quelle énergie ». La validation du scénario est mentionnée ici comme fonction ; ses contrôles sont détaillés en IV.D. Elle est distincte de la vérification des exigences après simulation.

- Requirements Verification Loop: links simulated attributes to modeled requirement constraints and is intended to return verification evidence to the architecture workflow. Retain this developed branch in the architecture, but do not claim integrated verification results or a fully tested automatic loop in this submission.

- CAD Submission: responds to geometry and tool interoperability needs by associating stakeholder models with selected systems, converting supported formats, and preserving provenance and controlled metadata write-back. The intended criterion is the correct resolved geometry and metadata association for each scenario asset.

- Visualization: responds to mission interpretation and spatial/temporal coherence needs by combining the selected scenario geometry, prepared terrain, routes, and recorded behavior. The intended criterion is correspondence between the selected engineering scenario and the rendered scene and telemetry.

- Collaboration: responds to multi-user support, interoperability, traceability, and versioning needs through specialist contributions, shared repository models and CAD, named scenario saving/loading, and result comparison. State which artifacts and revisions can be shared, without equating this workflow with simultaneous editing.

Note Arthur N12  On a aussi mtn la possibiité de chatgé des scenarios etc de faire du versioning de scenario entre les users etc, ce qui ajoute a la collaboration.

Réponse V2 N12  Traité. Oui : les scénarios sauvegardés, leur chargement par les contributeurs ayant accès au dépôt, la comparaison et le versioning font partie du support à la collaboration. Le bloc et IV.H le disent maintenant explicitement. Cela reste distinct d’une édition simultanée du même scénario par plusieurs utilisateurs.

### B Scenario lifecycle and data authority

- Describe the lifecycle from reference model to selected instances, spatial layout, operational configuration, execution, saved outputs, comparison, and playback.

- Explain authority with concrete examples: SysML defines reference dimensions and technical properties; the saved scenario records local overrides, routes, and equations for the run; submitted CAD carries geometry and provenance; the DES outputs the resulting histories; the manifest identifies which artifacts are read together for playback.

Note Arthur N13   la je ne comprends pas bien, peux tu me donner plus de details?

Réponse V2 N13  Traité. Il s’agit de dire quelle donnée fait référence et qui a le droit de la remplacer dans le workflow. Les dimensions de conception proviennent du SysML ; une surcharge de scénario est une hypothèse locale à cet essai ; le CAD apporte une géométrie et une provenance ; le DES produit les résultats ; le manifest indique les fichiers à lire ensemble. Le CAD ne doit donc pas redéfinir silencieusement les dimensions SysML et un ancien résultat ne doit pas être associé à une nouvelle configuration.

- A scenario binds these artifacts together. Saving scenario A with identifiable inputs and outputs allows a contributor to return to A after running scenario B, instead of accidentally displaying B with A’s assumptions. Separate named-scenario output paths do not by themselves create an immutable archive of every revision or every run; record file and code revisions when exact historical reproduction is required.

Note Arthur N14  (j’aime beaucoup cette phrase, elle claque). je ne comprends pas cette deuxieme partie de phrase, a quoi fais tu références?

Réponse V2 N14  Traité. Je conserve l’idée « a scenario binds these artifacts together ». La suite est réécrite concrètement : les entrées et sorties de deux scénarios nommés restent identifiables séparément, ce qui permet de revenir au scénario A après avoir exécuté B. Cela ne promet pas des snapshots immuables pour chaque run d’un même scénario ; une reproduction historique exacte requiert aussi la révision des fichiers et dépendances.

- Separate logical resource interfaces from physical transport paths. A resource-flow arrow does not by itself define a terrain route or a separate transporter.

- Show the requirement-feedback path and the CAD-metadata enrichment path as distinct connections to the authoritative model.

Conclude with how the eight responsibilities connect in one scenario-centered workflow. Keep the distinction between the functional architecture and its interface realization explicit; no second copy of the global figure is needed.

Architecture figure brief. Keep the eight logical blocks and specialist entry points. Update Module Selection to distinguish type activation from later instancing; show instances, routes, equations, and configuration entering the operational scenario; show saved-scenario loading and comparison within the cross-cutting Collaboration layer; show the CAD-metadata feedback to SysML; and connect DES results and recorded logs with the scenario visualization package. Use a small scenario artifact connection rather than inventing a ninth functional block. Show current requirement-verification maturity in the caption or legend.

Note Arthur N15  Ah donc tu penses que la figure on la laisse a la fin, oui c’est peut etre mieux possiblement mais en meme temps ca facilite peut etre la lecture si c’est au debut. En fait je pense que pour la lecture c’est mieux au début, mais pour la continuité logique c’est mieux a la fin.


Réponse V2 N15  Traité. La décision est prise en faveur de la lecture : figure en début de III, après les thèmes d’exigences et une courte présentation. La continuité logique est conservée en justifiant ensuite les blocs dans l’ordre du flux, puis en terminant par un paragraphe de synthèse.

Note Arthur N16  Donc concretement pour update cette figure, tu penses a quoi? Qu’est ce qui doitetre ajouté a la figure actuelle?

Réponse V2 N16  Traité. Le brief de mise à jour est maintenant explicite : conserver les huit blocs ; montrer la définition de scénario avec instances, routes, équations et réglages ; ajouter sauvegarde/chargement/comparaison à la couche Collaboration ; représenter le retour des métadonnées CAD vers SysML ; et montrer le package de visualisation et la télémétrie enregistrée. Les rôles d’acteurs restent visibles. La figure principale reste fonctionnelle : les fichiers et les détails d’algorithmes vont dans le texte d’implémentation, sans multiplier les schémas.

## IV Implementation

### A Authoritative model and model exchange

- Describe SysML v2 modeling in MSOSA, system identifiers, typed resource and power ports, dimensions, and reference attributes.

- Explain the implemented export and parsing path into the JSON representations consumed by downstream tools. State which properties and relationships are preserved and checked.

- Explain the developed link between requirement expressions and simulated attributes. A satisfy relationship expresses a modeled allocation; it is not by itself evidence of an executed verification. Describe the current verification branch without presenting an integrated pass/fail demonstration in Results.

- Explain where scenario-specific values override model defaults and how their provenance is retained.

### B Scenario initialization and module selection

- Introduce the ISRU preset, saved scenario loading, and new generic scenario workflow. Explain what is prepopulated by the preset and what the user must define.

- Describe architecture parsing, the directed system graph, port and connection checks, activation of a subset, and preservation of instance identity.

- Distinguish system-type activation and class review in Step 2 from fixed-module instancing and placement in Step 4.2 Phase 1, rover fleets and route assignment in Phase 2, interfaces and equations in Phase 3, and scenario consistency validation in Phase 4. Give this mapping once in a compact paragraph.

- Keep detailed role inference and equation execution in Section IV.D. This subsection establishes the system graph they consume.

### C GIS planning and operational routes

- Retain the original regional site-assessment method and its criteria, normalization, weighting, data provenance, and planning resolution.

- Explain creation of fixed-module instances in Step 4.2 Phase 1 and their placement in the local map frame. Distinguish the graph’s active system types from their physical instances, regional suitability from local route feasibility, and operational role from system type.

- Describe the actual routing objective and constraints implemented in the chosen paper version. Use qualified language for route optimality.

- Explain instance-level route endpoints, waypoints, optional stops, transporter assignments, route lengths, and available slope metrics.

- State how those outputs feed the DES and visualization. Distinguish a route-level travel approximation from detailed vehicle dynamics over every waypoint.

Figures: a compact system-connectivity example; one site and local-layout figure if it adds information beyond the final architecture diagram. Move large interface walkthroughs to supplementary material when they compete with technical evidence.

Source integration: reuse the ECLIPSE material on SysML, activation, GIS, and placement, then update the scenario entry points, multiplicity, and operational-route contract from the 8900 work and later repository discussions.

### D Configurable and extensible behavior engine

Give this subsection substantial space. Its contribution has two separate levels: a transparent and configurable ISRU model, and a generic framework for scenarios expressible through the supported operational roles.

1 User-visible operational definition. Explain how selected instances, resource and power interfaces, transporter assignments, routes, equations, and numerical assumptions become the executable scenario. Expose the causal connection between a user decision and a simulated outcome.

2 Configurable ISRU implementation. Describe multiple regolith and LOX rovers, multiple plants, per-plant input inventories, dispatch logic, pickup thresholds, loading assumptions, and outbound and empty return travel. Identify which operations remain simplified. Make explicit that the detailed process and energy equations are inspectable and editable, reference coefficients come from the scenario's SysML/assets, and simulation settings or supported overrides are exposed through configuration.

3 Equation and parameter provenance. Explain the detailed production and energy chains, including intermediate quantities. Separate technological assumptions, physical constants, scenario overrides, and execution settings. Document the active precedence rules and fallback behavior. A default value in a configurable field is different from a hidden assumption that a user cannot change.

4 Generic role interpretation. Describe Source, Processor, Storage, Consumer, Transporter, and PowerGenerator. Treat Passive as a supported classification where relevant, rather than implying an additional independent physics model. Explain inference from directed resource and power interfaces and explicit route assignment, user overrides, and ambiguous topologies. Distinguish the normal UI classification path from backend compatibility fallbacks.

5 Behavior compilation. Show how role assignments, inventories, routes, equations, and power configuration become SimPy processes. Use a Processor example to explain input delivery, transformation, delay, and output availability. Describe this implemented mechanism without treating the small experimental non-ISRU scenarios as validated results.

6 Equation contracts and validation. Describe the restricted expression parser, intermediate variables, recognized variables, required outputs, and binding of outputs to resource, time, storage, or energy effects. Explain checks for missing equations, incompatible connections, absent transporters, invalid routes, and unknown variables. Validation checks executable consistency; it does not establish physical accuracy.

7 Power and travel models. Explain configured generation, stationary battery capacity and initial charge, demand modes, event energy, management interval, and inclusion of plant processing and storage demand in the system balance. Explain flat-terrain speed and the implemented route-slope adjustment. State the role of the explicit energy-unconstrained mode and distinguish it from power-feasible operation. Rover charging is not an implemented closed operational cycle.

Figures and table: one operational configuration figure; one role-to-SimPy behavior diagram; a compact role and equation-contract table. Include a numerical-settings capture only if readable and informative. Put actual case-study coefficient values and their sources in Section V.A.

### E Requirements verification

- Describe the developed link from logged simulation attributes to modeled constraints, including the expected matching keys, time sampling, and feedback path. State the level actually tested. Keep this subsection brief because a current integrated verification demonstration is not part of the selected Results.

- Explain the intended pass/fail semantics and reporting, distinguishing sampled checks from continuous guarantees. Identify the additional integration checks needed before presenting the loop as validated.

- Retain the team-developed requirement-verification work in the method, with its present maturity made explicit. Do not report a successful automatic feedback cycle or executed requirement result unless the corresponding evidence is later established.

### F CAD conversion and authoritative metadata

- Describe supported STEP/STP, STL, OBJ, and USD-family input paths; the OpenCascade/pythonOCC, trimesh, and USD readers; generated USD assets; and browser previews.

- Explain source-CAD metadata separately from generated visualization metadata. Record provenance, units, geometry bounds, materials where available, and reliability of derived properties.

- Explain up-axis handling and the user-selected front reference. For native USD, respect the stage's orientation metadata; for converted formats, describe the applicable user choices. Apply front direction consistently to static placement orientation and moving actors.

- Preserve SysML dimensions as authoritative. Describe the actual geometry fitting policy, resulting length scale, and consistent transformation of area, volume, and center information before metadata write-back.

- Describe scenario-specific CAD storage, selection from the repository library, and resolved geometry references. Explain how distinct model choices remain associated with distinct modules and scenarios.

- Qualify volume and center calculations by geometric closure and material/density assumptions. Derived geometric properties are not a certified mass model.

### G Scenario packages and Omniverse playback

- Describe generation of the scene, waypoint layer, results, recorded log, terrain reference, actor definitions, and scenario manifest.

- Explain how the Omniverse extension selects and reads the package. Describe recorded-time synchronization, seeking, rate control, reset, route visibility, and camera targeting.

- Explain the common metric frame, terrain triangle sampling, interpolation, footprint-based plane fitting, pitch/roll, and vertical clearance adjustment.

- Describe route densification and terrain projection, slope diagnostics, rover orientation, and distance-based interpolation. Grounding does not flatten the terrain or create foundations.

- State the distinction between alignment of a prepared mesh and automatic retrieval of the exact geographic terrain patch. Identify remaining ISRU-oriented playback and telemetry compatibility logic.

### H Collaboration scenario versioning and automation

Note Arthur N17   la tu as enlevé le mot collaboration d’ici alors que c’est un mot clé du projet.

Réponse V2 N17  Traité. Collaboration est rétabli dans le titre de IV.H et dans son contenu : contributions aux étapes, partage et chargement des scénarios, historique des modèles et CAD, comparaison et automatisation. Le multi-user support reste une exigence ; son niveau de réalisation est décrit précisément.

- Explain specialist contributions and multi-user support through repository-shared models, CAD and saved scenarios; describe the inputs, geometry references, assumptions, results, and visualization artifacts associated with each named scenario, and how another authorized contributor can load that configuration.

- Describe GitHub Pages, explicit workflow dispatches, GitHub Actions, versioned repository artifacts, and local Omniverse synchronization. State how scenario and CAD revisions relate to Git history, and distinguish scenario output separation from immutable run versioning.

- Explain saved scenario selection, loading, a selected comparison baseline, available final metrics and relative changes, and overlaid histories. Relate these mechanisms to collaborative discussion of alternatives.

- Specify how asynchronous contributions become part of a shared mission definition. Retain multi-user support as a requirement while identifying concurrent editing and application-level synchronization as future capabilities.

Figures: one dual-metadata CAD diagram, with orientation and write-back examples only where needed; one manifest and terrain-integration diagram. Keep result dashboards for Section V.

## V Demonstration and results

### A Cases assumptions and evaluation protocol

- Define the current Lunar Spaceport-1 ISRU baseline from its saved configuration, rather than reconstructing it from prose in the old paper.

- Give active types and instance counts, site, coordinates and route lengths, duration, processing and conversion assumptions, inventory capacities, transport parameters, power demand and generation, battery initial conditions, and energy-constraint mode.

- Provide an assumptions table with each important coefficient's value, units, source or rationale, scope, and configured location. Include process coefficients, dispatch intervals, and the route-slope speed model.

- Identify software revision, scenario and run identifiers, terrain source and preparation, and output files used for the figures. Distinguish total simulation duration from individual plant operating time.

- Define a small controlled comparison campaign. Recommended cases: baseline; changed rover fleet; changed processing capacity; and changed power supply. Add a changed-route case if needed to substantiate the terrain-to-operations connection. Hold other assumptions fixed and explain exceptions.

- Include an analytical or independently calculated check of a simple resource and travel case, an energy-accounting check, and a documented insufficient-power case. These proposed checks are evidence to produce, not results already obtained.

### B Site assessment and complete workflow execution

- Retain the regional GIS ranking if its original method, inputs, and weights remain applicable. Report the selected site's rank under those criteria rather than calling it universally optimal.

- Show the actual local layout and routes used by the current DES and Omniverse package.

- Demonstrate the current ISRU path from activation and instance placement to configuration, DES outputs, saved scenario artifacts, and selected Omniverse playback. Describe the requirements-verification branch separately; exclude untested integrated verification from this end-to-end evidence claim.

- Trace a changed input through the affected downstream artifacts. Demonstrate contribution continuity without inferring a measured improvement in collaboration efficiency.

### C ISRU outcomes and scenario comparison

- Report LOX produced, LOX delivered, retained inventories, regolith delivered and processed, plant activity, rover trips and distances, energy demand and generation, and battery state where modeled and logged.

- Separate total production from delivery fraction and inventory carryover. Delivery fraction over a finite horizon is not a thermodynamic or transport efficiency.

- Show time histories of the quantities needed to explain resource or power bottlenecks. Interpret changes in terms of the configured parameters and scheduling assumptions.

- Compare completed scenarios on common axes and state the selected baseline. Do not imply statistical significance for deterministic case comparisons.

- Replace the old numerical table with current outputs. The historical 111.23 kg LOX result and full-battery interpretation cannot be carried into the new abstract without regeneration and verification under the current model.

Evidence: case and assumptions table; updated GIS/layout figure; baseline and variant result table; aligned production, delivery, energy, and battery histories. Include only available and meaningful signals.

- Generalization scope. Explain the role-based framework in Section IV.D and its evaluation boundary in VI. The Results section remains centered on the current ISRU case; simple exploratory non-ISRU runs are not presented as validated demonstrations.

Note Arthur N21  Tu parles souvent de generic démonstrations, a quoi tu fais ref?

Réponse V2 N21  Traité. Je faisais référence aux essais cargo relay, ice processing et water transfer cités dans les échanges précédents. Ta précision prévaut : des scénarios simples ont été générés et exécutés, mais leur chaîne complète jusqu’à la visualisation n’a pas été validée. Je retire leur statut de démonstrations et leurs résultats du plan scientifique.

Note Arthur N18    ca on l’a pas vrm fait, je ne pense pas que ca serve a quelque chose de parler de ca. je pense la stratégie qu’on peut prendre c’est d’expliquer concretemtn ce qu’on peut faire, dire que de base ca a été consrutit sur un scenario ISRU mais qu’on a généralisé le process et que mtn ca peut etre faoit sur tou type de scenario mais ca n’a pas été encore testé sur des scenarios vrm tres different. Je evux dire ok tu m’avais généré d’autres scenarios et on les avait run mais concretemtn on n’avais pas regarder si tout marchait bien jusqu’a la visualization et c’était des scenarios tres simples.

Réponse V2 N18  Traité. Je retire la sous-partie de résultats consacrée aux trois exemples génériques et les demandes de les reproduire pour ce paper. Tu confirmes des essais simples exécutés, mais pas une validation de bout en bout jusqu’à Omniverse. La méthode explique la généralisation réellement implémentée ; la discussion précise qu’elle reste à évaluer sur des scénarios significativement différents. On peut exposer l’ambition de couvrir plusieurs types de scénarios, sans conclure que tous les scénarios sont déjà supportés ou validés.

### D CAD and playback consistency

- Demonstrate conversion and metadata propagation on representative supported input formats. Report the original format, resolved orientation, applied scale, resulting geometry reference, and SysML metadata update.

- Show that two scenario-specific CAD selections remain distinct when saved and loaded. Check scenario identity across the selected configuration, results, manifest, geometry, and playback.

- Present terrain-grounded placement and projected operational routes. Use available slope and projection diagnostics to report consistency and limitations of the supplied terrain asset.

- Show an Omniverse frame with telemetry at a stated recorded simulation time and compare selected displayed values with the corresponding log entries.

- Describe the visual information stakeholders can inspect. Reserve claims about improved comprehension or decision performance for a separate evaluated study.

Note Arthur N19   ca pareil je pense qu’on va l’enlever car cette partioe a été faite mais pas vrm testé.

Réponse V2 N19  Traité. Je retire la sous-partie V.F qui demandait une démonstration actuelle de vérification et de couverture. La boucle d’exigences reste décrite dans Architecture et Implementation comme un développement dont la validation intégrée n’est pas établie ici. Le paper ne présentera ni rapport pass/fail ni automatisation complète comme résultat sans preuve correspondante.

Results figures: the ISRU layout and routes, quantitative comparisons of completed ISRU runs, a CAD metadata example where needed, and the matching Omniverse scene with recorded-time telemetry. Omit the three generic-case panels and the untested requirement-verification report.

Evidence priorities: regenerate the declared ISRU baseline and selected variants, preserve their assumptions and output identity, and check the displayed CAD and Omniverse associations. Keep the literature matrix and method figures compact within the page budget.

## VI Discussion

### A Answers to the research questions

- RQ1 Modularity and scalability: interpret system-type activation, module instancing, architecture and parameter changes, reusable equation contracts, and the limits of the behavior vocabulary. Separate observed configuration flexibility from unmeasured performance at large system or user counts.

- RQ2 Collaboration and interoperability: explain how common identifiers, authoritative properties, scenario overrides, versioned CAD/models, saved-scenario sharing and comparison preserve engineering context across contributors. State the current asynchronous multi-user support.

- RQ3 Visualization-based mission evaluation: interpret the correspondence between the selected scenario, numerical results, placement, routes, rover motion, and recorded-time telemetry. Distinguish inspectable information from a measured benefit to stakeholder decision performance.

### B Limitations and interpretation

- Generic behavior uses a constrained role vocabulary and predominantly mass-based resources. Simple exploratory runs do not establish end-to-end validity for substantially different missions. Coupled reactants, complex resource networks, richer inventories, failures, and stochastic operations require further work.

- Power is a simplified balance. Energy-unconstrained runs establish no power feasibility; complete rover charging and electrical-network design are not implemented.

- DES travel uses simplified route metrics. Omniverse movement does not establish validated vehicle dynamics.

- Prepared-mesh grounding requires appropriate geographic source data and does not prove constructability. CAD properties depend on units, closure, scale, and density assumptions.

- GitHub supports asynchronous contributions. Simultaneous editing, access-control guarantees, conflict prevention, and quantified collaboration benefits require separate evidence.

- State physical-model validation limits, untested integrated requirements verification, and remaining scenario-specific comparison and telemetry logic. The selected evidence does not constitute a scalability benchmark or a simultaneous-user test.

## VII Conclusions and future work

### A Conclusions

Answer the objective through the current ISRU evidence while preserving the main contribution axes: integrated pipeline, modularity/scalability, collaboration, and visualization-based evaluation, supported by configurable simulation and CAD/model consistency. Use only regenerated numerical findings. Describe generalization and verification at their demonstrated maturity.

### B Future work

Note Arthur N20   une npuvelle team bosse sur le projet, on va les introduire je pense ici et je t’enverrai leur ppt le plus recent au niveau des points. On peut aussi dire que je vais contnuer la rechercher dessus dans le cadre de mon phd?

Réponse V2 N20  Pris en compte et à compléter. Oui, Future Work peut situer la poursuite du projet par une nouvelle équipe et par tes recherches doctorales prévues, en restant centré sur les questions scientifiques. Je prévois une phrase collective et sobre. Le périmètre précis de la nouvelle équipe sera intégré après lecture de son PPT ; je ne lui attribue pas à ce stade les tâches de la liste.

- Extend and evaluate the generic behavior vocabulary, unit handling, resource synchronization, power and mobility models, and charging. Test complete non-ISRU workflows through visualization and assess the developed requirement-verification loop before claiming integrated validation.

- Automate geographic terrain preparation; enrich the CAD library with traceable engineering components; and strengthen scenario/run revision tracking and resource-independent comparison and telemetry.

- Develop multi-user application services and evaluate collaborative use, concurrent access, and scale. Situate the continuation through the new project team and planned doctoral research, with precise research directions added after review of the team presentation.

Continuation sentence. Further development of ECLIPSE is planned through a new project team and continuing doctoral research. Specify the next scientific objectives after reviewing the team’s latest presentation; distinguish planned work from work already completed. Avoid personal biography or unconfirmed institutional commitments.

Do not list existing saved scenarios, baseline comparison, multiformat CAD, terrain sampling, or synchronized playback telemetry as future features. Future work should name the additional maturity or scope required.

## Integration map and source record

### Placement of the main 8900 capabilities

### Architecture and implementation boundary

Architecture specifies the purpose, relationships, authority rules, and information that must cross each boundary. Implementation explains the chosen representations, tools, algorithms, equations, controls, and execution mechanisms. Results show the artifacts and measured behavior obtained from declared cases. Discussion interprets those findings and their limits.

Keep one explanation of each mechanism. For example, the architecture requires a traceable scenario package; implementation defines the manifest and package generation; results demonstrate loading the matching package; discussion assesses the resulting traceability and remaining dependencies.

### Source record

- ECLIPSE paper: ECLIPSE_PAPER.pdf, supplied SciTech copy, 19 PDF pages. Primary source for the original ecosystem, eight-block architecture, GIS method, and team-developed verification workflow. Its old results and broad claims require the updates identified above.

- 8900 paper: Final-Paper_Brunier_Arthur.pdf, 23 PDF pages. Use its technical detail for the implemented mechanisms. Arthur’s V2 clarification governs evidence status: simple non-ISRU runs were exploratory and were not fully checked through Omniverse.

- Original outline and annotated V1: Detailed Outline2.docx and SCITECH_Outline_v1.docx. Preserve the annotated V1 unchanged. This V2 restores the original project vocabulary, addresses each red note locally, and adds the manuscript length budget.

- Repository discussions: Étudier intégration Omniverse, 359 retrieved turns; Expliquer la généralisation DES, 111 retrieved turns; Rédiger l’abstract du projet, including the final-tool and specialist-collaboration narrative decisions. The TRC discussion provides submission context rather than technical evidence.

- Repository evidence: scenario runner and configuration, generic compiler and equation evaluator, active ISRU engine, CAD conversion and SysML updater, scene and manifest generation, web interface, user guide, and GitHub workflows. The historic DES diagnosis describes the former implementation and must not override the current sources.

- Review guidance: advisor comments supplied with the request and three annotated photographs. They motivate the literature synthesis, architecture/implementation separation, revised motivation, and replacement of historical results.

SciTech length guidance: AIAA, Technical Presenter Resources, manuscript FAQ, accessed 18 November 2026. https://scitech.aiaa.org/call-for-content/technical-presenter-resources/. Apply any more specific instructions supplied by the accepted session.

LUNAverse context: Mueller, R. P., McCoy, M., Paul, D. J., Pinon Fischer, O. J., Caldwell, B., and Ingham, M. D., The Case for the LUNAverse. Supplied 30-page preprint, not peer reviewed. Key sections: 2 and 5 for coordination; 6 for spatial reference; 8 for the iterative architecture; 10 for specialist-tool integration. Cite the specific preprint version actually used and verify underlying references individually.

The literature assessment and refreshed ISRU comparison campaign are the next evidence-producing stages. Generalized non-ISRU end-to-end validation and integrated requirement verification are future evaluation needs rather than completed results in this paper.
