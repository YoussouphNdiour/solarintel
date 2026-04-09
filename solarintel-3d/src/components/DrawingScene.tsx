import { useRef } from 'react'
import { ThreeEvent } from '@react-three/fiber'
import { Line } from '@react-three/drei'
import * as THREE from 'three'
import { useStore } from '../store/useStore'

export default function DrawingScene() {
  const {
    drawTool, drawPhase,
    drawCorner1, drawLinePoints, drawPreviewPos, drawPreviewHeight,
    setDrawPhase, setDrawCorner1, setDrawLinePoints, setDrawPreviewPos,
    setDrawFootprint,
    drawnBuildings, selectedDrawnId, setSelectedDrawnId,
    updateDrawnBuilding,
  } = useStore()

  // Don't render ground interaction mesh in orbit mode
  if (drawTool === 'orbit') return null

  function worldToLocal(wx: number, wz: number): [number, number] {
    return [wx, -wz]
  }

  function handleGroundMove(e: ThreeEvent<PointerEvent>) {
    e.stopPropagation()
    setDrawPreviewPos(worldToLocal(e.point.x, e.point.z))
  }

  function handleGroundClick(e: ThreeEvent<MouseEvent>) {
    e.stopPropagation()
    const [lx, ly] = worldToLocal(e.point.x, e.point.z)

    if (drawTool === 'rectangle') {
      if (drawPhase === 'idle') {
        setDrawCorner1([lx, ly])
        setDrawPreviewPos([lx, ly])
        setDrawPhase('rect-corner2')
      } else if (drawPhase === 'rect-corner2' && drawCorner1) {
        // Save confirmed footprint, then go to height phase
        const [x1, y1] = drawCorner1
        const [x2, y2] = [lx, ly]
        const footprint: [number, number][] = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
        setDrawFootprint(footprint)
        setDrawPreviewPos([lx, ly])
        setDrawPhase('rect-height')
      }
    }

    if (drawTool === 'line') {
      if (drawPhase === 'idle') {
        setDrawLinePoints([[lx, ly]])
        setDrawPhase('line-placing')
      } else if (drawPhase === 'line-placing') {
        const pts = drawLinePoints
        // Check if clicking near the first point to close the polygon
        if (pts.length >= 3) {
          const [fx, fy] = pts[0]
          const dist = Math.sqrt((lx - fx) ** 2 + (ly - fy) ** 2)
          if (dist < 0.8) {
            setDrawFootprint([...pts])
            setDrawPhase('line-height')
            return
          }
        }
        setDrawLinePoints([...pts, [lx, ly]])
      }
    }
  }

  // Build preview rectangle footprint from corner1 + current previewPos
  function getPreviewRect(): [number, number][] | null {
    const c1 = drawCorner1
    const c2 = drawPreviewPos
    if (!c1 || !c2) return null
    const [x1, y1] = c1
    const [x2, y2] = c2
    return [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
  }

  const showRectPreview =
    drawTool === 'rectangle' &&
    (drawPhase === 'rect-corner2' || drawPhase === 'rect-height')
  const previewRect = showRectPreview ? getPreviewRect() : null

  const showLinePreview = drawTool === 'line' && drawPhase === 'line-placing'
  const previewLinePts: [number, number][] = showLinePreview
    ? [...drawLinePoints, ...(drawPreviewPos ? [drawPreviewPos as [number, number]] : [])]
    : []

  return (
    <>
      {/* Transparent ground plane for pointer interaction */}
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, 0, 0]}
        onPointerMove={handleGroundMove}
        onClick={handleGroundClick}
      >
        <planeGeometry args={[500, 500]} />
        <meshBasicMaterial visible={false} side={THREE.DoubleSide} />
      </mesh>

      {/* Cursor dot on ground */}
      {drawPreviewPos && drawPhase !== 'rect-height' && drawPhase !== 'line-height' && (
        <mesh position={[drawPreviewPos[0], 0.02, -drawPreviewPos[1]]}>
          <sphereGeometry args={[0.12, 16, 16]} />
          <meshBasicMaterial color="#0EA5E9" />
        </mesh>
      )}

      {/* Rectangle footprint wireframe preview (corner2 phase) */}
      {previewRect && drawPhase === 'rect-corner2' && (
        <RectFootprintPreview pts={previewRect} />
      )}

      {/* Rectangle extruded preview (height phase) */}
      {previewRect && drawPhase === 'rect-height' && drawPreviewHeight > 0 && (
        <RectExtrudedPreview pts={previewRect} height={drawPreviewHeight} />
      )}

      {/* Line segments preview */}
      {previewLinePts.length >= 2 && (
        <Line
          points={previewLinePts.map(([x, y]) => [x, 0.05, -y] as [number, number, number])}
          color="#10B981"
          lineWidth={2}
        />
      )}

      {/* First point marker for line tool — yellow dot shows where polygon will close */}
      {drawTool === 'line' && drawLinePoints.length > 0 && (
        <mesh position={[drawLinePoints[0][0], 0.1, -drawLinePoints[0][1]]}>
          <sphereGeometry args={[0.18, 16, 16]} />
          <meshBasicMaterial color="#F59E0B" />
        </mesh>
      )}
    </>
  )
}

// ── Sub-components ────────────────────────────────────────────────────────────

function RectFootprintPreview({ pts }: { pts: [number, number][] }) {
  const closed = [...pts, pts[0]] as [number, number][]
  return (
    <Line
      points={closed.map(([x, y]) => [x, 0.05, -y] as [number, number, number])}
      color="#0EA5E9"
      lineWidth={2}
    />
  )
}

function RectExtrudedPreview({ pts, height }: { pts: [number, number][]; height: number }) {
  const shape = new THREE.Shape(pts.map(([x, y]) => new THREE.Vector2(x, y)))
  const geo = new THREE.ExtrudeGeometry(shape, { depth: height, bevelEnabled: false })
  geo.rotateX(-Math.PI / 2)
  return (
    <mesh geometry={geo}>
      <meshBasicMaterial color="#0EA5E9" wireframe />
    </mesh>
  )
}
