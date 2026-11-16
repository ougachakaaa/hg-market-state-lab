import { cleanup, render } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { Histogram } from './Histogram'

const captured = vi.hoisted(() => ({ props: undefined as any }))
vi.mock('react-plotly.js', () => ({ default: (props: any) => { captured.props = props; return <div /> } }))
afterEach(cleanup)

it('keeps distinct raw bin identity when rounded percentage labels collide', () => {
  const distribution = {
    stage: '0_7',
    histogram: { result: { unit: 'decimal_ratio', bins: [
      { left: 0, right: 0.0001, right_inclusive: false, count: 1, frequency: 0.5 },
      { left: 0.0001, right: 0.0002, right_inclusive: true, count: 1, frequency: 0.5 },
    ] } },
  } as any
  render(<Histogram distribution={distribution} />)
  const data = captured.props.data[0]
  const layout = captured.props.layout
  expect(data.x).toEqual(['[0, 0.0001)', '[0.0001, 0.0002]'])
  expect(layout.xaxis.tickvals).toEqual(data.x)
  expect(layout.xaxis.ticktext).toEqual(['[0.0%, 0.0%)', '[0.0%, 0.0%]'])
  expect(data.text[0]).toContain('frequency=50.0%')
  expect(data.text[1]).toContain('frequency=50.0%')
  expect(layout.yaxis.tickformat).toBe('d')
})
