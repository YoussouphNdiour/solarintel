export type RoofType = 'flat' | 'shed' | 'gable' | 'hip'

export type InstallType = 'autoconsommation' | 'hybride' | 'autonome'

export type WeatherMode = 'clear' | 'cloudy' | 'overcast'

export type RoofMaterial = 'tuile-rouge' | 'tuile-grise' | 'zinc' | 'bac-acier' | 'beton'

export type DrawTool = 'orbit' | 'select' | 'rectangle' | 'line' | 'push-pull' | 'move' | 'erase'

export type DrawPhase =
  | 'idle'
  | 'rect-corner2'     // placed corner1, waiting for corner2
  | 'rect-height'      // footprint set, inputting height
  | 'line-placing'     // drawing line segments
  | 'line-height'      // polygon closed, inputting height
  | 'push-pull-drag'   // dragging to change height
  | 'move-drag'        // dragging to move building

export interface DrawnBuilding {
  id: string
  footprint: [number, number][]   // local XY (meters from global origin)
  height: number
  color: string
}

export interface LocalPolygon {
  points: [number, number][]
  centroid: [number, number]
  bbox: {
    w: number
    h: number
    angle: number
    cx: number
    cy: number
  }
}

export interface SunPosition {
  azimuth: number    // degrees, 0=N, 90=E, 180=S, 270=W
  elevation: number  // degrees, 0=horizon, 90=zenith
}

export interface PanelInfo {
  index: number
  x: number
  y: number
  z: number
  tilt: number
  azimuth: number
  estimatedProduction: number
}

export interface ZoneConfig {
  id: string                          // index stringifié ou uuid
  polygon: [number, number][]         // WGS84 ring [[lon,lat],...]
  centroid: [number, number]          // [lon, lat]
  roofType: RoofType | null
  pitch: number
  azimuth: number
  wallHeight: number
  roofMaterial: RoofMaterial
  panelCount: number
  panelPositions: [number, number][] | null
  panelWidthMm: number
  panelHeightMm: number
  orientation: 'portrait' | 'landscape'
  spacingHCm: number
  spacingVCm: number
  holePolygons: [number, number][][] | null
  label?: string
  area?: number
}

export interface ParentMessage {
  type: 'INIT' | 'UPDATE_PANELS' | 'SET_AZIMUTH' | 'REQUEST_SCREENSHOTS' | 'REQUEST_SHADOW'
  polygon?: [number, number][]
  panelCount?: number
  panelPositions?: [number, number][]   // lon/lat center of each active 2D panel
  holePolygons?: [number, number][][]   // WGS84 rings of drawn hole zones
  lat?: number
  lon?: number
  annualConsumption?: number
  installType?: InstallType
  panelWidthMm?: number
  panelHeightMm?: number
  orientation?: 'portrait' | 'landscape'
  spacingHCm?: number
  spacingVCm?: number
  azimuth?: number
  zones?: ZoneConfig[]
}

export interface ChildMessage {
  type: 'TILT_AZIMUTH' | 'READY' | 'REMOVE_PANEL' | 'ADD_PANEL' | 'SCREENSHOT_3D' | 'SHADOW_FACTOR'
  tilt?: number
  azimuth?: number
  zoneId?: string
  // SCREENSHOT_3D
  dataUrl?: string
  mode?: string   // 'normal' | 'irradiance'
  // SHADOW_FACTOR
  shadingPct?: number
  obstacleCount?: number
}

export type ObstacleType = 'chimney' | 'ac' | 'tank' | 'tree' | 'building' | 'antenna' | 'mast'

export type SceneMode = 'view' | 'place-obstacle' | 'add-panel'

export interface Obstacle {
  type: ObstacleType
  x: number
  y: number   // base Y (= wallHeight)
  z: number
  id: number
}
