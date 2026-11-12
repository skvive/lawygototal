"""Regression tests for CMS production session cookie security.

Executes only the small pure configuration helper: never connects to the database,
logs in, or reads production user data.
"""
import ast
import os
import unittest
from pathlib import Path
from unittest.mock import patch


def load_secure_helper():
    root = Path(__file__).resolve().parents[1]
    original = (root / "app.py").read_text(encoding="utf-8")
    tree = ast.parse(original)
    fn = next(
        (n for n in tree.body if isinstance(n, ast.FunctionDef)
         and n.name == "secure_session_cookies"),
        None,
    )
    if fn is None:
        raise RuntimeError("Required cookie security helper is absent")
    namespace = {"os": os}
    exec(compile(ast.Module(body=[fn], type_ignores=[]),
                 str(root / "app.py"), "exec"), namespace)
    return namespace["secure_session_cookies"]


class CookieSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.check = staticmethod(load_secure_helper())

    def check_env(self, env, expected):
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(self.check(), expected)

    def test_https_public_url(self):
        self.check_env({"LAWYGO_PUBLIC_URL": "https://lawygo.lexid.site"}, True)

    def test_vercel_production_without_explicit_secure_variable(self):
        self.check_env({"VERCEL_ENV": "production"}, True)

    def test_explicit_false_cannot_downgrade_https(self):
        self.check_env({"LAWYGO_PUBLIC_URL": "https://lawygo.lexid.site",
                        "LAWYGO_SECURE_COOKIES": "false"}, True)

    def test_explicit_true_enforces_secure(self):
        self.check_env({"LAWYGO_SECURE_COOKIES": "true"}, True)

    def test_local_http_without_public_url(self):
        self.check_env({}, False)


if __name__ == "__main__":
    unittest.main()
