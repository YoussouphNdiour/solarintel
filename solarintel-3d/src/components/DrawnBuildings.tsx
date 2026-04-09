import * as THREE from 'three'
import { ThreeEvent } from '@react-three/fiber'
import { useMemo, useRef } from 'react'
import { useStore } from '../store/useStore'
import { DrawnBuilding } from '../types'

interface DragState {
  active: boolean
  buildingId: string | null
  startClientY: number
  startHeight: number
  startClientX: number
  startClientZ: number
  startBuildingX: number
  startBuildingZ: number
}

function DrawnBuildingMesh({ building, dragRef }: { building: DrawnBuilding; dragRef: React.MutableRefObject<DragState> }) {
  const {
    drawTool, selectedDrawnId,
    setSelectedDrawnId, removeDrawnBuilding, updateDrawnBuilding,
  } = useStore()

  const isSelected = selectedDrawnId === building.id

  const geometry = useMemo(() => {
    const pts = building.footprint
    if (pts.length < 3) return null
    const shape = new THREE.Shape(pts.map(([x, y]) => new THREE.Vector2(x, y)))
    const geo = new THREE.ExtrudeGeometry(shape, { depth: building.height, bevelEnabled: false })
    geo.rotateX(-Math.PI / 2)
    return geo
  }, [building.footprint, building.height])

  if (!geometry) return null

  function handleClick(e: ThreeEvent<MouseEvent>) {
    e.stopPropagation()
    if (drawTool === 'erase') {
      removeDrawnBuilding(building.id)
    } else if (drawTool === 'select' || drawTool === 'move' || drawTool === 'push-pull') {
      setSelectedDrawnId(isSelected ? null : building.id)
    }
  }

  function handlePointerDown(e: ThreeEvent<PointerEvent>) {
    if (!isSelected) return
    e.stopPropagation()

    if (drawTool === 'push-pull') {
      dragRef.current = {
        active: true,
        buildingId: building.id,
        startClientY: e.clientY,
        startHeight: building.height,
        startClientX: 0,
        startClientZ: 0,
        startBuildingX: 0,
        startBuildingZ: 0,
      }
      ;(e.target as HTMLElement).setPointerCapture?.(e.pointerId)
    }
  }

  function handlePointerMove(e: ThreeEvent<PointerEvent>) {
    if (!dragRef.current.active || dragRef.current.buildingId !== building.id) return
    if (drawTool !== 'push-pull') return

    const deltaY = dragRef.current.startClientY - e.clientY
    const newHeight = Math.max(1, Math.min(50, dragRef.current.startHeight + deltaY / 15))
    updateDrawnBuilding(building.id, { height: newHeight })
  }

  function handlePointerUp(e: ThreeEvent<PointerEvent>) {
    if (dragRef.current.buildingId === building.id) {
      dragRef.current = { ...dragRef.current, active: false, buildingId: null }
    }
  }

  return (
    <mesh
      geometry={geometry}
      castShadow
      receiveShadow
      onClick={handleClick}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
    >
      <meshStandardMaterial
        color={isSelected ? '#F59E0B' : building.color}
        roughness={0.7}
        metalness={0.1}
        transparent
        opacity={isSelected ? 1.0 : 0.85}
      />
    </mesh>
  )
}

export default function DrawnBuildings() {
  const { drawnBuildings } = useStore()

  const dragRef = useRef<DragState>({
    active: false,
    buildingId: null,
    startClientY: 0,
    startHeight: 3,
    startClientX: 0,
    startClientZ: 0,
    startBuildingX: 0,
    startBuildingZ: 0,
  })

  return (
    <>
      {drawnBuildings.map((b) => (
        <DrawnBuildingMesh key={b.id} building={b} dragRef={dragRef} />
      ))}
    </>
  )
}
