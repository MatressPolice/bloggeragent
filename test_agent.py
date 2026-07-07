from unittest.mock import patch, MagicMock
from agent import BlogPostValidationChecker

def test_blog_post_validation_checker():
    # Instantiate the agent
    checker = BlogPostValidationChecker()
    
    # Assert properties are initialized correctly
    assert checker.name == "BlogPostValidationChecker"
    assert "Validates the final written post" in checker.description
    assert checker.output_key == "validation_result"
    
    # Mock the __call__ method of the Agent to test its behavior
    with patch("google.adk.agents.Agent.__call__") as mock_call:
        # Simulate a successful validation response from the LLM
        mock_call.return_value = {"validation_result": "ok"}
        
        # Test calling the agent with a dummy state
        result = checker({"blog_post": "Here is a blog post."})
        
        # Verify the agent was called with the state and returns the expected output
        assert result["validation_result"] == "ok"
        mock_call.assert_called_once_with({"blog_post": "Here is a blog post."})
