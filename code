import { useState } from 'react';
import * as Slider from '@radix-ui/react-slider';
import { SBMLSimulator } from './components/SBMLSimulator';

type ModuleKey = 'cross_feeding' | 'nitrogen_cycle' | 'electrogenesis' | 'quorum_sensing' | 'kill_switch' | 'metabolite_production';

interface Circuit {
  id: string;
  name: string;
  category: ModuleKey;
  organism: string;
  goldbar: string;
  image: string;
  requires: string[];
}

const CIRCUITS: Circuit[] = [
  // Cross-feeding (6)
  { id: 'cf1', name: 'Ecoli_K', category: 'cross_feeding', organism: 'E. coli (lys+/leu-)', goldbar: 'Ptrc → RBS2 → lysC+argD+lysA → T2', image: 'https://images.unsplash.com/photo-1707079918041-2f7ae196b5eb?w=400', requires: [] },
  { id: 'cf2', name: 'Ecoli_L', category: 'cross_feeding', organism: 'E. coli (leu+/lys-)', goldbar: 'Ptrc → RBS1 → leuB+leuC+leuD → T1', image: 'https://images.unsplash.com/photo-1707079917592-9fba05b06904?w=400', requires: [] },
  { id: 'cf3', name: 'Ecoli_Trp', category: 'cross_feeding', organism: 'E. coli (trp+/his-)', goldbar: 'Ptrc → RBS1 → trpA+trpB → T1', image: 'https://images.unsplash.com/photo-1574341792525-683b103fffe8?w=400', requires: [] },
  { id: 'cf4', name: 'Ecoli_His', category: 'cross_feeding', organism: 'E. coli (his+/trp-)', goldbar: 'Ptrc → RBS2 → hisA+hisB → T2', image: 'https://images.unsplash.com/photo-1707079918208-d4b0c55eded6?w=400', requires: [] },
  { id: 'cf5', name: 'StrainA_Gsulfurreducens', category: 'cross_feeding', organism: 'G. sulfurreducens', goldbar: 'Ptrc → RBS1 → acs → Term1', image: 'https://images.unsplash.com/photo-1706204077098-44d96b1be00b?w=400', requires: [] },
  { id: 'cf6', name: 'StrainB_Gmetallireducens', category: 'cross_feeding', organism: 'G. metallireducens', goldbar: 'PnifH → RBS2 → omcZ → Term2', image: 'https://images.unsplash.com/photo-1707079917453-19d68310327d?w=400', requires: [] },

  // Electrogenesis (2)
  { id: 'ea1', name: 'OmcZ_Booster_StrainA', category: 'electrogenesis', organism: 'G. sulfurreducens', goldbar: 'PomcZ → RBS1 → omcZ → Term1', image: 'https://images.unsplash.com/photo-1707861107901-4a98927cbc61?w=400', requires: ['StrainA_Gsulfurreducens'] },
  { id: 'ea2', name: 'EET_Booster_StrainB', category: 'electrogenesis', organism: 'G. metallireducens', goldbar: 'PimcH → RBS2 → imcH → Term2', image: 'https://images.unsplash.com/photo-1706643569034-2cb3262d63d2?w=400', requires: ['StrainB_Gmetallireducens'] },

  // Kill switch (2)
  { id: 'ks1', name: 'KillSwitch_StrainA', category: 'kill_switch', organism: 'G. sulfurreducens', goldbar: 'Pconst → mazE → T1 / Prep → mazF → T1', image: 'https://images.unsplash.com/photo-1708939859511-cc70bedf725a?w=400', requires: ['StrainA_Gsulfurreducens'] },
  { id: 'ks2', name: 'KillSwitch_StrainB', category: 'kill_switch', organism: 'G. metallireducens', goldbar: 'Pconst → mazE → T2 / Prep → mazF → T2', image: 'https://images.unsplash.com/photo-1706647155464-30b5485c394c?w=400', requires: ['StrainB_Gmetallireducens'] },

  // Quorum sensing (2)
  { id: 'qs1', name: 'LuxI_LuxR_circuit', category: 'quorum_sensing', organism: 'V. fischeri chassis', goldbar: 'Ptrc → RBS1 → luxR+luxI → T1', image: 'https://images.unsplash.com/photo-1698840379986-57d8b9aff4e0?w=400', requires: [] },
  { id: 'qs2', name: 'LuxS_circuit', category: 'quorum_sensing', organism: 'V. fischeri chassis', goldbar: 'Ptrc → RBS2 → luxS → T2', image: 'https://images.unsplash.com/photo-1754149613894-87e8c37abd7b?w=400', requires: [] },

  // Nitrogen cycle (4)
  { id: 'ni1', name: 'Nitrosomonas', category: 'nitrogen_cycle', organism: 'Nitrosomonas europaea', goldbar: 'Ptrc → RBS1 → amoA+hao → T1', image: 'https://images.unsplash.com/photo-1574342117829-f44f2cd15fc4?w=400', requires: [] },
  { id: 'ni2', name: 'Nitrobacter', category: 'nitrogen_cycle', organism: 'Nitrobacter winogradskyi', goldbar: 'Ptrc → RBS2 → nxrA → T2', image: 'https://images.unsplash.com/photo-1626269822793-87cced4ebb77?w=400', requires: ['Nitrosomonas'] },
  { id: 'dn1', name: 'Pseudomonas_stutzeri', category: 'nitrogen_cycle', organism: 'P. stutzeri', goldbar: 'Ptrc → RBS1 → narG+nirS → T1', image: 'https://images.unsplash.com/photo-1707386821135-f4417f81dc3a?w=400', requires: [] },
  { id: 'dn2', name: 'Paracoccus_denitrificans', category: 'nitrogen_cycle', organism: 'P. denitrificans', goldbar: 'Ptrc → RBS2 → norB+nosZ → T2', image: 'https://images.unsplash.com/photo-1631824683860-9a7aa1fe0713?w=400', requires: ['Pseudomonas_stutzeri'] },

  // Metabolite production (4)
  { id: 'pr1', name: 'MalonylCoA_Producer', category: 'metabolite_production', organism: 'E. coli', goldbar: 'Ptrc → RBS1 → fapR+fabH → T1', image: 'https://images.unsplash.com/photo-1579781354171-45f67f0d8f18?w=400', requires: [] },
  { id: 'pr2', name: 'Naringenin_Producer', category: 'metabolite_production', organism: 'E. coli', goldbar: 'Ptrc → RBS2 → TAL+4CL+CHS+CHI → T2', image: 'https://images.unsplash.com/photo-1707386820771-da4014d34ea3?w=400', requires: ['MalonylCoA_Producer'] },
  { id: 'pr3', name: 'Isoprenoid_Producer', category: 'metabolite_production', organism: 'E. coli', goldbar: 'Ptrc → RBS1 → atoB+HMGS+HMGR → T1', image: 'https://images.unsplash.com/photo-1579781354147-e863d998e97f?w=400', requires: [] },
  { id: 'pr4', name: 'BetaCarotene_Producer', category: 'metabolite_production', organism: 'E. coli', goldbar: 'Ptrc → RBS2 → crtE+crtB+crtI → T2', image: 'https://images.unsplash.com/photo-1643625794877-b808168ba474?w=400', requires: ['Isoprenoid_Producer'] },
];

const MODULE_COLORS: Record<ModuleKey, string> = {
  cross_feeding: '#8FD14F',
  nitrogen_cycle: '#A855F7',
  electrogenesis: '#00B4B4',
  quorum_sensing: '#3B82F6',
  kill_switch: '#F59E0B',
  metabolite_production: '#EF4444',
};

const MODULE_LABELS: Record<ModuleKey, string> = {
  cross_feeding: 'Cross-feeding',
  nitrogen_cycle: 'Nitrogen cycle',
  electrogenesis: 'Electrogenesis',
  quorum_sensing: 'Quorum sensing',
  kill_switch: 'Kill switch',
  metabolite_production: 'Metabolite production',
};

export default function App() {
  const [modules, setModules] = useState<Record<ModuleKey, number>>({
    cross_feeding: 0.7,
    nitrogen_cycle: 0.7,
    electrogenesis: 0.7,
    quorum_sensing: 0.7,
    kill_switch: 0.7,
    metabolite_production: 0.7,
  });

  // Calculate fitness scores for each circuit
  const getCircuitScore = (circuit: Circuit) => {
    return modules[circuit.category];
  };

  // Score all circuits
  const circuitsWithScores = CIRCUITS.map(circuit => ({
    ...circuit,
    score: getCircuitScore(circuit),
  }));

  // Select circuits above threshold (threshold = 0)
  const preliminarySelected = new Set(
    circuitsWithScores
      .filter(c => c.score > 0)
      .map(c => c.name)
  );

  // Dependency closure: add required circuits
  const selectedCircuits = new Set(preliminarySelected);
  let changed = true;
  while (changed) {
    changed = false;
    for (const name of Array.from(selectedCircuits)) {
      const circuit = CIRCUITS.find(c => c.name === name);
      if (circuit) {
        for (const req of circuit.requires) {
          if (!selectedCircuits.has(req)) {
            selectedCircuits.add(req);
            changed = true;
          }
        }
      }
    }
  }

  // Get final selected circuits sorted by score
  const finalSelected = circuitsWithScores
    .filter(c => selectedCircuits.has(c.name))
    .sort((a, b) => b.score - a.score);

  // Category counts for ecosystem summary
  const categoryCounts = finalSelected.reduce((acc, circuit) => {
    acc[circuit.category] = (acc[circuit.category] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const updateModule = (key: ModuleKey, value: number) => {
    setModules({ ...modules, [key]: value });
  };

  const applyPreset = (preset: string) => {
    switch (preset) {
      case 'mfc':
        setModules({
          cross_feeding: 0.9,
          nitrogen_cycle: 0.3,
          electrogenesis: 1.0,
          quorum_sensing: 0.4,
          kill_switch: 0.2,
          metabolite_production: 0.1,
        });
        break;
      case 'nitrogen':
        setModules({
          cross_feeding: 0.4,
          nitrogen_cycle: 1.0,
          electrogenesis: 0.2,
          quorum_sensing: 0.5,
          kill_switch: 0.3,
          metabolite_production: 0.1,
        });
        break;
      case 'production':
        setModules({
          cross_feeding: 0.7,
          nitrogen_cycle: 0.2,
          electrogenesis: 0.3,
          quorum_sensing: 0.6,
          kill_switch: 0.4,
          metabolite_production: 1.0,
        });
        break;
      case 'reset':
        setModules({
          cross_feeding: 0.7,
          nitrogen_cycle: 0.7,
          electrogenesis: 0.7,
          quorum_sensing: 0.7,
          kill_switch: 0.7,
          metabolite_production: 0.7,
        });
        break;
    }
  };

  return (
    <div className="h-screen bg-[#0F172A] text-slate-100 flex flex-col overflow-hidden">
      {/* Header */}
      <header className="border-b border-slate-800 px-8 py-4 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <span className="text-2xl">🧬</span>
              <h1 className="text-xl">ConsortiumTuner v0.3</h1>
            </div>
            <p className="text-sm text-slate-400 mt-1">
              20 circuits × 6 modules = tunable microbial ecosystem designer
            </p>
          </div>
          <div className="text-sm text-slate-400">
            Jonathan · Jaleel · William · Nora
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Module Sliders */}
        <aside className="w-80 border-r border-slate-800 p-6 overflow-y-auto flex-shrink-0">
          <h2 className="text-sm uppercase tracking-wider text-slate-400 mb-6">
            MODULE KNOBS (6)
          </h2>

          <div className="space-y-6">
            {(Object.keys(modules) as ModuleKey[]).map((key) => (
              <div key={key}>
                <div className="flex justify-between mb-2">
                  <label className="text-sm">{MODULE_LABELS[key]}</label>
                  <span className="text-sm text-slate-400">
                    {modules[key].toFixed(2)}
                  </span>
                </div>
                <Slider.Root
                  className="relative flex items-center select-none touch-none w-full h-5"
                  value={[modules[key]]}
                  onValueChange={([v]) => updateModule(key, v)}
                  max={1}
                  step={0.05}
                >
                  <Slider.Track
                    className="relative grow rounded-full h-1.5"
                    style={{ backgroundColor: '#1e293b' }}
                  >
                    <Slider.Range
                      className="absolute rounded-full h-full"
                      style={{ backgroundColor: MODULE_COLORS[key] }}
                    />
                  </Slider.Track>
                  <Slider.Thumb
                    className="block w-4 h-4 rounded-full shadow-lg hover:shadow-xl transition-shadow"
                    style={{ backgroundColor: MODULE_COLORS[key] }}
                  />
                </Slider.Root>
              </div>
            ))}
          </div>

          <div className="mt-8 space-y-2">
            <button
              onClick={() => applyPreset('mfc')}
              className="w-full px-4 py-2 text-sm bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
            >
              Max MFC current
            </button>
            <button
              onClick={() => applyPreset('nitrogen')}
              className="w-full px-4 py-2 text-sm bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
            >
              N removal
            </button>
            <button
              onClick={() => applyPreset('production')}
              className="w-full px-4 py-2 text-sm bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
            >
              Production
            </button>
            <button
              onClick={() => applyPreset('reset')}
              className="w-full px-4 py-2 text-sm bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
            >
              Reset
            </button>
          </div>
        </aside>

        {/* Main Canvas */}
        <main className="flex-1 overflow-y-auto p-8">
          <div className="max-w-7xl mx-auto space-y-8">
            {/* 33-species ODE Simulator - MOVED TO TOP */}
            <SBMLSimulator modules={modules} />

            {/* Selected Consortium Table */}
            <section className="bg-slate-900/50 rounded-2xl p-6">
              <h3 className="text-lg mb-4">
                Your consortium — <span className="text-[#8FD14F]">{finalSelected.length}</span> / 20 circuits selected
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-slate-400 border-b border-slate-800">
                      <th className="text-left py-2 px-3">Score</th>
                      <th className="text-left py-2 px-3">Circuit name</th>
                      <th className="text-left py-2 px-3">Organism</th>
                      <th className="text-left py-2 px-3">Module</th>
                    </tr>
                  </thead>
                  <tbody>
                    {finalSelected.map((circuit) => (
                      <tr
                        key={circuit.id}
                        className="border-b border-slate-800/50 hover:bg-slate-800/30"
                      >
                        <td className="py-3 px-3">
                          <div className="flex items-center gap-2">
                            <div
                              className="w-2 h-2 rounded-full"
                              style={{
                                backgroundColor: MODULE_COLORS[circuit.category],
                              }}
                            />
                            <span>{circuit.score.toFixed(2)}</span>
                          </div>
                        </td>
                        <td className="py-3 px-3 font-mono text-xs">{circuit.name}</td>
                        <td className="py-3 px-3 text-slate-400">{circuit.organism}</td>
                        <td className="py-3 px-3 text-slate-400 text-xs">
                          {MODULE_LABELS[circuit.category]}
                        </td>
                      </tr>
                    ))}
                    {finalSelected.length === 0 && (
                      <tr>
                        <td colSpan={4} className="py-8 text-center text-slate-500">
                          No circuits selected. Lower threshold or increase module weights.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>

            {/* GOLDBAR Genetic Parts Table */}
            <section className="bg-slate-900/50 rounded-2xl p-6">
              <h3 className="text-lg mb-4">Genetic parts (GOLDBAR specs)</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-slate-400 border-b border-slate-800">
                      <th className="text-left py-2 px-3">Circuit</th>
                      <th className="text-left py-2 px-3">GOLDBAR specification</th>
                    </tr>
                  </thead>
                  <tbody>
                    {finalSelected.map((circuit) => (
                      <tr
                        key={circuit.id}
                        className="border-b border-slate-800/50 hover:bg-slate-800/30"
                      >
                        <td className="py-3 px-3 font-mono text-xs">{circuit.name}</td>
                        <td className="py-3 px-3">
                          <code className="text-xs text-slate-300">{circuit.goldbar}</code>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            {/* Ecosystem Summary */}
            <section className="bg-slate-900/50 rounded-2xl p-6">
                <h3 className="text-lg mb-4">Ecosystem summary</h3>
                <div className="space-y-3">
                  {(Object.keys(MODULE_LABELS) as ModuleKey[]).map((key) => {
                    const count = categoryCounts[key] || 0;
                    return (
                      <div key={key} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div
                            className="w-3 h-3 rounded-sm"
                            style={{ backgroundColor: MODULE_COLORS[key] }}
                          />
                          <span className="text-sm">{MODULE_LABELS[key]}</span>
                        </div>
                        <span className="text-sm text-slate-400">{count}</span>
                      </div>
                    );
                  })}
                </div>
                <p className="text-xs text-slate-500 mt-6 leading-relaxed">
                  Circuit selection driven by module weights &gt; 0. Dependency closure ensures required
                  base circuits are included.
                </p>
                <div className="mt-4 pt-4 border-t border-slate-800">
                  <div className="text-xs text-slate-400 space-y-1">
                    <div>Total organisms: {new Set(finalSelected.map(c => c.organism)).size}</div>
                    <div>Total circuits: {finalSelected.length} / 20</div>
                  </div>
                </div>
              </section>
          </div>
        </main>
      </div>
    </div>
  );
}
