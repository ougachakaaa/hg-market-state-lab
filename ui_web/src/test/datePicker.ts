import { fireEvent } from '@testing-library/react'

/** Commit a calendar date using the DatePicker keyboard interaction. */
export function commitDate(input: HTMLElement, value: string) {
  if (!value && input.closest('.ant-picker')?.querySelector('.ant-picker-clear')) {
    fireEvent.click(input.closest('.ant-picker')!.querySelector('.ant-picker-clear')!)
    return
  }
  fireEvent.change(input, { target: { value } })
  fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' })
  fireEvent.blur(input)
}
