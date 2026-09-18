import ast

def test_no_os_import_in_test_agent():
    with open("test_agent.py", "r") as f:
        content = f.read()
    assert "import os" not in content, "test_agent.py should not contain 'import os'"

def test_no_nested_patch_in_test_main():
    filepath = "test_main.py"
    with open(filepath, "r") as f:
        tree = ast.parse(f.read(), filename=filepath)

    class NestedWithVisitor(ast.NodeVisitor):
        def __init__(self):
            self.has_nested_patch = False
            self.violations = []

        def visit_With(self, node):
            for stmt in node.body:
                if isinstance(stmt, ast.With):
                    self.has_nested_patch = True
                    self.violations.append(stmt.lineno)
            self.generic_visit(node)

    visitor = NestedWithVisitor()
    visitor.visit(tree)
    assert not visitor.has_nested_patch, f"Found deeply nested with contexts in test_main.py at lines: {visitor.violations}"

def test_no_redundant_abspath_in_middleware():
    filepath = "main.py"
    with open(filepath, "r") as f:
        tree = ast.parse(f.read(), filename=filepath)

    class RedundantAbspathVisitor(ast.NodeVisitor):
        def __init__(self):
            self.violations = []
            self.in_middleware = False

        def visit_AsyncFunctionDef(self, node):
            if node.name in ("verify_api_key", "add_security_headers"):
                self.in_middleware = True
                self.generic_visit(node)
                self.in_middleware = False
            else:
                self.generic_visit(node)

        def visit_Call(self, node):
            if self.in_middleware:
                if (isinstance(node.func, ast.Attribute) and
                    node.func.attr == 'abspath' and
                    isinstance(node.func.value, ast.Attribute) and
                    node.func.value.attr == 'path' and
                    isinstance(node.func.value.value, ast.Name) and
                    node.func.value.value.id == 'os'):
                    if len(node.args) > 0 and isinstance(node.args[0], ast.Name) and node.args[0].id == 'FRONTEND_DIR':
                        self.violations.append(node.lineno)
            self.generic_visit(node)

    visitor = RedundantAbspathVisitor()
    visitor.visit(tree)
    assert not visitor.violations, f"Found redundant os.path.abspath(FRONTEND_DIR) calls in middleware at lines: {visitor.violations}"
