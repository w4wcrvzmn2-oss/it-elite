import { describe, it, expect, beforeEach } from 'vitest'
import { useProjectStore } from '../stores/projectStore'

describe('projectStore', () => {
  beforeEach(() => {
    useProjectStore.getState().reset()
  })

  it('sets file and job', () => {
    useProjectStore.getState().setFile('f1', 'test.dxf')
    useProjectStore.getState().setJob('j1')
    expect(useProjectStore.getState().fileId).toBe('f1')
    expect(useProjectStore.getState().jobId).toBe('j1')
  })

  it('toggles layers', () => {
    useProjectStore.getState().toggleLayer('trees')
    expect(useProjectStore.getState().layers.trees).toBe(false)
  })
})
