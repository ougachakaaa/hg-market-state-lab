# Offline Chinese font

`report-cjk.woff` is a subset of Noto Sans CJK SC Regular, distributed under the
adjacent SIL Open Font License. Source:
https://github.com/notofonts/noto-cjk/blob/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf

The subset includes printable ASCII and all characters in the production
Research `report.py` / `evidence.py`, offline `Report.tsx` and generic `ChartView.tsx`
as of WP5, plus the shared reader’s WP3-B fixed presentation copy. Existing glyph coverage is retained. The derived font family is renamed R01A Report CJK; original
copyright/license/designer records are retained. It is a checked-in rendering asset, not market data. Add any new reader
copy's characters when updating the font; arbitrary external text can fall back
to the operating system's fonts. No runtime font-generation dependency is added.

One-time generation uses FontTools' subset API: load the upstream OTF, set
`Options.flavor='woff'`, retain naming/license records, populate a Subsetter with
the above source text plus ASCII U+0020..U+007E, subset, and save this file.
The report CSS embeds the font through Vite's inline asset packaging; browsers
never contact a font server. The generated report retains the font copyright and
license in its WOFF name records; the packager also embeds the full OFL text.

Upstream OTF SHA-256: `2c76254f6fc379fddfce0a7e84fb5385bb135d3e399294f6eeb6680d0365b74b`.
