import os
import datetime
from dotenv import load_dotenv
from google.adk.agents import Agent, LoopAgent
from google.adk.tools import agent_tool

# Load environment variables
load_dotenv()
MODEL = os.getenv("MODEL", "gemini-flash-latest")

# ---------------------------------------------------------
# Sub-Agent 1: The Planner & Validator
# ---------------------------------------------------------
blog_planner = Agent(
    name="BlogPlanner",
    model=MODEL,
    description="Creates a practical, skimmable outline in Markdown.",
    instruction="""
You are a technical content strategist. Produce a clear Markdown outline with:
- Title
- Short intro
- 4-6 main sections (each with 2-3 bullets)
- Conclusion
Return only the outline in Markdown.
""",
    output_key="blog_outline",
)

class OutlineValidationChecker(Agent):
    def __init__(self):
        super().__init__(
            name="OutlineValidationChecker",
            model=MODEL,
            description="Validates that the outline meets structural requirements.",
            instruction="""
Check the outline in state `blog_outline`. If it has a title, intro, 4-6 sections, and a conclusion, respond exactly "ok".
Otherwise respond exactly "retry" and list the missing pieces.
""",
            output_key="validation_result",
        )

# LoopAgent automatically retries the planner if the validator fails
robust_blog_planner = LoopAgent(
    name="RobustBlogPlanner",
    description="Retries planning if validation fails.",
    sub_agents=[blog_planner, OutlineValidationChecker()],
    max_iterations=3,
)

# ---------------------------------------------------------
# Sub-Agent 2: The Writer & Validator
# ---------------------------------------------------------
blog_writer = Agent(
    name="BlogWriter",
    model=MODEL,
    description="Writes a technical blog post from the provided outline.",
    instruction="""
Write a complete Markdown article using the outline in `blog_outline`.
Guidelines:
- Audience: Industry professionals; focus on practical, technical insight.
- Explain both the 'how' and 'why'.
- Output only the final article in Markdown.
""",
    output_key="blog_post",
)

class BlogPostValidationChecker(Agent):
    def __init__(self):
        super().__init__(
            name="BlogPostValidationChecker",
            model=MODEL,
            description="Validates the final written post.",
            instruction="""
Check `blog_post` for: intro, clear sections matching the outline, conclusion, and technical clarity.
If it passes, respond "ok". Else respond "retry" with specific necessary fixes.
""",
            output_key="validation_result",
        )

robust_blog_writer = LoopAgent(
    name="RobustBlogWriter",
    description="Retries writing if validation fails.",
    sub_agents=[blog_writer, BlogPostValidationChecker()],
    max_iterations=3,
)

# ---------------------------------------------------------
# Root Agent: Orchestrator
# ---------------------------------------------------------
planner_tool = agent_tool.AgentTool(agent=robust_blog_planner)
writer_tool  = agent_tool.AgentTool(agent=robust_blog_writer)

root_agent = Agent(
    name="Blogger",
    model=MODEL,
    description="Multi-agent blogger orchestrator.",
    instruction=f"""
When the user provides a topic:
1) Call the planner tool to generate the outline.
2) Call the writer tool to produce the full draft based on the outline.
3) End the output with 3 alternate titles and 2 tweet-length hooks.
Date: {datetime.datetime.now().strftime("%Y-%m-%d")}
""",
    tools=[planner_tool, writer_tool],
)