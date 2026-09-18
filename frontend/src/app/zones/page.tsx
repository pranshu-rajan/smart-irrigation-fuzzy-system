'use client';

import React, { useState, useEffect } from 'react';
import { api, ZoneConfig } from '@/lib/api';

export default function ZonesManagementPage() {
  const [zones, setZones] = useState<ZoneConfig[]>([]);
  const [crops, setCrops] = useState<any[]>([]);
  const [soils, setSoils] = useState<any[]>([]);
  const [editingZone, setEditingZone] = useState<ZoneConfig | null>(null);
  const [loading, setLoading] = useState(true);

  const loadZoneData = async () => {
    try {
      const [zonesData, cropsData, soilsData] = await Promise.all([
        api.getZones(),
        api.getCrops(),
        api.getSoils(),
      ]);
      setZones(zonesData);
      setCrops(cropsData);
      setSoils(soilsData);
    } catch (err) {
      console.error('Failed to load zones data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadZoneData();
  }, []);

  const handleSaveZone = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingZone) return;

    try {
      await api.updateZone(editingZone.id, editingZone);
      await loadZoneData();
      setEditingZone(null);
      alert(`Zone ${editingZone.id} updated successfully!`);
    } catch (err: any) {
      alert(`Failed to update zone: ${err.message}`);
    }
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Zone Configuration & Agronomy Management</h1>
        <p className="mt-1 text-sm text-slate-400">
          Configure crop agronomic parameters, soil hydraulic properties, surface areas, and priority weights across all irrigation zones.
        </p>
      </div>

      {/* Zones Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {zones.map((z) => (
          <div
            key={z.id}
            className="flex flex-col justify-between rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur transition-all hover:border-slate-700"
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-semibold text-emerald-400">ZONE 0{z.id}</span>
                <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                  z.is_active ? 'bg-emerald-950 text-emerald-400 border border-emerald-500/20' : 'bg-slate-800 text-slate-400'
                }`}>
                  {z.is_active ? 'ACTIVE' : 'INACTIVE'}
                </span>
              </div>

              <h2 className="mt-2 text-xl font-bold text-white">{z.name}</h2>
              <div className="mt-2 space-y-2 text-xs text-slate-300">
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Crop Cultivar:</span>
                  <span className="font-semibold text-white">🌱 {z.crop_type}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Soil Texture:</span>
                  <span className="font-semibold text-white">🪨 {z.soil_type}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Cultivated Area:</span>
                  <span className="font-mono text-white">{z.area_m2} m²</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Target Moisture:</span>
                  <span className="font-mono text-cyan-400 font-bold">
                    {(z.target_moisture_fraction * 100).toFixed(1)}% vol
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Valve Flow Rate:</span>
                  <span className="font-mono text-white">{z.flow_rate_lpm} L/min</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-400">Supervisory Priority:</span>
                  <span className="font-mono text-amber-400 font-bold">
                    {(z.priority_weight * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-slate-800">
              <button
                onClick={() => setEditingZone(z)}
                className="w-full rounded-lg bg-slate-800 hover:bg-slate-700 py-2 text-xs font-semibold text-white transition-colors"
              >
                ✏️ Edit Zone Properties
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Edit Modal */}
      {editingZone && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-xl border border-slate-700 bg-slate-900 p-6 shadow-2xl space-y-4">
            <h2 className="text-lg font-bold text-white">Edit Zone {editingZone.id} Parameters</h2>
            <form onSubmit={handleSaveZone} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Zone Name</label>
                <input
                  type="text"
                  value={editingZone.name}
                  onChange={(e) => setEditingZone({ ...editingZone, name: e.target.value })}
                  className="w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-white"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Crop Type</label>
                  <select
                    value={editingZone.crop_type}
                    onChange={(e) => setEditingZone({ ...editingZone, crop_type: e.target.value })}
                    className="w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-white"
                  >
                    <option value="Tomato">Tomato</option>
                    <option value="Potato">Potato</option>
                    <option value="Maize">Maize</option>
                    <option value="Wheat">Wheat</option>
                    <option value="Soybean">Soybean</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">Soil Type</label>
                  <select
                    value={editingZone.soil_type}
                    onChange={(e) => setEditingZone({ ...editingZone, soil_type: e.target.value })}
                    className="w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-white"
                  >
                    <option value="Loam">Loam</option>
                    <option value="Sandy Loam">Sandy Loam</option>
                    <option value="Clay Loam">Clay Loam</option>
                    <option value="Clay">Clay</option>
                    <option value="Sand">Sand</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Area (m²)</label>
                  <input
                    type="number"
                    value={editingZone.area_m2}
                    onChange={(e) => setEditingZone({ ...editingZone, area_m2: parseFloat(e.target.value) || 0 })}
                    className="w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-white font-mono"
                  />
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">Flow Rate (L/min)</label>
                  <input
                    type="number"
                    value={editingZone.flow_rate_lpm}
                    onChange={(e) => setEditingZone({ ...editingZone, flow_rate_lpm: parseFloat(e.target.value) || 0 })}
                    className="w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-white font-mono"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Target Moisture (0.1–0.5)</label>
                  <input
                    type="number"
                    step={0.01}
                    min={0.1}
                    max={0.5}
                    value={editingZone.target_moisture_fraction}
                    onChange={(e) => setEditingZone({ ...editingZone, target_moisture_fraction: parseFloat(e.target.value) || 0.28 })}
                    className="w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-white font-mono"
                  />
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">Priority Weight (0.1–1.0)</label>
                  <input
                    type="number"
                    step={0.1}
                    min={0.1}
                    max={1.0}
                    value={editingZone.priority_weight}
                    onChange={(e) => setEditingZone({ ...editingZone, priority_weight: parseFloat(e.target.value) || 1.0 })}
                    className="w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-white font-mono"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setEditingZone(null)}
                  className="rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-emerald-500 px-5 py-2 text-xs font-bold text-slate-950 hover:bg-emerald-400"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reference Agronomy & Soil Physics Specifications */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-white">Agronomic Soil Hydraulic Reference Table</h2>
        <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/40">
          <table className="w-full text-left text-xs text-slate-300 font-mono">
            <thead className="border-b border-slate-800 bg-slate-900 text-[11px] uppercase tracking-wider text-slate-400">
              <tr>
                <th className="px-4 py-3">Soil Texture</th>
                <th className="px-4 py-3">Field Capacity (θ_FC)</th>
                <th className="px-4 py-3">Wilting Point (θ_WP)</th>
                <th className="px-4 py-3">Available Water Capacity (AWC)</th>
                <th className="px-4 py-3">Infiltration Rate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-[11px]">
              <tr className="hover:bg-slate-800/30">
                <td className="px-4 py-2.5 font-bold text-white">Loam (Zone 1)</td>
                <td className="px-4 py-2.5">0.27 vol fraction</td>
                <td className="px-4 py-2.5">0.12 vol fraction</td>
                <td className="px-4 py-2.5 text-cyan-400">0.15 vol fraction</td>
                <td className="px-4 py-2.5">13.0 mm/hr</td>
              </tr>
              <tr className="hover:bg-slate-800/30">
                <td className="px-4 py-2.5 font-bold text-white">Sandy Loam (Zone 2)</td>
                <td className="px-4 py-2.5">0.18 vol fraction</td>
                <td className="px-4 py-2.5">0.08 vol fraction</td>
                <td className="px-4 py-2.5 text-cyan-400">0.10 vol fraction</td>
                <td className="px-4 py-2.5">25.0 mm/hr</td>
              </tr>
              <tr className="hover:bg-slate-800/30">
                <td className="px-4 py-2.5 font-bold text-white">Clay Loam (Zone 3)</td>
                <td className="px-4 py-2.5">0.32 vol fraction</td>
                <td className="px-4 py-2.5">0.18 vol fraction</td>
                <td className="px-4 py-2.5 text-cyan-400">0.14 vol fraction</td>
                <td className="px-4 py-2.5">8.0 mm/hr</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
