import { describe, expect, it } from 'vitest'
import {
  FAIL,
  NOT_RUN,
  PARTIAL,
  PASS,
  classifyHttpAcceptance,
  classifyOverall,
  classifyPythonAcceptance,
  classifyReproduction,
  classifyWindowsAcceptance,
  combineStatuses,
  exitCode,
} from './wp8_acceptance_status.mjs'

const profiles = ['expiry_to_M1_v1', 'expiry_to_Q1_v1']
const fingerprint = 'b83a38c9bdc83f082eda87e93c1babdb9950dacad1e316b4186a2e07e0ef557c'

function pythonAcceptance(status = PASS) {
  return {
    kind: 'actual_real_market',
    status,
    run_id: 'run-1',
    same_input: status === PASS,
    profiles: Object.fromEntries(
      profiles.map(profile => [profile, { status, fingerprint }]),
    ),
  }
}

function reproduction(overrides = {}) {
  return {
    kind: 'offline_evidence_reproduction',
    status: PASS,
    acceptance_run_id: 'run-1',
    profiles: Object.fromEntries(
      profiles.map(profile => [
        profile,
        { status: PASS, reproduction: 'verified', fingerprint, events: 10 },
      ]),
    ),
    ...overrides,
  }
}

function httpAcceptance(overrides = {}) {
  return {
    kind: 'actual_http_auth_real_market',
    status: PASS,
    python_run_id: 'run-1',
    profiles: Object.fromEntries(
      profiles.map(profile => [
        profile,
        { status: PASS, terminal: 'COMPLETED', run_id: `run-${profile}`, fingerprint },
      ]),
    ),
    ...overrides,
  }
}

function windowsAcceptance(overrides = {}) {
  return {
    kind: 'actual_windows_chrome_real_market',
    status: PASS,
    version: '157.0.8103.39',
    errors: [],
    profiles: Object.fromEntries(
      profiles.map(profile => [
        profile,
        { status: PASS, run_id: `windows-${profile}`, fingerprint },
      ]),
    ),
    ...overrides,
  }
}

const windowsEvidence = { processExit: 0, screenshots: [true, true], profiles }

describe('acceptance exit semantics', () => {
  it('maps PASS to 0 and every other classification to a nonzero code', () => {
    expect(exitCode(PASS)).toBe(0)
    expect(exitCode(FAIL)).toBeGreaterThan(0)
    expect(exitCode(PARTIAL)).toBeGreaterThan(0)
    expect(exitCode(NOT_RUN)).toBeGreaterThan(0)
    expect(exitCode('UNKNOWN')).toBeGreaterThan(0)
  })

  it('never combines a failure or missing stage into PASS', () => {
    expect(combineStatuses([PASS, PASS])).toBe(PASS)
    expect(combineStatuses([PASS, FAIL, PASS])).toBe(FAIL)
    expect(combineStatuses([PASS, NOT_RUN])).toBe(PARTIAL)
    expect(combineStatuses([NOT_RUN, NOT_RUN])).toBe(NOT_RUN)
    expect(combineStatuses([PASS, PARTIAL])).toBe(PARTIAL)
    expect(combineStatuses([])).toBe(NOT_RUN)
  })
})

describe('Python acceptance artifact', () => {
  it('accepts a complete, same-input, stamped round', () => {
    expect(classifyPythonAcceptance(pythonAcceptance(), profiles)).toBe(PASS)
  })

  it('rejects a stale or unidentifiable PASS artifact', () => {
    expect(classifyPythonAcceptance({ ...pythonAcceptance(), run_id: '' }, profiles)).toBe(FAIL)
    expect(classifyPythonAcceptance({ ...pythonAcceptance(), same_input: false }, profiles)).toBe(FAIL)
    expect(classifyPythonAcceptance(null, profiles)).toBe(NOT_RUN)
  })

  it('preserves FAIL/PARTIAL, and treats a missing profile as not passing', () => {
    expect(classifyPythonAcceptance(pythonAcceptance(FAIL), profiles)).toBe(FAIL)
    expect(classifyPythonAcceptance(pythonAcceptance(PARTIAL), profiles)).toBe(PARTIAL)
    const incomplete = pythonAcceptance()
    delete incomplete.profiles[profiles[1]]
    expect(classifyPythonAcceptance(incomplete, profiles)).toBe(FAIL)
  })

  it('rejects mismatched profile fingerprints', () => {
    const report = pythonAcceptance()
    report.profiles[profiles[1]].fingerprint = 'f'.repeat(64)
    expect(classifyPythonAcceptance(report, profiles)).toBe(FAIL)
  })
})

describe('offline reproduction artifact', () => {
  it('requires a verified reproduction of the same acceptance round', () => {
    expect(classifyReproduction(reproduction(), pythonAcceptance(), profiles)).toBe(PASS)
    expect(classifyReproduction(null, pythonAcceptance(), profiles)).toBe(NOT_RUN)
    expect(
      classifyReproduction(reproduction({ acceptance_run_id: 'other' }), pythonAcceptance(), profiles),
    ).toBe(FAIL)
  })

  it('rejects unverified or mismatched evidence', () => {
    const unverified = reproduction()
    unverified.profiles[profiles[0]].reproduction = 'changed'
    expect(classifyReproduction(unverified, pythonAcceptance(), profiles)).toBe(FAIL)
    const mismatch = reproduction()
    mismatch.profiles[profiles[0]].fingerprint = 'f'.repeat(64)
    expect(classifyReproduction(mismatch, pythonAcceptance(), profiles)).toBe(FAIL)
    expect(classifyReproduction(reproduction({ status: FAIL }), pythonAcceptance(), profiles)).toBe(FAIL)
  })
})

describe('HTTP acceptance artifact', () => {
  it('requires both profiles and the Python run association', () => {
    expect(classifyHttpAcceptance(httpAcceptance(), pythonAcceptance(), profiles)).toBe(PASS)
    expect(classifyHttpAcceptance(null, pythonAcceptance(), profiles)).toBe(NOT_RUN)
    expect(classifyHttpAcceptance(httpAcceptance({ python_run_id: 'other' }), pythonAcceptance(), profiles)).toBe(FAIL)
  })

  it('rejects a non-completed terminal or failed profile', () => {
    const notCompleted = httpAcceptance()
    notCompleted.profiles[profiles[1]].terminal = 'FAILED'
    expect(classifyHttpAcceptance(notCompleted, pythonAcceptance(), profiles)).toBe(FAIL)
    expect(classifyHttpAcceptance(httpAcceptance({ status: FAIL }), pythonAcceptance(), profiles)).toBe(FAIL)
  })
})

describe('Windows Chrome artifact', () => {
  it('requires an actual, successful, fully evidenced browser execution', () => {
    expect(classifyWindowsAcceptance(windowsAcceptance(), windowsEvidence)).toBe(PASS)
  })

  it('never passes when Windows Chrome was not executed', () => {
    expect(classifyWindowsAcceptance(null, windowsEvidence)).toBe(NOT_RUN)
    expect(
      classifyWindowsAcceptance(windowsAcceptance(), { ...windowsEvidence, processExit: null }),
    ).toBe(FAIL)
    expect(
      classifyWindowsAcceptance(windowsAcceptance(), { ...windowsEvidence, screenshots: [true, false] }),
    ).toBe(FAIL)
    expect(
      classifyWindowsAcceptance(windowsAcceptance({ status: NOT_RUN }), windowsEvidence),
    ).toBe(NOT_RUN)
  })

  it('rejects incomplete browser evidence even if the artifact claims PASS', () => {
    expect(classifyWindowsAcceptance(windowsAcceptance({ version: '' }), windowsEvidence)).toBe(FAIL)
    expect(classifyWindowsAcceptance(windowsAcceptance({ errors: ['TypeError'] }), windowsEvidence)).toBe(FAIL)
    const missingErrors = windowsAcceptance()
    delete missingErrors.errors
    expect(classifyWindowsAcceptance(missingErrors, windowsEvidence)).toBe(FAIL)
    const missingRun = windowsAcceptance()
    missingRun.profiles[profiles[1]].run_id = ''
    expect(classifyWindowsAcceptance(missingRun, windowsEvidence)).toBe(FAIL)
  })
})

describe('aggregate gate', () => {
  const passing = { python: PASS, reproduction: PASS, http: PASS, windows: PASS }

  it('is PASS only when every stage passes', () => {
    expect(classifyOverall(passing)).toBe(PASS)
  })

  it('cannot be masked by later successful checks', () => {
    expect(classifyOverall({ ...passing, http: FAIL })).toBe(FAIL)
    expect(classifyOverall({ ...passing, python: FAIL })).toBe(FAIL)
    expect(classifyOverall({ ...passing, windows: FAIL })).toBe(FAIL)
    expect(classifyOverall({ ...passing, windows: NOT_RUN })).toBe(PARTIAL)
    expect(classifyOverall({ python: PASS, reproduction: PASS })).not.toBe(PASS)
    expect(exitCode(classifyOverall({ ...passing, http: FAIL }))).toBeGreaterThan(0)
  })
})
