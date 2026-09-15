def test_no_os_import_in_test_agent():
    with open("test_agent.py", "r") as f:
        content = f.read()
    assert "import os" not in content, "test_agent.py should not contain 'import os'"
