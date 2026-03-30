import { create } from 'zustand'
import { RoofType, InstallType, Obstacle, ObstacleType, SceneMode } from '../types'

let _obstacleIdCounter = 0

interface AppState {
  // From parent iframe
  polygon: [number, number][] | null
  panelCount: number
  lat: number
  lon: number
  annualConsumption: number
  installType: InstallType

  // Roof configuration
  roofType: RoofType | null
  pitch: number
  azimuth: number
  wallHeight: number

  // Sun simulation
  simDate: Date
  simHour: number
  isPlaying: boolean

  // Scene interaction mode
  sceneMode: SceneMode
  obstacleTypeToPlace: ObstacleType | null

  // Obstacles
  obstacles: Obstacle[]
  selectedObstacle: number | null   // obstacle id

  // Panel interaction
  selectedPanel: number | null
  removedPanels: Set<number>        // indices of manually removed panels

  // UI state
  controlsOpen: boolean

  // Internal popup state
  _popupData: { index: number; tilt: number; azimuth: number; estimatedProduction: number } | null
  _popupX: number
  _popupY: number
  _obstaclePanelOpen: boolean

  // Actions
  setFromParent: (data: {
    polygon?: [number, number][]
    panelCount?: number
    lat?: number
    lon?: number
    annualConsumption?: number
    installType?: InstallType
  }) => void
  setPanelCount: (count: number) => void
  setRoofType: (type: RoofType) => void
  setPitch: (pitch: number) => void
  setAzimuth: (azimuth: number) => void
  setWallHeight: (h: number) => void
  setSimDate: (date: Date) => void
  setSimHour: (hour: number) => void
  setIsPlaying: (playing: boolean) => void
  setSceneMode: (mode: SceneMode, obstacleType?: ObstacleType) => void
  addObstacle: (obs: Omit<Obstacle, 'id'>) => void
  removeObstacle: (id: number) => void
  setSelectedObstacle: (id: number | null) => void
  setSelectedPanel: (idx: number | null) => void
  removeSelectedPanel: () => void
  toggleControls: () => void
  tickSimulation: () => void
}

export const useStore = create<AppState>((set, get) => ({
  polygon: null,
  panelCount: 12,
  lat: 14.716,
  lon: -17.467,
  annualConsumption: 0,
  installType: 'autoconsommation',

  roofType: null,
  pitch: 15,
  azimuth: 180,
  wallHeight: 3,

  simDate: new Date(),
  simHour: 12,
  isPlaying: false,

  sceneMode: 'view',
  obstacleTypeToPlace: null,

  obstacles: [],
  selectedObstacle: null,

  selectedPanel: null,
  removedPanels: new Set(),
  controlsOpen: true,

  _popupData: null,
  _popupX: 0,
  _popupY: 0,
  _obstaclePanelOpen: false,

  // ── Actions ────────────────────────────────────────────────────────────────

  setFromParent: (data) =>
    set((s) => ({
      polygon: data.polygon ?? s.polygon,
      panelCount: data.panelCount ?? s.panelCount,
      lat: data.lat ?? s.lat,
      lon: data.lon ?? s.lon,
      annualConsumption: data.annualConsumption ?? s.annualConsumption,
      installType: data.installType ?? s.installType,
    })),

  setPanelCount: (count) => set({ panelCount: count, removedPanels: new Set() }),

  setRoofType: (type) => set({ roofType: type }),

  setPitch: (pitch) => {
    set({ pitch })
    window.parent.postMessage({ type: 'TILT_AZIMUTH', tilt: pitch, azimuth: get().azimuth }, '*')
  },

  setAzimuth: (azimuth) => {
    set({ azimuth })
    window.parent.postMessage({ type: 'TILT_AZIMUTH', tilt: get().pitch, azimuth }, '*')
  },

  setWallHeight: (wallHeight) => set({ wallHeight }),

  setSimDate: (simDate) => set({ simDate }),

  setSimHour: (simHour) => set({ simHour }),

  setIsPlaying: (isPlaying) => set({ isPlaying }),

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
    const { selectedPanel, removedPanels, panelCount } = get()
    if (selectedPanel === null) return
    const next = new Set(removedPanels)
    next.add(selectedPanel)
    set({ removedPanels: next, selectedPanel: null, _popupData: null })
    // Notify parent to decrement panel count
    window.parent.postMessage({ type: 'REMOVE_PANEL' }, '*')
    set({ panelCount: Math.max(0, panelCount - 1) })
  },

  toggleControls: () => set((s) => ({ controlsOpen: !s.controlsOpen })),

  tickSimulation: () => {
    const next = (get().simHour + 0.05) % 24
    set({ simHour: next })
  },
}))
