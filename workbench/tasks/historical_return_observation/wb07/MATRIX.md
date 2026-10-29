# WB-07 actual Cold/Warm research matrix

Source: immutable actual Research BatchResult `06f9fc648e16494dbf79ab35585a3a09`, SHA-256 `e59d737f93212b48b934926b19833b7f2fc832327ee726e434deab2b45d40fb1`. Full precision values and interval outcomes: [results.json](results.json). Independent saved-Export verification passed for all 16 Jobs / 32 analyses.

Inclusive question window: 2026-01-01..2026-10-29. First open anchor 2026-01-05; final anchor 2026-10-29 is present. Each H uses the full formal SSE Calendar; H=10 warm-up begins 2025-12-18. Percentages below are display conversions from decimal_ratio; no observation rounding was used.

| Index | H | Sample | Eligible | Unavailable | Excluded | Obs coverage | Fact coverage | P5 | P10 | P25 | Median | P75 | P90 | P95 | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 000852.SH 中证1000 | 1 | 197 | 197 | 0 | 0 | 100% | 100% | -3.0792% | -2.4456% | -1.3230% | 0.1974% | 1.0241% | 2.1091% | 2.5621% | Success |
| 000852.SH 中证1000 | 3 | 197 | 197 | 0 | 0 | 100% | 100% | -4.8620% | -3.9655% | -2.1453% | -0.1828% | 1.9973% | 3.3600% | 4.3781% | Success |
| 000852.SH 中证1000 | 5 | 197 | 197 | 0 | 0 | 100% | 100% | -6.4790% | -5.2328% | -3.0954% | -0.2284% | 2.5500% | 4.5547% | 6.2583% | Success |
| 000852.SH 中证1000 | 10 | 197 | 197 | 0 | 0 | 100% | 100% | -11.3772% | -8.5580% | -4.2710% | -0.5547% | 4.2370% | 7.3440% | 9.0101% | Success |
| 000905.SH 中证500 | 1 | 197 | 197 | 0 | 0 | 100% | 100% | -3.0033% | -2.5495% | -1.2831% | 0.0355% | 1.1245% | 2.1743% | 2.5001% | Success |
| 000905.SH 中证500 | 3 | 197 | 197 | 0 | 0 | 100% | 100% | -4.5289% | -3.9819% | -2.2535% | 0.0625% | 1.9235% | 3.4036% | 4.5123% | Success |
| 000905.SH 中证500 | 5 | 197 | 197 | 0 | 0 | 100% | 100% | -5.8439% | -5.1455% | -2.9828% | -0.4030% | 2.8900% | 4.5797% | 5.9765% | Success |
| 000905.SH 中证500 | 10 | 197 | 197 | 0 | 0 | 100% | 100% | -9.7520% | -8.1237% | -4.2776% | -0.6966% | 4.4278% | 8.0548% | 9.1199% | Success |
| 000300.SH 沪深300 | 1 | 197 | 197 | 0 | 0 | 100% | 100% | -1.9937% | -1.4518% | -0.6897% | -0.0435% | 0.6634% | 1.4218% | 1.6541% | Success |
| 000300.SH 沪深300 | 3 | 197 | 197 | 0 | 0 | 100% | 100% | -3.1527% | -2.2747% | -1.2409% | -0.2081% | 0.9453% | 1.8683% | 2.8512% | Success |
| 000300.SH 沪深300 | 5 | 197 | 197 | 0 | 0 | 100% | 100% | -3.7548% | -3.2656% | -1.7554% | -0.2794% | 1.2206% | 2.4468% | 3.0214% | Success |
| 000300.SH 沪深300 | 10 | 197 | 197 | 0 | 0 | 100% | 100% | -4.8760% | -4.1147% | -2.5841% | -0.8747% | 1.6261% | 3.1726% | 4.6534% | Success |
| 000016.SH 上证50 | 1 | 197 | 197 | 0 | 0 | 100% | 100% | -1.4840% | -1.2652% | -0.6915% | -0.0511% | 0.4636% | 1.2307% | 1.6473% | Success |
| 000016.SH 上证50 | 3 | 197 | 197 | 0 | 0 | 100% | 100% | -2.4738% | -1.8639% | -1.0470% | -0.1951% | 0.7146% | 1.8217% | 2.3934% | Success |
| 000016.SH 上证50 | 5 | 197 | 197 | 0 | 0 | 100% | 100% | -2.7297% | -2.4365% | -1.5446% | -0.3850% | 1.0264% | 2.3570% | 2.8762% | Success |
| 000016.SH 上证50 | 10 | 197 | 197 | 0 | 0 | 100% | 100% | -4.0527% | -3.2149% | -2.2080% | -0.8611% | 1.2935% | 3.1581% | 3.6143% | Success |

All figures describe historical distributions. Overlapping lookback spans share market inputs; no IID, prediction, tradability or strategy-return claim follows.

The four H=1 medians are 中证1000 0.1974%, 中证500 0.0355%, 沪深300 -0.0435%, 上证50 -0.0511%. At H=10 the corresponding medians are 中证1000 -0.5547%, 中证500 -0.6966%, 沪深300 -0.8747%, 上证50 -0.8611%. These are descriptive endpoint returns, not annualized or strategy returns.

The independently authorized Warm Run `7ac42795d02f453496b6cc95fc0ec173` produced
identical full-precision values for every row. Its own saved-Export oracle verified all
16 Jobs / 32 analyses; [Cold/Warm audit](cache_audit.json) binds the separate result
artifact and all original fingerprint/observation/statistical equality checks.
