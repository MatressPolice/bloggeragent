import pytest
import asyncio
from unittest.mock import patch
from google.adk.events.event import Event
from google.adk.events.event_actions import EventActions
from google.adk.sessions.in_memory_session_service import InMemorySessionService
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

async def _run_loop_agent_integration_test(agent, request_input, output_key, draft1, draft2):
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.adk.agents.base_agent import Event
    from google.adk.events.event_actions import EventActions
    from google.genai.types import Content, Part

    with patch.object(agent.sub_agents[0], "_run_async_impl") as mock_sub_agent, \
         patch.object(agent.sub_agents[1], "_run_async_impl") as mock_validator:

        async def mock_sub_agent_1(*args, **kwargs):
            yield Event(content=Content(parts=[Part.from_text(text=draft1)]), actions=EventActions(state_delta={output_key: draft1}))

        async def mock_sub_agent_2(*args, **kwargs):
            yield Event(content=Content(parts=[Part.from_text(text=draft2)]), actions=EventActions(state_delta={output_key: draft2}))

        async def mock_validator_1(*args, **kwargs):
            yield Event(content=Content(parts=[Part.from_text(text="retry")]), actions=EventActions(state_delta={"validation_result": "retry"}))

        async def mock_validator_2(*args, **kwargs):
            yield Event(content=Content(parts=[Part.from_text(text="ok")]), actions=EventActions(state_delta={"validation_result": "ok"}, escalate=True))

        mock_sub_agent.side_effect = [mock_sub_agent_1(), mock_sub_agent_2()]
        mock_validator.side_effect = [mock_validator_1(), mock_validator_2()]

        session_service = InMemorySessionService()
        session = await session_service.create_session(app_name="test_app", user_id="user1")
        runner = Runner(app_name="test_app", agent=agent, session_service=session_service)

        try:
            async for _ in runner.run_async(
                user_id="user1",
                session_id=session.id,
                state_delta=request_input,
                new_message=Content(parts=[Part.from_text(text="Start")])
            ):
                pass
        except RuntimeError:
            pass

        assert mock_sub_agent.call_count == 2
        assert mock_validator.call_count == 2
        final_state = await session_service.get_session(app_name="test_app", user_id="user1", session_id=session.id)
        assert final_state.state.get("validation_result") == "ok"
        assert final_state.state.get(output_key) == draft2

def test_robust_blog_writer_integration():
    asyncio.run(_run_loop_agent_integration_test(
        agent=robust_blog_writer,
        request_input={"blog_outline": "My outline"},
        output_key="blog_post",
        draft1="First draft",
        draft2="Second draft"
    ))

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

def test_robust_blog_planner_integration():
    asyncio.run(_run_loop_agent_integration_test(
        agent=robust_blog_planner,
        request_input={"topic": "My topic"},
        output_key="blog_outline",
        draft1="First outline",
        draft2="Second outline"
    ))
