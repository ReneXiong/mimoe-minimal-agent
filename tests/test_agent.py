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
        self.assertEqual(agent.plan_query('{"tool":"search_runbooks","query":"lag"}'), "lag")
        for action in ['not JSON', '{"tool":"shell","query":"rm -rf /"}',
                       '{"tool":"search_runbooks","query":""}',
                       '{"tool":"search_runbooks","query":"lag","path":"/etc/passwd"}']:
            with self.subTest(action=action), self.assertRaises(agent.AgentError):
                agent.plan_query(action)

    def test_search_ranks_and_ignores_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "queue.md").write_text("queue backlog consumer lag")
            (root / "other.md").write_text("database connection")
            (root / "link.md").symlink_to(root / "queue.md")
            self.assertEqual(agent.search_runbooks("consumer lag", root), [
                {"source": "queue.md", "text": "queue backlog consumer lag"}])
            self.assertEqual(agent.search_runbooks("volcano", root), [])
            self.assertEqual(agent.search_runbooks("What should I do?", root), [])

    def test_agent_uses_model_query_and_feeds_tool_result_back(self):
        client = Mock()
        client.chat.side_effect = [
            '{"tool":"search_runbooks","query":"consumer lag"}',
            'Check processing rate [queue-backlog.md].',
        ]
        answer = agent.run_agent(client, "local", "Messages are piling up")
        self.assertIn("queue-backlog.md", answer)
        self.assertEqual(client.chat.call_count, 2)
        second_messages = client.chat.call_args_list[1].args[1]
        self.assertIn("Preserve failed messages", second_messages[1]["content"])

    def test_invalid_action_fallback_is_visible(self):
        client = Mock()
        client.chat.side_effect = ['I cannot use JSON', 'Check consumer logs.']
        with patch("sys.stderr", new_callable=io.StringIO) as output:
            answer = agent.run_agent(client, "local", "consumer lag", trace=True)
        self.assertIn("invalid model action", output.getvalue())
        self.assertIn("queue-backlog.md", answer)

    def test_no_evidence_stops_without_invented_answer(self):
        client = Mock()
        client.chat.return_value = '{"tool":"search_runbooks","query":"volcano"}'
        self.assertIn("could not find", agent.run_agent(client, "local", "volcano"))
        self.assertEqual(client.chat.call_count, 1)

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
