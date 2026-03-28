from unittest.mock import patch

from marple.arraymodel import S
from marple.engine import Interpreter


class TestConstruction:
    @patch("marple.config.get_default_io", return_value=1)
    def test_construct_default(self, _mock_io: object) -> None:
        interp = Interpreter()
        assert interp.env["⎕IO"] == S(1)
