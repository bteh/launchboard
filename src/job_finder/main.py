#!/usr/bin/env python
"""CLI entry points for the Job Finder pipeline."""

from __future__ import annotations

import os
import sys
import warnings

from dotenv import load_dotenv

load_dotenv()
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """Run the full job search pipeline."""
    from job_finder.crew import JobFinderCrew

    print("\n" + "=" * 70)
    print("  JOB FINDER — AI-Powered Job Search Pipeline")
    print("=" * 70)
    print("Using Claude as LLM | Searching 5+ job boards | Scoring against resume")
    print("=" * 70 + "\n")

    crew = JobFinderCrew()
    result = crew.crew().kickoff()

    report_path = os.path.join(
        os.path.dirname(__file__), "output", "job_search_report.md"
    )

    print("\n" + "=" * 70)
    print("  Pipeline complete! Results saved to:")
    print(f"    Report: {report_path}")
    print("    DB: data/job_tracker.db")
    print("=" * 70 + "\n")

    return result


def search():
    """Run only the job search step (no scoring/optimization)."""
    import json
    from job_finder.tools.job_search_tool import JobSearchTool

    tool = JobSearchTool()

    searches = [
        ("senior data engineer", "Los Angeles, CA"),
        ("staff data engineer", "Remote"),
        ("head of data", "Los Angeles, CA"),
        ("head of data", "Remote"),
        ("data platform engineer", "Remote"),
        ("manager data engineering", "Remote"),
        ("dbt data engineer", "Remote"),
    ]

    all_jobs = []
    for term, location in searches:
        print(f"Searching: '{term}' in {location}...")
        result = json.loads(tool._run(search_term=term, location=location, results_wanted=15))
        if "jobs" in result:
            all_jobs.extend(result["jobs"])
            print(f"   Found {len(result['jobs'])} listings")
        else:
            print(f"   Warning: {result.get('error', 'No results')}")

    # Deduplicate by URL
    seen_urls = set()
    unique_jobs = []
    for job in all_jobs:
        url = job.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_jobs.append(job)

    print(f"\nTotal unique jobs found: {len(unique_jobs)}")

    # Save to file
    output_path = os.path.join(os.path.dirname(__file__), "output", "raw_search_results.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(unique_jobs, f, indent=2)
    print(f"Saved to {output_path}")

    return unique_jobs


def score():
    """Run the full pipeline (search + scoring + optimization + cover letters)."""
    from job_finder.crew import JobFinderCrew

    print("Running full pipeline...")
    crew = JobFinderCrew()
    result = crew.crew().kickoff()
    return result


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "search":
            search()
        elif command == "score":
            score()
        else:
            print(f"Unknown command: {command}")
            print("Usage: python -m job_finder.main [search|score]")
    else:
        run()
