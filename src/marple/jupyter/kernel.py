"""Jupyter kernel for MARPLE - flat-array APL interpreter."""

from ipykernel.kernelbase import Kernel

from marple import __version__
from marple.adapters.buffered_console import BufferedConsole
from marple.engine import Interpreter
from marple.errors import APLError
from marple.glyphs import expand_glyphs
from marple.jupyter.html_render import aplarray_to_html, ARRAY_CSS
from marple.system_commands import run_system_command


class MARPLEKernel(Kernel):
    implementation = 'marple'
    implementation_version = __version__
    language_info = {
        'name': 'apl',
        'mimetype': 'text/x-apl',
        'file_extension': '.apl',
        'codemirror_mode': 'apl',
        'pygments_lexer': 'apl',
    }
    banner = f"MARPLE v{__version__} - flat-array APL interpreter"

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._console = BufferedConsole()
        self.interp = Interpreter(io=1, console=self._console)
        self._css_sent = False

    async def do_execute(  # type: ignore[override]
        self, code: str, silent: bool, store_history: bool = True,
        user_expressions: object = None, allow_stdin: bool = False,
    ) -> dict[str, object]:
        if not self._css_sent and not silent:
            self.send_response(self.iopub_socket, 'display_data', {
                'data': {'text/html': ARRAY_CSS},
                'metadata': {},
            })
            self._css_sent = True

        code = expand_glyphs(code.strip())
        if not code:
            return self._ok_reply()

        if code.startswith(')'):
            return await self._handle_system_command(code, silent)

        try:
            self._console.clear()
            r = self.interp.execute(code)
            console_output = self._console.output
            if not silent and console_output:
                self.send_response(self.iopub_socket, 'stream', {
                    'name': 'stdout',
                    'text': console_output,
                })
            if not silent and not r.silent:
                html = aplarray_to_html(r.value)
                self.send_response(self.iopub_socket, 'execute_result', {
                    'execution_count': self.execution_count,
                    'data': {
                        'text/plain': r.display_text,
                        'text/html': html,
                    },
                    'metadata': {},
                })
            return self._ok_reply()
        except APLError as e:
            return self._error_reply(e.name, str(e))
        except Exception as e:
            return self._error_reply(type(e).__name__, str(e))

    async def _handle_system_command(self, cmd: str,
                                     silent: bool) -> dict[str, object]:
        output, _ = run_system_command(self.interp, cmd)
        if not silent and output:
            self.send_response(self.iopub_socket, 'stream', {
                'name': 'stdout',
                'text': output + '\n',
            })
        return self._ok_reply()

    async def do_complete(self, code: str,  # type: ignore[override]
                          cursor_pos: int) -> dict[str, object]:
        token = self._extract_token(code, cursor_pos)
        if not token:
            return self._empty_complete(cursor_pos)
        all_names = (
            [name for name, _ in self.interp.env.list_variables()] +
            [name for name, _ in self.interp.env.list_functions()]
        )
        matches = sorted(n for n in all_names if n.startswith(token))
        return {
            'matches': matches,
            'cursor_start': cursor_pos - len(token),
            'cursor_end': cursor_pos,
            'metadata': {},
            'status': 'ok',
        }

    async def do_inspect(self, code: str, cursor_pos: int,  # type: ignore[override]
                         detail_level: int = 0,
                         omit_sections: tuple[str, ...] = ()) -> dict[str, object]:
        token = self._extract_token(code, cursor_pos)
        if not token:
            return {'status': 'ok', 'found': False, 'data': {}, 'metadata': {}}
        val = self.interp.env.get(token)
        if val is None:
            return {'status': 'ok', 'found': False, 'data': {}, 'metadata': {}}
        info = self._describe(token, val)
        return {
            'status': 'ok',
            'found': True,
            'data': {'text/plain': info},
            'metadata': {},
        }

    async def do_is_complete(self, code: str) -> dict[str, object]:  # type: ignore[override]
        from marple.parser import is_balanced
        if is_balanced(code):
            return {'status': 'complete'}
        return {'status': 'incomplete', 'indent': '  '}

    def _extract_token(self, code: str, cursor_pos: int) -> str:
        i = cursor_pos - 1
        while i >= 0 and (code[i].isalnum() or code[i] in '_⎕∆⍙'):
            i -= 1
        return code[i + 1:cursor_pos]

    def _describe(self, name: str, val: object) -> str:
        from marple.arraymodel import APLArray
        lines = [f"Name: {name}"]
        if isinstance(val, APLArray):
            shape_str = ' '.join(str(s) for s in val.shape) if val.shape else 'scalar'
            lines.append(f"Shape: {shape_str}")
            lines.append(f"Rank: {len(val.shape)}")
            lines.append(f"Elements: {len(val.data)}")
        else:
            source = self.interp.env.get_source(name)
            if source:
                lines.append(f"Source: {source}")
            else:
                lines.append(f"Type: {type(val).__name__}")
        return '\n'.join(lines)

    def _ok_reply(self) -> dict[str, object]:
        return {
            'status': 'ok',
            'execution_count': self.execution_count,
            'payload': [],
            'user_expressions': {},
        }

    def _error_reply(self, ename: str, evalue: str) -> dict[str, object]:
        content: dict[str, object] = {
            'ename': ename,
            'evalue': evalue,
            'traceback': [f'\x1b[0;31m{ename}\x1b[0m: {evalue}'],
        }
        self.send_response(self.iopub_socket, 'error', content)
        return {'status': 'error', **content}

    def _empty_complete(self, cursor_pos: int) -> dict[str, object]:
        return {
            'matches': [],
            'cursor_start': cursor_pos,
            'cursor_end': cursor_pos,
            'metadata': {},
            'status': 'ok',
        }
