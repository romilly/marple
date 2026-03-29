"""Kernel unit tests with mocked ZeroMQ socket."""

import pytest
from unittest.mock import MagicMock

from marple.engine import Interpreter
from marple.jupyter.kernel import MARPLEKernel


@pytest.fixture
def kernel() -> MARPLEKernel:
    k = MARPLEKernel.instance()
    k.send_response = MagicMock()  # type: ignore[method-assign]
    k.execution_count = 1
    k.interp = Interpreter(io=1)
    k._css_sent = True  # skip CSS injection for cleaner test output
    return k


def _result_calls(kernel: MARPLEKernel) -> list[object]:
    return [c for c in kernel.send_response.call_args_list  # type: ignore[union-attr]
            if c[0][1] == 'execute_result']


def _stream_calls(kernel: MARPLEKernel) -> list[object]:
    return [c for c in kernel.send_response.call_args_list  # type: ignore[union-attr]
            if c[0][1] == 'stream']


class TestDoExecute:
    @pytest.mark.asyncio
    async def test_simple_arithmetic(self, kernel: MARPLEKernel) -> None:
        result = await kernel.do_execute('2+3', silent=False)
        assert result['status'] == 'ok'
        calls = _result_calls(kernel)
        assert len(calls) == 1
        data = calls[0][0][2]['data']  # type: ignore[index]
        assert data['text/plain'] == '5'
        assert '<' in data['text/html']

    @pytest.mark.asyncio
    async def test_assignment_is_silent(self, kernel: MARPLEKernel) -> None:
        result = await kernel.do_execute('x←42', silent=False)
        assert result['status'] == 'ok'
        assert len(_result_calls(kernel)) == 0

    @pytest.mark.asyncio
    async def test_variable_persists(self, kernel: MARPLEKernel) -> None:
        await kernel.do_execute('x←10', silent=False)
        kernel.send_response.reset_mock()  # type: ignore[union-attr]
        result = await kernel.do_execute('x×x', silent=False)
        assert result['status'] == 'ok'
        calls = _result_calls(kernel)
        assert calls[0][0][2]['data']['text/plain'] == '100'  # type: ignore[index]

    @pytest.mark.asyncio
    async def test_error(self, kernel: MARPLEKernel) -> None:
        result = await kernel.do_execute('1÷0', silent=False)
        assert result['status'] == 'error'
        assert 'DOMAIN' in str(result['ename'])

    @pytest.mark.asyncio
    async def test_matrix_html(self, kernel: MARPLEKernel) -> None:
        result = await kernel.do_execute('2 3⍴⍳6', silent=False)
        calls = _result_calls(kernel)
        html = calls[0][0][2]['data']['text/html']  # type: ignore[index]
        assert '<table' in html
        assert '<tr>' in html

    @pytest.mark.asyncio
    async def test_backtick_translation(self, kernel: MARPLEKernel) -> None:
        result = await kernel.do_execute('`r 2 3', silent=False)
        assert result['status'] == 'ok'

    @pytest.mark.asyncio
    async def test_dfn(self, kernel: MARPLEKernel) -> None:
        await kernel.do_execute('double←{⍵+⍵}', silent=False)
        kernel.send_response.reset_mock()  # type: ignore[union-attr]
        result = await kernel.do_execute('double 21', silent=False)
        assert result['status'] == 'ok'
        calls = _result_calls(kernel)
        assert calls[0][0][2]['data']['text/plain'] == '42'  # type: ignore[index]


class TestSystemCommands:
    @pytest.mark.asyncio
    async def test_vars(self, kernel: MARPLEKernel) -> None:
        await kernel.do_execute('x←1', silent=False)
        kernel.send_response.reset_mock()  # type: ignore[union-attr]
        result = await kernel.do_execute(')vars', silent=False)
        assert result['status'] == 'ok'
        calls = _stream_calls(kernel)
        assert any('x' in c[0][2]['text'] for c in calls)  # type: ignore[index]


class TestCompletion:
    @pytest.mark.asyncio
    async def test_complete(self, kernel: MARPLEKernel) -> None:
        await kernel.do_execute('alpha←1', silent=False)
        await kernel.do_execute('alphabet←2', silent=False)
        result = await kernel.do_complete('alph', 4)
        assert 'alpha' in result['matches']
        assert 'alphabet' in result['matches']


class TestIsComplete:
    @pytest.mark.asyncio
    async def test_complete(self, kernel: MARPLEKernel) -> None:
        result = await kernel.do_is_complete('2+3')
        assert result['status'] == 'complete'

    @pytest.mark.asyncio
    async def test_incomplete(self, kernel: MARPLEKernel) -> None:
        result = await kernel.do_is_complete('f←{⍵+1')
        assert result['status'] == 'incomplete'
