import os
import re
from pathlib import Path


def _handlers_source() -> str:
    root = Path(__file__).resolve().parents[1]
    path = root / "Bismillah" / "app" / "handlers_autotrade.py"
    return path.read_text(encoding="utf-8")


def test_registers_mixed_mode_callback_routes():
    src = _handlers_source()
    patterns = [
        r'CallbackQueryHandler\(callback_trading_mode_menu,\s*pattern="\^trading_mode_menu\$"\)',
        r'CallbackQueryHandler\(callback_select_scalping,\s*pattern="\^mode_select_scalping\$"\)',
        r'CallbackQueryHandler\(callback_select_swing,\s*pattern="\^mode_select_swing\$"\)',
        r'CallbackQueryHandler\(callback_select_mixed,\s*pattern="\^mode_select_mixed\$"\)',
    ]
    for p in patterns:
        assert re.search(p, src), f"Missing callback registration: {p}"


def test_registers_dead_path_callback_routes():
    src = _handlers_source()
    patterns = [
        r'CallbackQueryHandler\(callback_dashboard,\s*pattern="\^at_dashboard\$"\)',
        r'CallbackQueryHandler\(callback_switch_risk_mode,\s*pattern="\^at_switch_risk_mode\$"\)',
        r'CallbackQueryHandler\(callback_settings,\s*pattern="\^at_settings\$"\)',
    ]
    for p in patterns:
        assert re.search(p, src), f"Missing callback registration: {p}"


def test_settings_dependencies_are_imported():
    src = _handlers_source()
    assert "get_risk_mode" in src
    assert "get_risk_per_trade" in src
    assert "set_risk_mode" in src
    assert "section_header" in src
    assert "settings_group" in src

