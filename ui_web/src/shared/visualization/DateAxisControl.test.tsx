import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { DateAxisControl } from './DateAxisControl'

afterEach(cleanup)

it('renders the single Trading Days / Calendar Days control and reports the chosen mode', () => {
  const onChange = vi.fn()
  render(<DateAxisControl label="时间轴" value="trading" onChange={onChange} />)
  expect(screen.getByLabelText('时间轴')).toBeTruthy()
  expect(screen.getByText('Trading Days')).toBeTruthy()
  fireEvent.click(screen.getByText('Calendar Days'))
  expect(onChange).toHaveBeenCalledWith('calendar')
  expect(onChange).toHaveBeenCalledTimes(1)
})
