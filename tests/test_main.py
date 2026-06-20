import pytest

from main import select_index


class TestSelectIndex:
    def test_parses_clean_json(self):
        assert select_index('{"index": 3}', 10) == 3

    def test_parses_json_with_surrounding_prose(self):
        # Small models often wrap the answer in chatter; fall back to the int.
        assert select_index("Sure! The best match is {'index': 2}", 10) == 2

    def test_falls_back_to_first_integer(self):
        assert select_index("I think result 4 fits best", 10) == 4

    def test_clamps_out_of_range_high(self):
        assert select_index('{"index": 99}', 5) == 4

    def test_clamps_negative(self):
        assert select_index('{"index": -3}', 5) == 0

    @pytest.mark.parametrize("raw", ["", "no number here", "nonsense"])
    def test_defaults_to_zero_when_unparseable(self, raw):
        assert select_index(raw, 5) == 0

    def test_none_reply_defaults_to_zero(self):
        # The model can return null content; select_index must not crash.
        assert select_index(None, 5) == 0
