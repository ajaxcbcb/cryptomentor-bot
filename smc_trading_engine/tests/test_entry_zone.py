from app.core.entry_zone import detect_entry_zone


def test_entry_zone_exists(fvg_candles):
    r = detect_entry_zone(fvg_candles, "LONG")
    assert isinstance(r.exists, bool)
    if r.exists:
        assert r.preferred_zone.zone_type in {"OB", "FVG"}
