import json
import os
import random
import hashlib
import time
import sys

LIBRARY_PATH = "circuit_library.json"
VERIFICATION_TOP_N = 3
SIMULATION_HOURS = 48
SIMULATION_STEPS = 241
UNCERTAINTY_ENABLED = True
UNCERTAINTY_SAMPLES = 20
UNCERTAINTY_NOISE_STD = 0.20
SENSITIVITY_ENABLED = True
SENSITIVITY_DELTA = 0.12
SENSITIVITY_KEYS = ["mu_e", "mu_g", "prod_eg", "prod_ge"]
DEFAULT_CALIBRATION_PATH = "user_calibration.json"

MODEL_PARAMETER_KEYS = {
    "mu_e", "mu_g", "d_e", "d_g", "prod_eg", "prod_ge", "cons_eg", "cons_ge",
    "loss_eg", "loss_ge", "K_eg", "K_ge", "K_e", "K_g", "ks_e", "ks_g",
    "h_prod_e", "h_prod_g", "h_decay", "electron_transfer_coeff",
    "E0", "G0", "MEG0", "MGE0", "H0"
}

WEIGHT_MAP = {
    "none":   0,
    "low":    1,
    "medium": 5,
    "high":   10
}

CATEGORY_LABELS = {
    "electron_donation":      "Electron Donation",
    "auxotrophic_crossfeeding": "Auxotrophic Crossfeeding",
    "hydrogen_generation":    "Hydrogen Generation",
    "evolutionary_resistance": "Evolutionary Resistance"
}

SEVERITY_PENALTY = {
    "severe": 25,
    "medium": 10,
    "info": 0
}

try:
    import tellurium as te
    TELLURIUM_AVAILABLE = True
    TELLURIUM_IMPORT_ERROR = ""
except Exception as exc:
    te = None
    TELLURIUM_AVAILABLE = False
    TELLURIUM_IMPORT_ERROR = str(exc)

SIMULATION_CACHE = {}

PROMOTER_ACTIVITY = {
    "Pconst": 0.90,
    "Ptrc": 1.00,
    "PnifH": 0.86,
    "PomcZ": 1.08,
    "Prep": 0.72,
    "Phyd": 0.95
}

RBS_ACTIVITY = {
    "RBS1": 1.00,
    "RBS2": 1.00
}

def score_label(score):
    if score >= 7:   return "High"
    elif score >= 4: return "Medium"
    else:            return "Low"

def percentile(values, pct):
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * pct
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    if low == high:
        return ordered[low]
    weight = position - low
    return ordered[low] * (1 - weight) + ordered[high] * weight

def verdict_label(status, agreement_pct):
    if status == "STABLE":
        return "Likely Stable" if agreement_pct >= 65 else "Uncertain"
    if status == "UNSTABLE":
        return "Likely Unstable" if agreement_pct >= 65 else "Uncertain"
    return "Uncertain"

def uncertainty_tier(agreement_pct, interval_low, interval_high):
    width = interval_high - interval_low
    if agreement_pct >= 80 and width <= 20:
        return "High"
    if agreement_pct >= 65 and width <= 35:
        return "Medium"
    return "Low"

def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))

def normalize_trait(score):
    return clamp(score / 10.0, 0.0, 1.0)

def model_limitations_message():
    return (
        "Simulation note: in-silico verification uses uncertain kinetic assumptions; "
        "treat results as hypothesis-level guidance, not lab guarantees."
    )

def calibration_guidance_message():
    return (
        "Accuracy upgrade: provide calibration data (measured rates/outcomes) to override "
        "heuristic parameters for stronger confidence."
    )

def runtime_python_message():
    return f"Python runtime: {sys.executable}"

def uncertainty_terminal_message():
    return (
        "Uncertainty handling: each simulated pair is stress-tested with parameter perturbations "
        f"({UNCERTAINTY_SAMPLES} runs, {int(UNCERTAINTY_NOISE_STD*100)}% noise) to estimate confidence bounds."
    )

def tellurium_runtime_details():
    if TELLURIUM_AVAILABLE:
        version = getattr(te, "__version__", "unknown")
        return (
            "Tellurium runtime detected "
            f"(version {version}). Dynamic simulation will run for top {VERIFICATION_TOP_N} pairs."
        )
    return (
        "Tellurium runtime REQUIRED but missing in this interpreter. Install in active environment with: "
        f"\"{sys.executable}\" -m pip install tellurium"
    )

def require_tellurium():
    if TELLURIUM_AVAILABLE:
        return
    raise RuntimeError(
        "Tellurium is required for design verification but is not available in active interpreter "
        f"({sys.executable}). Install with: \"{sys.executable}\" -m pip install tellurium"
    )

def score_max_raw(weights):
    total_weight = sum(float(max(0.0, weights.get(key, 0.0))) for key in CATEGORY_LABELS)
    return 10.0 * total_weight

def to_percent(raw_value, max_raw):
    if max_raw <= 0:
        return 0.0
    return round((100.0 * float(raw_value)) / float(max_raw), 2)

def sanitize_parameter_overrides(overrides):
    clean = {}
    ignored = []
    if not isinstance(overrides, dict):
        return clean, ignored

    for key, value in overrides.items():
        if key not in MODEL_PARAMETER_KEYS:
            ignored.append(key)
            continue
        if not isinstance(value, (int, float)):
            ignored.append(key)
            continue
        clean[key] = float(value)
    return clean, ignored

def calibration_cache_token(calibration):
    if not calibration:
        return "none"
    payload = json.dumps(
        {
            "global_overrides": calibration.get("global_overrides", {}),
            "pair_overrides": calibration.get("pair_overrides", {})
        },
        sort_keys=True
    )
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]

def load_calibration_data(path):
    if not os.path.exists(path):
        return None, f"Calibration file not found: {path}"

    try:
        with open(path) as f:
            raw = json.load(f)
    except Exception as exc:
        return None, f"Failed to read calibration JSON ({path}): {exc}"

    return load_calibration_from_dict(raw, source_name=path)

def load_calibration_from_dict(raw, source_name="inline calibration"):
    global_overrides = {}
    ignored_fields = []
    pair_overrides = {}

    if isinstance(raw, dict):
        if "global_parameter_overrides" in raw:
            global_overrides, ignored_global = sanitize_parameter_overrides(raw.get("global_parameter_overrides", {}))
            ignored_fields.extend(ignored_global)
        else:
            inferred_global, ignored_inferred = sanitize_parameter_overrides(raw)
            global_overrides.update(inferred_global)
            ignored_fields.extend(ignored_inferred)

        raw_pair_overrides = raw.get("pair_overrides", {})
        if isinstance(raw_pair_overrides, dict):
            for pair_id, override_map in raw_pair_overrides.items():
                clean_map, ignored_pair = sanitize_parameter_overrides(override_map)
                if clean_map:
                    pair_overrides[str(pair_id)] = clean_map
                ignored_fields.extend([f"{pair_id}.{field}" for field in ignored_pair])

    calibration = {
        "source_path": source_name,
        "global_overrides": global_overrides,
        "pair_overrides": pair_overrides,
        "ignored_fields": ignored_fields
    }
    calibration["cache_token"] = calibration_cache_token(calibration)
    return calibration, None

def validate_weights(weights):
    if not isinstance(weights, dict):
        raise ValueError("weights must be a dictionary keyed by category.")

    missing = [key for key in CATEGORY_LABELS if key not in weights]
    if missing:
        raise ValueError(f"weights missing required categories: {', '.join(missing)}")

    validated = {}
    for key in CATEGORY_LABELS:
        value = weights[key]
        if not isinstance(value, (int, float)):
            raise ValueError(f"weight for {key} must be numeric.")
        if value < 0:
            raise ValueError(f"weight for {key} must be >= 0.")
        if value > 10:
            raise ValueError(f"weight for {key} must be <= 10.")
        validated[key] = float(value)
    return validated

def weights_from_labels(label_weights):
    if not isinstance(label_weights, dict):
        raise ValueError("label_weights must be a dictionary keyed by category.")

    mapped = {}
    for key in CATEGORY_LABELS:
        if key not in label_weights:
            raise ValueError(f"label_weights missing required category: {key}")
        label = str(label_weights[key]).strip().lower()
        if label not in WEIGHT_MAP:
            raise ValueError(
                f"invalid weight label '{label}' for {key}. "
                "Use one of: none, low, medium, high."
            )
        mapped[key] = float(WEIGHT_MAP[label])
    return mapped

def run_recommender(weights, calibration=None, library=None, top_n=3, verify_top_n=VERIFICATION_TOP_N):
    validated_weights = validate_weights(weights)
    active_library = library if library is not None else load_library(LIBRARY_PATH)
    verify_count = max(0, int(verify_top_n))
    if verify_count > 0:
        require_tellurium()

    ranked_pairs = build_pair_recommendations(active_library, validated_weights)
    if not ranked_pairs:
        return {
            "weights": validated_weights,
            "ranked_pairs": [],
            "top_pairs": [],
            "total_pairs": 0,
            "verify_top_n": 0,
            "top_n": max(1, int(top_n)),
            "calibration_loaded": bool(calibration)
        }

    ranked_pairs = attach_verification_to_top_pairs(
        ranked_pairs,
        top_n=min(verify_count, len(ranked_pairs)),
        calibration=calibration
    )

    top_count = max(1, int(top_n))
    return {
        "weights": validated_weights,
        "ranked_pairs": ranked_pairs,
        "top_pairs": ranked_pairs[:min(top_count, len(ranked_pairs))],
        "total_pairs": len(ranked_pairs),
        "verify_top_n": min(verify_count, len(ranked_pairs)),
        "top_n": top_count,
        "calibration_loaded": bool(calibration)
    }

def get_calibration_for_session():
    if not get_yes_no_default(
        "\nLoad optional user calibration data to improve prediction confidence? (y/n, default n): ",
        default=False,
    ):
        print("  Calibration skipped (default theoretical parameter set).")
        return None

    user_path = input(
        f"  Calibration JSON path (press Enter for {DEFAULT_CALIBRATION_PATH}): "
    ).strip()
    path = user_path or DEFAULT_CALIBRATION_PATH

    calibration, error = load_calibration_data(path)
    if error:
        print(f"  Calibration unavailable: {error}")
        print("  Continuing with default heuristic model.")
        return None

    global_count = len(calibration["global_overrides"])
    pair_count = len(calibration["pair_overrides"])
    ignored_count = len(calibration["ignored_fields"])
    print(
        "  Calibration loaded: "
        f"{global_count} global override(s), {pair_count} pair-specific map(s)."
    )
    if ignored_count:
        print(f"  Note: ignored {ignored_count} unsupported/non-numeric calibration field(s).")
    return calibration

def apply_calibration_to_params(pair, base_params, calibration):
    if not calibration:
        return dict(base_params), []

    updated = dict(base_params)
    applied = []

    for key, value in calibration.get("global_overrides", {}).items():
        updated[key] = max(1e-6, float(value))
        applied.append(f"global:{key}")

    pair_specific = calibration.get("pair_overrides", {}).get(pair["pair_id"], {})
    for key, value in pair_specific.items():
        updated[key] = max(1e-6, float(value))
        applied.append(f"pair:{key}")

    return updated, applied

def load_library(path):
    if not os.path.exists(path):
        print(f"ERROR: Could not find {path}")
        print("Make sure circuit_library.json is in the same folder as recommend.py")
        exit(1)
    with open(path) as f:
        library = json.load(f)
    print(f"Loading circuit library... {len(library)} circuits loaded.")
    return library

def get_user_weights():
    print("\nHow important is each trait to you?")
    print("Enter an integer from 0 to 10 for each trait (0 = lowest priority, 10 = highest).\n")
    weights = {}
    for key, label in CATEGORY_LABELS.items():
        while True:
            val = input(f"  {label:30s}: ").strip()
            try:
                score = int(val)
            except ValueError:
                print("  Invalid input. Please enter an integer from 0 to 10.")
                continue

            if 0 <= score <= 10:
                weights[key] = score
                break
            print("  Invalid input. Please enter an integer from 0 to 10.")
    return weights

def get_yes_no(prompt):
    while True:
        response = input(prompt).strip().lower()
        if response in {"y", "n"}:
            return response == "y"
        print("  Invalid input. Please enter y or n.")

def get_yes_no_default(prompt, default=False):
    while True:
        response = input(prompt).strip().lower()
        if response == "":
            return default
        if response in {"y", "n"}:
            return response == "y"
        print("  Invalid input. Please enter y or n (or press Enter for default).")

def classify_organism(organism):
    lowered = organism.lower()
    if "e. coli" in lowered or "escherichia" in lowered:
        return "ecoli"
    if "geobacter" in lowered or "g. sulfurreducens" in lowered or "g. metallireducens" in lowered:
        return "geobacter"
    return "other"

def split_by_organism(library):
    ecoli = []
    geobacter = []
    for circuit in library:
        organism_type = classify_organism(circuit["organism"])
        if organism_type == "ecoli":
            ecoli.append(circuit)
        elif organism_type == "geobacter":
            geobacter.append(circuit)
    return ecoli, geobacter

def knox_tokens(knox_spec):
    return [t.strip() for t in knox_spec.split("then") if t.strip()]

def extract_promoters(circuit):
    if circuit.get("promoters"):
        return set(circuit["promoters"])
    return {token for token in knox_tokens(circuit["knox_spec"]) if token.startswith("P")}

def evaluate_internal_compatibility(circuit):
    issues = []
    org_type = classify_organism(circuit["organism"])
    tokens = set(knox_tokens(circuit["knox_spec"]))

    if org_type == "ecoli":
        if "RBS2" in tokens or "Term2" in tokens:
            issues.append({
                "level": "severe",
                "message": (
                    f"{circuit['circuit_id']}: E. coli circuit contains Geobacter-specific "
                    "parts (RBS2/Term2)."
                )
            })
    if org_type == "geobacter":
        if "RBS1" in tokens or "Term1" in tokens:
            issues.append({
                "level": "severe",
                "message": (
                    f"{circuit['circuit_id']}: Geobacter circuit contains E. coli-specific "
                    "parts (RBS1/Term1)."
                )
            })
    return issues

def evaluate_pair_conflicts(ecoli_circuit, geobacter_circuit):
    issues = []

    shared_promoters = extract_promoters(ecoli_circuit) & extract_promoters(geobacter_circuit)
    if shared_promoters:
        promoter_list = ", ".join(sorted(shared_promoters))
        issues.append({
            "level": "medium",
            "message": (
                "Shared promoter(s) across pair: "
                f"{promoter_list}. Possible crosstalk if constructs are co-localized."
            )
        })

    for circuit in (ecoli_circuit, geobacter_circuit):
        if circuit.get("biological_warning"):
            issues.append({
                "level": "info",
                "message": f"{circuit['circuit_id']}: {circuit['biological_warning']}"
            })

    return issues

def combine_pair_traits(ecoli_circuit, geobacter_circuit):
    e_cat = ecoli_circuit["categories"]
    g_cat = geobacter_circuit["categories"]

    combined = {
        # Geobacter usually dominates direct electron transfer to the anode.
        "electron_donation": round(0.25 * e_cat["electron_donation"] + 0.75 * g_cat["electron_donation"], 2),
        # Cross-feeding is strongest when both partners contribute, so use the weaker link.
        "auxotrophic_crossfeeding": min(e_cat["auxotrophic_crossfeeding"], g_cat["auxotrophic_crossfeeding"]),
        # Hydrogen generation can come from either partner's pathway.
        "hydrogen_generation": max(e_cat["hydrogen_generation"], g_cat["hydrogen_generation"]),
        # Consortium stability depends on both strains.
        "evolutionary_resistance": round(
            0.5 * e_cat["evolutionary_resistance"] + 0.5 * g_cat["evolutionary_resistance"],
            2
        )
    }
    return combined

def weighted_score(categories, weights):
    return sum(weights.get(cat, 0) * categories.get(cat, 0) for cat in weights)

def circuit_design_profile(circuit):
    token_set = set(knox_tokens(circuit["knox_spec"]))
    promoters = extract_promoters(circuit)
    genes = {g.lower() for g in circuit.get("genes", [])}

    promoter_values = [PROMOTER_ACTIVITY.get(p, 0.85) for p in promoters] or [0.85]
    rbs_tokens = [token for token in token_set if token.startswith("RBS")]
    rbs_values = [RBS_ACTIVITY.get(token, 1.0) for token in rbs_tokens] or [1.0]

    expression_drive = clamp(
        (sum(promoter_values) / len(promoter_values))
        * (sum(rbs_values) / len(rbs_values)),
        0.5,
        1.4
    )

    crossfeed_signal = 0.25
    if {"leua", "leub", "leuc", "leud"} & genes:
        crossfeed_signal += 0.35
    if {"lysc", "argd"} & genes:
        crossfeed_signal += 0.22
    if "trpb" in genes:
        crossfeed_signal += 0.45

    electron_signal = 0.20
    if "omcz" in genes:
        electron_signal += 0.70
    if "hyab" in genes:
        electron_signal += 0.25

    hydrogen_signal = 0.10
    if "hyda" in genes:
        hydrogen_signal += 0.65
    if "hyab" in genes:
        hydrogen_signal += 0.35

    has_hyda = "hyda" in genes
    has_hyd_maturases = {"hyde", "hydf", "hydg"}.issubset(genes)
    hydrogen_maturity = 1.0
    if has_hyda and not has_hyd_maturases:
        hydrogen_maturity = 0.35

    stability_signal = 0.20
    killswitch_signal = 0.00
    if "maze" in genes:
        stability_signal += 0.25
    if "mazf" in genes:
        stability_signal += 0.30
        killswitch_signal += 0.55
    if "maze" in genes and "mazf" in genes:
        killswitch_signal += 0.25

    return {
        "expression_drive": expression_drive,
        "crossfeed_signal": clamp(crossfeed_signal, 0.0, 1.2),
        "electron_signal": clamp(electron_signal, 0.0, 1.3),
        "hydrogen_signal": clamp(hydrogen_signal, 0.0, 1.2),
        "hydrogen_maturity": hydrogen_maturity,
        "stability_signal": clamp(stability_signal, 0.0, 1.0),
        "killswitch_signal": clamp(killswitch_signal, 0.0, 1.0)
    }

def simulation_parameters(ecoli_circuit, geobacter_circuit, combined_categories):
    cf = normalize_trait(combined_categories["auxotrophic_crossfeeding"])
    ed = normalize_trait(combined_categories["electron_donation"])
    hg = normalize_trait(combined_categories["hydrogen_generation"])
    er = normalize_trait(combined_categories["evolutionary_resistance"])

    e_profile = circuit_design_profile(ecoli_circuit)
    g_profile = circuit_design_profile(geobacter_circuit)

    mu_e = 0.14 + 0.16 * cf + 0.05 * hg + 0.04 * e_profile["expression_drive"]
    mu_g = 0.13 + 0.16 * cf + 0.10 * ed + 0.04 * g_profile["electron_signal"]

    d_e = clamp(0.10 - 0.05 * er - 0.02 * e_profile["stability_signal"], 0.015, 0.14)
    d_g = clamp(0.10 - 0.05 * er - 0.02 * g_profile["stability_signal"], 0.015, 0.14)

    prod_eg = 0.18 + 0.85 * cf * e_profile["crossfeed_signal"] * e_profile["expression_drive"]
    prod_ge = 0.18 + 0.85 * cf * g_profile["crossfeed_signal"] * g_profile["expression_drive"]

    ks_e = clamp(0.002 + 0.05 * e_profile["killswitch_signal"] * (1.0 - er), 0.0, 0.08)
    ks_g = clamp(0.002 + 0.05 * g_profile["killswitch_signal"] * (1.0 - er), 0.0, 0.08)

    h_prod_e = 0.02 + 0.30 * hg * e_profile["hydrogen_signal"] * e_profile["hydrogen_maturity"]
    h_prod_g = 0.02 + 0.30 * hg * g_profile["hydrogen_signal"] * g_profile["hydrogen_maturity"]

    electron_transfer_coeff = 0.12 + 0.45 * ed * g_profile["electron_signal"]

    return {
        "mu_e": mu_e,
        "mu_g": mu_g,
        "d_e": d_e,
        "d_g": d_g,
        "prod_eg": prod_eg,
        "prod_ge": prod_ge,
        "cons_eg": 0.16,
        "cons_ge": 0.16,
        "loss_eg": 0.08 + 0.05 * (1.0 - er),
        "loss_ge": 0.08 + 0.05 * (1.0 - er),
        "K_eg": 0.40,
        "K_ge": 0.40,
        "K_e": 1.45 + 0.85 * er,
        "K_g": 1.45 + 0.85 * er,
        "ks_e": ks_e,
        "ks_g": ks_g,
        "h_prod_e": h_prod_e,
        "h_prod_g": h_prod_g,
        "h_decay": 0.20,
        "electron_transfer_coeff": electron_transfer_coeff,
        "E0": 0.15,
        "G0": 0.15,
        "MEG0": 0.20 + 0.35 * e_profile["crossfeed_signal"],
        "MGE0": 0.20 + 0.35 * g_profile["crossfeed_signal"],
        "H0": 0.03
    }

def build_antimony_model(params):
    return f"""
model coculture_verification()
  species E, G, M_EG, M_GE, H;

    J_growth_e: -> E; (mu_e * E * (0.25 + 0.75 * (M_GE / (K_ge + M_GE)))) * (1 - E / K_e);
  J_decay_e: E -> ; d_e * E;
  J_kill_e: E -> ; ks_e * E * (K_ge / (K_ge + M_GE));
    J_growth_g: -> G; (mu_g * G * (0.25 + 0.75 * (M_EG / (K_eg + M_EG)))) * (1 - G / K_g);
  J_decay_g: G -> ; d_g * G;
  J_kill_g: G -> ; ks_g * G * (K_eg / (K_eg + M_EG));

  J_prod_eg: -> M_EG; prod_eg * E;
  J_cons_eg: M_EG -> ; cons_eg * G * (M_EG / (K_eg + M_EG));
  J_loss_eg: M_EG -> ; loss_eg * M_EG;

  J_prod_ge: -> M_GE; prod_ge * G;
  J_cons_ge: M_GE -> ; cons_ge * E * (M_GE / (K_ge + M_GE));
  J_loss_ge: M_GE -> ; loss_ge * M_GE;

  J_hydrogen: -> H; h_prod_e * E + h_prod_g * G;
  J_hydrogen_decay: H -> ; h_decay * H;

  mu_e = {params['mu_e']};
  mu_g = {params['mu_g']};
  d_e = {params['d_e']};
  d_g = {params['d_g']};
  prod_eg = {params['prod_eg']};
  prod_ge = {params['prod_ge']};
  cons_eg = {params['cons_eg']};
  cons_ge = {params['cons_ge']};
  loss_eg = {params['loss_eg']};
  loss_ge = {params['loss_ge']};
  K_eg = {params['K_eg']};
  K_ge = {params['K_ge']};
  K_e = {params['K_e']};
  K_g = {params['K_g']};
  ks_e = {params['ks_e']};
  ks_g = {params['ks_g']};
  h_prod_e = {params['h_prod_e']};
  h_prod_g = {params['h_prod_g']};
  h_decay = {params['h_decay']};

  E = {params['E0']};
  G = {params['G0']};
  M_EG = {params['MEG0']};
  M_GE = {params['MGE0']};
  H = {params['H0']};
end
"""

def classify_simulation_result(
    initial_e,
    initial_g,
    e_values,
    g_values,
    m_eg_values,
    m_ge_values,
    coupling_signal,
    resistance_signal,
    conflict_penalty_signal
):
    final_e = e_values[-1]
    final_g = g_values[-1]
    min_e = min(e_values)
    min_g = min(g_values)
    min_m_eg = min(m_eg_values)
    min_m_ge = min(m_ge_values)

    survival_balance = min(final_e, final_g) / max(1e-9, max(final_e, final_g))
    floor_ratio = min(min_e, min_g) / max(1e-9, min(initial_e, initial_g))
    growth_ratio = min(final_e / max(1e-9, initial_e), final_g / max(1e-9, initial_g))
    nutrient_floor = min(min_m_eg, min_m_ge)
    nutrient_score = clamp(nutrient_floor / 0.12, 0.0, 1.0)

    raw_stability = (
        0.24 * clamp(floor_ratio, 0.0, 1.0)
        + 0.22 * clamp(survival_balance, 0.0, 1.0)
        + 0.14 * clamp(growth_ratio / 2.0, 0.0, 1.0)
        + 0.14 * nutrient_score
        + 0.18 * clamp(coupling_signal, 0.0, 1.0)
        + 0.08 * clamp(resistance_signal, 0.0, 1.0)
        - 0.20 * clamp(conflict_penalty_signal, 0.0, 1.0)
    )
    stability_score = round(100.0 * clamp(raw_stability, 0.0, 1.0), 2)

    if final_e < 0.03 or final_g < 0.03:
        status = "UNSTABLE"
        reason = "One population collapsed below the survival threshold."
    elif coupling_signal < 0.25:
        status = "UNSTABLE"
        reason = "Circuit pair does not provide enough cross-feeding coupling for co-culture support."
    elif nutrient_floor < 0.02:
        status = "CAUTION"
        reason = "Metabolite exchange dipped near starvation even though populations persisted."
    elif stability_score >= 72:
        status = "STABLE"
        reason = "Both populations persisted with balanced coexistence and sustained cross-feeding."
    elif stability_score >= 50:
        status = "CAUTION"
        reason = "Populations persist but show imbalance or weak resilience."
    else:
        status = "UNSTABLE"
        reason = "Co-culture coupling appears too weak for stable coexistence."

    if status == "STABLE" and conflict_penalty_signal >= 0.35:
        status = "CAUTION"
        reason = "Dynamic profile is stable, but compatibility conflicts reduce confidence."

    if status == "UNSTABLE":
        unstable_ceiling = 35.0 + 20.0 * clamp(coupling_signal, 0.0, 1.0) + 10.0 * clamp(resistance_signal, 0.0, 1.0)
        stability_score = min(stability_score, round(unstable_ceiling, 2))
    elif status == "CAUTION":
        stability_score = clamp(stability_score, 40.0, 69.99)
    else:
        stability_score = max(stability_score, 70.0)

    return status, reason, stability_score

def compute_pair_signals(pair, params):
    medium_conflicts = sum(1 for issue in pair["issues"] if issue["level"] == "medium")
    severe_conflicts = sum(1 for issue in pair["issues"] if issue["level"] == "severe")
    info_notes = sum(1 for issue in pair["issues"] if issue["level"] == "info")

    coupling_signal = clamp(
        (
            normalize_trait(pair["combined_categories"]["auxotrophic_crossfeeding"])
            + clamp((params["prod_eg"] + params["prod_ge"]) / 2.2, 0.0, 1.0)
        ) / 2.0,
        0.0,
        1.0
    )
    resistance_signal = normalize_trait(pair["combined_categories"]["evolutionary_resistance"])
    conflict_penalty_signal = clamp(
        0.45 * severe_conflicts + 0.18 * medium_conflicts + 0.05 * info_notes,
        0.0,
        1.0
    )
    return coupling_signal, resistance_signal, conflict_penalty_signal

def run_simulation_with_params(pair, params):
    rr = te.loada(build_antimony_model(params))
    rr.timeCourseSelections = ["time", "E", "G", "M_EG", "M_GE", "H"]
    result = rr.simulate(0, SIMULATION_HOURS, SIMULATION_STEPS)

    e_values = [float(v) for v in result[:, 1]]
    g_values = [float(v) for v in result[:, 2]]
    m_eg_values = [float(v) for v in result[:, 3]]
    m_ge_values = [float(v) for v in result[:, 4]]
    h_values = [float(v) for v in result[:, 5]]

    coupling_signal, resistance_signal, conflict_penalty_signal = compute_pair_signals(pair, params)

    status, reason, stability_score = classify_simulation_result(
        params["E0"],
        params["G0"],
        e_values,
        g_values,
        m_eg_values,
        m_ge_values,
        coupling_signal,
        resistance_signal,
        conflict_penalty_signal
    )

    electron_transfer_index = params["electron_transfer_coeff"] * g_values[-1]

    return {
        "status": status,
        "reason": reason,
        "stability_score": stability_score,
        "final_ecoli": round(e_values[-1], 4),
        "final_geobacter": round(g_values[-1], 4),
        "final_metabolite_eg": round(m_eg_values[-1], 4),
        "final_metabolite_ge": round(m_ge_values[-1], 4),
        "final_hydrogen": round(h_values[-1], 4),
        "electron_transfer_index": round(electron_transfer_index, 4)
    }

def perturb_parameters(base_params, rng):
    perturbed = {}
    for key, value in base_params.items():
        if not isinstance(value, (int, float)):
            perturbed[key] = value
            continue
        if key in {"E0", "G0", "MEG0", "MGE0", "H0"}:
            multiplier = rng.gauss(1.0, UNCERTAINTY_NOISE_STD / 2.0)
        else:
            multiplier = rng.gauss(1.0, UNCERTAINTY_NOISE_STD)
        perturbed[key] = max(1e-6, value * multiplier)
    return perturbed

def run_uncertainty_analysis(pair, base_params, nominal_result):
    if not UNCERTAINTY_ENABLED or UNCERTAINTY_SAMPLES <= 1:
        nominal_result["interval"] = None
        nominal_result["agreement_pct"] = 100
        nominal_result["distribution"] = {nominal_result["status"]: 1}
        nominal_result["confidence_tier"] = "Medium"
        nominal_result["verdict"] = verdict_label(nominal_result["status"], 100)
        nominal_result["sample_count"] = 1
        return nominal_result

    rng = random.Random()
    scores = [nominal_result["stability_score"]]
    statuses = [nominal_result["status"]]

    for _ in range(UNCERTAINTY_SAMPLES - 1):
        try:
            perturbed = perturb_parameters(base_params, rng)
            result = run_simulation_with_params(pair, perturbed)
            scores.append(result["stability_score"])
            statuses.append(result["status"])
        except Exception:
            continue

    counts = {}
    for label in statuses:
        counts[label] = counts.get(label, 0) + 1

    total = max(1, len(statuses))
    dominant_count = max(counts.values()) if counts else total
    agreement_pct = int(round(100.0 * dominant_count / total))

    interval_low = round(percentile(scores, 0.10), 2)
    interval_mid = round(percentile(scores, 0.50), 2)
    interval_high = round(percentile(scores, 0.90), 2)

    nominal_result["interval"] = (interval_low, interval_mid, interval_high)
    nominal_result["agreement_pct"] = agreement_pct
    nominal_result["distribution"] = counts
    nominal_result["confidence_tier"] = uncertainty_tier(agreement_pct, interval_low, interval_high)
    nominal_result["verdict"] = verdict_label(nominal_result["status"], agreement_pct)
    nominal_result["sample_count"] = total
    return nominal_result

def run_sensitivity_analysis(pair, base_params, nominal_result):
    if not SENSITIVITY_ENABLED:
        nominal_result["sensitivity"] = []
        nominal_result["brittle"] = False
        return nominal_result

    base_score = nominal_result["stability_score"]
    base_status = nominal_result["status"]
    effects = []
    brittle = False

    for key in SENSITIVITY_KEYS:
        if key not in base_params:
            continue
        deltas = []
        for direction in (-1, 1):
            perturbed = dict(base_params)
            perturbed[key] = max(1e-6, perturbed[key] * (1.0 + direction * SENSITIVITY_DELTA))
            try:
                result = run_simulation_with_params(pair, perturbed)
            except Exception:
                continue
            deltas.append(abs(result["stability_score"] - base_score))
            if result["status"] != base_status:
                brittle = True
        if deltas:
            effects.append({"parameter": key, "effect": round(sum(deltas) / len(deltas), 2)})

    effects.sort(key=lambda x: x["effect"], reverse=True)
    if effects and effects[0]["effect"] >= 12:
        brittle = True

    nominal_result["sensitivity"] = effects[:3]
    nominal_result["brittle"] = brittle
    return nominal_result

def build_design_trace(pair, params, applied_overrides):
    key_parameters = {
        key: round(float(params[key]), 4)
        for key in ["mu_e", "mu_g", "prod_eg", "prod_ge", "h_prod_e", "h_prod_g", "electron_transfer_coeff"]
    }

    return {
        "ecoli_circuit_id": pair["ecoli"]["circuit_id"],
        "geobacter_circuit_id": pair["geobacter"]["circuit_id"],
        "ecoli_knox_spec": pair["ecoli"]["knox_spec"],
        "geobacter_knox_spec": pair["geobacter"]["knox_spec"],
        "ecoli_genes": pair["ecoli"].get("genes", []),
        "geobacter_genes": pair["geobacter"].get("genes", []),
        "ecoli_promoters": pair["ecoli"].get("promoters", []),
        "geobacter_promoters": pair["geobacter"].get("promoters", []),
        "key_parameters": key_parameters,
        "applied_overrides": list(applied_overrides),
    }

def run_tellurium_verification(pair, calibration=None):
    require_tellurium()

    base_params = simulation_parameters(
        pair["ecoli"],
        pair["geobacter"],
        pair["combined_categories"]
    )
    calibrated_params, applied_overrides = apply_calibration_to_params(pair, base_params, calibration)
    design_trace = build_design_trace(pair, calibrated_params, applied_overrides)

    try:
        nominal_result = run_simulation_with_params(pair, calibrated_params)
        nominal_result = run_uncertainty_analysis(pair, calibrated_params, nominal_result)
        nominal_result = run_sensitivity_analysis(pair, calibrated_params, nominal_result)
        nominal_result["calibrated"] = bool(applied_overrides)
        nominal_result["calibration_source"] = calibration.get("source_path") if applied_overrides and calibration else None
        nominal_result["applied_overrides"] = applied_overrides
        nominal_result["design_trace"] = design_trace
        return nominal_result
    except Exception as exc:
        return {
            "status": "UNAVAILABLE",
            "reason": f"Tellurium simulation failed: {exc}",
            "stability_score": None,
            "final_ecoli": None,
            "final_geobacter": None,
            "final_metabolite_eg": None,
            "final_metabolite_ge": None,
            "final_hydrogen": None,
            "electron_transfer_index": None,
            "interval": None,
            "agreement_pct": None,
            "distribution": None,
            "confidence_tier": None,
            "verdict": "Uncertain",
            "sample_count": 0,
            "sensitivity": [],
            "brittle": False,
            "calibrated": False,
            "calibration_source": None,
            "applied_overrides": [],
            "design_trace": design_trace
        }

def verify_pair(pair, calibration=None, include_cache_status=False):
    combined = pair["combined_categories"]
    cache_key = (
        pair["pair_id"],
        tuple(round(combined[k], 3) for k in CATEGORY_LABELS),
        UNCERTAINTY_ENABLED,
        UNCERTAINTY_SAMPLES,
        round(UNCERTAINTY_NOISE_STD, 3),
        SENSITIVITY_ENABLED,
        round(SENSITIVITY_DELTA, 3),
        calibration_cache_token(calibration)
    )

    from_cache = cache_key in SIMULATION_CACHE
    if cache_key not in SIMULATION_CACHE:
        SIMULATION_CACHE[cache_key] = run_tellurium_verification(pair, calibration=calibration)
    if include_cache_status:
        return SIMULATION_CACHE[cache_key], from_cache
    return SIMULATION_CACHE[cache_key]

def attach_verification_to_top_pairs(ranked_pairs, top_n=VERIFICATION_TOP_N, calibration=None, verbose=False):
    verify_limit = min(top_n, len(ranked_pairs))
    if verify_limit > 0:
        require_tellurium()

    if verbose:
        print("\nVerification Pipeline")
        print("-" * 80)
        if verify_limit <= 0:
            print("No pairs selected for simulation.")
        else:
            print(
                "Running Tellurium on top "
                f"{verify_limit} pair(s) using circuit-derived parameters and uncertainty analysis..."
            )

    for idx, pair in enumerate(ranked_pairs):
        if idx < verify_limit:
            if verbose:
                print(f"  [{idx + 1}/{verify_limit}] {pair['pair_id']}")
                start = time.time()
                verification, from_cache = verify_pair(
                    pair,
                    calibration=calibration,
                    include_cache_status=True,
                )
                elapsed = time.time() - start
                cache_label = "cache" if from_cache else "fresh"
                print(
                    "       -> "
                    f"{verification.get('status', 'UNKNOWN')} "
                    f"({cache_label}, {elapsed:.2f}s)"
                )
            else:
                verification = verify_pair(pair, calibration=calibration)

            pair["verification"] = verification
        else:
            pair.setdefault("verification", None)

    if verbose and verify_limit > 0:
        print("-" * 80)

    return ranked_pairs

def simulator_status_message():
    if TELLURIUM_AVAILABLE:
        return (
            "Tellurium verification: enabled (top-3 circuit-aware, uncertainty-aware). "
            f"Samples={UNCERTAINTY_SAMPLES}, noise={int(UNCERTAINTY_NOISE_STD*100)}%."
        )
    return "Tellurium verification: REQUIRED but unavailable in active interpreter."

def build_pair_recommendations(library, weights):
    ecoli_circuits, geobacter_circuits = split_by_organism(library)
    max_raw = score_max_raw(weights)

    results = []
    for ecoli_circuit in ecoli_circuits:
        for geobacter_circuit in geobacter_circuits:
            combined = combine_pair_traits(ecoli_circuit, geobacter_circuit)
            base_score_raw = weighted_score(combined, weights)

            issues = []
            issues.extend(evaluate_internal_compatibility(ecoli_circuit))
            issues.extend(evaluate_internal_compatibility(geobacter_circuit))
            issues.extend(evaluate_pair_conflicts(ecoli_circuit, geobacter_circuit))

            penalty_raw = float(sum(SEVERITY_PENALTY[item["level"]] for item in issues))
            final_raw = max(0.0, base_score_raw - penalty_raw)
            base_score = to_percent(base_score_raw, max_raw)
            penalty = to_percent(penalty_raw, max_raw)
            final_score = to_percent(final_raw, max_raw)

            results.append({
                "pair_id": f"{ecoli_circuit['circuit_id']} + {geobacter_circuit['circuit_id']}",
                "ecoli": ecoli_circuit,
                "geobacter": geobacter_circuit,
                "combined_categories": combined,
                "match_score": final_score,
                "base_score": base_score,
                "penalty": penalty,
                "match_score_raw": round(final_raw, 2),
                "base_score_raw": round(base_score_raw, 2),
                "penalty_raw": round(penalty_raw, 2),
                "max_raw_score": round(max_raw, 2),
                "issues": issues
            })

    return sorted(results, key=lambda x: x["match_score_raw"], reverse=True)

def score_circuits(library, weights):
    max_raw = score_max_raw(weights)
    results = []
    for circuit in library:
        score_raw = sum(
            weights.get(cat, 0) * circuit["categories"].get(cat, 0)
            for cat in weights
        )
        results.append({
            "circuit_id":       circuit["circuit_id"],
            "organism":         circuit["organism"],
            "description":      circuit["description"],
            "knox_spec":        circuit["knox_spec"],
            "categories":       circuit["categories"],
            "match_score":      to_percent(score_raw, max_raw),
            "match_score_raw":  round(score_raw, 2),
            "max_raw_score":    round(max_raw, 2),
            "warning":          circuit.get("biological_warning", None)
        })
    return sorted(results, key=lambda x: x["match_score_raw"], reverse=True)

def trait_bar(score, width=10):
    filled = int(round((max(0, min(score, 10)) / 10.0) * width))
    return "#" * filled + "-" * (width - filled)

def print_circuit(rank, c):
    print(f"\n#{rank}  {c['circuit_id']}  ({c['organism']})")
    print(f"    Match Score : {c['match_score']}/100")
    cat_line = " | ".join(
        f"{CATEGORY_LABELS[k]}: {score_label(c['categories'][k])}"
        for k in CATEGORY_LABELS
    )
    print(f"    Traits      : {cat_line}")
    print(f"    Knox Spec   : {c['knox_spec']}")
    print(f"    Description : {c['description']}")
    if c["warning"]:
        print(f"    ⚠ WARNING   : {c['warning']}")

def print_pair(rank, pair):
    ecoli = pair["ecoli"]
    geobacter = pair["geobacter"]
    combined = pair["combined_categories"]

    print(f"\n#{rank}  {pair['pair_id']}")
    print(
        "    Pair Score  : "
        f"{pair['match_score']}/100 "
        f"(base {pair['base_score']} - penalty {pair['penalty']})"
    )

    cat_line = " | ".join(
        f"{CATEGORY_LABELS[key]}: {score_label(combined[key])} ({combined[key]})"
        for key in CATEGORY_LABELS
    )
    print(f"    Pair Traits : {cat_line}")

    print(f"    E. coli     : {ecoli['circuit_id']} | {ecoli['knox_spec']}")
    print(f"    Geobacter   : {geobacter['circuit_id']} | {geobacter['knox_spec']}")

    verification = pair.get("verification")
    if verification:
        design_trace = verification.get("design_trace") or {}
        if design_trace:
            key_params = design_trace.get("key_parameters", {})
            key_line = ", ".join(f"{k}={v}" for k, v in key_params.items())
            print("    Design Check : Parameters generated from circuit genes/promoters/Knox design")
            if key_line:
                print(f"    Design Params: {key_line}")

        if verification["status"] == "UNAVAILABLE":
            print(f"    Verification: {verification['status']} ({verification['reason']})")
        else:
            interval = verification.get("interval")
            agreement = verification.get("agreement_pct", 100)
            confidence = verification.get("confidence_tier", "Medium")
            verdict = verification.get("verdict", "Uncertain")
            print(
                "    Verification: "
                f"{verdict} | Stability {verification['stability_score']}/100"
            )
            if interval:
                print(
                    "    Uncertainty : "
                    f"[{interval[0]}, {interval[1]}, {interval[2]}] | "
                    f"Agreement {agreement}% ({verification.get('sample_count', 1)} runs)"
                )
            print(f"    Confidence  : {confidence}")
            print(
                "    Sim Endpoints: "
                f"E. coli={verification['final_ecoli']}, "
                f"Geobacter={verification['final_geobacter']}, "
                f"E->G={verification['final_metabolite_eg']}, "
                f"G->E={verification['final_metabolite_ge']}"
            )
            print(
                "    Sim Outputs  : "
                f"Hydrogen={verification['final_hydrogen']}, "
                f"ElectronIndex={verification['electron_transfer_index']}"
            )
            if verification.get("sensitivity"):
                drivers = ", ".join(
                    f"{item['parameter']} (±{item['effect']})" for item in verification["sensitivity"]
                )
                print(f"    Sensitivity : {drivers}")
            if verification.get("brittle"):
                print("    Robustness  : Brittle under small parameter shifts")
            if verification.get("calibrated"):
                source = verification.get("calibration_source", "user calibration")
                print(f"    Calibration : Applied user data ({source})")
            print(f"    Sim Note     : {verification['reason']}")
            print("    Caution      : In-silico evidence only; lab validation is still required.")

    if pair["issues"]:
        print("    Compatibility Notes:")
        for issue in pair["issues"]:
            print(f"      - [{issue['level'].upper()}] {issue['message']}")

def print_pair_tradeoff_table(pairs):
    print("\n" + "-" * 100)
    print("Top Pair Tradeoffs (0-10 trait bars)")
    print("-" * 100)
    print(f"{'Pair':38s} {'Score/100':>8s} {'ED':>12s} {'AX':>12s} {'HG':>12s} {'ER':>12s}")
    print("-" * 100)

    for pair in pairs:
        combined = pair["combined_categories"]
        pair_name = pair["pair_id"][:38]
        ed = trait_bar(combined["electron_donation"])
        ax = trait_bar(combined["auxotrophic_crossfeeding"])
        hg = trait_bar(combined["hydrogen_generation"])
        er = trait_bar(combined["evolutionary_resistance"])
        print(f"{pair_name:38s} {pair['match_score']:8.2f} {ed:>12s} {ax:>12s} {hg:>12s} {er:>12s}")

def show_recommendations(ranked, top_n=3):
    print(f"\n{'='*60}")
    print(f"  Top {top_n} Recommended Circuits")
    print(f"{'='*60}")
    for i, c in enumerate(ranked[:top_n], 1):
        print_circuit(i, c)

def show_pair_recommendations(ranked_pairs, top_n=3):
    print(f"\n{'='*80}")
    print(f"  Top {top_n} Recommended E. coli + Geobacter Pairs")
    print(f"{'='*80}")

    top = ranked_pairs[:top_n]
    for i, pair in enumerate(top, 1):
        print_pair(i, pair)

    print_pair_tradeoff_table(top)

def interval_width(interval):
    if not interval:
        return None
    return round(float(interval[2]) - float(interval[0]), 2)

def evidence_risk_label(verification, calibration_loaded):
    if not verification or verification.get("status") == "UNAVAILABLE":
        return "NO_SIM"

    score = 0
    confidence = verification.get("confidence_tier", "Medium")
    if confidence == "Low":
        score += 2
    elif confidence == "Medium":
        score += 1

    if verification.get("brittle"):
        score += 1
    if (verification.get("agreement_pct") or 100) < 65:
        score += 1

    width = interval_width(verification.get("interval"))
    if width is not None and width > 35:
        score += 1

    if not calibration_loaded:
        score += 1

    if score >= 4:
        return "HIGH"
    if score >= 2:
        return "MEDIUM"
    return "LOW"

def print_uncertainty_and_evidence_summary(ranked_pairs, simulated_count, calibration):
    print("\n" + "=" * 100)
    print("  Uncertainty & Evidence Quality Summary")
    print("=" * 100)

    print(
        "Simulation protocol: "
        f"{UNCERTAINTY_SAMPLES} uncertainty run(s) per pair, "
        f"{int(UNCERTAINTY_NOISE_STD*100)}% parameter noise, "
        f"sensitivity delta {int(SENSITIVITY_DELTA*100)}%."
    )
    print(f"Simulated pairs this run: {simulated_count}")

    if calibration:
        print("Calibration status: loaded (empirical override path enabled).")
    else:
        print("Calibration status: not loaded (theoretical defaults only).")
        print(
            "Evidence pitfall: without real measurements, rankings are best treated as "
            "hypothesis-level guidance."
        )
        print(
            "Upgrade path: provide user calibration data (growth, metabolite, electron-transfer metrics) "
            "to tighten confidence bounds."
        )

    if simulated_count <= 0:
        print("No simulation outputs were generated for this run.")
        return

    print("-" * 100)
    print(f"{'Pair':38s} {'Status':10s} {'Conf':>7s} {'Agree%':>7s} {'Width':>8s} {'Risk':>8s}")
    print("-" * 100)

    for pair in ranked_pairs[:simulated_count]:
        verification = pair.get("verification") or {}
        status = str(verification.get("status", "UNAVAILABLE"))
        confidence = str(verification.get("confidence_tier", "N/A"))
        agreement = verification.get("agreement_pct")
        agreement_display = f"{agreement}" if agreement is not None else "N/A"
        width = interval_width(verification.get("interval"))
        width_display = f"{width}" if width is not None else "N/A"
        risk = evidence_risk_label(verification, calibration_loaded=bool(calibration))

        pair_name = pair["pair_id"][:38]
        print(
            f"{pair_name:38s} {status:10s} {confidence:>7s} {agreement_display:>7s} "
            f"{width_display:>8s} {risk:>8s}"
        )

    print("-" * 100)
    print("Risk legend: LOW/MEDIUM/HIGH reflect uncertainty robustness, not biological safety.")

def run_session(library):
    weights = get_user_weights()

    if all(w == 0 for w in weights.values()):
        print("\nAll trait weights are 0 - no recommendation possible.")
        print("Please set at least one trait weight above 0.")
        return

    ranked_pairs = build_pair_recommendations(library, weights)
    if not ranked_pairs:
        print("\nNo valid E. coli + Geobacter pairs were found in the library.")
        return

    calibration = get_calibration_for_session()

    ranked_pairs = attach_verification_to_top_pairs(
        ranked_pairs,
        top_n=min(VERIFICATION_TOP_N, len(ranked_pairs)),
        calibration=calibration,
        verbose=True
    )

    print_uncertainty_and_evidence_summary(
        ranked_pairs,
        simulated_count=min(VERIFICATION_TOP_N, len(ranked_pairs)),
        calibration=calibration,
    )

    show_pair_recommendations(ranked_pairs, top_n=3)

    if get_yes_no("\nShow top 10 ranked circuit pairs? (y/n): "):
        show_pair_recommendations(ranked_pairs, top_n=min(10, len(ranked_pairs)))

    if get_yes_no("\nShow top 10 single-circuit ranking too? (y/n): "):
        ranked = score_circuits(library, weights)
        show_recommendations(ranked, top_n=min(10, len(ranked)))

def main():
    print("=" * 60)
    print("  MFC Co-Culture Circuit Recommender")
    print("  EC/BE 552 — Computational Synthetic Biology")
    print("=" * 60)
    print(runtime_python_message())
    print(simulator_status_message())
    print(tellurium_runtime_details())
    print(uncertainty_terminal_message())
    print(model_limitations_message())
    print(calibration_guidance_message())

    try:
        require_tellurium()
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)

    library = load_library(LIBRARY_PATH)

    while True:
        run_session(library)
        if not get_yes_no("\nRun again with different trait weights? (y/n): "):
            print("\nExiting recommender.")
            break

if __name__ == "__main__":
    main()
