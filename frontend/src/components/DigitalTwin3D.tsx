'use client';

import React, { useEffect, useRef, useState, useMemo } from 'react';
import * as THREE from 'three';
import { Droplets, Sparkles, CheckCircle, Eye, Compass, Layers, RotateCcw } from 'lucide-react';
import { useTheme } from '@/context/ThemeContext';
import { soundEngine } from '@/lib/audioHaptics';

export interface DigitalTwinZoneProp {
  id: number;
  name: string;
  crop: string;
  soil: string;
  moisture: number;
  target: number;
  isIrrigating: boolean;
  flowRateLpm?: number;
}

interface DigitalTwin3DProps {
  zones?: DigitalTwinZoneProp[];
  selectedZoneId?: number;
  onZoneSelect?: (id: number) => void;
  className?: string;
}

const DEFAULT_ZONES: DigitalTwinZoneProp[] = [
  { id: 1, name: 'Zone 1: Cash Crop', crop: 'Tomato', soil: 'Loam', moisture: 23.5, target: 28.0, isIrrigating: true, flowRateLpm: 15.8 },
  { id: 2, name: 'Zone 2: Grain Field', crop: 'Wheat', soil: 'Sandy Loam', moisture: 21.0, target: 24.0, isIrrigating: false, flowRateLpm: 0.0 },
  { id: 3, name: 'Zone 3: Pasture', crop: 'Maize', soil: 'Clay', moisture: 29.5, target: 30.0, isIrrigating: true, flowRateLpm: 12.4 },
];

export default function DigitalTwin3D({
  zones: propZones,
  selectedZoneId: propSelectedId,
  onZoneSelect,
  className = '',
}: DigitalTwin3DProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const { theme } = useTheme();

  const zones = propZones && propZones.length > 0 ? propZones : DEFAULT_ZONES;
  const [activeZoneId, setActiveZoneId] = useState<number>(propSelectedId || 1);
  const [cameraView, setCameraView] = useState<'overview' | 1 | 2 | 3>('overview');

  // Three.js refs for live mutation
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const soilMeshesRef = useRef<THREE.Mesh[]>([]);
  const particleSystemsRef = useRef<{ points: THREE.Points; geo: THREE.BufferGeometry; vel: Float32Array; active: boolean }[]>([]);
  const targetCamPosRef = useRef<THREE.Vector3>(new THREE.Vector3(0, 18, 26));
  const targetCamLookRef = useRef<THREE.Vector3>(new THREE.Vector3(0, 1, 0));

  // Sync selected zone from props
  useEffect(() => {
    if (propSelectedId !== undefined) {
      setActiveZoneId(propSelectedId);
    }
  }, [propSelectedId]);

  // Handle camera view presets
  const switchCameraView = (view: 'overview' | 1 | 2 | 3) => {
    setCameraView(view);
    soundEngine.playSliderTick();
    const zoneSpacing = 8.5;

    if (view === 'overview') {
      targetCamPosRef.current.set(0, 18, 26);
      targetCamLookRef.current.set(0, 1, 0);
    } else {
      const idx = view - 1;
      const posX = (idx - 1) * zoneSpacing;
      targetCamPosRef.current.set(posX, 9, 14);
      targetCamLookRef.current.set(posX, 1.5, 0);
      setActiveZoneId(view);
      if (onZoneSelect) onZoneSelect(view);
    }
  };

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    // 1. Scene & Camera
    const width = container.clientWidth;
    const height = container.clientHeight || 420;
    const scene = new THREE.Scene();
    sceneRef.current = scene;

    const isDark = theme === 'dark';
    scene.background = new THREE.Color(isDark ? 0x070d0a : 0xf1f5f9);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 18, 26);
    camera.lookAt(0, 1, 0);
    cameraRef.current = camera;

    // 2. Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // 3. Lighting
    const ambientLight = new THREE.AmbientLight(isDark ? 0x94a3b8 : 0xffffff, isDark ? 0.6 : 0.85);
    scene.add(ambientLight);

    const sunLight = new THREE.DirectionalLight(isDark ? 0x38bdf8 : 0xfef08a, isDark ? 1.2 : 1.4);
    sunLight.position.set(15, 25, 12);
    sunLight.castShadow = true;
    sunLight.shadow.mapSize.width = 1024;
    sunLight.shadow.mapSize.height = 1024;
    scene.add(sunLight);

    const hemiLight = new THREE.HemisphereLight(
      isDark ? 0x064e3b : 0xe0f2fe,
      isDark ? 0x022c22 : 0xf0fdf4,
      0.6
    );
    scene.add(hemiLight);

    // 4. Base Foundation Plot
    const baseGeo = new THREE.BoxGeometry(28, 0.8, 14);
    const baseMat = new THREE.MeshStandardMaterial({
      color: isDark ? 0x0f1b15 : 0xe2e8f0,
      roughness: 0.8,
      metalness: 0.1,
    });
    const baseMesh = new THREE.Mesh(baseGeo, baseMat);
    baseMesh.position.y = -0.5;
    baseMesh.receiveShadow = true;
    scene.add(baseMesh);

    // Grid Floor Overlay
    const gridHelper = new THREE.GridHelper(30, 20, isDark ? 0x10b981 : 0x94a3b8, isDark ? 0x134e4a : 0xcbd5e1);
    gridHelper.position.y = -0.09;
    scene.add(gridHelper);

    // 5. Build 3 Agricultural Zones
    const zoneMeshes: THREE.Mesh[] = [];
    const particleSystems: { points: THREE.Points; geo: THREE.BufferGeometry; vel: Float32Array; active: boolean }[] = [];
    const zoneWidth = 7.5;
    const zoneDepth = 10;
    const zoneSpacing = 8.5;

    const cropColors = [0x15803d, 0xca8a04, 0x16a34a];

    for (let i = 0; i < 3; i++) {
      const posX = (i - 1) * zoneSpacing;

      // Soil Block (material will be mutated live based on moisture)
      const soilGeo = new THREE.BoxGeometry(zoneWidth, 1.2, zoneDepth);
      const soilMat = new THREE.MeshStandardMaterial({
        color: 0x543d2b,
        roughness: 0.85,
        metalness: 0.05,
      });
      const soilMesh = new THREE.Mesh(soilGeo, soilMat);
      soilMesh.position.set(posX, 0.5, 0);
      soilMesh.castShadow = true;
      soilMesh.receiveShadow = true;
      soilMesh.userData = { zoneIndex: i };
      scene.add(soilMesh);
      zoneMeshes.push(soilMesh);

      // Furrows & Crop Foliage
      const furrowCount = 5;
      for (let f = 0; f < furrowCount; f++) {
        const furrowZ = -4 + f * 2;
        const furrowGeo = new THREE.BoxGeometry(zoneWidth - 0.4, 0.15, 1.2);
        const furrowMat = new THREE.MeshStandardMaterial({
          color: cropColors[i],
          roughness: 0.7,
        });
        const furrowMesh = new THREE.Mesh(furrowGeo, furrowMat);
        furrowMesh.position.set(posX, 1.15, furrowZ);
        scene.add(furrowMesh);

        // Procedural plants
        for (let p = 0; p < 4; p++) {
          const plantX = posX - 2.8 + p * 1.8;
          const plantGeo = new THREE.ConeGeometry(0.35, 0.9 + (i === 1 ? 0.3 : i === 2 ? 0.6 : 0), 5);
          const plantMat = new THREE.MeshStandardMaterial({
            color: i === 1 ? 0xd97706 : i === 2 ? 0x16a34a : 0x22c55e,
          });
          const plantMesh = new THREE.Mesh(plantGeo, plantMat);
          plantMesh.position.set(plantX, 1.6 + (i === 2 ? 0.2 : 0), furrowZ);
          plantMesh.castShadow = true;
          scene.add(plantMesh);
        }
      }

      // Sprinkler Riser
      const postGeo = new THREE.CylinderGeometry(0.08, 0.08, 1.8);
      const postMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.8 });
      const post = new THREE.Mesh(postGeo, postMat);
      post.position.set(posX, 1.9, 0);
      scene.add(post);

      const headGeo = new THREE.SphereGeometry(0.18, 8, 8);
      const headMat = new THREE.MeshStandardMaterial({ color: 0x0284c7, metalness: 0.9 });
      const head = new THREE.Mesh(headGeo, headMat);
      head.position.set(posX, 2.8, 0);
      scene.add(head);

      // Sprinkler Mist Particle System per zone
      const pCount = 280;
      const pGeo = new THREE.BufferGeometry();
      const pPos = new Float32Array(pCount * 3);
      const pVel = new Float32Array(pCount * 3);

      for (let p = 0; p < pCount; p++) {
        pPos[p * 3] = posX;
        pPos[p * 3 + 1] = 2.8;
        pPos[p * 3 + 2] = 0;

        const angle = Math.random() * Math.PI * 2;
        const spd = 0.05 + Math.random() * 0.07;
        pVel[p * 3] = Math.cos(angle) * spd;
        pVel[p * 3 + 1] = 0.04 + Math.random() * 0.05;
        pVel[p * 3 + 2] = Math.sin(angle) * spd;
      }

      pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
      const pMat = new THREE.PointsMaterial({
        color: isDark ? 0x38bdf8 : 0x0284c7,
        size: 0.16,
        transparent: true,
        opacity: 0.85,
      });

      const pPoints = new THREE.Points(pGeo, pMat);
      pPoints.visible = false;
      scene.add(pPoints);

      particleSystems.push({
        points: pPoints,
        geo: pGeo,
        vel: pVel,
        active: false,
      });
    }

    soilMeshesRef.current = zoneMeshes;
    particleSystemsRef.current = particleSystems;

    // Interactive mouse rotation controls
    let isDragging = false;
    let prevMouseX = 0;
    let prevMouseY = 0;
    let rotationY = 0;
    let rotationX = 0.35;

    const handleMouseDown = (e: MouseEvent) => {
      isDragging = true;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };

    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      const deltaX = e.clientX - prevMouseX;
      const deltaY = e.clientY - prevMouseY;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;

      rotationY += deltaX * 0.008;
      rotationX = Math.max(0.1, Math.min(1.0, rotationX + deltaY * 0.005));

      const radius = 28;
      targetCamPosRef.current.x = Math.sin(rotationY) * radius * Math.cos(rotationX);
      targetCamPosRef.current.z = Math.cos(rotationY) * radius * Math.cos(rotationX);
      targetCamPosRef.current.y = radius * Math.sin(rotationX);
    };

    const handleMouseUp = () => {
      isDragging = false;
    };

    const canvasDom = renderer.domElement;
    canvasDom.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    // Animation Loop with smooth slerp camera transitions
    let animationFrameId: number;

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);

      // Smooth camera interpolation
      camera.position.lerp(targetCamPosRef.current, 0.06);
      camera.lookAt(targetCamLookRef.current);

      // Animate active particle systems
      particleSystemsRef.current.forEach((ps, idx) => {
        if (!ps.active) {
          ps.points.visible = false;
          return;
        }

        ps.points.visible = true;
        const pos = ps.geo.attributes.position.array as Float32Array;
        const vel = ps.vel;
        const originX = (idx - 1) * zoneSpacing;

        for (let i = 0; i < 280; i++) {
          const i3 = i * 3;
          pos[i3] += vel[i3];
          pos[i3 + 1] += vel[i3 + 1];
          pos[i3 + 2] += vel[i3 + 2];

          vel[i3 + 1] -= 0.0022; // gravity

          // Ground impact reset
          if (pos[i3 + 1] <= 1.15) {
            pos[i3] = originX;
            pos[i3 + 1] = 2.8;
            pos[i3 + 2] = 0;

            const angle = Math.random() * Math.PI * 2;
            const spd = 0.04 + Math.random() * 0.06;
            vel[i3] = Math.cos(angle) * spd;
            vel[i3 + 1] = 0.04 + Math.random() * 0.04;
            vel[i3 + 2] = Math.sin(angle) * spd;
          }
        }
        ps.geo.attributes.position.needsUpdate = true;
      });

      renderer.render(scene, camera);
    };

    animate();

    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight || 420;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      canvasDom.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      if (container && renderer.domElement) {
        container.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [theme]);

  // Live update: Soil hydration color & particle sprinkler activity
  useEffect(() => {
    zones.forEach((z, i) => {
      // 1. Soil shader color transition based on moisture percentage
      const mesh = soilMeshesRef.current[i];
      if (mesh) {
        const mat = mesh.material as THREE.MeshStandardMaterial;
        const m = z.moisture;

        if (m < 20) {
          // Dry sandy-tan
          mat.color.setHex(0xb58e58);
          mat.roughness = 0.95;
          mat.metalness = 0.0;
        } else if (m < 26) {
          // Optimal balanced loam brown
          mat.color.setHex(0x5a3d28);
          mat.roughness = 0.8;
          mat.metalness = 0.05;
        } else {
          // Deep wet loam with specular gloss
          mat.color.setHex(0x352317);
          mat.roughness = 0.45;
          mat.metalness = 0.15;
        }
      }

      // 2. Sprinkler particle system active state
      const ps = particleSystemsRef.current[i];
      if (ps) {
        ps.active = z.isIrrigating;
      }
    });
  }, [zones]);

  const selectedZone = useMemo(() => {
    return zones.find((z) => z.id === activeZoneId) || zones[0];
  }, [zones, activeZoneId]);

  return (
    <div className={`relative rounded-2xl bg-white dark:bg-[#09120e] border border-slate-200 dark:border-emerald-950/80 shadow-xl overflow-hidden transition-all ${className}`}>
      {/* 3D Viewport Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 border-b border-slate-100 dark:border-emerald-950/80 bg-slate-50/70 dark:bg-[#070e0a] gap-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-md shadow-emerald-500/20">
            <Sparkles className="h-4.5 w-4.5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              Living 3D Digital Twin Field
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 font-bold border border-emerald-300/40">
                WebGL 2026
              </span>
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Live root-zone soil hydrology shaders, dynamic mist particles & active flow rates
            </p>
          </div>
        </div>

        {/* Camera Preset Quick Buttons */}
        <div className="flex items-center gap-1.5 bg-slate-100 dark:bg-[#0c1511] p-1 rounded-xl border border-slate-200 dark:border-emerald-950">
          <button
            onClick={() => switchCameraView('overview')}
            className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              cameraView === 'overview'
                ? 'bg-emerald-600 text-white shadow-xs'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            <Compass className="h-3.5 w-3.5" />
            <span>Overview</span>
          </button>
          {[1, 2, 3].map((num) => (
            <button
              key={num}
              onClick={() => switchCameraView(num as 1 | 2 | 3)}
              className={`px-2.5 py-1 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer ${
                cameraView === num
                  ? 'bg-emerald-600 text-white shadow-xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              Zone {num}
            </button>
          ))}
        </div>
      </div>

      {/* 3D WebGL Canvas */}
      <div
        ref={mountRef}
        role="img"
        aria-label="3D living agricultural digital twin with synchronized particle mist"
        className="w-full h-[320px] sm:h-[400px] cursor-grab active:cursor-grabbing bg-slate-50 dark:bg-[#060b09]"
      />

      {/* Synchronized Zone Telemetry Cards */}
      <div className="p-3 border-t border-slate-100 dark:border-emerald-950/80 bg-white dark:bg-[#070e0a] grid grid-cols-1 sm:grid-cols-3 gap-2.5">
        {zones.map((zone) => {
          const isSelected = activeZoneId === zone.id;
          return (
            <button
              key={zone.id}
              onClick={() => switchCameraView(zone.id as 1 | 2 | 3)}
              className={`flex items-center justify-between p-3 rounded-xl border text-left transition-all cursor-pointer ${
                isSelected
                  ? 'bg-emerald-50/90 dark:bg-emerald-950/50 border-emerald-400 dark:border-emerald-600 shadow-md shadow-emerald-950/30 ring-1 ring-emerald-500/30'
                  : 'bg-slate-50/70 dark:bg-[#0c1511] border-slate-200 dark:border-emerald-950/60 hover:border-emerald-400/50'
              }`}
            >
              <div>
                <div className="flex items-center gap-1.5">
                  <span className="font-bold text-xs text-slate-900 dark:text-slate-100">{zone.name}</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-200/70 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                    {zone.crop}
                  </span>
                </div>
                <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
                  Moisture:{' '}
                  <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">
                    {zone.moisture.toFixed(1)}%
                  </span>{' '}
                  <span className="text-[10px] text-slate-400">/ {zone.target}% tgt</span>
                </div>
              </div>

              <div className="flex flex-col items-end gap-1">
                {zone.isIrrigating ? (
                  <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-sky-100 dark:bg-sky-950/80 text-sky-800 dark:text-sky-300 border border-sky-300 dark:border-sky-800 animate-pulse">
                    <Droplets className="h-3 w-3" /> {zone.flowRateLpm ? `${zone.flowRateLpm} L/m` : 'SPRAYING'}
                  </span>
                ) : (
                  <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                    <CheckCircle className="h-3 w-3 text-emerald-500" /> OPTIMAL
                  </span>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
