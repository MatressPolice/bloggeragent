import pytest
import asyncio
from unittest.mock import patch
from google.adk.events.event import Event
from google.adk.events.event_actions import EventActions
from google.adk.tools.tool_context import ToolContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.sessions.session import Session
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.agents.run_config import RunConfig
from agent import (
    BlogPostValidationChecker,
    OutlineValidationChecker,
    blog_planner,
    robust_blog_planner,
    blog_writer,
    robust_blog_writer,
    root_agent
)

@pytest.fixture
def mock_agent_call():
    with patch("google.adk.agents.Agent.__call__") as mock_call:
        yield mock_call

def test_blog_post_validation_checker(mock_agent_call):
    checker = BlogPostValidationChecker()
    assert checker.name == "BlogPostValidationChecker"
    assert "Validates the final written post" in checker.description
    assert checker.output_key == "validation_result"
    
    mock_agent_call.return_value = {"validation_result": "ok"}
    result = checker({"blog_post": "Here is a blog post."})
    assert result["validation_result"] == "ok"
    mock_agent_call.assert_called_once_with({"blog_post": "Here is a blog post."})

def test_outline_validation_checker(mock_agent_call):
    checker = OutlineValidationChecker()
    assert checker.name == "OutlineValidationChecker"
    assert "Validates that the outline meets structural requirements" in checker.description
    assert checker.output_key == "validation_result"
    
    mock_agent_call.return_value = {"validation_result": "ok"}
    result = checker({"blog_outline": "Here is an outline."})
    assert result["validation_result"] == "ok"
    mock_agent_call.assert_called_once_with({"blog_outline": "Here is an outline."})

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

def test_root_agent_integration(mock_agent_call):
    mock_output = {"output": "Final Result with hooks and titles"}
    mock_agent_call.return_value = mock_output

    request_input = {"request": "Write a post about AI."}
    result = root_agent(request_input)

    assert result == mock_output
    mock_agent_call.assert_called_once_with(request_input)

    assert len(root_agent.tools) == 2
    assert root_agent.tools[0].name == "RobustBlogPlanner"
    assert root_agent.tools[1].name == "RobustBlogWriter"

def test_robust_blog_planner_integration_retry_loop():
    async def _test():
        with patch("google.adk.agents.llm_agent.LlmAgent.run_async") as mock_agent_run:
            async def mock_run_1(*args, **kwargs):
                yield Event(output={"blog_outline": "Attempt 1"})

            async def mock_run_2(*args, **kwargs):
                yield Event(output={"validation_result": "retry"})

            async def mock_run_3(*args, **kwargs):
                yield Event(output={"blog_outline": "Attempt 2"})

            async def mock_run_4(*args, **kwargs):
                yield Event(output={"validation_result": "ok"}, actions=EventActions(escalate=True))

            mock_agent_run.side_effect = [
                mock_run_1(),
                mock_run_2(),
                mock_run_3(),
                mock_run_4()
            ]

            session = Session(id="test_session", appName="test_app", userId="test_user")
            session_service = InMemorySessionService()
            rc = RunConfig()
            inv_ctx = InvocationContext(
                agent=root_agent.tools[0].agent,
                session=session,
                session_service=session_service,
                invocation_id="123",
                run_config=rc
            )

            tool_ctx = ToolContext(invocation_context=inv_ctx)

            events = []
            async for e in root_agent.tools[0].agent._run_async_impl(tool_ctx.get_invocation_context()):
                events.append(e)

            assert len(events) == 4
            assert mock_agent_run.call_count == 4

    asyncio.run(_test())
