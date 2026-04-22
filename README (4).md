# 🧬 Microbial Cell Ecosystem — BE/EC 552 Final Project

**Spring 2026 · Prof. Douglas Densmore**
**Team:** Jonathan · Jaleel · William · Nora

A tunable engineered microbial consortium for MFC-driven wastewater treatment. This repo holds the three deliverables of our project: a Knox-derived genetic circuit library, an interactive tuning GUI, and an iBioSim ecosystem simulation.

---

## 📁 What's in this repo

| File | What it is |
|---|---|
| `ConsortiumTuner.ipynb` | Interactive Jupyter GUI — 7 sliders, 20-circuit scoring engine |
| `images/` | 14 Knox design-space screenshots used by the GUI |
| `whole_ecosystem.xml` | SBML model of the consortium — imports into iBioSim |
| `README.md` | This file |

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

## 🎛️ The GUI — `ConsortiumTuner.ipynb`

### What it does

A Jupyter notebook with 7 interactive sliders. As you move them, the notebook ranks the 20 circuits against your priorities and outputs:

1. A table of the selected consortium with GOLDBAR specs
2. A grid of Knox design-space screenshots for each selected circuit
3. A horizontal fitness bar chart
4. An ecosystem summary by category

### How the scoring works

Each circuit has a 7-element score vector — one number per slider axis. All circuits use **equal weighting** (score of 1.0 on the axis they were designed for, 0.0 elsewhere).

For each circuit, the fitness is:

```
fitness(circuit) = Σᵢ weightᵢ × scoreᵢ
```

where `weightᵢ` is the slider position (0.0–1.0) for axis i. Circuits above the threshold slider are selected. **Dependency closure** pulls in prerequisite circuits automatically — e.g. selecting `KillSwitch_StrainA` also adds `StrainA_Gsulfurreducens`; `Nitrobacter` requires `Nitrosomonas`; `Paracoccus_denitrificans` requires `Pseudomonas_stutzeri`.

### The 7 slider axes

| Slider | Module | Circuits |
|---|---|---|
| Cross-feeding | Obligate amino acid mutualism | StrainA/B, Ecoli_L/K/Trp/His |
| Kill switch | MazE/MazF biosafety | KillSwitch_A/B |
| Electroactivity | EET + current output | OmcZ_Booster, EET_Booster |
| Nitrification | NH₄⁺ → NO₃⁻ | Nitrosomonas, Nitrobacter |
| Denitrification | NO₃⁻ → N₂ | Pseudomonas, Paracoccus |
| Production | Secondary metabolites | ProdLyc, ProdIso, ProdNar, ProdMal |
| Quorum sensing | Cell-density coordination | LuxR, LuxS |

### How to run the GUI

**Option A — Google Colab (easiest):**

1. Open Colab at [colab.research.google.com](https://colab.research.google.com)
2. File → Upload notebook → `ConsortiumTuner.ipynb`
3. In the left sidebar, click the folder icon 📁
4. Drag the `images/` folder into the sidebar
5. Add a new cell at the top and run:
   ```python
   from google.colab import output
   output.enable_custom_widget_manager()
   ```
6. Runtime → Run all
7. Scroll to the sliders section — move the knobs, watch the output update live

**Option B — Local Jupyter:**

```bash
git clone <this-repo>
cd <this-repo>
pip install jupyter ipywidgets matplotlib numpy
jupyter notebook ConsortiumTuner.ipynb
```

Then Cell → Run All.

### Honest limitations

- Scores are **design-intent weights**, not experimental measurements
- Every circuit equally weighted (1.0 on its axis) — doesn't reflect that some circuits contribute more strongly than others in practice
- The image grid shows Knox design spaces, not actual simulation output — for dynamics see the iBioSim model below

---

## 🔬 The iBioSim Simulation — `whole_ecosystem.xml`

### What it models

A reduced-order SBML ecosystem model of the engineered consortium:

- **9 species:** GA (Geobacter A biomass), GB (Geobacter B biomass), Trp, Leu, Current, NH4, NO2, NO3, N2
- **10 reactions:** cross-feeding production, growth, death, current generation, and the full nitrogen cascade
- **12 parameters** with names tied to the Knox circuits — e.g. `boostA` corresponds to the `OmcZ_Booster_StrainA` circuit, `k_current` corresponds to the EET boosters

**What the file is:** a hand-written SBML (Systems Biology Markup Language) model. Knox does not export SBML automatically, so the file was constructed to represent the ecosystem-level behavior of the Knox circuit library. Each circuit maps to a named parameter rather than being simulated gene-by-gene.

### Installing iBioSim

1. Download iBioSim from the [GitHub releases page](https://github.com/MyersResearchGroup/iBioSim/releases)
   - Windows: `iBioSim-win64.zip`
   - macOS: `iBioSim-mac64.zip`
   - Linux: `iBioSim-linux64.zip`
2. Requires **Java Runtime Environment** — install from [java.com/download](https://www.java.com/download/) if missing
3. Extract the zip to a simple path (e.g. `C:\iBioSim\` on Windows — avoid OneDrive paths and paths with spaces)

### Launching iBioSim (Windows)

The double-click launcher often fails silently. The reliable method is via Command Prompt:

```cmd
cd C:\Users\<you>\Downloads\iBioSim-win64\iBioSim-win64
iBioSim.bat
```

Keep the Command Prompt window open — closing it closes iBioSim. If you see warnings about `GeneNet not functional` or `Yosys not found`, ignore them — those are optional components.

### Importing the SBML model

1. **Create a project:**
   - File → New Project
   - Create a new folder (e.g. `ecosystem_sim`) and select it

2. **Copy the SBML file into the project:**
   - Copy `whole_ecosystem.xml` into the project folder on your file system
   - ⚠️ On Windows, if Notepad saves it as `whole_ecosystem.xml.txt`, rename it with quotes: `"whole_ecosystem.xml"` so the extension sticks

3. **Open the model in iBioSim:**
   - Double-click `whole_ecosystem.xml` in the left panel
   - You should see the model's parameters, species, and reactions load

### Running the simulation

1. **Create an analysis:**
   - Right-click `whole_ecosystem.xml` → Create Analysis View
   - Name it `sim1` → OK

2. **Configure:**
   - Analysis Type: **ODE**
   - Simulator: **Runge-Kutta-Fehlberg (Hierarchical)**
   - Initial Time: `0`
   - Time Limit: `100`
   - Print Interval: `1`

3. **Run:**
   - Click the green ▶ play button
   - Wait for `Total Simulation Time: X seconds` to appear in the bottom log

4. **View results:**
   - Click the **TSD Graph** tab
   - Click "Click here to create graph"
   - Expand `run-1` in the left tree
   - Check the boxes for: `GA`, `GB`, `Trp`, `Leu`, `Current`, `NH4`, `NO2`, `NO3`, `N2`
   - Click OK

### Expected output

A time-course plot showing:

- **NH₄⁺** drops exponentially from 10 → ~0 (ammonia consumption)
- **NO₂⁻** peaks around t=10–15, then falls (intermediate)
- **NO₃⁻** peaks around t=20–25, then falls (intermediate)
- **N₂** rises steadily to a plateau at ~10 (end-product; mass conserved with NH₄⁺ input)
- **Leu** stabilizes at ~1 (cross-feeding steady state)
- **GA, GB, Current** low and stable

This demonstrates complete nitrogen transformation, mass balance across the cascade, and stable cross-feeding dynamics.

### Parameter reference

The 12 parameters in the model and their default values (tuned for numerical stability):

| Parameter | Value | Represents |
|---|---|---|
| `k_trp_prod` | 0.15 | Trp production rate by StrainA |
| `k_leu_prod` | 0.15 | Leu production rate by StrainB |
| `k_GA_growth` | 0.04 | Cross-feeding-driven GA growth |
| `k_GB_growth` | 0.04 | Cross-feeding-driven GB growth |
| `k_GA_death` | 0.15 | Baseline GA death |
| `k_GB_death` | 0.15 | Baseline GB death |
| `k_current` | 0.02 | Current generation coefficient |
| `boostA` | 1.5 | OmcZ_Booster_StrainA multiplier |
| `boostB` | 1.3 | EET_Booster_StrainB multiplier |
| `k_nh4_no2` | 0.15 | Nitrosomonas rate |
| `k_no2_no3` | 0.12 | Nitrobacter rate |
| `k_no3_n2` | 0.08 | Pseudomonas + Paracoccus combined rate |

These are **qualitative heuristics**, not kinetic constants from literature. Empirical parameterization is future work.

---

## 🔍 Honest Limitations

For full scientific transparency:

1. **SBML is hand-written.** Knox did not auto-export to SBML. The model abstracts circuit-level detail into ecosystem-level parameters.
2. **Parameters are qualitative.** No kinetic constants from literature or experiment — values were tuned for numerical stability.
3. **No spatial structure.** Real MFC reactors require spatial separation (aerobic cathode chamber for nitrifiers, anaerobic anode for Geobacter). The model is well-mixed.
4. **No oxygen.** The biggest real-world constraint for this consortium (nitrifiers need O₂, Geobacter cannot tolerate it) is not represented.
5. **Not every Knox circuit becomes its own SBML species.** The 20 circuits in the GUI are represented collectively via the 12 parameters in the model.

---

## 👥 Attribution

| Contributor | Scope |
|---|---|
| **Jonathan** | Knox circuit library · SBML model · iBioSim simulation |
| **Jaleel** | Tuner scoring engine |
| **William** | Tellurium verification CLI |
| **Nora** | Ecosystem ODE · production & QS modules |

---

## 📚 References

- Knox: [https://github.com/MyersResearchGroup/Knox](https://github.com/MyersResearchGroup/Knox)
- iBioSim: [https://github.com/MyersResearchGroup/iBioSim](https://github.com/MyersResearchGroup/iBioSim)
- SBML specification: [https://sbml.org](https://sbml.org)
