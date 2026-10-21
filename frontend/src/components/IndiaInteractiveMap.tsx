'use client';

import React, { useEffect, useRef, useState, useMemo } from 'react';
import { api } from '@/lib/api';
import {
  MapPin,
  Search,
  Layers,
  Crosshair,
  Compass,
  Sparkles,
  Info,
  Maximize2,
  RefreshCw,
  Sprout,
  Check
} from 'lucide-react';

export interface SelectedLocation {
  district: string;
  state: string;
  agro_climatic_zone?: string;
  latitude: number;
  longitude: number;
  elevation_m?: number;
  soil_type?: string;
}

interface IndiaInteractiveMapProps {
  onLocationSelect: (location: SelectedLocation) => void;
  selectedLocation?: SelectedLocation | null;
  className?: string;
}

// Major agricultural presets across India's distinct agro-climatic zones
const AGRO_PRESETS = [
  { name: 'Punjab (Ludhiana)', district: 'Ludhiana', state: 'Punjab', lat: 30.9010, lng: 75.8573, crop: 'Wheat-Paddy Basin' },
  { name: 'Maharashtra (Nashik)', district: 'Nashik', state: 'Maharashtra', lat: 19.9975, lng: 73.7898, crop: 'Sugarcane & Grapes' },
  { name: 'Gujarat (Rajkot)', district: 'Rajkot', state: 'Gujarat', lat: 22.3039, lng: 70.8022, crop: 'Groundnut & Cotton' },
  { name: 'Andhra (Guntur)', district: 'Guntur', state: 'Andhra Pradesh', lat: 16.3067, lng: 80.4365, crop: 'Chilli & Rice Delta' },
  { name: 'Rajasthan (Jodhpur)', district: 'Jodhpur', state: 'Rajasthan', lat: 26.2389, lng: 73.0243, crop: 'Arid Micro-Drip' },
  { name: 'Karnataka (Mandya)', district: 'Mandya', state: 'Karnataka', lat: 12.5238, lng: 76.8967, crop: 'Cauvery Sugarcane' },
  { name: 'Assam (Jorhat)', district: 'Jorhat', state: 'Assam', lat: 26.7509, lng: 94.2037, crop: 'Humid Tea Gardens' },
];

interface MapLayerConfig {
  name: string;
  tileUrl: string;
  attribution: string;
  overlayUrl?: string;
}

const MAP_LAYERS: Record<'satellite' | 'street' | 'dark', MapLayerConfig> = {
  satellite: {
    name: 'Satellite Hybrid',
    tileUrl: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: '&copy; Esri, Maxar, Earthstar Geographics',
    overlayUrl: 'https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
  },
  street: {
    name: 'Topographic Voyager',
    tileUrl: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
    attribution: '&copy; OpenStreetMap &copy; CARTO',
  },
  dark: {
    name: 'Dark Tactical',
    tileUrl: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; OpenStreetMap &copy; CARTO',
  },
};

export default function IndiaInteractiveMap({
  onLocationSelect,
  selectedLocation,
  className = '',
}: IndiaInteractiveMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const markerRef = useRef<any>(null);
  const tileLayerRef = useRef<any>(null);
  const overlayLayerRef = useRef<any>(null);

  const [activeLayer, setActiveLayer] = useState<'satellite' | 'street' | 'dark'>('satellite');
  const [districts, setDistricts] = useState<Array<{ district: string; state: string; agro_climatic_zone: string; latitude: number; longitude: number }>>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [hoverInfo, setHoverInfo] = useState<{
    lat: number;
    lng: number;
    nearestDistrict?: string;
    nearestState?: string;
    zone?: string;
  } | null>(null);

  // Load district catalog for fast local spatial indexing
  useEffect(() => {
    let mounted = true;
    api.getIndiaDistricts()
      .then((data) => {
        if (mounted && Array.isArray(data)) {
          setDistricts(data);
        }
      })
      .catch((err) => {
        console.warn('Could not prefetch India districts catalog:', err);
      });
    return () => {
      mounted = false;
    };
  }, []);

  // Filtered districts for auto-complete search
  const filteredDistricts = useMemo(() => {
    if (!searchQuery.trim() || searchQuery.length < 2) return [];
    const q = searchQuery.toLowerCase();
    return districts
      .filter((d) => d.district.toLowerCase().includes(q) || d.state.toLowerCase().includes(q))
      .slice(0, 8);
  }, [searchQuery, districts]);

  // Find nearest district from catalog based on coordinates
  const findNearestDistrict = (lat: number, lng: number) => {
    if (!districts.length) return null;
    let minDistance = Infinity;
    let nearest: typeof districts[0] | null = null;

    for (let i = 0; i < districts.length; i++) {
      const d = districts[i];
      const dLat = d.latitude - lat;
      const dLng = d.longitude - lng;
      const distSq = dLat * dLat + dLng * dLng;
      if (distSq < minDistance) {
        minDistance = distSq;
        nearest = d;
      }
    }
    return nearest;
  };

  // Initialize Leaflet Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    let isCancelled = false;

    // Dynamically import Leaflet to avoid SSR window errors
    import('leaflet').then((L) => {
      if (isCancelled || !mapContainerRef.current) return;

      const initialLat = selectedLocation?.latitude || 22.5937;
      const initialLng = selectedLocation?.longitude || 78.9629;
      const initialZoom = selectedLocation ? 9 : 5;

      const map = L.map(mapContainerRef.current, {
        center: [initialLat, initialLng],
        zoom: initialZoom,
        minZoom: 4,
        maxZoom: 18,
        zoomControl: false,
        attributionControl: false,
      });

      // Custom sleek zoom control in top-right
      L.control.zoom({ position: 'topright' }).addTo(map);

      // Add Basemap Layer
      const layerConfig = MAP_LAYERS[activeLayer];
      const baseTileLayer = L.tileLayer(layerConfig.tileUrl, {
        maxZoom: 18,
        subdomains: 'abcd',
      }).addTo(map);
      tileLayerRef.current = baseTileLayer;

      if (layerConfig.overlayUrl) {
        overlayLayerRef.current = L.tileLayer(layerConfig.overlayUrl, { maxZoom: 18 }).addTo(map);
      }

      // Add Custom Glowing Marker
      const customIcon = L.divIcon({
        className: 'custom-pulse-marker',
        html: `
          <div class="relative flex items-center justify-center">
            <div class="absolute h-8 w-8 rounded-full bg-emerald-500/30 animate-ping"></div>
            <div class="absolute h-5 w-5 rounded-full bg-emerald-400/60 animate-pulse"></div>
            <div class="h-3.5 w-3.5 rounded-full bg-emerald-500 border-2 border-white shadow-lg"></div>
          </div>
        `,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
      });

      const marker = L.marker([initialLat, initialLng], { icon: customIcon }).addTo(map);
      markerRef.current = marker;

      // Mouse Move Listener (Hover Spatial Inspector)
      map.on('mousemove', (e: any) => {
        const { lat, lng } = e.latlng;
        // Restrict inspection within reasonable Indian subcontinent bounds
        if (lat >= 6.0 && lat <= 38.0 && lng >= 68.0 && lng <= 98.0) {
          const nearest = findNearestDistrict(lat, lng);
          setHoverInfo({
            lat,
            lng,
            nearestDistrict: nearest?.district,
            nearestState: nearest?.state,
            zone: nearest?.agro_climatic_zone,
          });
        }
      });

      // Click to select location
      map.on('click', (e: any) => {
        const { lat, lng } = e.latlng;
        marker.setLatLng([lat, lng]);
        
        const nearest = findNearestDistrict(lat, lng);
        const resolvedLocation: SelectedLocation = {
          district: nearest ? nearest.district : 'Custom Coordinates',
          state: nearest ? nearest.state : 'India',
          agro_climatic_zone: nearest?.agro_climatic_zone,
          latitude: Number(lat.toFixed(4)),
          longitude: Number(lng.toFixed(4)),
        };

        onLocationSelect(resolvedLocation);
      });

      mapInstanceRef.current = map;
    });

    return () => {
      isCancelled = true;
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update map layer when changed
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    import('leaflet').then((L) => {
      const map = mapInstanceRef.current;
      const config = MAP_LAYERS[activeLayer];

      if (tileLayerRef.current) {
        map.removeLayer(tileLayerRef.current);
      }
      if (overlayLayerRef.current) {
        map.removeLayer(overlayLayerRef.current);
        overlayLayerRef.current = null;
      }

      tileLayerRef.current = L.tileLayer(config.tileUrl, {
        maxZoom: 18,
        subdomains: 'abcd',
      }).addTo(map);

      if (config.overlayUrl) {
        overlayLayerRef.current = L.tileLayer(config.overlayUrl, { maxZoom: 18 }).addTo(map);
      }
    });
  }, [activeLayer]);

  // Sync marker position when selectedLocation changes externally
  useEffect(() => {
    if (!selectedLocation || !mapInstanceRef.current || !markerRef.current) return;
    const { latitude, longitude } = selectedLocation;
    markerRef.current.setLatLng([latitude, longitude]);
    mapInstanceRef.current.flyTo([latitude, longitude], Math.max(mapInstanceRef.current.getZoom(), 8), {
      duration: 1.2,
    });
  }, [selectedLocation?.latitude, selectedLocation?.longitude]);

  // Select Preset Hub
  const handleSelectPreset = (preset: typeof AGRO_PRESETS[0]) => {
    const loc: SelectedLocation = {
      district: preset.district,
      state: preset.state,
      latitude: preset.lat,
      longitude: preset.lng,
    };
    onLocationSelect(loc);
    if (mapInstanceRef.current) {
      mapInstanceRef.current.flyTo([preset.lat, preset.lng], 9, { duration: 1.2 });
    }
  };

  // Select from Search Dropdown
  const handleSelectDistrict = (d: typeof districts[0]) => {
    const loc: SelectedLocation = {
      district: d.district,
      state: d.state,
      agro_climatic_zone: d.agro_climatic_zone,
      latitude: d.latitude,
      longitude: d.longitude,
    };
    onLocationSelect(loc);
    setSearchQuery('');
    setIsSearching(false);
    if (mapInstanceRef.current) {
      mapInstanceRef.current.flyTo([d.latitude, d.longitude], 10, { duration: 1.2 });
    }
  };

  return (
    <div className={`relative flex flex-col rounded-2xl overflow-hidden border border-slate-700/60 bg-slate-950 shadow-2xl ${className}`}>
      {/* 1. Header Toolbar & Search Bar */}
      <div className="z-10 flex flex-wrap items-center justify-between gap-3 bg-slate-900/90 backdrop-blur-md px-4 py-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
            <Compass className="h-4 w-4 animate-spin-slow" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-white tracking-wide uppercase">
                India Spatial Geo-Inspector
              </span>
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.2 text-[10px] font-semibold text-emerald-400">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Live Map
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Hover across India to inspect regional soil & climate; click to evaluate fuzzy irrigation.
            </p>
          </div>
        </div>

        {/* Search & Basemap Layer Switcher */}
        <div className="flex items-center gap-2">
          {/* Autocomplete District Search */}
          <div className="relative">
            <div className="relative flex items-center">
              <Search className="absolute left-2.5 h-3.5 w-3.5 text-slate-400" />
              <input
                type="text"
                placeholder="Search district, city or PIN..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setIsSearching(true);
                }}
                onFocus={() => setIsSearching(true)}
                className="w-48 sm:w-60 rounded-xl border border-slate-700 bg-slate-800/90 pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 transition"
              />
            </div>

            {/* Dropdown Results */}
            {isSearching && filteredDistricts.length > 0 && (
              <div className="absolute left-0 mt-1.5 w-72 rounded-xl border border-slate-700 bg-slate-900/95 backdrop-blur-xl shadow-2xl overflow-hidden z-50 divide-y divide-slate-800">
                {filteredDistricts.map((d) => (
                  <button
                    key={`${d.district}-${d.state}`}
                    onClick={() => handleSelectDistrict(d)}
                    className="w-full px-3.5 py-2.5 text-left text-xs hover:bg-emerald-950/40 hover:text-emerald-300 transition flex items-center justify-between group cursor-pointer"
                  >
                    <div>
                      <div className="font-semibold text-slate-200 group-hover:text-emerald-300">
                        {d.district}, {d.state}
                      </div>
                      <div className="text-[10px] text-slate-500">{d.agro_climatic_zone}</div>
                    </div>
                    <MapPin className="h-3.5 w-3.5 text-slate-600 group-hover:text-emerald-400 shrink-0" />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Layer Selector */}
          <div className="flex items-center rounded-xl border border-slate-700 bg-slate-800/80 p-0.5 text-[11px] font-medium text-slate-300">
            <button
              onClick={() => setActiveLayer('satellite')}
              className={`px-2.5 py-1 rounded-lg transition cursor-pointer ${
                activeLayer === 'satellite' ? 'bg-emerald-600 text-white font-semibold' : 'hover:text-white'
              }`}
            >
              Satellite
            </button>
            <button
              onClick={() => setActiveLayer('street')}
              className={`px-2.5 py-1 rounded-lg transition cursor-pointer ${
                activeLayer === 'street' ? 'bg-emerald-600 text-white font-semibold' : 'hover:text-white'
              }`}
            >
              Terrain
            </button>
            <button
              onClick={() => setActiveLayer('dark')}
              className={`px-2.5 py-1 rounded-lg transition cursor-pointer ${
                activeLayer === 'dark' ? 'bg-emerald-600 text-white font-semibold' : 'hover:text-white'
              }`}
            >
              Dark
            </button>
          </div>
        </div>
      </div>

      {/* 2. Map Canvas Viewport */}
      <div className="relative h-[420px] sm:h-[480px] w-full bg-slate-950">
        <div ref={mapContainerRef} className="h-full w-full z-0" />

        {/* Floating Spatial Hover HUD (Top-Left of Map) */}
        {hoverInfo && (
          <div className="absolute top-3 left-3 z-20 pointer-events-none rounded-xl border border-emerald-500/30 bg-slate-900/90 backdrop-blur-md px-3.5 py-2.5 text-slate-200 shadow-xl max-w-xs animate-in fade-in duration-150">
            <div className="flex items-center gap-1.5 text-[10px] font-bold text-emerald-400 tracking-wider uppercase">
              <Crosshair className="h-3 w-3 animate-spin-slow" />
              <span>Spatial Telemetry Cursor</span>
            </div>
            <div className="mt-1 font-semibold text-xs text-white">
              {hoverInfo.nearestDistrict ? `${hoverInfo.nearestDistrict}, ${hoverInfo.nearestState}` : 'Subcontinent Region'}
            </div>
            {hoverInfo.zone && (
              <div className="text-[10px] text-slate-400 truncate mt-0.5">{hoverInfo.zone}</div>
            )}
            <div className="mt-1.5 flex items-center gap-3 font-mono text-[10px] text-slate-400 border-t border-slate-800 pt-1">
              <span>Lat: {hoverInfo.lat.toFixed(4)}°N</span>
              <span>Lng: {hoverInfo.lng.toFixed(4)}°E</span>
            </div>
          </div>
        )}

        {/* Selected Location Pill (Bottom-Left of Map) */}
        {selectedLocation && (
          <div className="absolute bottom-3 left-3 z-20 rounded-xl border border-emerald-500/40 bg-slate-900/90 backdrop-blur-md px-4 py-2.5 shadow-2xl">
            <div className="flex items-center gap-2">
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400">
                <Check className="h-3.5 w-3.5" />
              </div>
              <div>
                <span className="text-[10px] uppercase font-bold text-emerald-400 block tracking-wider">
                  Target Location Locked
                </span>
                <span className="text-xs font-bold text-white block">
                  {selectedLocation.district}, {selectedLocation.state}
                </span>
              </div>
              <div className="ml-3 pl-3 border-l border-slate-700 text-right font-mono text-[11px] text-slate-300">
                <div>{selectedLocation.latitude}° N</div>
                <div>{selectedLocation.longitude}° E</div>
              </div>
            </div>
          </div>
        )}

        {/* Quick Instructional Overlay (Bottom-Right) */}
        <div className="absolute bottom-3 right-3 z-20 pointer-events-none rounded-lg bg-slate-900/80 backdrop-blur-sm border border-slate-800 px-2.5 py-1 text-[10px] text-slate-400">
          Click any point to lock location & evaluate FIS
        </div>
      </div>

      {/* 3. Rapid Agricultural Hub Presets Ribbon */}
      <div className="z-10 bg-slate-900/95 border-t border-slate-800 px-4 py-2.5 flex items-center gap-2 overflow-x-auto touch-scroll">
        <span className="text-[11px] font-semibold text-slate-400 shrink-0 flex items-center gap-1">
          <Sprout className="h-3.5 w-3.5 text-emerald-400" />
          Agro Hubs:
        </span>
        <div className="flex items-center gap-1.5 shrink-0">
          {AGRO_PRESETS.map((p) => {
            const isSelected = selectedLocation?.district === p.district;
            return (
              <button
                key={p.name}
                onClick={() => handleSelectPreset(p)}
                className={`rounded-xl px-2.5 py-1 text-[11px] font-medium transition cursor-pointer flex items-center gap-1.5 ${
                  isSelected
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-semibold'
                    : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700 hover:text-white border border-slate-700/50'
                }`}
                title={p.crop}
              >
                <span>{p.name}</span>
                <span className="text-[9px] text-slate-500 hidden sm:inline">({p.crop})</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
