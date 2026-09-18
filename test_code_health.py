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

def test_robust_blog_writer_integration_exists():
    filepath = "test_agent.py"
    with open(filepath, "r") as f:
        tree = ast.parse(f.read(), filename=filepath)

    class FunctionVisitor(ast.NodeVisitor):
        def __init__(self):
            self.found = False

        def visit_FunctionDef(self, node):
            if node.name == "test_robust_blog_writer_integration":
                self.found = True
            self.generic_visit(node)

    visitor = FunctionVisitor()
    visitor.visit(tree)
    assert visitor.found, "test_robust_blog_writer_integration is missing from test_agent.py"
