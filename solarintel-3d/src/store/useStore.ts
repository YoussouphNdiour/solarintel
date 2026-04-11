import { create } from 'zustand'
import { RoofType, InstallType, Obstacle, ObstacleType, SceneMode, WeatherMode, RoofMaterial, ZoneConfig, DrawTool, DrawPhase, DrawnBuilding } from '../types'

let _obstacleIdCounter = 0

interface AppState {
  // From parent iframe
  polygon: [number, number][] | null
  panelCount: number
  panelPositions: [number, number][] | null   // exact 2D panel center positions (lon/lat)
  holePolygons: [number, number][][] | null   // WGS84 rings of drawn hole zones
  lat: number
  lon: number
  annualConsumption: number
  installType: InstallType
  // Panel physical dimensions (mm) + orientation + spacing from 2D calpinage
  panelWidthMm: number
  panelHeightMm: number
  orientation: 'portrait' | 'landscape'
  spacingHCm: number
  spacingVCm: number

  // Multi-zone
  zones: ZoneConfig[]
  selectedZoneId: string | null

  // Roof configuration
  roofType: RoofType | null
  pitch: number
  azimuth: number
  wallHeight: number
  roofMaterial: RoofMaterial

  // Weather
  weatherMode: WeatherMode

  // Sun simulation
  simDate: Date
  simHour: number
  isPlaying: boolean
  simSpeed: number

  // Scene interaction mode
  sceneMode: SceneMode
  obstacleTypeToPlace: ObstacleType | null

  // Obstacles
  obstacles: Obstacle[]
  selectedObstacle: number | null
  shadingPct: number  // facteur d'ombrage obstacles (0-100)

  // Panel interaction
  selectedPanel: number | null
  removedPanels: Set<number>

  // Roof face selection (gable: 2 faces, hip: 4 faces)
  selectedRoofFaces: Set<number>

  // UI state
  controlsOpen: boolean
  showStats: boolean
  irradianceMode: boolean

  // Internal popup state
  _popupData: { index: number; tilt: number; azimuth: number; estimatedProduction: number } | null
  _popupX: number
  _popupY: number
  _obstaclePanelOpen: boolean

  // Internal GL ref for screenshot
  _glCanvas: HTMLCanvasElement | null

  // Drawing tool state
  drawTool: DrawTool
  drawPhase: DrawPhase
  drawCorner1: [number, number] | null
  drawLinePoints: [number, number][]
  drawPreviewPos: [number, number] | null
  drawPreviewHeight: number
  drawFootprint: [number, number][] | null
  drawnBuildings: DrawnBuilding[]
  selectedDrawnId: string | null

  // Actions
  setFromParent: (data: {
    polygon?: [number, number][]
    panelCount?: number
    panelPositions?: [number, number][]
    holePolygons?: [number, number][][]
    lat?: number
    lon?: number
    annualConsumption?: number
    installType?: InstallType
    panelWidthMm?: number
    panelHeightMm?: number
    orientation?: 'portrait' | 'landscape'
    spacingHCm?: number
    spacingVCm?: number
    zones?: ZoneConfig[]
  }) => void
  setZones: (zones: ZoneConfig[]) => void
  updateZone: (id: string, patch: Partial<ZoneConfig>) => void
  selectZone: (id: string | null) => void
  setPanelCount: (count: number) => void
  setRoofType: (type: RoofType) => void
  setPitch: (pitch: number) => void
  setAzimuth: (azimuth: number) => void
  setWallHeight: (h: number) => void
  setRoofMaterial: (m: RoofMaterial) => void
  setWeatherMode: (m: WeatherMode) => void
  setSimDate: (date: Date) => void
  setSimHour: (hour: number) => void
  setIsPlaying: (playing: boolean) => void
  setSimSpeed: (speed: number) => void
  setSceneMode: (mode: SceneMode, obstacleType?: ObstacleType) => void
  addObstacle: (obs: Omit<Obstacle, 'id'>) => void
  removeObstacle: (id: number) => void
  setSelectedObstacle: (id: number | null) => void
  setSelectedPanel: (idx: number | null) => void
  removeSelectedPanel: () => void
  addPanel: () => void
  toggleRoofFace: (idx: number) => void
  resetRoofFaces: () => void

  toggleControls: () => void
  toggleStats: () => void
  toggleIrradiance: () => void
  tickSimulation: () => void
  setGlCanvas: (canvas: HTMLCanvasElement) => void
  takeScreenshot: () => void
  requestScreenshots: () => void

  // Drawing actions
  setDrawTool: (tool: DrawTool) => void
  setDrawPhase: (phase: DrawPhase) => void
  setDrawCorner1: (pt: [number, number] | null) => void
  setDrawLinePoints: (pts: [number, number][]) => void
  setDrawPreviewPos: (pt: [number, number] | null) => void
  setDrawPreviewHeight: (h: number) => void
  setDrawFootprint: (pts: [number, number][] | null) => void
  addDrawnBuilding: (b: DrawnBuilding) => void
  updateDrawnBuilding: (id: string, changes: Partial<DrawnBuilding>) => void
  removeDrawnBuilding: (id: string) => void
  setSelectedDrawnId: (id: string | null) => void
}

export const useStore = create<AppState>((set, get) => ({
  polygon: null,
  panelCount: 12,
  panelPositions: null,
  holePolygons: null,
  lat: 14.716,
  lon: -17.467,
  annualConsumption: 0,
  installType: 'autoconsommation',
  panelWidthMm: 1134,
  panelHeightMm: 2278,
  orientation: 'portrait',
  spacingHCm: 2,
  spacingVCm: 5,

  zones: [],
  selectedZoneId: null,

  roofType: null,
  pitch: 15,
  azimuth: 180,
  wallHeight: 3,
  roofMaterial: 'tuile-grise',

  weatherMode: 'clear',

  simDate: new Date(),
  simHour: 12,
  isPlaying: false,
  simSpeed: 1,

  sceneMode: 'view',
  obstacleTypeToPlace: null,

  obstacles: [],
  selectedObstacle: null,
  shadingPct: 0,

  selectedRoofFaces: new Set<number>([0]),

  selectedPanel: null,
  removedPanels: new Set(),
  controlsOpen: true,
  showStats: false,
  irradianceMode: false,

  _popupData: null,
  _popupX: 0,
  _popupY: 0,
  _obstaclePanelOpen: false,
  _glCanvas: null,

  drawTool: 'orbit',
  drawPhase: 'idle',
  drawCorner1: null,
  drawLinePoints: [],
  drawPreviewPos: null,
  drawPreviewHeight: 3,
  drawFootprint: null,
  drawnBuildings: [],
  selectedDrawnId: null,

  // ── Actions ────────────────────────────────────────────────────────────────

  setFromParent: (data) =>
    set((s) => {
      // Multi-zone support: if zones array is provided, extract first zone for backward compat
      const hasZones = Array.isArray(data.zones) && data.zones.length > 0
      const zones = hasZones ? data.zones! : s.zones
      const selectedZoneId = hasZones ? data.zones![0].id : s.selectedZoneId

      // Extract backward-compat fields from first zone when zones are provided
      const firstZone = hasZones ? data.zones![0] : null
      const effectivePolygon = firstZone ? firstZone.polygon : data.polygon
      const effectivePanelPositions = firstZone ? firstZone.panelPositions : data.panelPositions
      const effectiveHolePolygons = firstZone ? firstZone.holePolygons : data.holePolygons

      const hasPositions = Array.isArray(effectivePanelPositions) && effectivePanelPositions.length > 0
      const newPositions = hasPositions ? effectivePanelPositions! : s.panelPositions
      // Use position count when real positions are available; otherwise use explicit panelCount
      const newCount = hasPositions
        ? effectivePanelPositions!.length
        : (data.panelCount ?? s.panelCount)
      // Reset 3D-only panel removals only when fresh 2D positions arrive
      const newRemoved = hasPositions ? new Set<number>() : s.removedPanels
      return {
        zones,
        selectedZoneId,
        polygon: effectivePolygon ?? s.polygon,
        panelCount: newCount,
        panelPositions: newPositions,
        holePolygons: effectiveHolePolygons ?? s.holePolygons,
        removedPanels: newRemoved,
        lat: data.lat ?? s.lat,
        lon: data.lon ?? s.lon,
        annualConsumption: data.annualConsumption ?? s.annualConsumption,
        installType: data.installType ?? s.installType,
        panelWidthMm: data.panelWidthMm ?? s.panelWidthMm,
        panelHeightMm: data.panelHeightMm ?? s.panelHeightMm,
        orientation: data.orientation ?? s.orientation,
        spacingHCm: data.spacingHCm ?? s.spacingHCm,
        spacingVCm: data.spacingVCm ?? s.spacingVCm,
      }
    }),

  setZones: (zones) => set({ zones }),

  updateZone: (id, patch) =>
    set((s) => ({
      zones: s.zones.map((z) => (z.id === id ? { ...z, ...patch } : z)),
    })),

  selectZone: (id) => set({ selectedZoneId: id }),

  setPanelCount: (count) => set({ panelCount: count, removedPanels: new Set() }),

  setRoofType: (type) =>
    set((s) => {
      const faceReset = { selectedRoofFaces: new Set<number>([0]) }
      if (s.selectedZoneId) {
        // zones mode: only update the selected zone, leave global roofType untouched
        return {
          ...faceReset,
          zones: s.zones.map((z) =>
            z.id === s.selectedZoneId ? { ...z, roofType: type } : z
          ),
        }
      }
      return { roofType: type, ...faceReset }
    }),

  setPitch: (pitch) => {
    const { selectedZoneId, zones, azimuth } = get()
    if (selectedZoneId) {
      set({
        zones: zones.map((z) =>
          z.id === selectedZoneId ? { ...z, pitch } : z
        ),
      })
    } else {
      set({ pitch })
    }
    window.parent.postMessage({ type: 'TILT_AZIMUTH', tilt: pitch, azimuth }, '*')
  },

  setAzimuth: (azimuth) => {
    const { selectedZoneId, zones, pitch } = get()
    if (selectedZoneId) {
      set({
        zones: zones.map((z) =>
          z.id === selectedZoneId ? { ...z, azimuth } : z
        ),
      })
    } else {
      set({ azimuth })
    }
    window.parent.postMessage({ type: 'TILT_AZIMUTH', tilt: pitch, azimuth }, '*')
  },

  setWallHeight: (wallHeight) => {
    const { selectedZoneId, zones } = get()
    if (selectedZoneId) {
      set({
        zones: zones.map((z) =>
          z.id === selectedZoneId ? { ...z, wallHeight } : z
        ),
      })
    } else {
      set({ wallHeight })
    }
  },

  setRoofMaterial: (roofMaterial) => set({ roofMaterial }),

  setWeatherMode: (weatherMode) => set({ weatherMode }),

  setSimDate: (simDate) => set({ simDate }),

  setSimHour: (simHour) => set({ simHour }),

  setIsPlaying: (isPlaying) => set({ isPlaying }),

  setSimSpeed: (simSpeed) => set({ simSpeed }),

  setSceneMode: (mode, obstacleType) =>
    set({ sceneMode: mode, obstacleTypeToPlace: obstacleType ?? null, selectedPanel: null, _popupData: null }),

  addObstacle: (obs) => {
    const id = ++_obstacleIdCounter
    set((s) => ({ obstacles: [...s.obstacles, { ...obs, id }], sceneMode: 'view', obstacleTypeToPlace: null }))
  },

  removeObstacle: (id) =>
    set((s) => ({ obstacles: s.obstacles.filter((o) => o.id !== id), selectedObstacle: null })),

  setSelectedObstacle: (id) => set({ selectedObstacle: id, selectedPanel: null, _popupData: null }),

  setSelectedPanel: (idx) =>
    set({ selectedPanel: idx, selectedObstacle: null }),

  removeSelectedPanel: () => {
    const { selectedPanel, removedPanels } = get()
    if (selectedPanel === null) return
    const next = new Set(removedPanels)
    next.add(selectedPanel)
    // Ne pas decrementer panelCount : le compte "actif" = panelCount - removedPanels.size
    // Decrementer panelCount causerait une double exclusion (panneau absent + index tronque)
    set({ removedPanels: next, selectedPanel: null, _popupData: null })
    window.parent.postMessage({ type: 'REMOVE_PANEL' }, '*')
  },

  addPanel: () => {
    set((s) => ({ panelCount: s.panelCount + 1, sceneMode: 'view' }))
    window.parent.postMessage({ type: 'ADD_PANEL' }, '*')
  },

  toggleRoofFace: (idx) =>
    set((s) => {
      const next = new Set(s.selectedRoofFaces)
      if (next.has(idx)) {
        if (next.size <= 1) return {}  // prevent deselecting last face
        next.delete(idx)
      } else {
        next.add(idx)
      }
      return { selectedRoofFaces: next }
    }),

  resetRoofFaces: () => set({ selectedRoofFaces: new Set<number>([0]) }),

  toggleControls: () => set((s) => ({ controlsOpen: !s.controlsOpen })),

  toggleStats: () => set((s) => ({ showStats: !s.showStats })),

  toggleIrradiance: () => set((s) => ({ irradianceMode: !s.irradianceMode })),

  tickSimulation: () => {
    const { simHour, simSpeed } = get()
    const next = (simHour + 0.05 * simSpeed) % 24
    set({ simHour: next })
  },

  setGlCanvas: (canvas) => set({ _glCanvas: canvas }),

  takeScreenshot: () => {
    const { _glCanvas } = get()
    if (!_glCanvas) return
    const link = document.createElement('a')
    link.download = `solarintel-3d-${new Date().toISOString().slice(0, 10)}.png`
    link.href = _glCanvas.toDataURL('image/png')
    link.click()
  },

  requestScreenshots: () => {
    const { _glCanvas, irradianceMode, toggleIrradiance } = get()
    if (!_glCanvas) return
    const wasIrradiance = irradianceMode
    if (wasIrradiance) {
      // Etat initial: irradiance ON → passer en OFF pour capturer vue normale
      toggleIrradiance()
      setTimeout(() => {
        const normalUrl = _glCanvas.toDataURL('image/png')
        window.parent.postMessage({ type: 'SCREENSHOT_3D', dataUrl: normalUrl, mode: 'normal' }, '*')
        toggleIrradiance() // repasser en ON pour capturer vue irradiance
        setTimeout(() => {
          const irrUrl = _glCanvas.toDataURL('image/png')
          window.parent.postMessage({ type: 'SCREENSHOT_3D', dataUrl: irrUrl, mode: 'irradiance' }, '*')
          // Pas de 3eme toggle : on est deja revenu a l'etat initial (irradiance ON)
        }, 300)
      }, 300)
    } else {
      const normalUrl = _glCanvas.toDataURL('image/png')
      window.parent.postMessage({ type: 'SCREENSHOT_3D', dataUrl: normalUrl, mode: 'normal' }, '*')
      toggleIrradiance()
      setTimeout(() => {
        const irrUrl = _glCanvas.toDataURL('image/png')
        window.parent.postMessage({ type: 'SCREENSHOT_3D', dataUrl: irrUrl, mode: 'irradiance' }, '*')
        toggleIrradiance() // restore OFF
      }, 300)
    }
  },

  // ── Drawing actions ────────────────────────────────────────────────────────

  setDrawTool: (tool) =>
    set({
      drawTool: tool,
      drawPhase: 'idle',
      drawCorner1: null,
      drawLinePoints: [],
      drawPreviewPos: null,
      drawFootprint: null,
      selectedDrawnId: null,
    }),

  setDrawPhase: (phase) => set({ drawPhase: phase }),

  setDrawCorner1: (pt) => set({ drawCorner1: pt }),

  setDrawLinePoints: (pts) => set({ drawLinePoints: pts }),

  setDrawPreviewPos: (pt) => set({ drawPreviewPos: pt }),

  setDrawPreviewHeight: (h) => set({ drawPreviewHeight: h }),

  setDrawFootprint: (pts) => set({ drawFootprint: pts }),

  addDrawnBuilding: (b) =>
    set((s) => ({ drawnBuildings: [...s.drawnBuildings, b] })),

  updateDrawnBuilding: (id, changes) =>
    set((s) => ({
      drawnBuildings: s.drawnBuildings.map((b) => (b.id === id ? { ...b, ...changes } : b)),
    })),

  removeDrawnBuilding: (id) =>
    set((s) => ({
      drawnBuildings: s.drawnBuildings.filter((b) => b.id !== id),
      selectedDrawnId: s.selectedDrawnId === id ? null : s.selectedDrawnId,
    })),

  setSelectedDrawnId: (id) => set({ selectedDrawnId: id }),
}))
