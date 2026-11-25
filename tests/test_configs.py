from redteam.agent import BASE_SYSTEM
from redteam.configs import CONFIGS, HARDENED_SYSTEM


def test_hardened_prompt_keeps_every_baseline_rule():
    assert HARDENED_SYSTEM.startswith(BASE_SYSTEM)


def test_config_names_match_their_keys():
    assert all(k == c.name for k, c in CONFIGS.items())
