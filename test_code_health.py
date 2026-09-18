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
            if len(node.body) == 1 and isinstance(node.body[0], ast.With):
                self.has_nested_patch = True
                self.violations.append(node.lineno)
            self.generic_visit(node)

    visitor = NestedWithVisitor()
    visitor.visit(tree)
    assert not visitor.has_nested_patch, f"Found deeply nested with contexts in test_main.py at lines: {visitor.violations}"
