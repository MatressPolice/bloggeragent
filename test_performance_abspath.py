import ast
import sys

def check_file():
    with open("main.py", "r") as f:
        tree = ast.parse(f.read(), filename="main.py")

    class AbspathVisitor(ast.NodeVisitor):
        def __init__(self):
            self.found_in_middleware = False
            self.in_verify_api_key = False

        def visit_AsyncFunctionDef(self, node):
            if node.name == "verify_api_key":
                self.in_verify_api_key = True
                self.generic_visit(node)
                self.in_verify_api_key = False
            else:
                self.generic_visit(node)

        def visit_Call(self, node):
            if self.in_verify_api_key:
                # check for os.path.abspath(FRONTEND_DIR)
                if isinstance(node.func, ast.Attribute) and node.func.attr == 'abspath':
                    if isinstance(node.func.value, ast.Attribute) and node.func.value.attr == 'path':
                        if isinstance(node.func.value.value, ast.Name) and node.func.value.value.id == 'os':
                            if len(node.args) == 1 and isinstance(node.args[0], ast.Name) and node.args[0].id == 'FRONTEND_DIR':
                                self.found_in_middleware = True
            self.generic_visit(node)

    visitor = AbspathVisitor()
    visitor.visit(tree)

    if visitor.found_in_middleware:
        print("ERROR: os.path.abspath(FRONTEND_DIR) found in verify_api_key middleware.")
        sys.exit(1)
    else:
        print("SUCCESS: os.path.abspath(FRONTEND_DIR) not found in verify_api_key middleware.")
        sys.exit(0)

if __name__ == "__main__":
    check_file()
