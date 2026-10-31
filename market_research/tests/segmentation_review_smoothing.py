"""Deterministic, offline consolidation for human review only."""

from dataclasses import dataclass
from datetime import date
from statistics import median

from market_research.descriptive.cases.price_segmentation.models import PriceSegment


@dataclass(frozen=True)
class Profile:
    min_duration_sessions: int
    min_abs_amplitude: float

    def __post_init__(self) -> None:
        import math

        if (
            self.min_duration_sessions < 0
            or not math.isfinite(self.min_abs_amplitude)
            or self.min_abs_amplitude < 0
        ):
            raise ValueError("Thresholds must be nonnegative and finite")


PROFILES = {"light": Profile(1, 0.015), "medium": Profile(2, 0.025)}


@dataclass(frozen=True)
class ReviewSegment:
    start_index: int
    end_index: int
    start_date: date
    end_date: date
    start_close: float
    end_close: float
    base_segments: tuple[int, ...]

    @property
    def duration_sessions(self) -> int:
        return self.end_index - self.start_index

    @property
    def amplitude_ratio(self) -> float:
        return self.end_close / self.start_close - 1

    @property
    def direction(self) -> str:
        return (
            "up"
            if self.end_close > self.start_close
            else "down"
            if self.end_close < self.start_close
            else "flat"
        )


def smooth(base: tuple[PriceSegment, ...], profile: Profile) -> tuple[ReviewSegment, ...]:
    segments = [
        ReviewSegment(
            s.start_index, s.end_index, s.start_date, s.end_date, s.start_close, s.end_close, (i,)
        )
        for i, s in enumerate(base)
    ]
    if (
        not segments
        or any(
            a.end_index != b.start_index
            or a.end_date != b.start_date
            or a.end_close != b.start_close
            for a, b in zip(segments, segments[1:], strict=False)
        )
        or any(s.duration_sessions <= 0 or s.start_close <= 0 or s.end_close <= 0 for s in segments)
    ):
        raise ValueError("Expected continuous valid base segments")

    def tiny(s: ReviewSegment) -> bool:
        return (
            s.duration_sessions <= profile.min_duration_sessions
            or abs(s.amplitude_ratio) <= profile.min_abs_amplitude
        )

    while len(segments) > 1:
        sandwich = next(
            (
                i
                for i in range(1, len(segments) - 1)
                if tiny(segments[i])
                and segments[i - 1].direction != "flat"
                and segments[i - 1].direction == segments[i + 1].direction
                and segments[i].direction not in ("flat", segments[i - 1].direction)
            ),
            None,
        )
        if sandwich is not None:
            start, stop = sandwich - 1, sandwich + 2
        else:
            candidate = next((i for i, s in enumerate(segments) if tiny(s)), None)
            if candidate is None:
                break
            start = min(candidate, len(segments) - 2)
            stop = start + 2
        group = segments[start:stop]
        first, last = group[0], group[-1]
        segments[start:stop] = [
            ReviewSegment(
                first.start_index,
                last.end_index,
                first.start_date,
                last.end_date,
                first.start_close,
                last.end_close,
                tuple(i for s in group for i in s.base_segments),
            )
        ]
    return tuple(segments)


def diagnostics(segments: tuple[ReviewSegment, ...]) -> dict[str, float | int]:
    durations = [s.duration_sessions for s in segments]
    return {
        "segment_count": len(segments),
        "median_duration": median(durations),
        "single_session_ratio": durations.count(1) / len(durations),
    }
