# Paper Integration Map

Use the files in this order:

1. `01_summary_and_abstract.tex`
   - Replace the complete Executive Summary.
   - Replace the complete Abstract.
2. `02_body_replacements.tex`
   - Use `Revised Motivation` in the introduction.
   - Replace Section III.B with `Research Gap`.
   - Skip its `Technical Approach` section; the expanded version below supersedes it.
   - Use its Results, Discussion, and Conclusions and Future Work sections.
3. `03_expanded_part_IV_with_figures.tex`
   - Replace the complete former Part IV.
   - It includes five LaTeX figure blocks. Rename the image paths under `figures/`
     to match the figure names used by the manuscript.

Suggested source material for the five figures:

| Placeholder | Suggested content |
| --- | --- |
| `manifest_workflow` | The old-versus-new Omniverse workflow / manifest slide. |
| `terrain_route_slope` | Omniverse terrain screenshot with slope-colored route overlay. |
| `cad_metadata_pipeline` | The CAD submission, metadata, scaling, and SysML update diagram. |
| `isru_scenario_configuration` | A four-panel composition showing module multiplicity/routes, interfaces, equations, and DES configuration. |
| `generic_processor_behavior` | The generic Processor class / behavior / equation slide. |
