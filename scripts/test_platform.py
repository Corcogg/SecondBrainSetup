#!/usr/bin/env python3
"""
test_platform.py — unit tests for the pure-parsing helpers in
brain_platform.py and install_hooks.py.

These exercise only logic that does not require a real Windows machine:
feed fixture strings to the icacls/schtasks/process-CSV parsers, and feed
fixture hook-entry dicts to install_hooks.hook_entry_belongs. Nothing here
shells out to a real OS tool.
"""

import ntpath
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

from brain_platform import _parse_icacls, _parse_schtasks_csv, _parse_process_csv
from install_hooks import hook_entry_belongs


class TestParseIcacls(unittest.TestCase):
    """Fixtures below have already had the leading file-path prefix
    stripped by secrets_file_locked, matching what _parse_icacls receives.
    """

    def test_locked_single_user_ace(self):
        output = "J-PC\\j:(F)\n\nSuccessfully processed 1 files; Failed processing 0 files.\n"
        ok, detail = _parse_icacls(output, "J-PC\\j")
        self.assertTrue(ok, detail)
        self.assertIn("J-PC\\j", detail)

    def test_locked_matches_bare_username(self):
        # user passed as DOMAIN\name, but the ACE lists only the bare name.
        output = "j:(F)\n\nSuccessfully processed 1 files; Failed processing 0 files.\n"
        ok, detail = _parse_icacls(output, "J-PC\\j")
        self.assertTrue(ok, detail)

    def test_locked_with_system_and_administrators(self):
        # Real windows-latest output after `icacls /inheritance:r /grant:r`:
        # SYSTEM and Administrators remain as explicit ACEs. Allowed (OpenSSH rule).
        output = (
            "runneradmin\\runneradmin:(R,W)\n"
            "NT AUTHORITY\\SYSTEM:(F)\n"
            "BUILTIN\\Administrators:(F)\n\n"
            "Successfully processed 1 files; Failed processing 0 files.\n"
        )
        ok, detail = _parse_icacls(output, "runneradmin\\runneradmin")
        self.assertTrue(ok, detail)

    def test_unlocked_everyone_present(self):
        output = "J-PC\\j:(F)\nEveryone:(R)\n\nSuccessfully processed 1 files; Failed processing 0 files.\n"
        ok, detail = _parse_icacls(output, "J-PC\\j")
        self.assertFalse(ok)
        self.assertIn("Everyone", detail)

    def test_unlocked_builtin_users_present(self):
        output = (
            "J-PC\\j:(F)\n"
            "BUILTIN\\Users:(R)\n\n"
            "Successfully processed 1 files; Failed processing 0 files.\n"
        )
        ok, detail = _parse_icacls(output, "J-PC\\j")
        self.assertFalse(ok)
        self.assertIn("BUILTIN\\Users", detail)

    def test_unlocked_inherited_flag(self):
        output = "J-PC\\j:(I)(F)\n\nSuccessfully processed 1 files; Failed processing 0 files.\n"
        ok, detail = _parse_icacls(output, "J-PC\\j")
        self.assertFalse(ok)
        self.assertIn("inherited", detail.lower())

    def test_unparseable_output(self):
        ok, detail = _parse_icacls("", "J-PC\\j")
        self.assertFalse(ok)


class TestParseSchtasksCsv(unittest.TestCase):
    def test_running(self):
        output = (
            '"HostName","TaskName","Next Run Time","Status"\r\n'
            '"J-PC","\\com.secondbrain.watcher","N/A","Running"\r\n'
        )
        ok, detail = _parse_schtasks_csv(output)
        self.assertTrue(ok)
        self.assertEqual(detail, "Running")

    def test_ready_is_ok(self):
        output = (
            '"HostName","TaskName","Next Run Time","Status"\r\n'
            '"J-PC","\\com.secondbrain.watcher","4/15/2026 9:00:00 AM","Ready"\r\n'
        )
        ok, detail = _parse_schtasks_csv(output)
        self.assertTrue(ok)
        self.assertEqual(detail, "Ready")

    def test_disabled(self):
        output = (
            '"HostName","TaskName","Next Run Time","Status"\r\n'
            '"J-PC","\\com.secondbrain.watcher","Disabled","Disabled"\r\n'
        )
        ok, detail = _parse_schtasks_csv(output)
        self.assertFalse(ok)
        self.assertEqual(detail, "Disabled")

    def test_task_not_found(self):
        # schtasks writes an error to stderr and produces no CSV on stdout
        # when the task doesn't exist; service_loaded short-circuits on a
        # non-zero return code, but _parse_schtasks_csv itself must also
        # degrade gracefully on empty/garbage input.
        ok, detail = _parse_schtasks_csv("")
        self.assertFalse(ok)
        self.assertEqual(detail, "task not found")


class TestParseProcessCsv(unittest.TestCase):
    def test_one_matching_one_not(self):
        output = (
            '"ProcessId","CommandLine"\r\n'
            '"1234","C:\\SecondBrain\\app\\.venv\\Scripts\\pythonw.exe -u C:\\SecondBrain\\app\\scripts\\brain_watcher.py"\r\n'
            '"5678","C:\\Python311\\python.exe -m http.server"\r\n'
        )
        pids = _parse_process_csv(output)
        self.assertEqual(pids, ["1234"])

    def test_no_matches(self):
        output = (
            '"ProcessId","CommandLine"\r\n'
            '"5678","C:\\Python311\\python.exe -m http.server"\r\n'
        )
        self.assertEqual(_parse_process_csv(output), [])

    def test_empty_output(self):
        self.assertEqual(_parse_process_csv(""), [])


class TestHookEntryBelongs(unittest.TestCase):
    def setUp(self):
        self.hooks_dir = Path("/Users/j/SecondBrain/app/hooks")

    def test_shell_form_matches(self):
        entry = {
            "type": "command",
            "command": "'/Users/j/SecondBrain/app/.venv/bin/python' '/Users/j/SecondBrain/app/hooks/session-start-context.py'",
        }
        self.assertTrue(hook_entry_belongs(entry, self.hooks_dir))

    def test_exec_form_matches_via_args(self):
        # Windows paths/os.sep only behave this way on a real Windows host;
        # patch os.sep + os.path.normcase to ntpath's so this exercises the
        # Windows code path deterministically on any host (including macOS
        # CI). Production code never patches anything — on real Windows,
        # os.sep and os.path.normcase already behave like ntpath natively.
        entry = {
            "type": "command",
            "command": "C:\\SecondBrain\\app\\.venv\\Scripts\\python.exe",
            "args": ["C:\\SecondBrain\\app\\hooks\\session-start-context.py"],
        }
        hooks_dir = Path("C:\\SecondBrain\\app\\hooks")
        with patch("os.sep", ntpath.sep), patch("os.path.normcase", ntpath.normcase):
            self.assertTrue(hook_entry_belongs(entry, hooks_dir))

    def test_exec_form_case_insensitive(self):
        entry = {
            "type": "command",
            "command": "C:\\SecondBrain\\app\\.venv\\Scripts\\python.exe",
            "args": ["c:\\secondbrain\\app\\hooks\\session-start-context.py"],
        }
        hooks_dir = Path("C:\\SecondBrain\\app\\hooks")
        with patch("os.sep", ntpath.sep), patch("os.path.normcase", ntpath.normcase):
            self.assertTrue(hook_entry_belongs(entry, hooks_dir))

    def test_unrelated_entry_does_not_match(self):
        entry = {"type": "command", "command": "echo hello"}
        self.assertFalse(hook_entry_belongs(entry, self.hooks_dir))

    def test_similar_prefix_dir_does_not_match(self):
        # A hooks-extra/ dir must not be treated as belonging to hooks/.
        entry = {
            "type": "command",
            "command": "'/usr/bin/python3' '/Users/j/SecondBrain/app/hooks-extra/other.py'",
        }
        self.assertFalse(hook_entry_belongs(entry, self.hooks_dir))


if __name__ == "__main__":
    unittest.main()
