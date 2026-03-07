"""JobSpy-powered job search tool for CrewAI agents."""

from __future__ import annotations

import json
from typing import Any, Optional, Type

import pandas as pd
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class JobSearchInput(BaseModel):
    """Input schema for the job search tool."""

    search_term: str = Field(
        description="Job title or keyword to search for (e.g., 'senior data engineer', 'dbt')"
    )
    location: str = Field(
        default="Los Angeles, CA",
        description="Location to search in (e.g., 'Los Angeles, CA', 'Remote')",
    )
    results_wanted: int = Field(
        default=25,
        description="Number of results to return per job board",
    )
    hours_old: int = Field(
        default=336,  # 14 days
        description="Only return jobs posted within this many hours",
    )
    is_remote: Optional[bool] = Field(
        default=None,
        description="Filter for remote jobs only. None = no filter.",
    )
    country: str = Field(
        default="USA",
        description="Country to search in",
    )


class JobSearchTool(BaseTool):
    """
    Searches multiple job boards simultaneously using JobSpy.
    Scrapes LinkedIn, Indeed, Glassdoor, ZipRecruiter, and Google Jobs.
    Returns structured job listing data.
    """

    name: str = "job_board_search"
    description: str = (
        "Searches LinkedIn, Indeed, Glassdoor, ZipRecruiter, and Google Jobs "
        "simultaneously for job listings matching a search term and location. "
        "Returns job titles, companies, locations, URLs, descriptions, and salary info. "
        "Use this to find data engineering, analytics, and leadership roles."
    )
    args_schema: Type[BaseModel] = JobSearchInput

    @staticmethod
    def _safe_str(value: Any, default: str = "") -> str:
        """Safely convert a value to string, handling NaN and None."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return default
        return str(value)

    @staticmethod
    def _safe_float(value: Any) -> float | None:
        """Safely convert a value to float."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_bool(value: Any) -> bool:
        """Safely convert to bool, treating NaN as False."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return False
        return bool(value)

    def _run(
        self,
        search_term: str,
        location: str = "Los Angeles, CA",
        results_wanted: int = 25,
        hours_old: int = 336,
        is_remote: bool | None = None,
        country: str = "USA",
    ) -> str:
        """Execute the job search across multiple boards."""
        try:
            from jobspy import scrape_jobs
        except ImportError:
            return json.dumps(
                {"error": "python-jobspy not installed. Run: pip install python-jobspy"}
            )

        site_names = ["indeed", "linkedin", "glassdoor", "zip_recruiter", "google"]

        try:
            jobs_df: pd.DataFrame = scrape_jobs(
                site_name=site_names,
                search_term=search_term,
                location=location,
                results_wanted=results_wanted,
                hours_old=hours_old,
                is_remote=is_remote,
                country_indeed=country,
            )

            if jobs_df.empty:
                return json.dumps(
                    {
                        "jobs": [],
                        "total_found": 0,
                        "message": f"No jobs found for '{search_term}' in {location}",
                    }
                )

            # Normalize columns
            jobs_list = []
            for _, row in jobs_df.iterrows():
                # Handle URL fallback properly (pandas .get returns NaN, not None)
                url = row.get("job_url")
                if pd.isna(url) or not url:
                    url = row.get("job_url_direct", "")

                job = {
                    "title": self._safe_str(row.get("title", "")),
                    "company": self._safe_str(
                        row.get("company_name", row.get("company", ""))
                    ),
                    "location": self._safe_str(row.get("location", "")),
                    "url": self._safe_str(url),
                    "source": self._safe_str(row.get("site", "")),
                    "description": self._safe_str(row.get("description", ""))[:3000],
                    "salary_min": self._safe_float(row.get("min_amount")),
                    "salary_max": self._safe_float(row.get("max_amount")),
                    "date_posted": self._safe_str(row.get("date_posted", "")),
                    "is_remote": self._safe_bool(row.get("is_remote")),
                    "company_size": self._safe_str(
                        row.get("company_num_employees", "")
                    ),
                }
                jobs_list.append(job)

            return json.dumps(
                {
                    "jobs": jobs_list,
                    "total_found": len(jobs_list),
                    "search_term": search_term,
                    "location": location,
                    "boards_searched": site_names,
                },
                indent=2,
            )

        except Exception as e:
            return json.dumps(
                {
                    "error": str(e),
                    "search_term": search_term,
                    "location": location,
                    "hint": "If rate limited, try reducing results_wanted or wait a few minutes.",
                }
            )
