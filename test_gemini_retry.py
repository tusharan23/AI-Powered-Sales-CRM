"""Run with: python -m unittest test_gemini_retry"""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from gemini_retry import generate_with_retry, PRIMARY_MODEL, FALLBACK_MODEL


class APIError(Exception):
    def __init__(self, code):
        self.code = code


class RetryTests(unittest.TestCase):
    def run_case(self, results):
        generate = Mock(side_effect=results)
        client = SimpleNamespace(models=SimpleNamespace(generate_content=generate))
        sleep = Mock()
        return client, generate, sleep

    def test_success(self):
        client, generate, sleep = self.run_case(["ok"])
        self.assertEqual(generate_with_retry(client, "notes", sleep=sleep), "ok")
        generate.assert_called_once_with(model=PRIMARY_MODEL, contents="notes")
        sleep.assert_not_called()

    def test_temporary_failure(self):
        client, generate, sleep = self.run_case([APIError(503), "ok"])
        self.assertEqual(generate_with_retry(client, "notes", sleep=sleep), "ok")
        self.assertEqual(generate.call_count, 2)
        sleep.assert_called_once_with(1)

    def test_fallback(self):
        client, generate, sleep = self.run_case([APIError(503)] * 3 + ["ok"])
        self.assertEqual(generate_with_retry(client, "notes", sleep=sleep), "ok")
        self.assertEqual([c.kwargs["model"] for c in generate.call_args_list],
                         [PRIMARY_MODEL] * 3 + [FALLBACK_MODEL])
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [1, 2])

    def test_missing_primary(self):
        client, generate, sleep = self.run_case([APIError(404), "ok"])
        self.assertEqual(generate_with_retry(client, "notes", sleep=sleep), "ok")
        self.assertEqual(generate.call_args.kwargs["model"], FALLBACK_MODEL)
        sleep.assert_not_called()

    def test_both_unavailable(self):
        client, generate, sleep = self.run_case([APIError(503)] * 5)
        with self.assertRaises(APIError):
            generate_with_retry(client, "notes", sleep=sleep)
        self.assertEqual(generate.call_count, 5)

    def test_no_retry_for_auth_or_quota(self):
        for code in (400, 401, 403, 429):
            with self.subTest(code=code):
                client, generate, sleep = self.run_case([APIError(code)])
                with self.assertRaises(APIError):
                    generate_with_retry(client, "notes", sleep=sleep)
                self.assertEqual(generate.call_count, 1)
                sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
