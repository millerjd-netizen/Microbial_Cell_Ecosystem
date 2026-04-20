# Microbial Cell Ecosystem

This project recommends E. coli + Geobacter circuit pairs and verifies top candidates using a Tellurium simulation model with uncertainty and sensitivity reporting. It also includes an iBioSim ecosystem-level SBML simulation for whole-consortium validation.

> 📎 **Additional documentation and development history:** [Claude conversation log](https://claude.ai/share/ac52b5b9-2ccf-4b47-863b-258fecca1a30)

---

## Part 1 — Tellurium CLI Tool

### Run CLI

```powershell
python .\recommend.py
```

When prompted, enter trait priorities as integers from `0` to `10`.

This project is terminal-only.

Tellurium is required for verification. If missing, the CLI exits with an error.

Install Tellurium in the active interpreter with:

```powershell
python -m pip install tellurium
```

If your active interpreter is not the project virtual environment, use:

```powershell
& ".\.venv\Scripts\python.exe" .\recommend.py
```

### Tellurium Verification Visibility

During terminal runs, the CLI now prints:

- A verification pipeline section showing each pair being simulated.
- Per-pair simulation status with runtime (`fresh` vs `cache`, seconds).
- A design-check line showing circuit-derived parameters used by Tellurium.
- An `Uncertainty & Evidence Quality Summary` section that highlights:
  - uncertainty protocol (samples/noise),
  - calibration status,
  - a pitfall warning when no empirical data is loaded,
  - per-pair confidence/agreement/interval-width risk tags.

This makes it explicit that simulation is checking the designed circuits, not only static ranking.

Calibration prompt behavior:
- Calibration remains available for future real-world data integration.
- Pressing Enter at the calibration prompt now defaults to `n` (skip) for demo-friendly runs.

### Calibration

A sample calibration file is provided at [user_calibration.json](user_calibration.json).

- CLI: choose `y` when asked to load calibration and press Enter to use the default path.

Calibration overrides are optional. If no calibration is provided, the app uses the default heuristic model.

---

## Part 2 — iBioSim Ecosystem Simulation (Optional)

For whole-consortium ecosystem validation, we use iBioSim to run SBML-based ODE simulations of the full microbial ecosystem (cross-feeding, nitrogen cascade, current output).

### Installing iBioSim

iBioSim is a free desktop application developed by the Myers Research Group (Utah/Colorado) for simulating SBML genetic circuits.

**Requirements:**
- Windows, macOS, or Linux
- Java Runtime Environment (JRE) — install from [java.com/download](https://www.java.com/download/) if missing

**Steps:**

1. Go to the iBioSim releases page: [github.com/MyersResearchGroup/iBioSim/releases](https://github.com/MyersResearchGroup/iBioSim/releases)
2. Download the zip for your OS:
   - Windows: `iBioSim-win64.zip`
   - macOS: `iBioSim-mac64.zip`
   - Linux: `iBioSim-linux64.zip`
3. Extract the zip anywhere (Desktop or `C:\` recommended — avoid OneDrive folders, paths with spaces, or special characters)
4. Launch iBioSim:
   - **Windows:** double-click `iBioSim.bat` in the top-level folder
   - **macOS/Linux:** run `./iBioSim` from the terminal in the top-level folder

**Common startup issues:**

- *Black terminal flashes then disappears:* Java isn't installed or isn't on PATH. Open Command Prompt, run `java -version`. If it errors, install Java from the link above and relaunch.
- *"WARNING: GeneNet not functional / Yosys not found":* ignore — these are optional components. Simulation works fine without them.
- *GUI doesn't appear after startup:* check `Alt+Tab` — sometimes it opens behind other windows.
- *Fonts appear tiny on Windows:* right-click `java.exe` (usually in `C:\Program Files\Java\jre\bin`) → Properties → Compatibility → "Change high DPI settings" → Override and set to "System."

### Loading the Simulation Model

The ecosystem SBML file (`whole_ecosystem.xml`) contains the full reduced-order model of the engineered consortium:
- Geobacter cross-feeding (strain A + strain B via Trp/Leu exchange)
- Electroactivity with OmcZ/EET boosters
- Nitrogen cascade (NH4 → NO2 → NO3 → N2)
- MFC current output

**Steps to load and run:**

1. **Create a project in iBioSim**
   - File → New Project
   - In the folder dialog, click "New Folder" (icon in top-right of the dialog)
   - Name it `ecosystem_sim` (or similar) → Enter → select it → click "New"
   - You should see the project appear in the left panel

2. **Import the SBML model**
   - File → Import → Model → SBML Model
   - Select `whole_ecosystem.xml` from this repository
   - It should appear under your project on the left panel
   - Double-click it to open — you'll see the network diagram in the Schematic view

3. **Create a simulation analysis**
   - Right-click `whole_ecosystem.xml` in the left panel → Create Analysis View
   - Enter analysis ID: `sim1` → OK
   - A new `sim1` tab opens with Simulation Options

4. **Configure and run**
   - Analysis Type: ODE
   - Simulator: Runge-Kutta-Fehlberg (Hierarchical)
   - Initial Time: 0
   - Time Limit: 100
   - Print Interval: 1
   - Click the green ▶ play button (top toolbar)
   - Wait for "Total Simulation Time: X seconds" in the bottom log

5. **View results**
   - Click the TSD Graph tab
   - Click "Click here to create graph"
   - In the Edit Graph dialog, expand `run-1` in the left tree
   - Check the species you want to plot — recommended: **GA, GB, Trp, Leu, Current, NH4, NO2, NO3, N2**
   - Set colors via the Color dropdowns (optional)
   - Click OK → the time-course plot renders

**Expected ecosystem dynamics:**
- NH4 drops exponentially from 10 → ~0 (ammonia consumption)
- NO2 peaks around t=10-15, then falls (intermediate)
- NO3 peaks around t=20-25, then falls (intermediate)
- N2 rises steadily to ~10 (end-product, mass-conserved with NH4 input)
- Geobacter strains (GA, GB) stabilize at low steady-state
- Current rises to a stable plateau

### Tuning Parameters (if needed)

If the simulation is unstable (populations blow up exponentially), the growth rates are likely too high relative to death rates. Stable default values:

| Parameter | Value |
|---|---|
| `k_GA_growth`, `k_GB_growth` | 0.04 |
| `k_GA_death`, `k_GB_death` | 0.15 |
| `k_current` | 0.02 |
| `k_trp_prod`, `k_leu_prod` | 0.15 |
| `k_nh4_no2` | 0.15 |
| `k_no2_no3` | 0.12 |
| `k_no3_n2` | 0.08 |
| `boostA`, `boostB` | 1.5, 1.3 |

**To edit parameters in iBioSim:**
- Click the `whole_ecosystem.xml` tab → Constants tab
- Double-click any parameter → change Initial Value → OK
- Ctrl+S to save
- Switch to `sim1` tab → hit green ▶ → TSD Graph → check new plot

### Sharing the Project With Teammates

To share the iBioSim project with collaborators:

1. Close iBioSim
2. Open File Explorer → navigate to your project's parent folder
3. Right-click the project folder (e.g. `ecosystem_sim`) → Send to → Compressed (zipped) folder
4. Share the resulting `.zip` file

Collaborators install iBioSim (steps above), then: File → Open Project → select the unzipped folder → run as above.

---

## Notes

- [circuit_library.json](circuit_library.json) is the fixed dataset for this project.
- Simulation outputs are in-silico guidance and require lab validation for real-world claims.
- The iBioSim reduced-order ecosystem model uses qualitative parameter values; full kinetic parameterization is future work.
- For development notes, design decisions, and troubleshooting history, see the [Claude conversation log](https://claude.ai/share/ac52b5b9-2ccf-4b47-863b-258fecca1a30).
