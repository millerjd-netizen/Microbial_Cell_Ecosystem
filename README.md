# 🧬 Microbial Cell Ecosystem — BE/EC 552 Final Project

<div align="center">

## 🎛️ [**▶ Launch the Live GUI**](https://binary-depth-63163549.figma.site/)

### *This is the main entry point for the project — start here.*

</div>

---

**Spring 2026 · Prof. Douglas Densmore**
**Team:** Jonathan · Jaleel · William · Nora

A tunable engineered microbial consortium for MFC-driven wastewater treatment. This repo holds every deliverable of the project: a Knox-derived genetic circuit library, an interactive tuning GUI (web + Jupyter versions), an iBioSim ecosystem simulation, and the supporting documentation.

---

## 📁 What's in this repo

| File / Folder | What it is |
|---|---|
| 🎛️ **[Live GUI ↗](https://binary-depth-63163549.figma.site/)** | **Main deliverable.** Interactive React + TypeScript dashboard — six module sliders, three preset buttons, live GOLDBAR specs, and an embedded SBML simulator running the 33-species ODE model in-browser. Use this link to interact with the project. |
| `Design ConsortiumTuner Dashboard UI/` | Source code for the live GUI — React + TypeScript + Radix UI components. This is what powers the Figma-hosted site above. |
| `ConsortiumTuner_v3_fixed.ipynb` | Jupyter version of the tuner. Same 20-circuit library and scoring engine as the GUI, exposed through `ipywidgets` sliders. Best run on a live kernel (Colab, Binder, or local Jupyter); GitHub's static preview can't render the sliders interactively. |
| `whole_ecosystem.xml` | SBML model of the full consortium (33 species). Authored in iBioSim and consumed by both the GUI's in-browser simulator and the notebook's ODE solver. |
| `genetic circuits chosen.xlsx` | Catalog of all 20 candidate genetic circuits — names, organisms, modules, and the scoring inputs both the GUI and notebook read from. The source of truth for the circuit library. |
| `Literature Review.docx` | Background research and citations supporting the project's design choices. |
| `Microbial_Cell_Ecosystem Final Project Report.pdf` | Full written project report — formal writeup of methodology, results, and conclusions. |
| `Microbial_Cell_Ecosystem_FinalPresentation.pptx` | Slide deck used for the in-class final presentation. |
| `README.md` | This file. |

---

## 🧪 The 20 Engineered Circuit Modules

All circuits were designed in **Knox** using **GOLDBAR** grammars. They are organized into seven functional categories. Every circuit is equally weighted in the GUI (score = 1.0 on its designed axis).

### Cross-feeding (6 circuits)

Obligate amino acid mutualism — each strain produces one amino acid and requires another, creating a cheater-proof consortium.

| Circuit | Organism | GOLDBAR | Role |
|---|---|---|---|
| `StrainA_Gsulfurreducens` | *Geobacter sulfurreducens* | `Ptrc then RBS1 then trpB then Term1` | Tryptophan producer, leucine auxotroph |
| `StrainB_Gmetallireducens` | *Geobacter metallireducens* | `PnifH then RBS2 then leuA then Term2` | Leucine producer, tryptophan auxotroph |
| `Ecoli_L` | *E. coli* (leu+/lys−) | `Ptrc then RBS1 then leuB then leuC then leuD then T1` | Leucine producer, lysine auxotroph |
| `Ecoli_K` | *E. coli* (lys+/leu−) | `Ptrc then RBS2 then lysC then argD then lysA then T2` | Lysine producer, leucine auxotroph |
| `Ecoli_Trp` | *E. coli* (trp+/his−) | `Ptrc then RBS1 then trpA then trpB then T1` | Tryptophan producer, histidine auxotroph |
| `Ecoli_His` | *E. coli* (his+/trp−) | `Ptrc then RBS2 then hisA then hisB then T2` | Histidine producer, tryptophan auxotroph |

### Kill switches (2 circuits)

Toxin–antitoxin enforcement — if cross-feeding partners disappear, the strain self-destructs.

| Circuit | GOLDBAR | Role |
|---|---|---|
| `KillSwitch_StrainA` | `Pconst → RBS1 → mazE → Term1 → Prep → RBS1 → mazF → Term1` | MazE antitoxin + MazF toxin on StrainA |
| `KillSwitch_StrainB` | `Pconst → RBS2 → mazE → Term2 → Prep → RBS2 → mazF → Term2` | Orthogonal parts to prevent recombination |

### Electroactivity (2 circuits)

Overexpresses extracellular electron transfer (EET) cytochromes to amplify anode current.

| Circuit | GOLDBAR | Role |
|---|---|---|
| `OmcZ_Booster_StrainA` | `PomcZ then RBS1 then omcZ then Term1` | Overexpresses OmcZ (dominant cytochrome in *G. sulfurreducens*) |
| `EET_Booster_StrainB` | `PimcH then RBS2 then imcH then Term2` | Native ImcH for high-potential acceptor respiration in *G. metallireducens* |

### Nitrification (2 circuits)

Oxidizes ammonia stepwise: NH₄⁺ → NO₂⁻ → NO₃⁻

| Circuit | GOLDBAR | Role |
|---|---|---|
| `Nitrosomonas` | `Ptrc then RBS1 then amoA then hao then T1` | Ammonia monooxygenase + hydroxylamine oxidoreductase |
| `Nitrobacter` | `Ptrc then RBS2 then nxrA then T2` | Nitrite oxidoreductase |

### Denitrification (2 circuits)

Reduces nitrate to inert N₂ gas: NO₃⁻ → NO₂⁻ → NO → N₂

| Circuit | GOLDBAR | Role |
|---|---|---|
| `Pseudomonas_stutzeri` | `Ptrc then RBS1 then narG then nirS then T1` | Nitrate + nitrite reductases |
| `Paracoccus_denitrificans` | `Ptrc then RBS2 then norB then nosZ then T2` | NO + N₂O reductases — completes cascade to N₂ |

### Production (4 circuits)

Secondary metabolite biosynthesis — adds economic value on top of wastewater treatment.

| Circuit | GOLDBAR | Product |
|---|---|---|
| `ProdLyc` | `Ptrc then RBS1 then crtE then crtB then crtI then T1` | Lycopene (red carotenoid) |
| `ProdIso` | `Ptrc then RBS2 then idi then ispA then T2` | Isoprenoid (terpene precursor) |
| `ProdNar` | `Ptrc then RBS1 then pal then 4cl then chs then chi then T1` | Naringenin (flavonoid) |
| `ProdMal` | `Ptrc then RBS2 then accA then accB then accC then accD then T2` | Malonyl-CoA (polyketide precursor) |

### Quorum sensing (2 circuits)

Cell-density coordination — allows the consortium to synchronize behavior.

| Circuit | GOLDBAR | Role |
|---|---|---|
| `LuxR_circuit` | `Ptrc then RBS1 then luxR then luxI then T1` | AHL production + sensing (Gram-negative QS) |
| `LuxS_circuit` | `Ptrc then RBS2 then luxS then T2` | AI-2 production (universal interspecies QS) |

---

## 🌐 The Web GUI — Figma Site

The live site linked at the top of this README (`binary-depth-63163549.figma.site`) is a **React + TypeScript** port of the Jupyter notebook, built as a single-page app with **Radix UI** sliders and a dark dashboard layout. It collapses the notebook's seven axes into six module knobs — `cross_feeding`, `nitrogen_cycle`, `electrogenesis`, `quorum_sensing`, `kill_switch`, and `metabolite_production` (nitrification and denitrification are merged into one `nitrogen_cycle` slider for compactness) — and runs the same fitness-scoring and dependency-closure logic over the 20-circuit library: any circuit whose category weight is above zero is selected, and prerequisites (e.g. `KillSwitch_StrainA` pulling in `StrainA_Gsulfurreducens`, `Nitrobacter` pulling in `Nitrosomonas`) are added automatically. Three preset buttons — **Max MFC current**, **N removal**, and **Production** — snap the sliders to canonical configurations, and every slider edit rebuilds three live tables in place: the chosen consortium with module-color-coded scores, the GOLDBAR genetic-part specifications for each circuit, and an ecosystem summary tallying circuits per module. An embedded `<SBMLSimulator />` component runs the 33-species ODE model in-browser, so the same slider edits drive both the design view and the dynamics view without leaving the page.

---

## 🎛️ The Jupyter GUI — `ConsortiumTuner.ipynb`

### What it does

A Jupyter notebook with 7 interactive sliders. As you move them, the notebook ranks the 20 circuits against your priorities and outputs:

1. A table of the selected consortium with GOLDBAR specs
2. A grid of Knox design-space screenshots for each selected circuit
3. A horizontal fitness bar chart
4. An ecosystem summary by category

### How the scoring works

Each circuit has a 7-element score vector — one number per slider axis. All circuits use **equal weighting** (score of 1.0 on the axis they were designed for, 0.0 elsewhere).

For each circuit, the fitness is:
