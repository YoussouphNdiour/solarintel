export type RoofType = 'flat' | 'shed' | 'gable' | 'hip'

export type InstallType = 'autoconsommation' | 'hybride' | 'autonome'

export type WeatherMode = 'clear' | 'cloudy' | 'overcast'

export type RoofMaterial = 'tuile-rouge' | 'tuile-grise' | 'zinc' | 'bac-acier' | 'beton'

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

export interface ParentMessage {
  type: 'INIT' | 'UPDATE_PANELS'
  polygon?: [number, number][]
  panelCount?: number
  lat?: number
  lon?: number
  annualConsumption?: number
  installType?: InstallType
  panelWidthMm?: number
  panelHeightMm?: number
  orientation?: 'portrait' | 'landscape'
  spacingHCm?: number
  spacingVCm?: number
}

export interface ChildMessage {
  type: 'TILT_AZIMUTH' | 'READY' | 'REMOVE_PANEL' | 'ADD_PANEL'
  tilt?: number
  azimuth?: number
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
