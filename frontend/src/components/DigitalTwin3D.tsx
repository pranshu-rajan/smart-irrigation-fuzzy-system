'use client';

import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { Droplets, RotateCcw, Info, Sparkles, CheckCircle } from 'lucide-react';

interface ZoneData {
  id: number;
  name: string;
  crop: string;
  soil: string;
  moisture: number;
  target: number;
  isIrrigating: boolean;
  color: number;
}

const ZONES_INITIAL: ZoneData[] = [
  { id: 1, name: 'Zone 1', crop: 'Tomato', soil: 'Loam', moisture: 59.7, target: 60.0, isIrrigating: true, color: 0x22c55e },
  { id: 2, name: 'Zone 2', crop: 'Wheat', soil: 'Sandy', moisture: 54.6, target: 55.0, isIrrigating: false, color: 0xeab308 },
  { id: 3, name: 'Zone 3', crop: 'Maize', soil: 'Clay', moisture: 65.0, target: 65.0, isIrrigating: false, color: 0x10b981 },
];

export default function DigitalTwin3D() {
  const mountRef = useRef<HTMLDivElement>(null);
  const [selectedZone, setSelectedZone] = useState<ZoneData>(ZONES_INITIAL[0]);
  const [isSprinkling, setIsSprinkling] = useState<boolean>(true);
  const [zones, setZones] = useState<ZoneData[]>(ZONES_INITIAL);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    // 1. Scene & Camera
    const width = container.clientWidth;
    const height = container.clientHeight || 420;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf1f5f9);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 18, 26);
    camera.lookAt(0, 0, 0);

    // 2. Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    container.appendChild(renderer.domElement);

    // 3. Lighting (Warm Sunlight + Soft Ambient Sky)
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
    scene.add(ambientLight);

    const sunLight = new THREE.DirectionalLight(0xfef08a, 1.4);
    sunLight.position.set(15, 25, 12);
    sunLight.castShadow = true;
    sunLight.shadow.mapSize.width = 1024;
    sunLight.shadow.mapSize.height = 1024;
    scene.add(sunLight);

    const hemiLight = new THREE.HemisphereLight(0xe0f2fe, 0xf0fdf4, 0.6);
    scene.add(hemiLight);

    // 4. Ground Foundation Plot (Baseboard)
    const baseGeo = new THREE.BoxGeometry(26, 0.8, 12);
    const baseMat = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, roughness: 0.8 });
    const baseMesh = new THREE.Mesh(baseGeo, baseMat);
    baseMesh.position.y = -0.5;
    baseMesh.receiveShadow = true;
    scene.add(baseMesh);

    // 5. Build 3 Agricultural Zones
    const zoneMeshes: THREE.Mesh[] = [];
    const zoneWidth = 7.5;
    const zoneDepth = 10;
    const zoneSpacing = 8.5;

    // Soil colors: Loam (rich dark brown), Sandy (golden tan), Clay (dense reddish-brown)
    const soilColors = [0x543d2b, 0xc2a675, 0x6e4a36];
    const cropColors = [0x15803d, 0xd97706, 0x059669];

    for (let i = 0; i < 3; i++) {
      const posX = (i - 1) * zoneSpacing;

      // Soil Block
      const soilGeo = new THREE.BoxGeometry(zoneWidth, 1.2, zoneDepth);
      const soilMat = new THREE.MeshStandardMaterial({
        color: soilColors[i],
        roughness: 0.9,
      });
      const soilMesh = new THREE.Mesh(soilGeo, soilMat);
      soilMesh.position.set(posX, 0.5, 0);
      soilMesh.castShadow = true;
      soilMesh.receiveShadow = true;
      soilMesh.userData = { zoneIndex: i };
      scene.add(soilMesh);
      zoneMeshes.push(soilMesh);

      // Top Soil Grass / Field Furrows
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

        // Procedural Crop Foliage Plants
        for (let p = 0; p < 4; p++) {
          const plantX = posX - 2.8 + p * 1.8;
          const plantGeo = new THREE.ConeGeometry(0.35, 0.9 + (i === 1 ? 0.3 : i === 2 ? 0.6 : 0), 5);
          const plantMat = new THREE.MeshStandardMaterial({
            color: i === 1 ? 0xca8a04 : i === 2 ? 0x16a34a : 0x22c55e,
          });
          const plantMesh = new THREE.Mesh(plantGeo, plantMat);
          plantMesh.position.set(plantX, 1.6 + (i === 2 ? 0.2 : 0), furrowZ);
          plantMesh.castShadow = true;
          scene.add(plantMesh);
        }
      }

      // Sprinkler Riser Post in Center
      const postGeo = new THREE.CylinderGeometry(0.08, 0.08, 1.8);
      const postMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.7 });
      const post = new THREE.Mesh(postGeo, postMat);
      post.position.set(posX, 1.9, 0);
      scene.add(post);

      const headGeo = new THREE.SphereGeometry(0.18, 8, 8);
      const headMat = new THREE.MeshStandardMaterial({ color: 0x0284c7, metalness: 0.9 });
      const head = new THREE.Mesh(headGeo, headMat);
      head.position.set(posX, 2.8, 0);
      scene.add(head);
    }

    // 6. Animated Water Particle Sprinkler System
    const particleCount = 450;
    const particleGeo = new THREE.BufferGeometry();
    const particlePositions = new Float32Array(particleCount * 3);
    const particleVelocities: { x: number; y: number; z: number }[] = [];

    const activeSprinklerX = -zoneSpacing; // Zone 1 active

    for (let p = 0; p < particleCount; p++) {
      particlePositions[p * 3] = activeSprinklerX;
      particlePositions[p * 3 + 1] = 2.8;
      particlePositions[p * 3 + 2] = 0;

      const angle = Math.random() * Math.PI * 2;
      const speed = 0.06 + Math.random() * 0.08;
      particleVelocities.push({
        x: Math.cos(angle) * speed,
        y: 0.04 + Math.random() * 0.06,
        z: Math.sin(angle) * speed,
      });
    }

    particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
    const particleMat = new THREE.PointsMaterial({
      color: 0x38bdf8,
      size: 0.18,
      transparent: true,
      opacity: 0.85,
    });
    const waterParticles = new THREE.Points(particleGeo, particleMat);
    scene.add(waterParticles);

    // 7. Interactive Mouse Controls
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
      camera.position.x = Math.sin(rotationY) * radius * Math.cos(rotationX);
      camera.position.z = Math.cos(rotationY) * radius * Math.cos(rotationX);
      camera.position.y = radius * Math.sin(rotationX);
      camera.lookAt(0, 1, 0);
    };

    const handleMouseUp = () => {
      isDragging = false;
    };

    const canvasDom = renderer.domElement;
    canvasDom.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    // 8. Animation Loop
    let animationFrameId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const delta = clock.getDelta();

      // Animate water particles if sprinkling is on
      if (isSprinkling) {
        const positions = particleGeo.attributes.position.array as Float32Array;
        for (let i = 0; i < particleCount; i++) {
          const idx = i * 3;
          positions[idx] += particleVelocities[i].x;
          positions[idx + 1] += particleVelocities[i].y;
          positions[idx + 2] += particleVelocities[i].z;

          // Gravity effect
          particleVelocities[i].y -= 0.0025;

          // Ground impact reset
          if (positions[idx + 1] <= 1.1) {
            positions[idx] = activeSprinklerX;
            positions[idx + 1] = 2.8;
            positions[idx + 2] = 0;

            const angle = Math.random() * Math.PI * 2;
            const speed = 0.05 + Math.random() * 0.07;
            particleVelocities[i].x = Math.cos(angle) * speed;
            particleVelocities[i].y = 0.05 + Math.random() * 0.05;
            particleVelocities[i].z = Math.sin(angle) * speed;
          }
        }
        particleGeo.attributes.position.needsUpdate = true;
        waterParticles.visible = true;
      } else {
        waterParticles.visible = false;
      }

      renderer.render(scene, camera);
    };

    animate();

    // 9. Resize handler
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
  }, [isSprinkling]);

  return (
    <div className="relative rounded-2xl bg-white border border-emerald-100 shadow-sm overflow-hidden">
      {/* 3D Viewport Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 border-b border-slate-100 bg-gradient-to-r from-emerald-50/50 via-white to-white gap-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-600 text-white shadow-xs">
            <Sparkles className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
              Interactive 3D Digital Twin Farm
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-medium">
                Three.js WebGL
              </span>
            </h3>
            <p className="text-xs text-slate-500">
              Real-time spatial visualization of 3-zone root-zone soil strata & active sprinkler actuation
            </p>
          </div>
        </div>

        {/* Viewport Action Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsSprinkling(!isSprinkling)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              isSprinkling
                ? 'bg-sky-50 text-sky-700 border border-sky-200 shadow-2xs'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            <Droplets className="h-3.5 w-3.5 text-sky-500" />
            <span>{isSprinkling ? 'Sprinklers Spraying' : 'Sprinklers Off'}</span>
          </button>
        </div>
      </div>

      {/* 3D Canvas Mount */}
      <div
        ref={mountRef}
        className="w-full h-[380px] cursor-grab active:cursor-grabbing bg-slate-50"
      />

      {/* Interactive Zone Selector Pill Bar */}
      <div className="p-3 border-t border-slate-100 bg-white grid grid-cols-1 sm:grid-cols-3 gap-2.5">
        {zones.map((zone) => (
          <button
            key={zone.id}
            onClick={() => setSelectedZone(zone)}
            className={`flex items-center justify-between p-2.5 rounded-xl border text-left transition-all ${
              selectedZone.id === zone.id
                ? 'bg-emerald-50/80 border-emerald-300 shadow-2xs'
                : 'bg-white border-slate-200 hover:border-emerald-200'
            }`}
          >
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-semibold text-xs text-slate-900">{zone.name}</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-slate-100 text-slate-600 font-medium">
                  {zone.crop} &bull; {zone.soil}
                </span>
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">
                Target: <span className="font-mono font-medium text-slate-700">{zone.target}%</span> | Current:{' '}
                <span className="font-mono font-semibold text-emerald-700">{zone.moisture}%</span>
              </div>
            </div>

            {zone.isIrrigating ? (
              <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-sky-100 text-sky-800 border border-sky-200 animate-pulse">
                <Droplets className="h-3 w-3" /> VALVE OPEN
              </span>
            ) : (
              <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-slate-100 text-slate-600">
                <CheckCircle className="h-3 w-3 text-emerald-600" /> OPTIMAL
              </span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
