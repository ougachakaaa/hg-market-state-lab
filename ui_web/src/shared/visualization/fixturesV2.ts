import acceptance from './fixtureV2.json'
import type { ViewV2 } from './contractV2'

/** Verbatim fixed WP1 fixture; variants never modify this object. */
export const fixtureV2 = acceptance as ViewV2
export function extendedFixtureV2(): ViewV2 {
  const view = structuredClone(fixtureV2)
  view.events.push(
    { id: 'e2', x_axis: 'time', x: '2026-01-05', label: 'Same date', details: [{ label: 'Note', value: '<b>literal event</b>' }, { label: 'Note', value: 'Second detail' }] },
    { id: 'e3', x_axis: 'time', x: '2026-01-12', label: 'Event only date', details: [] },
  )
  return view
}
