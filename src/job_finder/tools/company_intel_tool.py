"""Company intelligence gathering tool for CrewAI agents."""

from __future__ import annotations

import json
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class CompanyIntelInput(BaseModel):
    """Input schema for company intelligence tool."""

    company_name: str = Field(description="Name of the company to research")
    job_title: str = Field(
        default="",
        description="The specific role being considered (for context)",
    )


class CompanyIntelTool(BaseTool):
    """
    Gathers intelligence about a company from multiple web sources.
    Combines web search results to build a company profile including
    funding, tech stack, team size, growth signals, and compensation data.
    """

    name: str = "company_intelligence"
    description: str = (
        "Researches a company to gather intelligence including funding stage, "
        "tech stack, team size, growth signals, compensation data, and red flags. "
        "Useful for evaluating whether a company meets your criteria for funding stage, "
        "growth trajectory, and leadership opportunity. "
        "Note: This tool builds a research prompt - the LLM will need to use web search "
        "tools separately to gather the actual data."
    )
    args_schema: Type[BaseModel] = CompanyIntelInput

    def _run(self, company_name: str, job_title: str = "") -> str:
        """Generate a structured company research brief."""
        research_prompt = {
            "company": company_name,
            "job_context": job_title,
            "research_areas": {
                "funding_and_financials": {
                    "queries": [
                        f"{company_name} funding round series",
                        f"{company_name} valuation revenue",
                        f"{company_name} investors",
                    ],
                    "data_points": [
                        "Latest funding round and amount",
                        "Total funding raised",
                        "Key investors",
                        "Revenue estimates if available",
                        "Runway / burn rate signals",
                    ],
                },
                "team_and_culture": {
                    "queries": [
                        f"{company_name} engineering team size",
                        f"{company_name} data team glassdoor",
                        f"{company_name} company culture reviews",
                    ],
                    "data_points": [
                        "Total employee count",
                        "Engineering team size",
                        "Data team size (critical: are you first hire or joining existing team?)",
                        "Glassdoor rating and review themes",
                        "Leadership team background",
                    ],
                },
                "tech_stack": {
                    "queries": [
                        f"{company_name} tech stack data engineering",
                        f"{company_name} engineering blog",
                        f"site:github.com {company_name}",
                    ],
                    "data_points": [
                        "Data infrastructure (warehouse, ETL, orchestration)",
                        "Cloud provider (AWS, GCP, Azure)",
                        "Key technologies (dbt, Spark, Airflow, Trino, etc.)",
                        "Open source contributions",
                    ],
                },
                "growth_signals": {
                    "queries": [
                        f"{company_name} hiring data engineer 2025 2026",
                        f"{company_name} growth expansion",
                        f"{company_name} recent news",
                    ],
                    "data_points": [
                        "Number of open data roles (signal of investment)",
                        "Recent product launches or expansions",
                        "Customer growth / revenue growth",
                        "Market position and competitors",
                    ],
                },
                "compensation": {
                    "queries": [
                        f"site:levels.fyi {company_name} data engineer",
                        f"{company_name} data engineer salary glassdoor",
                        f"site:teamblind.com {company_name} data engineer compensation",
                    ],
                    "data_points": [
                        "Base salary range for target level",
                        "Equity/RSU structure",
                        "Bonus structure",
                        "Total compensation range",
                        "Whether $300K+ TC is realistic at this company",
                    ],
                },
                "red_flags": {
                    "queries": [
                        f"{company_name} layoffs",
                        f"{company_name} glassdoor negative reviews",
                    ],
                    "data_points": [
                        "Recent layoffs",
                        "High turnover signals",
                        "Negative Glassdoor themes",
                        "Regulatory or legal issues",
                        "Runway concerns for startups",
                    ],
                },
            },
        }

        return json.dumps(research_prompt, indent=2)
