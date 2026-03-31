import { useRef, useEffect } from 'react'
import * as THREE from 'three'
import { ThreeEvent } from '@react-three/fiber'
import { useStore } from '../store/useStore'
import { Obstacle, ObstacleType } from '../types'
import { LocalPolygon } from '../types'

// Visual config for each obstacle type
export const OBSTACLE_CFG: Record<ObstacleType, {
  w: number; h: number; d: number
  color: string; label: string; icon: string
  shape: 'box' | 'cylinder' | 'tree' | 'antenna' | 'mast'
}> = {
  chimney:  { w: 0.5,  h: 1.5,  d: 0.5,  color: '#78716C', label: 'Cheminée',     icon: '🏭', shape: 'box' },
  ac:       { w: 0.8,  h: 0.4,  d: 0.6,  color: '#64748B', label: 'Climatiseur',  icon: '❄️', shape: 'box' },
  tank:     { w: 0.8,  h: 1.2,  d: 0.8,  color: '#475569', label: 'Citerne',      icon: '🪣', shape: 'cylinder' },
  tree:     { w: 2.5,  h: 5.0,  d: 2.5,  color: '#15803D', label: 'Arbre',        icon: '🌳', shape: 'tree' },
  building: { w: 6.0,  h: 10.0, d: 6.0,  color: '#94A3B8', label: 'Immeuble',     icon: '🏢', shape: 'box' },
  antenna:  { w: 0.2,  h: 8.0,  d: 0.2,  color: '#EF4444', label: 'Antenne',      icon: '📡', shape: 'antenna' },
  mast:     { w: 0.3,  h: 12.0, d: 0.3,  color: '#6B7280', label: 'Pylône',       icon: '🗼', shape: 'mast' },
}

interface ObstacleMeshProps {
  obs: Obstacle
  isSelected: boolean
  onClick: (e: ThreeEvent<MouseEvent>) => void
}

function ObstacleMesh({ obs, isSelected, onClick }: ObstacleMeshProps) {
  const cfg = OBSTACLE_CFG[obs.type]
  const baseColor = isSelected ? '#F59E0B' : cfg.color
  const ringRadius = Math.max(cfg.w, cfg.d)

  return (
    <group position={[obs.x, obs.y, obs.z]} onClick={onClick}>
      {cfg.shape === 'tree' && (
        <>
          {/* Trunk */}
          <mesh position={[0, cfg.h * 0.25, 0]} castShadow receiveShadow>
            <cylinderGeometry args={[0.15, 0.22, cfg.h * 0.5, 8]} />
            <meshStandardMaterial color={isSelected ? '#F59E0B' : '#713F12'} roughness={0.95} metalness={0.0} />
          </mesh>
          {/* Foliage — three stacked cones for density */}
          {[0, 0.35, 0.65].map((offset, i) => (
            <mesh key={i} position={[0, cfg.h * 0.4 + offset * cfg.h * 0.45, 0]} castShadow>
              <coneGeometry args={[cfg.w / 2 * (1 - i * 0.15), cfg.h * 0.45, 10]} />
              <meshStandardMaterial color={baseColor} roughness={0.9} metalness={0.0} />
            </mesh>
          ))}
        </>
      )}

      {cfg.shape === 'antenna' && (
        <>
          {/* Main pole */}
          <mesh position={[0, cfg.h / 2, 0]} castShadow receiveShadow>
            <cylinderGeometry args={[0.04, 0.06, cfg.h, 8]} />
            <meshStandardMaterial color={baseColor} roughness={0.4} metalness={0.7} />
          </mesh>
          {/* Horizontal cross-arms at 2/3 height */}
          <mesh position={[0, cfg.h * 0.7, 0]} rotation={[0, 0, Math.PI / 2]}>
            <cylinderGeometry args={[0.03, 0.03, cfg.w * 6, 8]} />
            <meshStandardMaterial color={baseColor} roughness={0.4} metalness={0.7} />
          </mesh>
          <mesh position={[0, cfg.h * 0.85, 0]} rotation={[0, 0, Math.PI / 2]}>
            <cylinderGeometry args={[0.025, 0.025, cfg.w * 4, 8]} />
            <meshStandardMaterial color={baseColor} roughness={0.4} metalness={0.7} />
          </mesh>
        </>
      )}

      {cfg.shape === 'mast' && (
        <>
          {/* Central column */}
          <mesh position={[0, cfg.h / 2, 0]} castShadow receiveShadow>
            <boxGeometry args={[cfg.w, cfg.h, cfg.d]} />
            <meshStandardMaterial color={baseColor} roughness={0.6} metalness={0.5} />
          </mesh>
          {/* Diagonal braces every 3m */}
          {[0.25, 0.5, 0.75].map((frac, i) => (
            <mesh key={i} position={[0, cfg.h * frac, 0]} rotation={[0, (i * Math.PI) / 3, Math.PI / 4]}>
              <boxGeometry args={[0.08, cfg.h * 0.3, 0.08]} />
              <meshStandardMaterial color={baseColor} roughness={0.6} metalness={0.5} />
            </mesh>
          ))}
        </>
      )}

      {(cfg.shape === 'box') && (
        <mesh position={[0, cfg.h / 2, 0]} castShadow receiveShadow>
          <boxGeometry args={[cfg.w, cfg.h, cfg.d]} />
          <meshStandardMaterial color={baseColor} roughness={0.85} metalness={0.1} />
        </mesh>
      )}

      {cfg.shape === 'cylinder' && (
        <mesh position={[0, cfg.h / 2, 0]} castShadow receiveShadow>
          <cylinderGeometry args={[cfg.w / 2, cfg.w / 2, cfg.h, 16]} />
          <meshStandardMaterial color={baseColor} roughness={0.85} metalness={0.1} />
        </mesh>
      )}

      {/* Selection ring */}
      {isSelected && (
        <mesh position={[0, 0.02, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[ringRadius * 0.7, ringRadius * 0.9, 32]} />
          <meshBasicMaterial color="#F59E0B" transparent opacity={0.8} side={THREE.DoubleSide} />
        </mesh>
      )}
    </group>
  )
}

// ── Transparent placement plane overlaid on the roof ──────────────────────
interface PlacementPlaneProps {
  localPoly: LocalPolygon
  wallHeight: number
}

export function PlacementPlane({ localPoly, wallHeight }: PlacementPlaneProps) {
  const { sceneMode, obstacleTypeToPlace, addObstacle } = useStore()

  if (sceneMode !== 'place-obstacle' || !obstacleTypeToPlace) return null

  const { bbox } = localPoly
  const size = Math.max(bbox.w, bbox.h) + 20

  function handleClick(e: ThreeEvent<MouseEvent>) {
    e.stopPropagation()
    const pt = e.point
    addObstacle({ type: obstacleTypeToPlace!, x: pt.x, y: wallHeight, z: pt.z })
  }

  return (
    <mesh
      position={[bbox.cx, wallHeight + 0.05, bbox.cy]}
      rotation={[-Math.PI / 2, 0, 0]}
      onClick={handleClick}
    >
      <planeGeometry args={[size, size]} />
      <meshBasicMaterial color="#0EA5E9" transparent opacity={0.06} side={THREE.DoubleSide} />
    </mesh>
  )
}

// ── Main Obstacles component ───────────────────────────────────────────────
interface Props {
  localPoly: LocalPolygon
  wallHeight: number
}

export default function Obstacles({ localPoly, wallHeight }: Props) {
  const { obstacles, selectedObstacle, setSelectedObstacle, sceneMode } = useStore()

  function handleObstacleClick(obs: Obstacle, e: ThreeEvent<MouseEvent>) {
    e.stopPropagation()
    if (sceneMode !== 'view') return
    const isAlreadySelected = selectedObstacle === obs.id
    setSelectedObstacle(isAlreadySelected ? null : obs.id)

    useStore.setState({
      _obstaclePopupX: e.nativeEvent.clientX,
      _obstaclePopupY: e.nativeEvent.clientY,
      _obstaclePopupId: isAlreadySelected ? null : obs.id,
    } as any)
  }

  return (
    <group>
      {obstacles.map((obs) => (
        <ObstacleMesh
          key={obs.id}
          obs={obs}
          isSelected={selectedObstacle === obs.id}
          onClick={(e) => handleObstacleClick(obs, e)}
        />
      ))}
      <PlacementPlane localPoly={localPoly} wallHeight={wallHeight} />
    </group>
  )
}
