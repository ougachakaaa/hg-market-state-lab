"""Public synthetic W2 Policy/replay/performance boundary; real-market API belongs to WP3."""

from .failures import FuturesRollError as FuturesRollError
from .models import PRODUCT_CODES as PRODUCT_CODES
from .models import STRATEGY_PROFILES as STRATEGY_PROFILES
from .models import ContractClose as ContractClose
from .models import DailyPerformance as DailyPerformance
from .models import DailyProjection as DailyProjection
from .models import DecisionContext as DecisionContext
from .models import DecisionSlotEvidence as DecisionSlotEvidence
from .models import Execution as Execution
from .models import FuturesRollInput as FuturesRollInput
from .models import FuturesRollPerformance as FuturesRollPerformance
from .models import FuturesRollReplay as FuturesRollReplay
from .models import IndexClose as IndexClose
from .models import PerformanceSummary as PerformanceSummary
from .models import ProductCode as ProductCode
from .models import RollEvent as RollEvent
from .models import SessionFacts as SessionFacts
from .models import StrategyProfile as StrategyProfile
from .performance import analyze_futures_roll as analyze_futures_roll
from .policy import MechanicalRollPolicy as MechanicalRollPolicy
from .replay import replay_futures_roll as replay_futures_roll
