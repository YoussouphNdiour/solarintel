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
  shape: 'box' | 'cylinder'
}> = {
  chimney: { w: 0.5,  h: 1.5, d: 0.5, color: '#78716C', label: 'Cheminée',     icon: '🏭', shape: 'box' },
  ac:      { w: 0.8,  h: 0.4, d: 0.6, color: '#64748B', label: 'Climatiseur',  icon: '❄️', shape: 'box' },
  tank:    { w: 0.8,  h: 1.2, d: 0.8, color: '#475569', label: 'Citerne',      icon: '🪣', shape: 'cylinder' },
}

interface ObstacleMeshProps {
  obs: Obstacle
  isSelected: boolean
  onClick: (e: ThreeEvent<MouseEvent>) => void
}

function ObstacleMesh({ obs, isSelected, onClick }: ObstacleMeshProps) {
  const cfg = OBSTACLE_CFG[obs.type]
  const baseColor = isSelected ? '#F59E0B' : cfg.color

  return (
    <group position={[obs.x, obs.y, obs.z]}>
      <mesh
        position={[0, cfg.h / 2, 0]}
        castShadow
        receiveShadow
        onClick={onClick}
      >
        {cfg.shape === 'cylinder' ? (
          <cylinderGeometry args={[cfg.w / 2, cfg.w / 2, cfg.h, 16]} />
        ) : (
          <boxGeometry args={[cfg.w, cfg.h, cfg.d]} />
        )}
        <meshStandardMaterial color={baseColor} roughness={0.85} metalness={0.1} />
      </mesh>

      {/* Selection ring */}
      {isSelected && (
        <mesh position={[0, 0.02, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[cfg.w * 0.7, cfg.w * 0.85, 32]} />
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
  const size = Math.max(bbox.w, bbox.h) + 6

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
      {/* Slightly visible in placement mode so user understands what's clickable */}
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
