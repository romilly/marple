from marple.glyphs import expand_glyphs


class TestExpandGlyphs:
    def test_rho(self) -> None:
        assert expand_glyphs("`r") == "⍴"

    def test_iota(self) -> None:
        assert expand_glyphs("`i") == "⍳"

    def test_assign(self) -> None:
        assert expand_glyphs("`l") == "←"

    def test_mixed(self) -> None:
        assert expand_glyphs("x`l3`r`i6") == "x←3⍴⍳6"

    def test_literal_backtick(self) -> None:
        assert expand_glyphs("``") == "`"

    def test_unknown_leaves_backtick(self) -> None:
        assert expand_glyphs("`9") == "`9"

    def test_no_backticks(self) -> None:
        assert expand_glyphs("2+3") == "2+3"

    def test_high_minus(self) -> None:
        assert expand_glyphs("`23") == "¯3"

    def test_omega_alpha(self) -> None:
        assert expand_glyphs("{`a+`w}") == "{⍺+⍵}"

    def test_diamond(self) -> None:
        assert expand_glyphs("x`l1`xy`l2") == "x←1⋄y←2"
