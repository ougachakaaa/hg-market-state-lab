"""Independent, pure numerical Statistics V1 public facade."""

from .api import compute as compute
from .failures import CalculationFailure as CalculationFailure
from .failures import InvalidSample as InvalidSample
from .failures import InvalidStatisticalSpec as InvalidStatisticalSpec
from .failures import StatisticalFailure as StatisticalFailure
from .models import IntervalBin as IntervalBin
from .models import IntervalCountResult as IntervalCountResult
from .models import IntervalCountSpec as IntervalCountSpec
from .models import MeanResult as MeanResult
from .models import MeanSpec as MeanSpec
from .models import NumericSample as NumericSample
from .models import QuantileResult as QuantileResult
from .models import QuantileSpec as QuantileSpec
from .models import StatisticalResult as StatisticalResult
from .models import StatisticalSpec as StatisticalSpec
from .validation import validate_spec as validate_spec
