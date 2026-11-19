import { createStrategyRoutes } from '../../src/app/strategyRoutes'

export const strategyRoutesFixture = createStrategyRoutes([
  { kind: 'strategy', id: 'strategy-fixture', title: '测试策略' },
  { kind: 'strategy', id: 'strategy-second-fixture', title: '第二测试策略' },
])
