# ECLIPSE SciTech paper outline V4

Integrated scenario definition simulation and visualization

Version 4 | 18 November 2026

Périmètre V4. Révision locale de la V3 annotée en vert. Les notes vertes et rouges restent visibles. Abstract, Introduction et Motivation sont conservés ; leur rédaction réutilisera le paper existant avec les améliorations de l’été et les notes déjà fournies. Les validations sont distinguées des demandes de changement. Les consignes complémentaires sur les sources et la portée de la généralisation sont appliquées uniquement aux passages correspondants.

The paper presents the complete ECLIPSE environment for collaborative lunar base architecting within LUNAverse. Four contribution axes organize the account: the integrated digital thread, modularity, collaboration, and quantitative and visual evaluation. The AE 8900 developments supply technical mechanisms within these axes, including configurable behavior, a role-based scenario language, CAD metadata propagation, scenario persistence, and automated visualization packages.

This revision starts from the annotated V1. Read the red notes as an evolving line of reasoning: a later clarification can resolve an earlier objection. Preserve the distinction between functional architecture and interface realization. The outline identifies implemented mechanisms, demonstrated outcomes, and evaluation still needed without treating those categories as interchangeable.

## Lecture critique et budget du manuscrit

Base de travail. V3 repart de la V1 annotée. Les notes rouges originales sont conservées ; les réponses distinguent explication, objection levée par une note ultérieure, choix éditorial et limite factuelle. Elles ne valent pas acceptation automatique de chaque proposition. N09–N10 est traité comme un seul raisonnement, et non comme deux ordres successifs.

Arbitrages globaux. A1 réunit vocabulaire, questions et contributions ; A2 relie exigences et preuves ; A3 distingue blocs fonctionnels et écrans ; A4 clarifie les notions sans redéfinir les fonctions ; A5 tranche le placement et le contenu du schéma ; A6 borne collaboration/versioning ; A7 sépare mécanismes implémentés et démonstrations ; A8 encadre Future Work. Les analyses locales renvoient à ces décisions communes.

Budget convenu. Cible de 22 à 24 pages tout compris. Répartition de travail sur 24 pages : titre/abstract 1 ; introduction 1 ; problem formulation et littérature 3 ; architecture 4 ; implementation 6 ; résultats 4 ; discussion 1,5 ; conclusion 0,5 ; remerciements/références 3. Figures et tableaux sont inclus. Ce budget guide la profondeur sans imposer de remplir chaque quota.

Priorité éditoriale. Garder quatre axes de contribution et développer les mécanismes DES/CAD qui les soutiennent. Éviter de répéter l’architecture dans le parcours d’interface. Donner les détails causaux utiles à la simulation et à la cohérence des données ; limiter les captures illustrant seulement des menus. Prévoir environ 6 à 8 figures et 3 à 4 tableaux, avec ajustement selon les résultats disponibles.

La longueur du présent outline annoté est indépendante de celle du manuscrit final. La FAQ générale SciTech consultée le 18 novembre 2026 indique une longueur courante de 12 à 24 pages, références comprises, et pas de limite générale ; les consignes propres à la session restent prioritaires. https://scitech.aiaa.org/call-for-content/technical-presenter-resources/

## Abstract

- Establish the engineering problem: interdependent lunar infrastructure must be designed by specialists using heterogeneous models and tools.

- Introduce ECLIPSE and its connected workflow from system definition and requirements to site planning, operational simulation, verification, and visualization.

- Explain modular scenario definition, configurable ISRU equations and parameters, the implemented generic behavior mechanism, CAD/model consistency, scenario sharing and comparison, and scenario-specific Omniverse playback. Keep the contribution axes broader than any one implementation mechanism.

- Summarize the demonstrations and include numerical findings only after the current simulation campaign has been completed and checked.

- State the demonstrated ISRU-centered scope. Describe the generic framework as an implemented approach whose broader end-to-end applicability has not been established. Do not use the small exploratory resource-chain runs as validated demonstrations.

## I Introduction

### A Background

- Introduce sustained lunar infrastructure as a system of interdependent habitats, power, communications, processing facilities, storage, and transport assets.

- Explain the coordination required between independently developed systems: their resource demands, interfaces, timing, and environmental assumptions must be compatible. Use the LUNAverse position paper to frame the need, then use primary technical studies for the particular claims assessed in the literature review.

- Use the lunar spaceport as the concrete design problem. Establish the coupled effects of placement, terrain, resource access, logistics, and power.

- LUNAverse context. Position ECLIPSE within the wider initiative described in The Case for the LUNAverse. Sections 2 and 5 motivate coordination of independently managed systems; Section 6 discusses shared spatial assumptions; Sections 8 and 10 discuss iterative model/evidence links and specialist-tool integration. Use this preprint for framing and verify its cited primary studies for comparative claims.

- Keep lunar program context brief and supported by current primary sources. Replace broad judgments about Apollo-era engineering with a precise description of the present integration problem.

### B Motivation

- Paragraph 1: recall the collaboration need from Background, then explain heterogeneous tools, data meanings, alternative models, and the coordination of assumptions. Introduce controlled information sharing as a need and describe implemented support later.

- Paragraph 2: explain why mission objectives change system types, quantities, connections, operating laws, and layouts. Derive modularity and scalability needs. Configurability supports some of those needs; extensibility is a separate property concerning additions to the behavior vocabulary.

- Paragraph 3: motivate explicit visualization of the simulated mission through time. Explain what spatial placement, rover movement, resource histories, and synchronized telemetry help stakeholders inspect alongside numerical measures of effectiveness.

- Paragraph 4: introduce digital engineering and ECLIPSE’s place within LUNAverse. Use the preprint to motivate shared design-time coordination and iteration between models, simulation, evidence, and decisions. Keep the assessment of published approaches in II and the wider LUNAverse ambitions separate from ECLIPSE’s delivered scope.

## II Problem formulation

### A Literature review

Groups 1–4 compare published approaches by the decision they support, the representation used and the scope of the evidence. Group 5 draws on method studies and specifications to establish the engineering criteria that connect these approaches.

Group 1 Lunar system architecture and multidisciplinary trade studies. Review system-of-systems studies and parametric or MBSE-linked sizing methods. Candidate starting points in the supplied bibliography include the Cislunar Architecture Study and the ISRU and power-system studies by Boyer, Ramkumar, and Mehta. Assess how they connect architectural decisions to performance, what they demonstrate about trade exploration, and which operational or integration questions remain outside their reported scope.

Group 2 Operational modeling and scenario construction. Review lunar logistics and surface-operations environments, followed by configurable or composable simulation approaches. The tabletop study and MORPH, DELOS, and PIONEER are starting points whose actual reports must be inspected. Compare event logic, resource contention, scenario input languages, user responsibility, and the effort required to express a different resource chain.

Group 3 Digital engineering integration and collaboration. Review authoritative models, digital threads, interoperability, versioning, and multi-user support. Compare the mechanisms actually reported. Use The Case for the LUNAverse as a contextual preprint explaining the wider integration objective; read its underlying references before using them as comparative evidence. Distinguish shared artifact contributions from concurrent editing services.

Group 4 Spatial planning and simulation visualization. Review GIS-informed infrastructure planning, simulation-linked 3D environments, and the role of scene interoperability. Compare coordinate consistency, terrain provenance, geometry association, time synchronization, and scenario regeneration. An operationally synchronized physical counterpart is a different claim from a design-stage simulation playback.

Group 5 Enabling Technologies and Engineering Standards. Establish three criteria: preserving typed requirements and interfaces across representations, expressing contention and event order among operational processes, and associating identified assets with terrain and simulation time in a composed scene. Ground each criterion in an application or empirical study. Cite specifications for their precise technical claims. Treat spatial provenance and structured exchange where they affect these criteria. Include repository-based collaboration only when it supports a distinct traceability claim. Allow two short paragraphs (about 130–180 words) within the existing Section II budget. Section III assigns information authority and responsibilities; Section IV explains the choice, use and limits of each software component.

Cross-cutting comparison criteria. Use interoperability, modularity, scalability, traceability, versioning, multi-user support, spatial/temporal consistency, and scenario preservation as a shared reading framework. For each study, assess only the criteria relevant to its stated scope and supported by its reported evidence. Summarize the main findings by methodological family rather than repeating a full checklist for every publication. Distinguish not addressed, not reported, and evaluated limitations.

Note Arthur G01  Donc ca tu veux qu’on le fasse pour chaque study?

Réponse V4 G01. Pas sous forme d’une grille exhaustive répétée pour chaque étude. Les critères servent à lire les travaux de façon cohérente ; on retient pour chacun les dimensions pertinentes et effectivement documentées, puis on synthétise par famille de méthodes. Un article qui ne traite pas la visualisation n’est pas nécessairement déficient sur ce point : cela peut être hors de son objectif.

Review output. Close II.A with the comparison matrix for Groups 1–4. Use the criteria from Group 5 to interpret its findings. Reserve the explicit statement of the remaining integration problem and ECLIPSE’s response for II.B Research gap.

Note Arthur G02  Mais ets ce que cette partie ne devrait pas aller dans research gap plutot? 

Réponse V4 G02. La comparaison et sa synthèse concluent la littérature ; le constat précis de ce qui reste à résoudre, puis le positionnement d’ECLIPSE, appartiennent au research gap. II.A et II.B sont ajustés pour rendre cette transition explicite sans répéter la matrice.

Audit and reuse the relevant references already present in the ECLIPSE paper, checking titles, identifiers, publication status, and the claims they support. For additional scientific evidence, select peer-reviewed articles in established scientific journals. Retain the supplied LUNAverse preprint for initiative context, identifying its publication status; it does not replace peer-reviewed evidence. Official software documentation may substantiate implementation details, not scientific novelty or engineering effectiveness.

Use of LUNAverse. The supplied 30-page preprint provides the strategic integration context, not independent validation of this prototype. Sections 2/5 address coordination, 6 shared spatial context, 8 iteration between data/models/evidence/decisions, and 10 integration of specialist tools. Verify the underlying studies before using them in the comparative review.

### B Research gap

- Use the comparative synthesis in II.A to state the specific integration problem that remains insufficiently addressed in the reviewed work and explain ECLIPSE’s response. Formulate a bounded gap: maintaining a consistent scenario definition across architecture, spatial planning, configurable operations, heterogeneous geometry, and quantitative and visual assessment.

- Separate limitations documented in prior publications from limitations observed in the original ECLIPSE prototype. A prototype limitation alone does not establish a field-wide research gap.

- Scope the novelty claim to the combination and implementation demonstrated in this paper. Finalize its wording after the comparative literature assessment.

### C Objectives and research questions

Objective. Develop and demonstrate a requirements-driven digital engineering ecosystem for collaborative lunar base architecting, enabling specialists to contribute to the definition and assembly of system and scenario configurations and to their simulation, comparison, and quantitative and visual evaluation.

Note Arthur G03  La il faudrait que tu parles de ecosystem plutot que worklow, c’est dans le titre DEE.

Note Arthur G04  Le preserved je n’aime pas trop, compared ok, inspected je preferais evaluated.

Réponse V4 G03 et G04. L’objectif emploie désormais digital engineering ecosystem et evaluated. Le workflow reste la façon dont on utilise cet écosystème. La sauvegarde reste une capacité décrite ailleurs ; elle n’a pas besoin d’alourdir l’énoncé de l’objectif.

RQ1 Modularity and scalability. How can a requirements-driven lunar scenario pipeline support changes in system composition and operational behavior through a common modular workflow, without rebuilding the process for each supported configuration?

Note Arthur G05  est ce qu’on ne parle que d’assumption dans « operationnal assumptions »? On pourrait aussi dire operational behaviour (je trouve que ce mot englobe les eq, les assumptions, les valeurs des param)

Note Arthur G06   mais oui en effet, je pref cette nouvelle formulation. 

Réponse V4 G05 et G06. Je conserve la formulation de RQ1 que tu valides et remplace uniquement operational assumptions par operational behavior. Behavior désigne le fonctionnement modélisé ; les équations, paramètres et hypothèses en donnent la définition. Ces termes sont liés sans être strictement synonymes.

Note Arthur N01  Là je crois que je preferais l’ancienne formulation, qu’en penses tu?

Analyse V3 N01  A1 Clarification et reformulation. N01 et N02 concernent ensemble le positionnement du paper. Je rétablis modularité, collaboration et visualisation comme axes explicites. Je ne reprends pas littéralement les formulations anciennes promettant n’importe quelle mission ou une optimisation généralisée : ces affirmations demandent des preuves distinctes.

RQ2 Collaboration and interoperability. How can independent stakeholders contribute systems, models, geometry, and scenario data while maintaining interoperability, traceability, and versioning within a shared mission workflow?

RQ3 Visualization-based evaluation. How can quantitative measures of effectiveness be connected to a coherent spatial and temporal representation of the same mission scenario to support shared inspection and comparison?

Note Arthur G07  J’ai lu et validé les trois recherches questions.

Réponse V4 G07. Validation consignée. RQ2 et RQ3 restent inchangées ; RQ1 reçoit seulement la précision terminologique ci-dessus.

### D Contributions and evaluation strategy

- C1 Integrated digital thread: connect system definition and requirements, configuration, GIS planning, operational simulation, geometry, and visualization by maintaining the association between a scenario’s selected systems and instances, layout, operational inputs, simulation outputs, and visualization data. Describe the requirements-verification branch according to the evidence available.

Note Arthur G08  (ca veut dire quoi cett ederniere partie de phrase, through identifiable scenario artifacts???)

Réponse V4 G08. Il s’agit de garder ensemble les données qui décrivent le même scénario : systèmes et instances choisis, implantation, entrées de simulation, résultats et données de visualisation. Les identifiants et références permettent, par exemple, de rattacher les résultats d’une usine à cette même usine dans la scène. C1 explicite ce lien au lieu de la formule abstraite identifiable scenario artifacts.

- C2 Modularity and scenario flexibility: support changes in participating systems, instance multiplicity, relationships, routes, equations, and operating assumptions. Explain transparent ISRU configuration and the role-based compiler as technical mechanisms supporting this axis; distinguish these capabilities from unmeasured scaling performance.

- C3 Collaboration and engineering interoperability: connect specialist contributions through the shared SysML reference model of systems, properties, requirements, and interfaces; controlled model/CAD metadata; versioned artifacts; and shared saved scenarios and comparison. Explain CAD conversion and authoritative metadata propagation here as enabling mechanisms, not a disconnected extra contribution claim.

Note Arthur G09  (ici tu fais ref a quoi avec common model)

Réponse V4 G09. Common models désignait surtout le modèle de référence SysML partagé : définition des systèmes, propriétés, exigences et interfaces auxquelles les contributions se rattachent. Cela n’impose pas un logiciel ou un modèle unique pour chaque spécialité. C3 nomme désormais cette référence explicitement.

- C4 Quantitative and visual evaluation: associate numerical outputs and scenario comparisons with terrain-aware placement, routes, recorded motion, and synchronized telemetry in Omniverse. Explain the manifest and saved outputs as the means of retaining the same engineering context.

Relate RQ1 to scenario architecture and behavior configuration; RQ2 to model/CAD authority, versioned contributions, and shared scenarios; and RQ3 to numerical comparison and playback consistency. Keep four contribution axes. Present detailed DES and CAD improvements in their corresponding technical sections rather than adding overlapping claims of novelty.

Note Arthur N02  Là j’ai l’impression que tu as pas mal change les axes de contributioons proposes non. Avant c’était end to end pipline (donc ok pour integrated ecosysteme), modularity, collaboration, visualization. Là tu skip c’est 3 derniers alors qu’ils sont centraux pour le projet (fin surotut les deux derniers car je opense que configurable behavior modeling est inclus dans modularity mais modularity incluait d’autres choses). Pourquoi ne pas juste ajouter des axes de contributions comme ca on prend tout en compte?

Analyse V3 N02  A1 Axes conservés et proposition partiellement écartée. Le souci de conserver les axes initiaux est fondé. En revanche, ajouter mécaniquement DES et CAD comme deux contributions parallèles crée des recouvrements avec modularité et interopérabilité. Je retiens quatre axes principaux et rends les apports DES/CAD explicites comme mécanismes techniques à l’intérieur de ces axes. Les mots-clés originaux restent des objectifs ; configurability et extensibility précisent des moyens ou propriétés différents.

### Editorial rules for the merged paper

- Present the final tool directly. Retain a short historical comparison only when it clarifies a measured capability or a design rationale.

- Describe requirements as guiding architecture and evaluation. Do not imply automatic synthesis of arbitrary mission architectures or a global optimization process unless such a process is demonstrated.

- Use collaboration to describe connected specialist contributions and the implemented versioned workflow. Claims about access control, intellectual-property protection, conflict prevention, and simultaneous editing require separate evidence.

- Describe visualization as complementary to quantitative analysis. Do not claim universal stakeholder comprehension or improved decision quality without an evaluation of those outcomes.

## III Architecture

The architecture follows the original requirements-to-blocks logic. A short opening explains the requirement themes and the global figure orients the reader. The detailed derivation then explains how the responsibilities connect. Four pages is the working allocation for this section.

- Introduce the six architectural requirement themes: interoperability, scalability, traceability, multi-user support, versioning, and modularity. Distinguish these objectives from mechanisms such as configurable equations, saved scenarios, and artifact exchange. Explain their scope before deriving the blocks.

Note Arthur N03  l’interoperability ne concerne que le data exchange?

Analyse V3 N03  A2 Clarification de portée. L’interopérabilité dépasse l’échange syntaxique : outils, modèles, significations, unités, repères et géométrie doivent être compatibles. La formulation est élargie. Un format commun facilite cette compatibilité sans prouver automatiquement la conservation de toute information.

Note Arthur N04  Tu as enlevé versioning: en, soi on a toiujours un versioning au niveau des scenarios et meme des cad ajoutés etc donc je pense qu’on peut le garde ren tant que req.

Analyse V3 N04  A2 Objectif retenu et preuve à distinguer. Versioning a sa place parmi les exigences. Je ne déduis cependant pas de la seule présence de scénarios sauvegardés que chaque run et chaque dépendance possèdent un historique immuable. Le texte distingue scénarios nommés, artefacts suivis dans Git et versions nécessaires pour reproduire un ancien résultat.

- For each block, explain the motivating needs, purpose, inputs and outputs, and intended success criterion. Define the criterion in Architecture, describe its realization in Implementation, and assess it against available Results. This chain does not imply that every requirement has already been verified.

Note Arthur N05  En vrai j’aimais bien la facon de rédiger les requirements de l’ancien paper. On dit ok on a ces grands themes de reqiuirements qui ont engendré la creation de l’arhitecture. Apres pour chaque bloc on dit explicitement quelles sont les req et puis les criteres de résuiites comme tu dis, opn dit ce qu’est le bloc et on vérifie que ca valide le critere, ou bien ca ca vient apres?

Analyse V3 N05  A2 Lecture conjointe N03 à N06. La dérivation exigences → blocs est le bon fil directeur pour ce paper. Le critère de réussite est défini dans Architecture, sa réalisation décrite dans Implementation, puis sa satisfaction évaluée dans Results. Définir un critère ne constitue pas déjà une vérification. Je préfère un court passage introductif sur les six thèmes à une sous-section autonome essentiellement énumérative.

Note Arthur G10  Oui c’est exactement ca, j’aime beaucoup cette vision. 

Réponse V4 G10. Accord consigné : critères dans Architecture, mécanismes dans Implementation, satisfaction évaluée dans Results selon les preuves disponibles. Aucune modification supplémentaire de ce principe.

Note Arthur N06  Je ne pense ^pas qu’il y ait besoin de faire une soys partie pour ca, je pense que je preferais comme avant.

Analyse V3 N06  A2 Choix éditorial. Cette préférence est retenue parce que six thèmes peuvent être introduits brièvement avant la dérivation, pas parce qu’une note demande à elle seule la suppression d’un titre. Voir l’analyse conjointe de N03 à N06.

- Explain the level of multi-user support being designed and delivered. Shared models, saved scenarios, and contributions across specialties are relevant mechanisms. Simultaneous editing and application-level synchronization require distinct evidence and services.

Note Arthur N07  Est ce que tu penses que je dois mettre ici le schema global de l’architectire (donc juste avant qu’on explique la decomposition des blocs) ou bien apres (comme ce que j’avais fait avant)? Je me demande si c’est pas mieux avant.

Analyse V3 N07  A5 Question à lire avec N15 et N16. La question du placement reste ouverte dans cette première note ; N15 en expose le compromis. Je recommande une figure globale après la courte introduction des exigences, avant les blocs détaillés. L’objectif est d’orienter la lecture sans répéter le schéma à la fin.

Note Arthur G11  Oui je valide ce choix.

Réponse V4 G11. Placement du schéma confirmé : après la courte introduction architecturale et avant la dérivation détaillée des blocs. Le passage existant reste inchangé.

Overview figure placement. Introduce the global architecture in two or three sentences, place its diagram here, and use it as a guide for the block derivation. Earlier placement favors navigation; the derivation still supplies the logical justification afterward.

### A Derivation of the main building blocks

The blocks below are logical responsibilities. A responsibility may span several interface stages, and one interface stage may realize several responsibilities. Derive each block from the requirements, then describe its implementation in IV. Keep control labels, workflow buttons, and step numbers out of the functional block definitions.

- Authoritative Source of Truth: provides the common model of systems, reference properties, requirements, and interfaces needed for traceability and versioning. Common identifiers connect modeled elements and downstream representations; describe what is actually preserved without assuming renaming-proof identity.

Note Arthur N08  (que veut dire stabe identifiers?)

Analyse V3 N08  A4 Explication sans changement de fonction. Un identifiant commun permet de reconnaître le même élément dans ses représentations successives, par exemple de rattacher la production à ISRUPlant_1 plutôt qu’à une autre usine. Je précise ce sens ; cette demande d’explication ne justifie pas de redéfinir le rôle de l’ASOT ou d’inventer un identifiant universel résistant à tout renommage.

- Module Selection and Scenario Configuration: defines the participating system types and their configured logical instances, multiplicities, and retained interfaces for a mission. This responsibility establishes the selected architecture; Urban Planning supplies its physical layout, while the behavior model describes its operations. Its realization can span several interface stages.

Note Arthur N09  c’est pas la qu’on choisit les instances des modules mais dans la step4.2 phase 1 qui s’appelle d’ailleurs asset instancing et placement) ici on choisit juste leur type (leur classe) et si on veut les active ou non

Analyse V3 N09  A3 Objection réinterprétée par N10. N09 exprime d’abord une lecture en termes d’écrans. N10 lève cette objection en distinguant architecture fonctionnelle et interface. Je ne retiens donc pas N09 comme une demande de limiter le bloc à Step 2. Les détails d’implémentation indiqués dans cette note sont conservés pour IV.B/IV.C.

Note Arthur N10  Ah mais je viens de comprendre. En fait ces blocs logiques ne correspondent pas necessaire aux steps de l’interface c’est ca? en gros c’est juste l’architectire logique et dans implementation on va voir concretement comment ca a été implémenté donc on aure peut etre des blocs mélangés ou séparés en deux?

Analyse V3 N10  A3 Arbitrage conjoint N09 et N10. La conclusion de N10 gouverne la lecture du couple de notes. Le bloc Module Selection and Scenario Configuration peut définir sélection et instances logiques même si ces choix se réalisent dans plusieurs écrans. Je conserve cette responsabilité dans Architecture. Implementation explique que Step 2 active les types, que Step 4.2 Phase 1 crée/place les instances fixes et que Phase 2 traite flottes et routes. La configuration logique et sa réalisation spatiale sont liées mais ne doivent pas devenir deux descriptions concurrentes du même écran.

- Urban Planning: evaluates candidate sites and assigns spatial positions, orientations, and operational routes to the configured mission architecture. It supplies the environmental and spatial context needed by simulation and visualization; it does not define the interface-screen boundaries of the other functional blocks.

- Behavior Engine: turns the selected architecture, resource relationships, operating equations, and power assumptions into time-dependent mission behavior. Its input must be consistent enough to execute. Explain scenario-consistency checking as a pre-execution function and distinguish it from post-simulation mission-requirement verification.

Note Arthur N11  je ne comprends pas bien ce que tu veux dire avec cette phrase) (quelle est la diff entre resource relashionship et equations?) Ne parle t-on pas de scenario validation aussi ou ca ca viendra dans implementation?

Analyse V3 N11  A4 Clarification et distinction des vérifications. Une relation de ressource décrit qui fournit quoi à qui ; une équation décrit les quantités, délais ou dépenses associés. La description opérationnelle rassemble ces liens et lois pour que le moteur puisse les exécuter. Le contrôle de cohérence avant simulation appartient au parcours opérationnel ; il ne vérifie pas les mêmes choses que la boucle d’exigences après simulation. Je clarifie ces fonctions sans introduire les contrôles UI dans la définition architecturale.

- Requirements Verification Loop: associates simulated attributes with evaluable requirement constraints and returns verification evidence to the architecture workflow.

- CAD Submission: associates stakeholder geometry with system identifiers and preserves engineering provenance while producing usable visualization assets.

- Visualization: combines the selected scenario's geometry, terrain, routes, and recorded behavior for spatial and temporal inspection.

- Collaboration: supports contributions across specialist roles through shared models, exchange contracts, versioned artifacts, and saved scenarios that contributors can load and compare. Explain the contribution and scenario-sharing mechanisms without implying simultaneous editing or unverified access-control guarantees.

Note Arthur N12  On a aussi mtn la possibiité de chatgé des scenarios etc de faire du versioning de scenario entre les users etc, ce qui ajoute a la collaboration.

Analyse V3 N12  A6 Collaboration et versioning lus ensemble. Le partage et le rechargement de scénarios renforcent bien la collaboration. Je les conserve avec les contributions par spécialité et l’historique des artefacts. Je limite la conclusion à ce workflow : cela ne démontre ni édition simultanée, ni absence de conflits, ni versionnage immuable de chaque exécution. Ce point complète N04 et N17.

### B Scenario lifecycle and information authority

- Describe the lifecycle from reference model to selected instances, spatial layout, operational configuration, execution, saved outputs, comparison, and playback.

- Define which representation supplies reference system properties, scenario choices, geometry provenance, and simulation outcomes, and how these responsibilities maintain a coherent scenario lifecycle. Keep these rules in Architecture; reserve specific tools, file structures, override precedence, and package-generation mechanisms for IV.

Note Arthur N13   la je ne comprends pas bien, peux tu me donner plus de details?

Analyse V3 N13  A4 Source des valeurs et non permissions. Information authority signifie ici quelle représentation fait référence : dimensions SysML, surcharges locales du scénario, géométrie/provenance du CAD, résultats DES et association des fichiers dans le manifest. Cela ne désigne pas un système d’autorisation des utilisateurs. Je rends cette règle concrète plutôt que de supprimer la notion parce que sa première formulation était abstraite.

Note Arthur G12  Mais est ce que information authority devrait aller dans architecture ou plutot implementation?

- A scenario binds these artifacts together. Identifiable inputs and outputs allow a user to return to scenario A after running scenario B, keeping the selected result and playback associated with the appropriate assumptions. Separate named scenarios do not automatically form immutable snapshots of every run; historical reproduction retained also depends on revisions and dependencies.

Note Arthur G13  Ah oui ok je comprends mieux avec ca paraphre pq tu veux mettre dabs architecture c’est parce qu’en fait c’est lié aux scéanrios lifecycle qui lui est une capability et donc appartient a l’archietecture?

Réponse V4 G12 et G13. Les deux notes se lisent ensemble : l’architecture définit quelles informations font référence et répartit les responsabilités qui assurent la cohérence du scénario. Ce n’est pas la seule notion de capability qui justifie ce placement. Les outils, formats, priorités de valeurs et mécanismes concrets restent dans Implementation. Le passage est recentré sur cette distinction.

Note Arthur N14  (j’aime beaucoup cette phrase, elle claque). je ne comprends pas cette deuxieme partie de phrase, a quoi fais tu références?

Analyse V3 N14  A4 Formulation conservée et explicitée. Je conserve « a scenario binds these artifacts together » pour sa précision conceptuelle. La sauvegarde permet de retrouver les hypothèses et les résultats du scénario A après avoir exécuté B. La formulation n’affirme pas que tous les runs d’un même scénario sont archivés séparément ; cela exige d’identifier les révisions conservées.

- Separate logical resource interfaces from physical transport paths. A resource-flow arrow does not by itself define a terrain route or a separate transporter.

- Show the requirement-feedback path and the CAD-metadata enrichment path as distinct connections to the authoritative model.

End the architecture account by tracing how the blocks jointly establish, evaluate, and preserve a scenario. Refer to the single global figure; do not repeat an implementation walkthrough.

Global figure brief. Keep the eight logical blocks. Show scenario definition through systems/instances, relationships, routes, equations, and assumptions; the CAD-metadata feedback to SysML; and the association of completed results, recorded logs, and visualization packages. Keep Collaboration cross-cutting, including shared scenarios and versioned contributions. Do not label a logical block as a specific interface step. Place the figure after the short architectural introduction, before detailed block derivation; conclude with a short synthesis instead of repeating it.

Note Arthur N15  Ah donc tu penses que la figure on la laisse a la fin, oui c’est peut etre mieux possiblement mais en meme temps ca facilite peut etre la lecture si c’est au debut. En fait je pense que pour la lecture c’est mieux au début, mais pour la continuité logique c’est mieux a la fin.


Analyse V3 N15  A5 Arbitrage conjoint N07 N15 et N16. N15 formule deux avantages concurrents ; elle ne confirme pas définitivement un placement en fin de section. Je tranche en faveur d’un schéma précoce comme carte de lecture. La progression logique reste assurée par la dérivation qui suit, puis une courte synthèse. Une seconde figure identique serait redondante.

Note Arthur N16  Donc concretement pour update cette figure, tu penses a quoi? Qu’est ce qui doitetre ajouté a la figure actuelle?

Analyse V3 N16  A5 Mise à jour ciblée de la figure. Je recommande de conserver les huit blocs, d’expliciter le scénario qui lie configuration, résultats et visualisation, d’ajouter le retour des métadonnées CAD et de faire apparaître sauvegarde/chargement/comparaison dans Collaboration. Je déconseille de charger ce schéma global avec les numéros d’écrans, les noms de fichiers ou tous les détails du compiler ; ces mécanismes seront expliqués en Implementation.

## IV Implementation

### A Authoritative model and model exchange

- Describe SysML v2 modeling in MSOSA, system identifiers, typed resource and power ports, dimensions, and reference attributes.

- Explain the implemented export and parsing path into the JSON representations consumed by downstream tools. State which properties and relationships are preserved and checked.

- Distinguish a requirement's satisfy relationship from execution of a verification expression. Specify the actual evaluation path in Section IV.E.

- Explain where scenario-specific values override model defaults and how their provenance is retained.

### B Scenario initialization and module selection

- Introduce the ISRU preset, saved scenario loading, and new generic scenario workflow. Explain what is prepopulated by the preset and what the user must define.

- Describe architecture parsing, the directed system graph, port and connection checks, activation of a subset, and preservation of instance identity.

- Explain that logical scenario configuration spans the interface: Step 2 selects active system types and reviews operational roles; Step 4.2 Phase 1 creates and places fixed instances; Phase 2 defines fleets and routes; Phase 3 defines interfaces and equations; and Phase 4 checks consistency. These screen boundaries do not redefine the logical blocks.

- Keep detailed role inference and equation execution in Section IV.D. This subsection establishes the system graph they consume.

### C GIS planning and operational routes

- Retain the original regional site-assessment method and its criteria, normalization, weighting, data provenance, and planning resolution.

- Explain instance creation and placement in the interface as the realization of related configuration and spatial-planning responsibilities. Distinguish a system type, an operational role, and an instance. Retain regional suitability, local map-frame definition, orientation, terrain guidance, and route construction.

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

5 Behavior compilation. Show how the selected roles, inventories, routes, equations, and power configuration become SimPy processes. Use a Processor example to connect an input delivery, inventory, transformation, processing delay, and output availability. Explain that new scenarios can be assembled within this vocabulary without a dedicated mission-specific controller.

6 Equation contracts and validation. Describe the restricted expression parser, intermediate variables, recognized variables, required outputs, and binding of outputs to resource, time, storage, or energy effects. Explain checks for missing equations, incompatible connections, absent transporters, invalid routes, and unknown variables. Validation checks executable consistency; it does not establish physical accuracy.

7 Power and travel models. Explain configured generation, stationary battery capacity and initial charge, demand modes, event energy, management interval, and inclusion of plant processing and storage demand in the system balance. Explain flat-terrain speed and the implemented route-slope adjustment. State the role of the explicit energy-unconstrained mode and distinguish it from power-feasible operation. Rover charging is not an implemented closed operational cycle.

Figures and table: one operational configuration figure; one role-to-SimPy behavior diagram; a compact role and equation-contract table. Include a numerical-settings capture only if readable and informative. Put actual case-study coefficient values and their sources in Section V.A.

### E Requirements verification

- Describe the implemented requirement-verification path, the mapping from logged attributes to model constraints, and the feedback mechanism. Report what has been tested. Implementation alone does not justify an integrated verification-results claim.

- Explain the evaluated sampling times, pass/fail semantics, reporting, and model update process. Distinguish discrete sampled checks from continuous-time guarantees.

- Retain the team-developed verification contribution. An untested or unavailable end-to-end result is a limit on the present demonstration, not proof that the underlying component is absent or nonfunctional.

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

### H Collaboration scenario sharing versioning and automation

Note Arthur N17   la tu as enlevé le mot collaboration d’ici alors que c’est un mot clé du projet.

Analyse V3 N17  A1 Terme rétabli sans promesse supplémentaire. Collaboration redevient explicite dans le titre et dans le contenu. N17 confirme l’importance du même axe discuté en N02 ; elle ne justifie pas une nouvelle contribution séparée pour chaque mécanisme de partage. Les exigences multi-user sont conservées avec leur niveau réel de réalisation.

- Explain how contributors share and reload named scenarios together with selected systems, instances, routes, equations, configuration, geometry references, and results. Connect these mechanisms to asynchronous collaboration and to the actual artifacts retained in the repository.

- Describe GitHub Pages, explicit workflow dispatches, Actions, versioned models/CAD, scenario artifacts, and local Omniverse synchronization. Distinguish a named scenario, its Git revisions, and a separately archived run; do not imply that every one is an immutable snapshot.

- Explain scenario selection for comparison, the selected baseline, available final metrics and percentage changes, and overlaid histories.

- Relate each specialist contribution to the engineering artifacts it produces. Distinguish this asynchronous workflow from transactional multi-user application services.

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

Note Arthur G14  Ca c’est la partie qui merge en fait l’ancienne demonstration et gis site selection?

Réponse V4 G14. Oui : V.B rassemble les résultats de sélection du site et la démonstration du parcours complet sur ce site. La méthode GIS reste en IV.C ; V.B en présente le site retenu, l’implantation et les liens entre étapes. Les performances numériques et comparaisons restent en V.C. L’organisation existante est conservée.

- Retain the regional GIS ranking if its original method, inputs, and weights remain applicable. Report the selected site's rank under those criteria rather than calling it universally optimal.

- Show the actual local layout and routes used by the current DES and Omniverse package.

- Demonstrate the identified current ISRU scenario from system selection and configuration through spatial planning, simulation outputs, saved artifacts, and selected visualization. Include an executed verification result only if its integrated evidence is available; otherwise describe that branch separately.

- Trace a changed input through the affected downstream artifacts. Demonstrate contribution continuity without inferring a measured improvement in collaboration efficiency.

### C ISRU outcomes and scenario comparison

- Report LOX produced, LOX delivered, retained inventories, regolith delivered and processed, plant activity, rover trips and distances, energy demand and generation, and battery state where modeled and logged.

- Separate total production from delivery fraction and inventory carryover. Delivery fraction over a finite horizon is not a thermodynamic or transport efficiency.

- Show time histories of the quantities needed to explain resource or power bottlenecks. Interpret changes in terms of the configured parameters and scheduling assumptions.

- Compare completed scenarios on common axes and state the selected baseline. Do not imply statistical significance for deterministic case comparisons.

- Replace the old numerical table with current outputs. The historical 111.23 kg LOX result and full-battery interpretation cannot be carried into the new abstract without regeneration and verification under the current model.

Evidence: case and assumptions table; updated GIS/layout figure; baseline and variant result table; aligned production, delivery, energy, and battery histories. Include only available and meaningful signals.

- Scope of the selected results. The detailed quantitative and visual demonstration uses the current ISRU application. The generic scenario compiler is operational and has executed simple non-ISRU resource-chain scenarios through simulation. Explain how supported operational roles, resource relationships, and user-defined equations allow different lunar scenarios to be assembled without writing a dedicated scenario controller. This reuse is bounded by the implemented behavior and equation vocabulary; coverage of every lunar mission type and complete non-ISRU visualization have not been established. Existing execution evidence may be summarized briefly where available, without adding a broad generalization test campaign to this submission.

Réponse V4 précision du message. La généralisation est présentée comme une capacité opérationnelle de construction et d’exécution de scénarios, avec de premiers essais non-ISRU jusqu’à la simulation. La démonstration intégrée jusqu’à la visualisation reste distincte. On peut l’expliquer et citer les traces existantes sans lancer une grande campagne additionnelle. Le protocole ISRU chiffré sera arrêté avant les runs à partir d’une configuration de référence et de ses équations, paramètres et hypothèses, plutôt que d’inventer ces valeurs ici.

Note Arthur N18    ca on l’a pas vrm fait, je ne pense pas que ca serve a quelque chose de parler de ca. je pense la stratégie qu’on peut prendre c’est d’expliquer concretemtn ce qu’on peut faire, dire que de base ca a été consrutit sur un scenario ISRU mais qu’on a généralisé le process et que mtn ca peut etre faoit sur tou type de scenario mais ca n’a pas été encore testé sur des scenarios vrm tres different. Je evux dire ok tu m’avais généré d’autres scenarios et on les avait run mais concretemtn on n’avais pas regarder si tout marchait bien jusqu’a la visualization et c’était des scenarios tres simples.

Analyse V3 N18  A7 Fait expérimental corrigé et généralisation bornée. Cette note apporte un fait décisif : des essais simples ont été exécutés mais leur chaîne complète jusqu’à Omniverse n’a pas été contrôlée. Ils ne seront pas présentés comme démonstrations validées. En revanche, la conclusion « tout type de scénario » dépasse ce fait : la généralisation est limitée par les rôles et comportements implémentés. Je conserve l’explication du mécanisme et place l’évaluation de scénarios significativement différents dans les limites et suites du travail.

### D CAD and playback consistency

- Demonstrate conversion and metadata propagation on representative supported input formats. Report the original format, resolved orientation, applied scale, resulting geometry reference, and SysML metadata update.

- Show that two scenario-specific CAD selections remain distinct when saved and loaded. Check scenario identity across the selected configuration, results, manifest, geometry, and playback.

- Present terrain-grounded placement and projected operational routes. Use available slope and projection diagnostics to report consistency and limitations of the supplied terrain asset.

- Show an Omniverse frame with telemetry at a stated recorded simulation time and compare selected displayed values with the corresponding log entries.

- Describe the visual information stakeholders can inspect. Reserve claims about improved comprehension or decision performance for a separate evaluated study.

Contexte de N19. La note suivante était rattachée dans la V1 à « Integrated requirement verification », rubrique de résultats retirée ici ; elle ne porte pas sur la sous-partie CAD/playback qui précède.

Note Arthur N19   ca pareil je pense qu’on va l’enlever car cette partioe a été faite mais pas vrm testé.

Analyse V3 N19  A7 Portée de N19 et interprétation prudente. N19 suit la rubrique de résultats sur la vérification : je l’interprète comme une réserve sur la preuve intégrée proposée. Je retire cette rubrique comme résultat acquis. Je ne transforme pas « pas vraiment testé » en « non développé » ou « absent » : la boucle reste dans Architecture et Implementation, avec ses preuves et limites à préciser. La vérification des modèles, celle des exigences et la validation physique restent des questions différentes.

Results figures: the current ISRU layout, completed-run comparison plots, CAD metadata evidence where useful, and the matching Omniverse playback with recorded-time telemetry. Omit the exploratory generic-case panels and any unsupported verification report.

Evidence priorities: regenerate and check the declared ISRU baseline and variants; retain their assumptions and scenario associations; and collect the matching CAD and visualization evidence. Preserve the distinction between implementation checks, physical validation, and mission-requirement verification.

## VI Discussion

### A Answers to the research questions

- RQ1: interpret modular composition and configurable behavior, including supported multiplicities, routes, and equations. Explain the role-based generalization mechanism without presenting its broad end-to-end coverage or computational scalability as measured.

- RQ2: interpret shared model/CAD information, scenario loading and comparison, artifact provenance, and versioned contributions. Distinguish the implemented collaboration workflow from simultaneous editing and stronger reproducibility guarantees.

- RQ3: interpret correspondence between the selected numerical scenario, its layout, terrain, routes, motion, and telemetry. Explain what can be inspected without claiming measured improvements to stakeholder comprehension or decisions.

### B Limitations and interpretation

- The generic framework supports a defined role vocabulary and predominantly mass-based resources. Simple exploratory runs do not establish complete validity for substantially different missions. Further evaluation is required, and new phenomena outside the behavior vocabulary require model development.

- Power is a simplified balance. Energy-unconstrained runs establish no power feasibility; complete rover charging and electrical-network design are not implemented.

- DES travel uses simplified route metrics. Omniverse movement does not establish validated vehicle dynamics.

- Prepared-mesh grounding requires appropriate geographic source data and does not prove constructability. CAD properties depend on units, closure, scale, and density assumptions.

- GitHub supports asynchronous contributions. Simultaneous editing, access-control guarantees, conflict prevention, and quantified collaboration benefits require separate evidence.

- State physical-validation limits, the scope of available integrated requirement-verification evidence, and remaining scenario-specific comparison/telemetry logic. Preserve implemented components in the account while qualifying the conclusions they support.

## VII Conclusions and future work

### A Conclusions

Conclude around the four contribution axes and the current evidence. Explain how the technical developments support modular configuration, collaboration, and coherent quantitative/visual evaluation. Use only regenerated numerical findings and scope broader generalization and verification claims to the evidence actually established.

### B Future work

Note Arthur N20   une npuvelle team bosse sur le projet, on va les introduire je pense ici et je t’enverrai leur ppt le plus recent au niveau des points. On peut aussi dire que je vais contnuer la rechercher dessus dans le cadre de mon phd?

Analyse V3 N20  A8 Continuité prévue et périmètre à préciser. Une courte mention de la nouvelle équipe et des recherches doctorales prévues peut situer la continuité. Je recommande de centrer Future Work sur les questions techniques, plutôt que sur un inventaire des personnes ou un engagement institutionnel non confirmé. Le PPT servira à définir les directions précises ; je ne les attribue pas d’avance à cette équipe.

- Prioritize integrated evaluation of significantly different scenarios, the generic behavior vocabulary, resource/unit handling, power and mobility fidelity, and the developed verification loop. State the scientific or technical question addressed by each priority.

- Automate geographic terrain preparation and enrich the existing CAD library with curated, traceable engineering components.

- Discuss services and evaluation needed for concurrent multi-user work and stronger scenario/run provenance. The new team and planned doctoral research can establish continuity in one brief sentence; specify their technical scope after reviewing the presentation, without assigning unconfirmed tasks.

Do not list existing saved scenarios, baseline comparison, multiformat CAD, terrain sampling, or synchronized playback telemetry as future features. Future work should name the additional maturity or scope required.

## Integration map and source record

### Placement of the main 8900 capabilities

| Capability | Implementation | Evidence |
| --- | --- | --- |
| Visible ISRU architecture assumptions and equations | IV D items 1 to 3 | V A and V C |
| Role inference overrides and generic compiler | IV D items 4 to 6 | IV D mechanism; VI evaluation scope |
| Multiple rovers plants inventories and return trips | IV D item 2 | V C |
| Configurable power and route-level travel | IV C and IV D item 7 | V A and V C |
| CAD formats orientation scaling and dual metadata | IV F | V D |
| Scenario-specific CAD and reusable library assets | IV F and<br>IV H | V D |
| Named scenarios reload and baseline comparison | IV B and IV H | V B and V C |
| Manifest packages and recorded-time telemetry | IV G | V D |
| Terrain sampling grounding and route projection | IV G | V B and V D |
| Original SysML GIS and requirement verification | IV A IV C and IV E | V B; verification evidence qualified |

### Architecture and implementation boundary

Architecture specifies the purpose, relationships, authority rules, and information that must cross each boundary. Implementation explains the chosen representations, tools, algorithms, equations, controls, and execution mechanisms. Results show the artifacts and measured behavior obtained from declared cases. Discussion interprets those findings and their limits.

Keep one explanation of each mechanism. For example, the architecture requires a traceable scenario package; implementation defines the manifest and package generation; results demonstrate loading the matching package; discussion assesses the resulting traceability and remaining dependencies.

### Source record

- ECLIPSE paper: ECLIPSE_PAPER.pdf, supplied SciTech copy, 19 PDF pages. Primary source for the original ecosystem, eight-block architecture, GIS method, and team-developed verification workflow. Its old results and broad claims require the updates identified above.

- 8900 paper: Final-Paper_Brunier_Arthur.pdf. Use its technical mechanisms and distinguish them from the experimental claims corrected by Arthur: simple non-ISRU executions were exploratory and their full visualization path was not checked.

- Editing base: the annotated SCITECH_Outline_v1.docx, with its original red notes. V3 is rebuilt from that document, not obtained by continuing the V2 transformations. Detailed Outline2.docx and the ECLIPSE paper remain architectural/content references.

- Repository discussions: Étudier intégration Omniverse, 359 retrieved turns; Expliquer la généralisation DES, 111 retrieved turns; Rédiger l’abstract du projet, including the final-tool and specialist-collaboration narrative decisions. The TRC discussion provides submission context rather than technical evidence.

- Repository evidence: scenario runner and configuration, generic compiler and equation evaluator, active ISRU engine, CAD conversion and SysML updater, scene and manifest generation, web interface, user guide, and GitHub workflows. The historic DES diagnosis describes the former implementation and must not override the current sources.

- Review guidance: advisor comments supplied with the request and three annotated photographs. They motivate the literature synthesis, architecture/implementation separation, revised motivation, and replacement of historical results.

Additional source: The Case for the LUNAverse, supplied preprint, 30 PDF pages, not peer reviewed. Use the version supplied and distinguish its wider ambitions from ECLIPSE implementation and evidence.

The literature assessment and refreshed ISRU campaign remain to be completed. Generalized non-ISRU end-to-end validation and integrated requirement verification are evaluation needs, not established results in this outline.
