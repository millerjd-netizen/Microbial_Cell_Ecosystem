# Microbial Cell Ecosystem

This project recommends E. coli + Geobacter circuit pairs and verifies top candidates using a Tellurium simulation model with uncertainty and sensitivity reporting.

## Run CLI

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

## Tellurium Verification Visibility

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

## Calibration

A sample calibration file is provided at [user_calibration.json](user_calibration.json).

- CLI: choose `y` when asked to load calibration and press Enter to use the default path.

Calibration overrides are optional. If no calibration is provided, the app uses the default heuristic model.

## Notes

- [circuit_library.json](circuit_library.json) is the fixed dataset for this project.
- Simulation outputs are in-silico guidance and require lab validation for real-world claims.
