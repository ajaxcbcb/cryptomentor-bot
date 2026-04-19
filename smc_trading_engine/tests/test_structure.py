from app.core.structure import detect_bos


def test_structure_bos(bos_candles):
    r = detect_bos(bos_candles)
    assert isinstance(r.confirmed, bool)
    assert r.direction in {"LONG", "SHORT", "NONE"}
