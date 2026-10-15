import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError

import agent


class AgentTests(unittest.TestCase):
    def test_loopback_only(self):
        for url in ["https://api.openai.com/v1", "http://example.com/v1",
                    "http://127.0.0.1.evil.test/v1", "http://key@localhost/v1"]:
            with self.subTest(url=url), self.assertRaises(agent.AgentError):
                agent.Client(url)

    def test_only_allowlisted_action(self):
        self.assertEqual(agent.parse_action('{"tool":"bash","command":"pwd"}')["command"], "pwd")
        self.assertEqual(agent.parse_action('{"answer":"done"}'), {"answer": "done"})
        self.assertEqual(agent.parse_action('```json\n{"answer":"done"}\n```'), {"answer": "done"})
        for action in ['not JSON', '{"tool":"python","command":"pass"}',
                       '{"tool":"bash","command":""}', '{"answer":""}',
                       '{"tool":"bash","command":"pwd","extra":true}']:
            with self.subTest(action=action), self.assertRaises(agent.AgentError):
                agent.parse_action(action)

    def test_loop_returns_tool_results_to_model(self):
        client, shell = Mock(), Mock()
        client.chat.side_effect = ['{"tool":"bash","command":"pwd"}', '{"answer":"done"}']
        shell.run.return_value = "/demo\n[exit code 0]"
        messages = [{"role": "user", "content": "Where am I?"}]
        with patch("sys.stdout", new_callable=io.StringIO):
            self.assertEqual(agent.run_agent(client, "local", messages, shell,
                                            approve=lambda _: True), "done")
        shell.run.assert_called_once_with("pwd")
        self.assertIn("/demo", messages[2]["content"])

    def test_declined_command_never_runs(self):
        client, shell = Mock(), Mock()
        client.chat.side_effect = ['{"tool":"bash","command":"pwd"}', '{"answer":"Declined."}']
        with patch("sys.stdout", new_callable=io.StringIO):
            agent.run_agent(client, "local", [], shell, approve=lambda _: False)
        shell.run.assert_not_called()

    def test_protocol_errors_are_repaired_within_turn_limit(self):
        client, shell = Mock(), Mock()
        client.chat.side_effect = ["invalid", '{"answer":"done"}']
        messages = []
        self.assertEqual(agent.run_agent(client, "local", messages, shell), "done")
        self.assertIn("Protocol error", messages[1]["content"])
        shell.run.assert_not_called()
        client.chat.side_effect = None
        client.chat.return_value = "invalid"
        with self.assertRaisesRegex(agent.AgentError, "Stopped after 2"):
            agent.run_agent(client, "local", [], shell, max_turns=2)

    def test_bash_preserves_state_and_reports_exit_status(self):
        with tempfile.TemporaryDirectory() as tmp, agent.Bash(tmp) as shell:
            shell.run("mkdir child; cd child; DEMO_STATE=hello")
            self.assertIn("hello", shell.run('printf "%s" "$DEMO_STATE"'))
            self.assertIn(str(Path(tmp).resolve() / "child"), shell.run("pwd"))
            self.assertEqual(shell.run("false"), "[exit code 1]")
            self.assertIn("alive", shell.run("echo alive"))

    def test_shell_does_not_inherit_api_credentials(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict("os.environ", {"MIMOE_API_KEY": "test-secret"}):
                with agent.Bash(tmp) as shell:
                    self.assertEqual(shell.run('printf "%s" "${MIMOE_API_KEY-unset}"'),
                                     "unset\n[exit code 0]")

    def test_shell_timeout_and_output_limit_stop_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            with agent.Bash(tmp, timeout=0.1) as shell:
                with self.assertRaisesRegex(agent.ShellError, "timed out"):
                    shell.run("sleep 5")
                self.assertIsNotNone(shell.process.returncode)
            with agent.Bash(tmp, output_limit=100) as shell:
                with self.assertRaisesRegex(agent.ShellError, "output limit"):
                    shell.run("while true; do echo output; done")
                self.assertIsNotNone(shell.process.returncode)

    def test_request_contract(self):
        client = agent.Client(api_key="test-key")
        response = Mock()
        response.__enter__ = Mock(return_value=io.StringIO(json.dumps({
            "choices": [{"message": {"content": "hello"}}]})))
        response.__exit__ = Mock(return_value=False)
        client.opener = Mock()
        client.opener.open.return_value = response
        self.assertEqual(client.chat("local", [{"role": "user", "content": "hi"}], 40), "hello")
        req = client.opener.open.call_args.args[0]
        self.assertEqual(req.full_url, agent.BASE_URL + "/chat/completions")
        self.assertEqual(req.get_header("Authorization"), "Bearer test-key")
        body = json.loads(req.data)
        self.assertEqual(body["model"], "local")
        self.assertFalse(body["stream"])

    def test_http_error_hides_response_and_key(self):
        client = agent.Client(api_key="test-key")
        client.opener = Mock()
        client.opener.open.side_effect = HTTPError(agent.BASE_URL, 401, "secret", {}, None)
        with self.assertRaisesRegex(agent.AgentError, "API key") as caught:
            client.models()
        self.assertNotIn("test-key", str(caught.exception))

    def test_redirects_are_rejected(self):
        with self.assertRaises(agent.AgentError):
            agent.NoRedirect().redirect_request(None, None, 302, "", {}, "https://example.com")


if __name__ == "__main__":
    unittest.main()
