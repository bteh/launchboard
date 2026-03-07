"""CrewAI crew orchestration for the Job Finder pipeline."""

from __future__ import annotations

import os

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import ScrapeWebsiteTool, SerperDevTool

from job_finder.tools.job_search_tool import JobSearchTool
from job_finder.tools.resume_parser_tool import ResumeParserTool
from job_finder.tools.company_intel_tool import CompanyIntelTool
from job_finder.models.database import init_db


def get_llm() -> LLM:
    """Configure the Claude LLM for all agents. Fails fast if API key missing."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY environment variable is required. "
            "Copy .env.example to .env and add your key."
        )

    try:
        max_tokens = int(os.getenv("MAX_TOKENS", "8192"))
    except ValueError:
        raise ValueError("MAX_TOKENS environment variable must be an integer")
    try:
        temperature = float(os.getenv("TEMPERATURE", "0.7"))
    except ValueError:
        raise ValueError("TEMPERATURE environment variable must be a float")

    return LLM(
        model=os.getenv("MODEL_NAME", "anthropic/claude-sonnet-4-20250514"),
        api_key=api_key,
        max_tokens=max_tokens,
        temperature=temperature,
    )


@CrewBase
class JobFinderCrew:
    """Job Finder crew that orchestrates the full job search pipeline."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self):
        """Initialize crew with database and tools."""
        init_db()
        self.llm = get_llm()

        # Ensure output directory exists
        output_dir = os.path.join(os.path.dirname(__file__), "output")
        os.makedirs(output_dir, exist_ok=True)

        # Shared tools
        self.job_search_tool = JobSearchTool()
        self.resume_parser_tool = ResumeParserTool()
        self.company_intel_tool = CompanyIntelTool()
        self.web_scraper = ScrapeWebsiteTool()
        self.web_search = SerperDevTool()

    # ── Agents ────────────────────────────────────────────────────────────

    @agent
    def job_searcher(self) -> Agent:
        return Agent(
            config=self.agents_config["job_searcher"],
            llm=self.llm,
            tools=[self.job_search_tool, self.web_scraper],
        )

    @agent
    def jd_scorer(self) -> Agent:
        return Agent(
            config=self.agents_config["jd_scorer"],
            llm=self.llm,
            tools=[self.resume_parser_tool, self.web_scraper],
        )

    @agent
    def resume_optimizer(self) -> Agent:
        return Agent(
            config=self.agents_config["resume_optimizer"],
            llm=self.llm,
            tools=[self.resume_parser_tool],
        )

    @agent
    def cover_letter_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["cover_letter_writer"],
            llm=self.llm,
            tools=[self.web_scraper, self.web_search],
        )

    @agent
    def company_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["company_researcher"],
            llm=self.llm,
            tools=[self.company_intel_tool, self.web_search, self.web_scraper],
        )

    @agent
    def pipeline_coordinator(self) -> Agent:
        return Agent(
            config=self.agents_config["pipeline_coordinator"],
            llm=self.llm,
            tools=[],
        )

    # ── Tasks ─────────────────────────────────────────────────────────────

    @task
    def search_jobs_task(self) -> Task:
        return Task(
            config=self.tasks_config["search_jobs_task"],
        )

    @task
    def score_jobs_task(self) -> Task:
        return Task(
            config=self.tasks_config["score_jobs_task"],
        )

    @task
    def optimize_resumes_task(self) -> Task:
        return Task(
            config=self.tasks_config["optimize_resumes_task"],
        )

    @task
    def write_cover_letters_task(self) -> Task:
        return Task(
            config=self.tasks_config["write_cover_letters_task"],
        )

    @task
    def research_companies_task(self) -> Task:
        return Task(
            config=self.tasks_config["research_companies_task"],
        )

    @task
    def compile_results_task(self) -> Task:
        return Task(
            config=self.tasks_config["compile_results_task"],
            output_file=os.path.join(
                os.path.dirname(__file__), "output", "job_search_report.md"
            ),
        )

    # ── Crew ──────────────────────────────────────────────────────────────

    @crew
    def crew(self) -> Crew:
        """Assemble the full job search crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
