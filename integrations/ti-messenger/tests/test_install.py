"""Offline installer integration tests. Fake git/codex, isolated HOME, no credentials."""
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.home = self.base / 'home'
        self.home.mkdir()
        self.bin = self.base / 'bin'
        self.bin.mkdir()
        self.fixture = self.base / 'fixture'
        target = self.fixture / 'integrations/ti-messenger'
        (target / 'tests').mkdir(parents=True)
        for name in ('ti_messenger_mcp.py', 'tests/test_ti_messenger.py'):
            shutil.copyfile(HERE / name, target / name)
        # These must never be imported or discovered, even from PYTHONPATH.
        poison = "raise RuntimeError('UNPINNED_CODE_EXECUTED')\n"
        (target / 'sitecustomize.py').write_text(poison)
        (target / 'tests/test_unpinned.py').write_text(poison)
        self.root = self.home / '.local/share/daube-ti-messenger'
        self.env = {
            'HOME': str(self.home), 'PATH': f'{self.bin}:/usr/bin:/bin',
            'FIXTURE': str(self.fixture), 'TEST_BASE': str(self.base),
            'REAL_PYTHON': sys.executable, 'PYTHONPATH': str(target),
        }
        self.script('python3', '''import os, signal, subprocess, sys
if os.environ.get('CASE') == 'validation_fail' and sys.argv[-1].endswith('/validation'):
    sys.exit(42)
if os.environ.get('CASE') == 'interrupt_promotion' and sys.argv[-1].endswith('/repo'):
    result = subprocess.run([os.environ['REAL_PYTHON']] + sys.argv[1:])
    assert result.returncode == 0
    os.kill(os.getppid(), signal.SIGTERM)
    sys.exit(0)
os.execv(os.environ['REAL_PYTHON'], [os.environ['REAL_PYTHON']] + sys.argv[1:])
''')
        self.script('git', '''import os, pathlib, shutil, signal, sys
assert sys.argv[1:5] == ['clone', '--depth', '1', '--branch']
base = pathlib.Path(os.environ['TEST_BASE'])
target = pathlib.Path(sys.argv[-1])
assert target.parent.stat().st_mode & 0o777 == 0o700
(base / 'git-called').touch()
shutil.copytree(os.environ['FIXTURE'], target)
case = os.environ.get('CASE')
root = pathlib.Path(os.environ['HOME']) / '.local/share/daube-ti-messenger'
if case == 'race':
    root.mkdir()
    (root / 'sentinel').write_text('untouched')
if case == 'interrupt_clone':
    os.kill(os.getppid(), signal.SIGTERM)
if case == 'clone_fail':
    sys.exit(7)
''')
        self.script('codex', '''import json, os, pathlib, signal, sys
base = pathlib.Path(os.environ['TEST_BASE'])
case = os.environ.get('CASE')
with (base / 'calls').open('a') as f:
    f.write(' '.join(sys.argv[1:]) + '\\n')
if sys.argv[1:3] == ['mcp', 'list']:
    assert sys.argv[3:] == ['--json']
    if case == 'config_fail': sys.exit(1)
    late = case == 'late_config' and (base / 'git-called').exists()
    if case == 'config_invalid': print('{}')
    else: print(json.dumps([{'name': 'daube-ti-messenger'}] if case == 'existing_config' or late else []))
elif sys.argv[1:3] == ['mcp', 'add']:
    assert sys.argv[3:7] == ['daube-ti-messenger', '--', 'python3', '-I']
    assert pathlib.Path(sys.argv[7]).is_file()
    if case != 'add_fail': (base / 'registered').write_text(sys.argv[7])
    if case == 'interrupt_add': os.kill(os.getppid(), signal.SIGTERM)
    if case in ('add_fail', 'add_partial'): sys.exit(1)
elif sys.argv[1:3] == ['mcp', 'get']:
    if case == 'readback_fail': sys.exit(1)
    assert (base / 'registered').is_file()
    assert sys.argv[3:] == ['daube-ti-messenger', '--json']
    command = 'wrong-python' if case == 'wrong_command' else 'python3'
    args = ['-I', (base / 'registered').read_text()]
    if case == 'wrong_args': args.append('--unexpected')
    print(json.dumps({'name': 'daube-ti-messenger', 'enabled': True,
                      'transport': {'type': 'stdio', 'command': command, 'args': args}}))
else: raise AssertionError('Unexpected Codex action')
''')

    def script(self, name, body):
        path = self.bin / name
        path.write_text(f'#!{sys.executable} -I\n' + body)
        path.chmod(0o700)

    def run_install(self, case=''):
        result = subprocess.run(
            ['/bin/sh', str(HERE / 'install.sh')],
            env=dict(self.env, CASE=case), cwd=self.base,
            capture_output=True, text=True, timeout=30,
        )
        self.assertNotIn('UNPINNED_CODE_EXECUTED', result.stderr)
        self.assertEqual(list(self.home.glob('.local/share/.daube-ti-messenger.*/mcp-*.json')), [])
        return result

    def assert_clean(self):
        self.assertFalse(os.path.lexists(self.root))
        self.assertEqual(list((self.home / '.local/share').glob('.daube-ti-messenger.*')), [])
        calls = self.base / 'calls'
        self.assertNotIn('mcp add', calls.read_text() if calls.exists() else '')

    def test_pins_match_repository_bytes(self):
        installer = (HERE / 'install.sh').read_text()
        for name in ('ti_messenger_mcp.py', 'tests/test_ti_messenger.py'):
            data = (HERE / name).read_bytes()
            digest = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
            self.assertRegex(installer, re.escape(repr(name)) + r': ' + re.escape(repr(digest)))

    def test_success_only_verified_payload(self):
        result = self.run_install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('CODEX_MCP_REGISTERED', result.stdout)
        self.assertTrue(self.root.is_symlink())
        payload = self.root / 'integrations/ti-messenger'
        self.assertEqual([x.name for x in payload.iterdir()], ['ti_messenger_mcp.py'])
        self.assertEqual((payload / 'ti_messenger_mcp.py').read_bytes(), (HERE / 'ti_messenger_mcp.py').read_bytes())
        self.assertEqual(Path(os.readlink(self.root)).parent.stat().st_mode & 0o777, 0o700)

    def test_no_codex_retains_validated_source_with_hold(self):
        (self.bin / 'codex').unlink()
        for command in ('mkdir', 'mktemp', 'rm', 'cp'):
            (self.bin / command).symlink_to(shutil.which(command))
        self.env['PATH'] = str(self.bin)
        result = self.run_install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('HOLD_NO_CODEX_CLI', result.stdout)
        self.assertTrue(self.root.is_symlink())
        self.assertFalse((self.base / 'calls').exists())

    def test_source_and_test_pin_drift_fail_closed(self):
        for name in ('ti_messenger_mcp.py', 'tests/test_ti_messenger.py'):
            with self.subTest(name=name):
                path = self.fixture / 'integrations/ti-messenger' / name
                original = path.read_bytes()
                path.write_bytes(original + b'\n# drift\n')
                result = self.run_install()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('HOLD_PINNED_CODE_CHANGED', result.stderr)
                self.assert_clean()
                path.write_bytes(original)

    def test_existing_directory_and_dangling_symlink_untouched(self):
        self.root.mkdir(parents=True)
        sentinel = self.root / 'sentinel'
        sentinel.write_text('untouched')
        self.assertNotEqual(self.run_install().returncode, 0)
        self.assertEqual(sentinel.read_text(), 'untouched')
        sentinel.unlink()
        self.root.rmdir()
        self.root.symlink_to(self.base / 'missing')
        self.assertNotEqual(self.run_install().returncode, 0)
        self.assertTrue(self.root.is_symlink())
        self.assertFalse((self.base / 'git-called').exists())

    def test_existing_or_unreadable_config_never_adds(self):
        for case in ('existing_config', 'config_fail', 'config_invalid'):
            with self.subTest(case=case):
                self.assertNotEqual(self.run_install(case).returncode, 0)
                self.assert_clean()
                self.assertFalse((self.base / 'git-called').exists())

    def test_clone_validation_and_interruption_roll_back(self):
        for case in ('clone_fail', 'validation_fail', 'interrupt_clone'):
            with self.subTest(case=case):
                self.assertNotEqual(self.run_install(case).returncode, 0)
                self.assert_clean()

    def test_raced_user_root_is_not_removed(self):
        result = self.run_install('race')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.root / 'sentinel').read_text(), 'untouched')
        self.assertFalse(self.root.is_symlink())
        self.assertEqual(list(self.root.parent.glob('.daube-ti-messenger.*')), [])
        self.assertNotIn('mcp add', (self.base / 'calls').read_text())

    def test_late_existing_config_rolls_back_without_add(self):
        result = self.run_install('late_config')
        self.assertNotEqual(result.returncode, 0)
        self.assert_clean()

    def test_wrong_readback_retains_payload_and_holds(self):
        # Independent homes because a retained install must block the next run.
        for case in ('wrong_command', 'wrong_args'):
            with self.subTest(case=case):
                result = self.run_install(case)
                self.assertEqual(result.returncode, 5, result.stderr)
                self.assertIn('HOLD_CODEX_REGISTRATION_READBACK_MISMATCH', result.stderr)
                self.assertTrue(Path((self.base / 'registered').read_text()).is_file())
                self.assertNotIn('CODEX_MCP_REGISTERED', result.stdout)
                target = Path(os.readlink(self.root)).parent
                self.root.unlink()
                shutil.rmtree(target)

    def test_add_failure_retains_payload_without_claiming_registration(self):
        result = self.run_install('add_fail')
        self.assertEqual(result.returncode, 5, result.stderr)
        self.assertIn('HOLD_CODEX_REGISTRATION_UNCERTAIN', result.stderr)
        self.assertTrue((self.root / 'integrations/ti-messenger/ti_messenger_mcp.py').is_file())
        self.assertNotIn('CODEX_MCP_REGISTERED', result.stdout)
        self.assertNotIn('mcp remove', (self.base / 'calls').read_text())

    def test_partial_add_failure_retains_registered_path(self):
        result = self.run_install('add_partial')
        self.assertEqual(result.returncode, 5, result.stderr)
        self.assertTrue(Path((self.base / 'registered').read_text()).is_file())
        self.assertNotIn('CODEX_MCP_REGISTERED', result.stdout)

    def test_readback_failure_retains_registered_path(self):
        result = self.run_install('readback_fail')
        self.assertEqual(result.returncode, 5, result.stderr)
        self.assertIn('HOLD_CODEX_REGISTRATION_READBACK_MISSING', result.stderr)
        self.assertTrue(Path((self.base / 'registered').read_text()).is_file())
        self.assertNotIn('CODEX_MCP_REGISTERED', result.stdout)

    def test_signal_after_promotion_before_keep_retains_payload(self):
        result = self.run_install('interrupt_promotion')
        self.assertEqual(result.returncode, 143, result.stderr)
        self.assertIn('HOLD_PUBLISHED_SOURCE_RETAINED', result.stderr)
        self.assertTrue((self.root / 'integrations/ti-messenger/ti_messenger_mcp.py').is_file())
        self.assertNotIn('mcp add', (self.base / 'calls').read_text())

    def test_interrupted_registration_retains_registered_path(self):
        result = self.run_install('interrupt_add')
        self.assertEqual(result.returncode, 143, result.stderr)
        self.assertTrue(Path((self.base / 'registered').read_text()).is_file())
        self.assertNotIn('CODEX_MCP_REGISTERED', result.stdout)


if __name__ == '__main__':
    unittest.main()
