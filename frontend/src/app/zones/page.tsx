'use client';

import React, { useState, useEffect } from 'react';
import { api, ZoneConfig } from '@/lib/api';
import { Sprout, Layers, Pencil } from 'lucide-react';

export default function ZonesManagementPage() {
  const [zones, setZones] = useState<ZoneConfig[]>([]);
  const [crops, setCrops] = useState<any[]>([]);
  const [soils, setSoils] = useState<any[]>([]);
  const [editingZone, setEditingZone] = useState<ZoneConfig | null>(null);
  const [zoneFeedback, setZoneFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [loading, setLoading] = useState(true);

  const loadZoneData = async () => {
    try {
      const [zonesData, cropsData, soilsData] = await Promise.all([
        api.getZones(),
        api.getCrops(),
        api.getSoils(),
      ]);

      const normalized = (zonesData || []).map((z: any, idx: number) => {
        const zoneNum = z.zone_id !== undefined ? Number(z.zone_id) : idx + 1;
        const targetMoistFrac = z.target_moisture_fraction !== undefined
          ? Number(z.target_moisture_fraction)
          : z.target_moisture !== undefined
          ? Number(z.target_moisture) > 1 ? Number(z.target_moisture) / 100 : Number(z.target_moisture)
          : 0.28;

        const priorityWt = z.priority_weight !== undefined
          ? Number(z.priority_weight)
          : z.priority !== undefined
          ? Number(z.priority) > 1 ? Number(z.priority) / 100 : Number(z.priority)
          : 0.8;

        return {
          id: zoneNum,
          name: z.name || `Zone ${zoneNum} - ${z.crop || 'Crop'} / ${z.soil || 'Soil'}`,
          crop_type: z.crop_type || z.crop || (zoneNum === 1 ? 'Tomato' : zoneNum === 2 ? 'Wheat' : 'Maize'),
          soil_type: z.soil_type || z.soil || (zoneNum === 1 ? 'Loam' : zoneNum === 2 ? 'Sandy Loam' : 'Clay Loam'),
          area_m2: Number(z.area_m2 || (zoneNum === 1 ? 100 : zoneNum === 2 ? 120 : 80)),
          target_moisture_fraction: targetMoistFrac,
          flow_rate_lpm: Number(z.flow_rate_lpm || 15.0),
          priority_weight: priorityWt,
          is_active: z.is_active !== undefined ? Boolean(z.is_active) : true,
        };
      });

      setZones(normalized);
      setCrops(cropsData || []);
      setSoils(soilsData || []);
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
    setZoneFeedback(null);

    try {
      await api.updateZone(editingZone.id, editingZone);
      await loadZoneData();
      setEditingZone(null);
      setZoneFeedback({
        type: 'success',
        message: `Zone ${editingZone.id} (${editingZone.name}) updated successfully!`,
      });
    } catch (err: any) {
      setZoneFeedback({
        type: 'error',
        message: `Failed to update zone: ${err.message}`,
      });
    }
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="inline-flex items-center rounded-md bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-800 border border-emerald-200/80">
            Agronomic Management
          </span>
          <span className="text-xs text-slate-400">•</span>
          <span className="text-xs text-slate-600 font-medium">Multi-Crop Soil Hydraulics & Flow Rates</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Zone Configuration & Agronomy Management</h1>
        <p className="mt-1 text-sm text-slate-600">
          Configure crop agronomic parameters, soil hydraulic properties, surface areas, and priority weights across all irrigation zones.
        </p>
      </div>

      {/* Accessible Inline Status Feedback */}
      {zoneFeedback && (
        <div
          role={zoneFeedback.type === 'error' ? 'alert' : 'status'}
          aria-live="polite"
          className={`rounded-2xl border p-4 text-xs font-semibold flex items-center justify-between gap-3 shadow-2xs ${
            zoneFeedback.type === 'error'
              ? 'border-rose-300 bg-rose-50 text-rose-900'
              : 'border-emerald-300 bg-emerald-50 text-emerald-950'
          }`}
        >
          <span>{zoneFeedback.message}</span>
          <button
            onClick={() => setZoneFeedback(null)}
            className="text-xs px-2 py-0.5 rounded hover:bg-black/5 font-mono cursor-pointer"
            aria-label="Dismiss notification"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Zones Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {zones.map((z) => (
          <div
            key={z.id}
            className="flex flex-col justify-between rounded-2xl border border-slate-200/90 bg-white p-6 shadow-xs transition-all hover:border-emerald-300 hover:shadow-sm"
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">ZONE 0{z.id}</span>
                <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold ${
                  z.is_active ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-600'
                }`}>
                  {z.is_active ? 'ACTIVE' : 'INACTIVE'}
                </span>
              </div>

              <h2 className="mt-3 text-lg font-bold text-slate-900">{z.name}</h2>
              <div className="mt-3 space-y-2 text-xs text-slate-700">
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">Crop Cultivar:</span>
                  <span className="inline-flex items-center gap-1 font-semibold text-slate-900">
                    <Sprout className="h-3.5 w-3.5 text-emerald-600" />
                    <span>{z.crop_type}</span>
                  </span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">Soil Texture:</span>
                  <span className="inline-flex items-center gap-1 font-semibold text-slate-900">
                    <Layers className="h-3.5 w-3.5 text-amber-700" />
                    <span>{z.soil_type}</span>
                  </span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">Cultivated Area:</span>
                  <span className="font-mono font-bold text-slate-900">{z.area_m2} m²</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">Target Moisture:</span>
                  <span className="font-mono text-sky-700 font-bold bg-sky-50 px-1.5 py-0.5 rounded border border-sky-200">
                    {(z.target_moisture_fraction * 100).toFixed(1)}% vol
                  </span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">Valve Flow Rate:</span>
                  <span className="font-mono font-bold text-slate-900">{z.flow_rate_lpm} L/min</span>
                </div>
                <div className="flex justify-between py-1.5">
                  <span className="text-slate-500">Supervisory Priority:</span>
                  <span className="font-mono text-amber-800 font-bold bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200">
                    {(z.priority_weight * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-slate-100">
              <button
                onClick={() => setEditingZone(z)}
                className="w-full rounded-xl bg-slate-100 hover:bg-slate-200/80 py-2.5 text-xs font-semibold text-slate-800 transition-colors cursor-pointer inline-flex items-center justify-center gap-1.5"
              >
                <Pencil className="h-3.5 w-3.5" />
                <span>Edit Zone Properties</span>
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Edit Modal */}
      {editingZone && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-xs">
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="edit-zone-title"
            className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl space-y-4"
          >
            <h2 id="edit-zone-title" className="text-base font-bold text-slate-900">
              Edit Zone {editingZone.id} Parameters
            </h2>
            <form onSubmit={handleSaveZone} className="space-y-3 text-xs">
              <div>
                <label htmlFor="edit-zone-name" className="block text-slate-700 font-semibold mb-1">Zone Name</label>
                <input
                  id="edit-zone-name"
                  type="text"
                  value={editingZone.name}
                  onChange={(e) => setEditingZone({ ...editingZone, name: e.target.value })}
                  aria-label="Zone name"
                  className="w-full rounded-lg border border-slate-300 bg-slate-50/70 px-3 py-2 text-slate-900 font-medium focus:bg-white focus:border-emerald-500 focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label htmlFor="edit-crop-type" className="block text-slate-700 font-semibold mb-1">Crop Type</label>
                  <select
                    id="edit-crop-type"
                    value={editingZone.crop_type}
                    onChange={(e) => setEditingZone({ ...editingZone, crop_type: e.target.value })}
                    aria-label="Crop cultivar"
                    className="w-full rounded-lg border border-slate-300 bg-slate-50/70 px-3 py-2 text-slate-900 font-medium focus:bg-white focus:border-emerald-500 focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none"
                  >
                    <option value="Tomato">Tomato</option>
                    <option value="Potato">Potato</option>
                    <option value="Maize">Maize</option>
                    <option value="Wheat">Wheat</option>
                    <option value="Soybean">Soybean</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="edit-soil-type" className="block text-slate-700 font-semibold mb-1">Soil Type</label>
                  <select
                    id="edit-soil-type"
                    value={editingZone.soil_type}
                    onChange={(e) => setEditingZone({ ...editingZone, soil_type: e.target.value })}
                    aria-label="Soil texture"
                    className="w-full rounded-lg border border-slate-300 bg-slate-50/70 px-3 py-2 text-slate-900 font-medium focus:bg-white focus:border-emerald-500 focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none"
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
                  <label htmlFor="edit-area-m2" className="block text-slate-700 font-semibold mb-1">Area (m²)</label>
                  <input
                    id="edit-area-m2"
                    type="number"
                    value={editingZone.area_m2}
                    onChange={(e) => setEditingZone({ ...editingZone, area_m2: parseFloat(e.target.value) || 0 })}
                    aria-label="Zone surface area in square meters"
                    className="w-full rounded-lg border border-slate-300 bg-slate-50/70 px-3 py-2 text-slate-900 font-mono focus:bg-white focus:border-emerald-500 focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none"
                  />
                </div>

                <div>
                  <label htmlFor="edit-flow-rate" className="block text-slate-700 font-semibold mb-1">Flow Rate (L/min)</label>
                  <input
                    id="edit-flow-rate"
                    type="number"
                    value={editingZone.flow_rate_lpm}
                    onChange={(e) => setEditingZone({ ...editingZone, flow_rate_lpm: parseFloat(e.target.value) || 0 })}
                    aria-label="Sprinkler flow rate in liters per minute"
                    className="w-full rounded-lg border border-slate-300 bg-slate-50/70 px-3 py-2 text-slate-900 font-mono focus:bg-white focus:border-emerald-500 focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label htmlFor="edit-target-moisture" className="block text-slate-700 font-semibold mb-1">Target Moisture (0.1–0.5)</label>
                  <input
                    id="edit-target-moisture"
                    type="number"
                    step={0.01}
                    min={0.1}
                    max={0.5}
                    value={editingZone.target_moisture_fraction}
                    onChange={(e) => setEditingZone({ ...editingZone, target_moisture_fraction: parseFloat(e.target.value) || 0.28 })}
                    aria-label="Target moisture volumetric fraction"
                    className="w-full rounded-lg border border-slate-300 bg-slate-50/70 px-3 py-2 text-slate-900 font-mono focus:bg-white focus:border-emerald-500 focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none"
                  />
                </div>

                <div>
                  <label htmlFor="edit-priority-weight" className="block text-slate-700 font-semibold mb-1">Priority Weight (0.1–1.0)</label>
                  <input
                    id="edit-priority-weight"
                    type="number"
                    step={0.1}
                    min={0.1}
                    max={1.0}
                    value={editingZone.priority_weight}
                    onChange={(e) => setEditingZone({ ...editingZone, priority_weight: parseFloat(e.target.value) || 1.0 })}
                    aria-label="Scarcity priority allocation weight"
                    className="w-full rounded-lg border border-slate-300 bg-slate-50/70 px-3 py-2 text-slate-900 font-mono focus:bg-white focus:border-emerald-500 focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setEditingZone(null)}
                  className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-xl bg-emerald-600 px-5 py-2 text-xs font-bold text-white hover:bg-emerald-700 shadow-md shadow-emerald-600/15 transition-all cursor-pointer focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none"
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
        <h2 className="text-lg font-bold text-slate-900">Agronomic Soil Hydraulic Reference Table</h2>
        <div className="overflow-hidden rounded-2xl border border-slate-200/90 bg-white shadow-xs">
          <table className="w-full text-left text-xs text-slate-700 font-mono">
            <thead className="border-b border-slate-200 bg-slate-50 text-[11px] uppercase tracking-wider text-slate-600">
              <tr>
                <th className="px-4 py-3">Soil Texture</th>
                <th className="px-4 py-3">Field Capacity (θ_FC)</th>
                <th className="px-4 py-3">Wilting Point (θ_WP)</th>
                <th className="px-4 py-3">Available Water Capacity (AWC)</th>
                <th className="px-4 py-3">Infiltration Rate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-[11px]">
              <tr className="hover:bg-emerald-50/40 transition-colors">
                <td className="px-4 py-2.5 font-bold text-slate-900">Loam (Zone 1)</td>
                <td className="px-4 py-2.5">0.27 vol fraction</td>
                <td className="px-4 py-2.5">0.12 vol fraction</td>
                <td className="px-4 py-2.5 text-emerald-700 font-bold">0.15 vol fraction</td>
                <td className="px-4 py-2.5">13.0 mm/hr</td>
              </tr>
              <tr className="hover:bg-emerald-50/40 transition-colors">
                <td className="px-4 py-2.5 font-bold text-slate-900">Sandy Loam (Zone 2)</td>
                <td className="px-4 py-2.5">0.18 vol fraction</td>
                <td className="px-4 py-2.5">0.08 vol fraction</td>
                <td className="px-4 py-2.5 text-emerald-700 font-bold">0.10 vol fraction</td>
                <td className="px-4 py-2.5">25.0 mm/hr</td>
              </tr>
              <tr className="hover:bg-emerald-50/40 transition-colors">
                <td className="px-4 py-2.5 font-bold text-slate-900">Clay Loam (Zone 3)</td>
                <td className="px-4 py-2.5">0.32 vol fraction</td>
                <td className="px-4 py-2.5">0.18 vol fraction</td>
                <td className="px-4 py-2.5 text-emerald-700 font-bold">0.14 vol fraction</td>
                <td className="px-4 py-2.5">8.0 mm/hr</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
