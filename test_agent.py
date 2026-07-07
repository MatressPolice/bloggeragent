from unittest.mock import patch, MagicMock
from agent import (
    BlogPostValidationChecker,
    OutlineValidationChecker,
    blog_planner,
    robust_blog_planner,
    blog_writer,
    robust_blog_writer,
    root_agent
)

def test_blog_post_validation_checker():
    checker = BlogPostValidationChecker()
    assert checker.name == "BlogPostValidationChecker"
    assert "Validates the final written post" in checker.description
    assert checker.output_key == "validation_result"
    
    with patch("google.adk.agents.Agent.__call__") as mock_call:
        mock_call.return_value = {"validation_result": "ok"}
        result = checker({"blog_post": "Here is a blog post."})
        assert result["validation_result"] == "ok"
        mock_call.assert_called_once_with({"blog_post": "Here is a blog post."})

def test_outline_validation_checker():
    checker = OutlineValidationChecker()
    assert checker.name == "OutlineValidationChecker"
    assert "Validates that the outline meets structural requirements" in checker.description
    assert checker.output_key == "validation_result"
    
    with patch("google.adk.agents.Agent.__call__") as mock_call:
        mock_call.return_value = {"validation_result": "ok"}
        result = checker({"blog_outline": "Here is an outline."})
        assert result["validation_result"] == "ok"
        mock_call.assert_called_once_with({"blog_outline": "Here is an outline."})

def test_blog_planner_config():
    assert blog_planner.name == "BlogPlanner"
    assert blog_planner.output_key == "blog_outline"
    assert "outline" in blog_planner.description

def test_robust_blog_planner_config():
    assert robust_blog_planner.name == "RobustBlogPlanner"
    assert len(robust_blog_planner.sub_agents) == 2
    assert robust_blog_planner.max_iterations == 3

def test_blog_writer_config():
    assert blog_writer.name == "BlogWriter"
    assert blog_writer.output_key == "blog_post"

def test_robust_blog_writer_config():
    assert robust_blog_writer.name == "RobustBlogWriter"
    assert len(robust_blog_writer.sub_agents) == 2
    assert robust_blog_writer.max_iterations == 3

def test_root_agent_config():
    assert root_agent.name == "Blogger"
    assert len(root_agent.tools) == 2
    assert "Multi-agent" in root_agent.description
