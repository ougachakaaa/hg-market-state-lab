"""Study-local identities and shared Method constants."""

FAMILIES = ("IF", "IH", "IC", "IM")
SLOTS = ("M0", "M1", "Q1", "Q2")
HORIZONS = (1, 3, 5, 10, 20)
PERCENTILES = (10, 20, 40, 50, 60, 80, 90)
STUDY_ID = "cffex-basis-forward-return-association"
PREDICTOR = "mean(M1,Q1,Q2 annualized_basis_pct)"


class CFFEXStudyError(ValueError):
    """Required Study observations or populations cannot produce evidence."""
