# Experimental segmentation review

The offline review tool consumes canonical Price Segmentation results and offers
experimental merged views solely for human comparison. It does not change or publish
another canonical observation, establish financial swing quality, or retain the PIP
error bound for merged lines. Smoothing does not modify the original observation set or
PIP algorithm, replace Base Segments, or automatically enter formal Statistics.
It does not acquire market facts or access a cache.

Each profile takes nonnegative duration and absolute amplitude thresholds. A segment
is tiny when either duration or absolute endpoint return is at most its threshold.
Repeatedly merge the first tiny countertrend segment with its two non-flat,
same-direction neighbors; if none exists, merge the first tiny segment with its
following neighbor, or its preceding neighbor at the end. Recompute direction,
duration and endpoint return after each merge and stop when no candidate remains or
only one segment remains. The deterministic left-to-right priority and threshold
comparison apply to current merged segments. Profiles light (1, 0.015) and medium
(2, 0.025) are review choices, not research defaults.

Merged segments use actual canonical endpoints and retain ordered zero-based base
segment ordinals. They partition the base segments, preserve shared boundaries and
cover the original scope. Their duration is the endpoint index difference and their
amplitude is end close / start close - 1. The review pack labels every profile and
exposes counts, median duration, single-session ratio and base mapping. Original
canonical result evidence remains unchanged. Close-space lines are visual aids.
