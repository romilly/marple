


from marple.adapters.numpy_array_builder import NumpyArrayBuilder


class TestArrayBuilder:
    def test_builds_apl_array(self):
        builder = NumpyArrayBuilder()
        result = builder.apl_array([3],[1, 2, 3], None)
        assert result is not None