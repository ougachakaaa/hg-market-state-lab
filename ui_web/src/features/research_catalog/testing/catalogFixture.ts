import descriptor from '../api/catalog.fixture.json'

// Test-only regression data. This is not an official D3 Capability Example and it is
// not live discovery: the existing API regression fixture is reused unchanged.
export const capabilityDetail = descriptor
export const capabilityList = [descriptor]
export const embeddedCatalog = { list: capabilityList, details: [descriptor] }
