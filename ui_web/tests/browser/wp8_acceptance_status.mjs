// Pure WP8 acceptance status classification shared by the harness and its tests.
// PASS is the only successful gate; FAIL, PARTIAL, NOT RUN and missing evidence are nonzero.
export const PASS = 'PASS'
export const FAIL = 'FAIL'
export const PARTIAL = 'PARTIAL'
export const NOT_RUN = 'NOT RUN'

export const EXIT_CODES = Object.freeze({ [PASS]: 0, [FAIL]: 1, [PARTIAL]: 2, [NOT_RUN]: 3 })
const KNOWN = new Set([PASS, FAIL, PARTIAL, NOT_RUN])

function knownStatus(value) {
  return KNOWN.has(value) ? value : NOT_RUN
}

export function exitCode(status) {
  return Object.hasOwn(EXIT_CODES, status) ? EXIT_CODES[status] : EXIT_CODES[FAIL]
}

export function combineStatuses(statuses) {
  const values = statuses.map(knownStatus)
  if (values.length === 0) return NOT_RUN
  if (values.every(value => value === PASS)) return PASS
  if (values.includes(FAIL)) return FAIL
  if (values.includes(PARTIAL)) return PARTIAL
  if (values.includes(PASS)) return PARTIAL
  return NOT_RUN
}

function profileEntries(report, profiles) {
  return profiles.map(profile => report?.profiles?.[profile])
}

function allPassing(entries) {
  return entries.length > 0 && entries.every(entry => entry && entry.status === PASS)
}

function allFingerprints(entries) {
  return entries.every(
    entry => typeof entry?.fingerprint === 'string' && entry.fingerprint.length > 0
  )
}

export function classifyPythonAcceptance(report, profiles) {
  if (!report || typeof report !== 'object') return NOT_RUN
  if (report.status === FAIL) return FAIL
  if (report.status === PARTIAL) return PARTIAL
  if (report.status !== PASS) return NOT_RUN
  if (typeof report.run_id !== 'string' || report.run_id.length === 0) return FAIL
  if (report.same_input !== true) return FAIL
  const entries = profileEntries(report, profiles)
  if (!allPassing(entries) || !allFingerprints(entries)) return FAIL
  if (new Set(entries.map(entry => entry.fingerprint)).size !== 1) return FAIL
  return PASS
}

export function classifyReproduction(report, pythonReport, profiles) {
  if (!report || typeof report !== 'object') return NOT_RUN
  if (report.status === FAIL) return FAIL
  if (report.status === PARTIAL) return PARTIAL
  if (report.status !== PASS) return NOT_RUN
  if (!pythonReport || pythonReport.status !== PASS) return NOT_RUN
  if (report.acceptance_run_id !== pythonReport.run_id) return FAIL
  const entries = profileEntries(report, profiles)
  if (!allPassing(entries)) return FAIL
  if (!entries.every(entry => entry.reproduction === 'verified')) return FAIL
  const expected = profileEntries(pythonReport, profiles)
  if (!entries.every((entry, index) => entry.fingerprint === expected[index]?.fingerprint)) {
    return FAIL
  }
  return PASS
}

export function classifyHttpAcceptance(report, pythonReport, profiles) {
  if (!report || typeof report !== 'object') return NOT_RUN
  if (report.status === FAIL) return FAIL
  if (report.status === PARTIAL) return PARTIAL
  if (report.status !== PASS) return NOT_RUN
  if (report.kind !== 'actual_http_auth_real_market') return FAIL
  if (!pythonReport || report.python_run_id !== pythonReport.run_id) return FAIL
  const entries = profileEntries(report, profiles)
  if (!allPassing(entries) || !allFingerprints(entries)) return FAIL
  if (!entries.every(entry => entry.terminal === 'COMPLETED')) return FAIL
  const expected = profileEntries(pythonReport, profiles)
  if (!entries.every((entry, index) => entry.fingerprint === expected[index]?.fingerprint)) {
    return FAIL
  }
  return PASS
}

export function classifyWindowsAcceptance(report, evidence = {}) {
  const { processExit = null, screenshots = [], profiles = [] } = evidence
  if (!report || typeof report !== 'object') return NOT_RUN
  if (report.status === FAIL) return FAIL
  if (report.status === NOT_RUN) return NOT_RUN
  if (report.status !== PASS) return NOT_RUN
  // A PASS requires an actual Windows Chrome process that exited successfully.
  if (processExit !== 0) return FAIL
  if (report.kind !== 'actual_windows_chrome_real_market') return FAIL
  if (typeof report.version !== 'string' || report.version.length === 0) return FAIL
  if (!Array.isArray(report.errors) || report.errors.length > 0) return FAIL
  const entries = profileEntries(report, profiles)
  if (!allPassing(entries) || !allFingerprints(entries)) return FAIL
  if (!entries.every(entry => typeof entry.run_id === 'string' && entry.run_id.length > 0)) {
    return FAIL
  }
  if (screenshots.length !== profiles.length || !screenshots.every(Boolean)) return FAIL
  return PASS
}

export function classifyOverall(stages) {
  return combineStatuses([
    stages?.python,
    stages?.reproduction,
    stages?.http,
    stages?.windows,
  ])
}
