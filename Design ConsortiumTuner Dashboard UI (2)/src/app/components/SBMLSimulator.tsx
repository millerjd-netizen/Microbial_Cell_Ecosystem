import { useEffect, useMemo, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

type ModuleKey =
  | 'cross_feeding'
  | 'nitrogen_cycle'
  | 'electrogenesis'
  | 'quorum_sensing'
  | 'kill_switch'
  | 'metabolite_production';

interface SimulatorProps {
  modules: Record<ModuleKey, number>;
}

// 33 species in exact order
const SPECIES = [
  'Ecoli_K',
  'Ecoli_L',
  'Ecoli_Trp',
  'Ecoli_His',
  'Lys',
  'Leu',
  'Trp',
  'His',
  'Gsulf',
  'Gmet',
  'Acs',
  'OmcZ_A',
  'OmcZ_B',
  'Current',
  'MazE_A',
  'MazF_A',
  'MazE_B',
  'MazF_B',
  'KillSignal',
  'AHL',
  'LuxR_AHL',
  'AI2',
  'NH4',
  'NO2',
  'NO3',
  'NO',
  'N2O',
  'N2',
  'AcetylCoA',
  'MalonylCoA',
  'Naringenin',
  'Isoprenoid',
  'BetaCarotene',
] as const;

type Species = (typeof SPECIES)[number];

const IDX: Record<string, number> = Object.fromEntries(
  SPECIES.map((s, i) => [s, i])
);

const SPECIES_GROUPS: Record<string, Species[]> = {
  'Cross-feeding': [
    'Ecoli_K',
    'Ecoli_L',
    'Ecoli_Trp',
    'Ecoli_His',
    'Lys',
    'Leu',
    'Trp',
    'His',
  ],
  Electrogenesis: ['Gsulf', 'Gmet', 'Acs', 'OmcZ_A', 'OmcZ_B', 'Current'],
  'Kill switch': ['MazE_A', 'MazF_A', 'MazE_B', 'MazF_B', 'KillSignal'],
  'Quorum sensing': ['AHL', 'LuxR_AHL', 'AI2'],
  'Nitrogen cycle': ['NH4', 'NO2', 'NO3', 'NO', 'N2O', 'N2'],
  'Metabolite production': [
    'AcetylCoA',
    'MalonylCoA',
    'Naringenin',
    'Isoprenoid',
    'BetaCarotene',
  ],
};

// Color palette matching notebook
const PALETTE = [
  '#E74C3C',
  '#3498DB',
  '#2ECC71',
  '#F39C12',
  '#9B59B6',
  '#1ABC9C',
  '#E67E22',
  '#34495E',
  '#16A085',
  '#D35400',
  '#8E44AD',
  '#27AE60',
  '#C0392B',
  '#2980B9',
  '#F1C40F',
  '#7F8C8D',
  '#E91E63',
  '#00BCD4',
  '#CDDC39',
  '#795548',
  '#607D8B',
  '#FF5722',
  '#009688',
  '#FFC107',
  '#673AB7',
  '#FF9800',
  '#4CAF50',
  '#F44336',
  '#2196F3',
  '#9C27B0',
  '#3F51B5',
  '#00ACC1',
  '#8BC34A',
];

const SPECIES_COLOR: Record<string, string> = Object.fromEntries(
  SPECIES.map((s, i) => [s, PALETTE[i % PALETTE.length]])
);

// Initial conditions Y0
const Y0: number[] = (() => {
  const y = new Array(SPECIES.length).fill(0);
  y[IDX.Ecoli_K] = 1.0;
  y[IDX.Ecoli_L] = 1.0;
  y[IDX.Ecoli_Trp] = 1.0;
  y[IDX.Ecoli_His] = 1.0;
  y[IDX.Gsulf] = 1.0;
  y[IDX.Gmet] = 1.0;
  y[IDX.MazE_A] = 5.0;
  y[IDX.MazE_B] = 5.0;
  y[IDX.NH4] = 10.0;
  y[IDX.AcetylCoA] = 5.0;
  return y;
})();

// Base rate constants with module associations
const RATES: Record<string, [number, ModuleKey]> = {
  // Cross-feeding
  k_K_lys: [0.15, 'cross_feeding'],
  k_L_leu: [0.15, 'cross_feeding'],
  k_Trp_trp: [0.15, 'cross_feeding'],
  k_His_his: [0.15, 'cross_feeding'],
  k_K_grow: [0.04, 'cross_feeding'],
  k_L_grow: [0.04, 'cross_feeding'],
  k_Trp_grow: [0.04, 'cross_feeding'],
  k_His_grow: [0.04, 'cross_feeding'],
  k_K_death: [0.05, 'cross_feeding'],
  k_L_death: [0.05, 'cross_feeding'],
  k_Trp_death: [0.05, 'cross_feeding'],
  k_His_death: [0.05, 'cross_feeding'],
  // Electrogenesis
  k_Gsulf_grow: [0.03, 'electrogenesis'],
  k_Gmet_grow: [0.03, 'electrogenesis'],
  k_Gsulf_death: [0.1, 'electrogenesis'],
  k_Gmet_death: [0.1, 'electrogenesis'],
  k_acs: [0.1, 'electrogenesis'],
  k_omcZ_B_basal: [0.05, 'electrogenesis'],
  k_omcZ_boost_A: [0.2, 'electrogenesis'],
  k_omcZ_boost_B: [0.2, 'electrogenesis'],
  k_current: [0.02, 'electrogenesis'],
  k_NO_induces_omcZ: [0.08, 'electrogenesis'],
  // Kill switch
  k_mazE_A: [0.1, 'kill_switch'],
  k_mazE_B: [0.1, 'kill_switch'],
  k_mazF_A: [0.15, 'kill_switch'],
  k_mazF_B: [0.15, 'kill_switch'],
  k_antitox: [0.5, 'kill_switch'],
  k_tox_kill: [0.25, 'kill_switch'],
  k_mazE_deg: [0.05, 'kill_switch'],
  // Quorum sensing
  k_luxI: [0.05, 'quorum_sensing'],
  k_luxS: [0.05, 'quorum_sensing'],
  k_luxR_act: [0.1, 'quorum_sensing'],
  k_killsig: [0.05, 'quorum_sensing'],
  k_AHL_deg: [0.02, 'quorum_sensing'],
  k_AI2_deg: [0.02, 'quorum_sensing'],
  k_killsig_deg: [0.05, 'quorum_sensing'],
  // Nitrogen cycle
  k_nitrosomonas: [0.15, 'nitrogen_cycle'],
  k_nitrobacter: [0.12, 'nitrogen_cycle'],
  k_pseud_narG: [0.1, 'nitrogen_cycle'],
  k_pseud_nirS: [0.1, 'nitrogen_cycle'],
  k_parac_norB: [0.1, 'nitrogen_cycle'],
  k_parac_nosZ: [0.1, 'nitrogen_cycle'],
  // Metabolite production
  k_malCoA: [0.08, 'metabolite_production'],
  k_naringenin: [0.06, 'metabolite_production'],
  k_isoprenoid: [0.08, 'metabolite_production'],
  k_betacarot: [0.06, 'metabolite_production'],
};

function effectiveRates(
  modules: Record<ModuleKey, number>
): Record<string, number> {
  const p: Record<string, number> = {};
  for (const k in RATES) {
    const [base, mod] = RATES[k];
    p[k] = base * modules[mod];
  }
  return p;
}

// 33-equation RHS (right-hand side of ODEs)
function rhs(y: number[], p: Record<string, number>): number[] {
  const max0 = (v: number) => Math.max(0, v);

  const Ecoli_K = max0(y[IDX.Ecoli_K]);
  const Ecoli_L = max0(y[IDX.Ecoli_L]);
  const Ecoli_Trp = max0(y[IDX.Ecoli_Trp]);
  const Ecoli_His = max0(y[IDX.Ecoli_His]);
  const Lys = max0(y[IDX.Lys]);
  const Leu = max0(y[IDX.Leu]);
  const Trp = max0(y[IDX.Trp]);
  const His = max0(y[IDX.His]);
  const Gsulf = max0(y[IDX.Gsulf]);
  const Gmet = max0(y[IDX.Gmet]);
  const OmcZ_A = max0(y[IDX.OmcZ_A]);
  const OmcZ_B = max0(y[IDX.OmcZ_B]);
  const MazE_A = max0(y[IDX.MazE_A]);
  const MazF_A = max0(y[IDX.MazF_A]);
  const MazE_B = max0(y[IDX.MazE_B]);
  const MazF_B = max0(y[IDX.MazF_B]);
  const KillSignal = max0(y[IDX.KillSignal]);
  const AHL = max0(y[IDX.AHL]);
  const LuxR_AHL = max0(y[IDX.LuxR_AHL]);
  const NH4 = max0(y[IDX.NH4]);
  const NO2 = max0(y[IDX.NO2]);
  const NO3 = max0(y[IDX.NO3]);
  const NO = max0(y[IDX.NO]);
  const N2O = max0(y[IDX.N2O]);
  const AcetylCoA = max0(y[IDX.AcetylCoA]);
  const MalonylCoA = max0(y[IDX.MalonylCoA]);
  const Isoprenoid = max0(y[IDX.Isoprenoid]);

  // Cross-feeding
  const v_K_lys = p.k_K_lys * Ecoli_K;
  const v_L_leu = p.k_L_leu * Ecoli_L;
  const v_Trp_prod = p.k_Trp_trp * Ecoli_Trp;
  const v_His_prod = p.k_His_his * Ecoli_His;
  const v_K_grow = p.k_K_grow * Ecoli_K * Leu;
  const v_L_grow = p.k_L_grow * Ecoli_L * Lys;
  const v_Trp_grow = p.k_Trp_grow * Ecoli_Trp * His;
  const v_His_grow = p.k_His_grow * Ecoli_His * Trp;
  const v_K_death = p.k_K_death * Ecoli_K;
  const v_L_death = p.k_L_death * Ecoli_L;
  const v_Trp_death = p.k_Trp_death * Ecoli_Trp;
  const v_His_death = p.k_His_death * Ecoli_His;

  // Electrogenesis
  const v_Gsulf_grow = p.k_Gsulf_grow * Gsulf;
  const v_Gmet_grow = p.k_Gmet_grow * Gmet;
  const v_Gsulf_death = p.k_Gsulf_death * Gsulf;
  const v_Gmet_death = p.k_Gmet_death * Gmet;
  const v_acs = p.k_acs * Gsulf;
  const v_omcZ_B_base = p.k_omcZ_B_basal * Gmet;
  const v_omcZ_B_ind = p.k_NO_induces_omcZ * Gmet * NO;
  const v_omcZ_bst_A = p.k_omcZ_boost_A * Gsulf;
  const v_omcZ_bst_B = p.k_omcZ_boost_B * Gmet;
  const v_current = p.k_current * Gsulf * Gmet * (1 + OmcZ_A) * (1 + OmcZ_B);

  // Kill switch
  const v_mazE_A = p.k_mazE_A * Gsulf;
  const v_mazF_A = p.k_mazF_A * KillSignal * Gsulf;
  const v_antitox_A = p.k_antitox * MazE_A * MazF_A;
  const v_kill_A = p.k_tox_kill * MazF_A * Gsulf;
  const v_mazE_A_dg = p.k_mazE_deg * MazE_A;
  const v_mazE_B = p.k_mazE_B * Gmet;
  const v_mazF_B = p.k_mazF_B * KillSignal * Gmet;
  const v_antitox_B = p.k_antitox * MazE_B * MazF_B;
  const v_kill_B = p.k_tox_kill * MazF_B * Gmet;
  const v_mazE_B_dg = p.k_mazE_deg * MazE_B;

  // Quorum sensing
  const v_AHL = p.k_luxI * Gsulf;
  const v_luxR = p.k_luxR_act * AHL;
  const v_killsig = p.k_killsig * LuxR_AHL;
  const v_AHL_dg = p.k_AHL_deg * AHL;
  const v_ksig_dg = p.k_killsig_deg * KillSignal;
  const v_AI2 = p.k_luxS * Gmet;
  const v_AI2_dg = p.k_AI2_deg * max0(y[IDX.AI2]);

  // Nitrogen cycle
  const v_nitroso = p.k_nitrosomonas * NH4;
  const v_nitroba = p.k_nitrobacter * NO2;
  const v_narG = p.k_pseud_narG * NO3;
  const v_nirS = p.k_pseud_nirS * NO2;
  const v_norB = p.k_parac_norB * NO;
  const v_nosZ = p.k_parac_nosZ * N2O;

  // Metabolite production
  const v_malCoA = p.k_malCoA * AcetylCoA;
  const v_naringen = p.k_naringenin * MalonylCoA;
  const v_isoprenoid = p.k_isoprenoid * AcetylCoA;
  const v_betacarot = p.k_betacarot * Isoprenoid;

  const dy = new Array(SPECIES.length).fill(0);
  dy[IDX.Ecoli_K] = v_K_grow - v_K_death;
  dy[IDX.Ecoli_L] = v_L_grow - v_L_death;
  dy[IDX.Ecoli_Trp] = v_Trp_grow - v_Trp_death;
  dy[IDX.Ecoli_His] = v_His_grow - v_His_death;
  dy[IDX.Lys] = v_K_lys - v_L_grow;
  dy[IDX.Leu] = v_L_leu - v_K_grow;
  dy[IDX.Trp] = v_Trp_prod - v_His_grow;
  dy[IDX.His] = v_His_prod - v_Trp_grow;
  dy[IDX.Gsulf] = v_Gsulf_grow - v_Gsulf_death - v_kill_A;
  dy[IDX.Gmet] = v_Gmet_grow - v_Gmet_death - v_kill_B;
  dy[IDX.Acs] = v_acs;
  dy[IDX.OmcZ_A] = v_omcZ_bst_A;
  dy[IDX.OmcZ_B] = v_omcZ_B_base + v_omcZ_B_ind + v_omcZ_bst_B;
  dy[IDX.Current] = v_current;
  dy[IDX.MazE_A] = v_mazE_A - v_antitox_A - v_mazE_A_dg;
  dy[IDX.MazF_A] = v_mazF_A - v_antitox_A;
  dy[IDX.MazE_B] = v_mazE_B - v_antitox_B - v_mazE_B_dg;
  dy[IDX.MazF_B] = v_mazF_B - v_antitox_B;
  dy[IDX.KillSignal] = v_killsig - v_ksig_dg;
  dy[IDX.AHL] = v_AHL - v_luxR - v_AHL_dg;
  dy[IDX.LuxR_AHL] = v_luxR;
  dy[IDX.AI2] = v_AI2 - v_AI2_dg;
  dy[IDX.NH4] = -v_nitroso;
  dy[IDX.NO2] = v_nitroso - v_nitroba + v_narG - v_nirS;
  dy[IDX.NO3] = v_nitroba - v_narG;
  dy[IDX.NO] = v_nirS - v_norB;
  dy[IDX.N2O] = v_norB - v_nosZ;
  dy[IDX.N2] = v_nosZ;
  dy[IDX.AcetylCoA] = -v_malCoA - v_isoprenoid;
  dy[IDX.MalonylCoA] = v_malCoA - v_naringen;
  dy[IDX.Naringenin] = v_naringen;
  dy[IDX.Isoprenoid] = v_isoprenoid - v_betacarot;
  dy[IDX.BetaCarotene] = v_betacarot;

  return dy;
}

// RK4 integrator
function simulate(
  modules: Record<ModuleKey, number>,
  tEnd = 100,
  dt = 0.1,
  sampleEvery = 10
): any[] {
  const p = effectiveRates(modules);
  const steps = Math.round(tEnd / dt);
  let y = Y0.slice();

  const initRow: any = { time: 0 };
  for (const s of SPECIES) initRow[s] = parseFloat(y[IDX[s]].toFixed(4));
  const rows: any[] = [initRow];

  const addScaled = (a: number[], b: number[], s: number) => {
    const out = new Array(a.length);
    for (let i = 0; i < a.length; i++) out[i] = a[i] + s * b[i];
    return out;
  };

  for (let i = 1; i <= steps; i++) {
    const k1 = rhs(y, p);
    const k2 = rhs(addScaled(y, k1, dt / 2), p);
    const k3 = rhs(addScaled(y, k2, dt / 2), p);
    const k4 = rhs(addScaled(y, k3, dt), p);
    const yNew = new Array(y.length);
    for (let j = 0; j < y.length; j++) {
      const v = y[j] + (dt / 6) * (k1[j] + 2 * k2[j] + 2 * k3[j] + k4[j]);
      yNew[j] = Math.max(0, v);
    }
    y = yNew;
    if (i % sampleEvery === 0) {
      const row: any = { time: parseFloat((i * dt).toFixed(2)) };
      for (const s of SPECIES) row[s] = parseFloat(y[IDX[s]].toFixed(4));
      rows.push(row);
    }
  }
  return rows;
}

// Species presets
const PRESETS: Record<string, Species[]> = {
  'Multi-module overview': [
    'Ecoli_K',
    'Ecoli_L',
    'Gsulf',
    'Gmet',
    'Current',
    'NH4',
    'NO3',
    'N2',
    'MazE_A',
    'BetaCarotene',
  ],
  'Nitrogen cycle': ['NH4', 'NO2', 'NO3', 'NO', 'N2O', 'N2'],
  'iBioSim default': [
    'AHL',
    'Current',
    'Gmet',
    'Gsulf',
    'KillSignal',
    'MazE_A',
    'OmcZ_A',
    'OmcZ_B',
  ],
  'Cross-feeding': [
    'Ecoli_K',
    'Ecoli_L',
    'Ecoli_Trp',
    'Ecoli_His',
    'Lys',
    'Leu',
    'Trp',
    'His',
  ],
  'Metabolite production': [
    'AcetylCoA',
    'MalonylCoA',
    'Naringenin',
    'Isoprenoid',
    'BetaCarotene',
  ],
  'Quorum sensing': [
    'AHL',
    'LuxR_AHL',
    'AI2',
    'KillSignal',
    'MazF_A',
    'MazF_B',
  ],
  'All 33 species': SPECIES.slice() as Species[],
};

const PRESET_NAMES = Object.keys(PRESETS);
const DEFAULT_PRESET = 'Multi-module overview';

export function SBMLSimulator({ modules }: SimulatorProps) {
  const [picked, setPicked] = useState<Set<Species>>(
    () => new Set(PRESETS[DEFAULT_PRESET])
  );
  const [showPicker, setShowPicker] = useState(false);
  const [logY, setLogY] = useState(false);
  const [simData, setSimData] = useState<any[]>([]);

  useEffect(() => {
    const rows = simulate(modules);
    setSimData(rows);
  }, [modules]);

  const togglePicked = (s: Species) => {
    const next = new Set(picked);
    if (next.has(s)) next.delete(s);
    else next.add(s);
    setPicked(next);
  };

  const applyPreset = (name: string) => {
    setPicked(new Set(PRESETS[name]));
  };

  const orderedPicked = useMemo(
    () => SPECIES.filter((s) => picked.has(s)),
    [picked]
  );

  return (
    <div className="bg-slate-900/50 rounded-2xl p-6">
      <div className="flex items-center justify-between mb-1">
        <h3 className="text-lg">Live ODE simulation — 33-species ecosystem</h3>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <label className="flex items-center gap-1.5 cursor-pointer">
            <input
              type="checkbox"
              checked={logY}
              onChange={(e) => setLogY(e.target.checked)}
              className="accent-cyan-400"
            />
            log y-axis
          </label>
          <button
            onClick={() => setShowPicker(!showPicker)}
            className="px-3 py-1 bg-slate-800 hover:bg-slate-700 rounded text-xs"
          >
            {showPicker ? 'hide' : 'show'} species picker
          </button>
        </div>
      </div>
      <p className="text-xs text-slate-500 mb-4">
        RK4 integration, dt = 0.1, t = 0…100 (matches notebook solve_ivp output)
      </p>

      {/* Preset buttons */}
      <div className="flex flex-wrap gap-2 mb-4">
        {PRESET_NAMES.map((n) => (
          <button
            key={n}
            onClick={() => applyPreset(n)}
            className="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
          >
            {n}
          </button>
        ))}
      </div>

      {/* Species checkbox grid */}
      {showPicker && (
        <div className="bg-slate-950/60 rounded-lg p-4 mb-4 border border-slate-800">
          <p className="text-xs text-slate-500 mb-3">
            Pick any subset of the 33 state variables to plot.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-2">
            {Object.entries(SPECIES_GROUPS).map(([group, ss]) => (
              <div key={group}>
                <div className="text-xs text-slate-400 uppercase tracking-wide mb-1">
                  {group}
                </div>
                {ss.map((s) => (
                  <label
                    key={s}
                    className="flex items-center gap-2 text-xs cursor-pointer hover:text-slate-100 py-0.5"
                  >
                    <input
                      type="checkbox"
                      checked={picked.has(s)}
                      onChange={() => togglePicked(s)}
                    />
                    <span
                      className="inline-block w-2.5 h-2.5 rounded-sm"
                      style={{ backgroundColor: SPECIES_COLOR[s] }}
                    />
                    <span className="font-mono">{s}</span>
                  </label>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}

      <ResponsiveContainer width="100%" height={460}>
        <LineChart
          data={simData}
          margin={{ top: 10, right: 30, left: 0, bottom: 30 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="time"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            label={{
              value: 'time (minutes)',
              position: 'insideBottom',
              offset: -10,
              fill: '#94a3b8',
              fontSize: 12,
            }}
          />
          <YAxis
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            scale={logY ? 'log' : 'linear'}
            domain={logY ? [0.001, 'auto'] : [0, 12]}
            allowDataOverflow={false}
            label={{
              value: 'concentration (AU)',
              angle: -90,
              position: 'insideLeft',
              fill: '#94a3b8',
              fontSize: 12,
            }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '8px',
              fontSize: '12px',
            }}
            labelStyle={{ color: '#e2e8f0' }}
          />
          <Legend
            wrapperStyle={{
              fontSize: '11px',
              paddingTop: '10px',
            }}
            iconType="line"
          />
          {orderedPicked.map((s) => (
            <Line
              key={s}
              type="monotone"
              dataKey={s}
              stroke={SPECIES_COLOR[s]}
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
              name={s}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>

      {orderedPicked.length === 0 && (
        <p className="text-center text-slate-500 text-sm py-4">
          No species selected — pick a preset or open the species picker.
        </p>
      )}
    </div>
  );
}
