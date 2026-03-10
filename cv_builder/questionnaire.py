"""Multi-stage questioning engine for the CV Builder application."""

from __future__ import annotations

import json
import sys
from typing import Callable, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich import print as rprint

from cv_builder.models import (
    Achievement,
    AdditionalInfo,
    Certification,
    Education,
    JobPreferences,
    Language,
    PersonalInfo,
    Project,
    Skills,
    TechnicalSkill,
    UserProfile,
    WorkExperience,
)
from cv_builder.constants import (
    EMPLOYMENT_TYPES,
    LANGUAGE_PROFICIENCY_LEVELS,
    TECHNICAL_PROFICIENCY_LEVELS,
    WORK_MODES,
)
from cv_builder.validators import (
    validate_date,
    validate_email,
    validate_phone,
    validate_url,
    normalize_date,
)
from cv_builder.utils import save_progress, load_progress, PROGRESS_FILE

console = Console()

TOTAL_STAGES = 7


def _print_stage_header(stage: int, title: str) -> None:
    console.print(
        Panel(
            f"[bold cyan]📋 Step {stage} of {TOTAL_STAGES}: {title}[/bold cyan]",
            border_style="cyan",
        )
    )


def _ask(prompt: str, required: bool = True, default: Optional[str] = None,
         validator: Optional[Callable[[str], bool]] = None,
         hint: Optional[str] = None) -> str:
    """Ask a single question with optional validation."""
    if hint:
        console.print(f"  [dim]{hint}[/dim]")

    suffix = ""
    if default:
        suffix = f" [dim](default: {default})[/dim]"
    if not required:
        suffix += " [dim](optional, press Enter to skip)[/dim]"

    while True:
        answer = Prompt.ask(f"  [yellow]{prompt}[/yellow]{suffix}",
                            default=default or ("" if not required else None),
                            show_default=False)
        answer = answer.strip() if answer else ""

        if not required and not answer:
            return ""

        if required and not answer:
            console.print("  [red]This field is required. Please enter a value.[/red]")
            continue

        if validator and answer:
            if not validator(answer):
                console.print("  [red]Invalid input. Please try again.[/red]")
                continue

        return answer


def _ask_choice(prompt: str, choices: list[str], default: Optional[str] = None) -> str:
    """Ask the user to pick from a list of choices."""
    choices_str = " / ".join(choices)
    console.print(f"  [dim]Options: {choices_str}[/dim]")
    while True:
        answer = Prompt.ask(
            f"  [yellow]{prompt}[/yellow]",
            default=default or choices[0],
        )
        normalized = answer.strip()
        match = next(
            (c for c in choices if c.lower() == normalized.lower()), None
        )
        if match:
            return match
        console.print(f"  [red]Please choose one of: {choices_str}[/red]")


def _ask_list(prompt: str, hint: str = "Enter each item on a new line. Leave blank to finish.") -> list[str]:
    """Collect multiple items from the user."""
    console.print(f"  [dim]{hint}[/dim]")
    items: list[str] = []
    idx = 1
    while True:
        val = Prompt.ask(f"  [yellow]{prompt} #{idx}[/yellow] [dim](or press Enter to finish)[/dim]",
                         default="")
        val = val.strip()
        if not val:
            break
        items.append(val)
        idx += 1
    return items


# ─── Stage 1: Personal Information ───────────────────────────────────────────

def collect_personal_info() -> PersonalInfo:
    _print_stage_header(1, "Personal Information")

    name = _ask("Full Name")

    console.print("\n  [dim]💡 Tips for a strong professional summary:[/dim]")
    console.print("  [dim]  • Mention your years of experience & key expertise[/dim]")
    console.print("  [dim]  • Highlight your most impressive achievement[/dim]")
    console.print("  [dim]  • Specify the value you bring to employers[/dim]")
    console.print("  [dim]  • Keep it to 2-4 sentences[/dim]\n")

    email = _ask("Email Address", validator=validate_email,
                 hint="Example: john.doe@example.com")
    phone = _ask("Phone Number", validator=validate_phone,
                 hint="Example: +1 234 567 8900")
    location = _ask("Location (City, Country)", hint="Example: London, UK")
    linkedin = _ask("LinkedIn URL", required=False,
                    validator=lambda u: validate_url(u) or not u,
                    hint="Example: https://linkedin.com/in/johndoe")
    portfolio = _ask("Portfolio / Website URL", required=False,
                     validator=lambda u: validate_url(u) or not u)

    summary = _ask(
        "Professional Summary / Elevator Pitch",
        required=False,
        hint=(
            "Write 2-4 sentences describing who you are, your key skills, "
            "and the value you bring to employers."
        ),
    )

    return PersonalInfo(
        full_name=name,
        email=email,
        phone=phone,
        location=location,
        linkedin=linkedin or None,
        portfolio=portfolio or None,
        summary=summary or None,
    )


# ─── Stage 2: Education ───────────────────────────────────────────────────────

def collect_education() -> list[Education]:
    _print_stage_header(2, "Education")
    console.print("  [dim]You can add multiple education entries.[/dim]\n")

    entries: list[Education] = []

    while True:
        degree = _ask("Degree (e.g., Bachelor of Science, Master of Arts)")
        field = _ask("Field of Study / Major")
        institution = _ask("Institution / University Name")
        start = _ask("Start Date (MM/YYYY or YYYY)", validator=validate_date)
        end = _ask("End Date (MM/YYYY, YYYY, or 'Present')",
                   validator=validate_date)
        gpa = _ask("GPA (optional)", required=False)
        honors = _ask("Honors / Awards (optional)", required=False)
        coursework = _ask(
            "Notable Coursework, Thesis, or Capstone Project (optional)",
            required=False,
        )

        entries.append(
            Education(
                degree=degree,
                field_of_study=field,
                institution=institution,
                start_date=normalize_date(start),
                end_date=normalize_date(end),
                gpa=gpa or None,
                honors=honors or None,
                notable_coursework=coursework or None,
            )
        )

        if not Confirm.ask("  [cyan]Add another education entry?[/cyan]", default=False):
            break

    return entries


# ─── Stage 3: Work Experience ────────────────────────────────────────────────

def _collect_achievements() -> list[Achievement]:
    achievements: list[Achievement] = []
    console.print("  [dim]Add 2-5 key responsibilities / achievements for this role.[/dim]")

    for i in range(1, 6):
        desc = Prompt.ask(
            f"  [yellow]Achievement #{i}[/yellow] [dim](or press Enter to finish)[/dim]",
            default="",
        ).strip()
        if not desc:
            if i <= 2:
                console.print("  [red]Please enter at least 1 achievement.[/red]")
                desc = Prompt.ask(f"  [yellow]Achievement #{i}[/yellow]").strip()
                if not desc:
                    break
            else:
                break

        # Probing follow-ups
        console.print("  [dim cyan]  → Probing questions (optional — press Enter to skip):[/dim cyan]")
        impact = _ask("    Can you quantify the impact? (e.g., increased sales by 20%)",
                      required=False)
        tools = _ask("    What tools or technologies did you use?", required=False)
        outcome = _ask("    What was the outcome or result?", required=False)

        achievements.append(
            Achievement(
                description=desc,
                quantified_impact=impact or None,
                tools_used=tools or None,
                outcome=outcome or None,
            )
        )

    return achievements


def collect_work_experience() -> list[WorkExperience]:
    _print_stage_header(3, "Work Experience")

    if not Confirm.ask(
        "  [cyan]Do you have any work experience to add?[/cyan]", default=True
    ):
        console.print("  [dim]Skipping work experience (fresh graduate mode).[/dim]")
        return []

    entries: list[WorkExperience] = []

    while True:
        console.print()
        title = _ask("Job Title")
        company = _ask("Company Name")
        location = _ask("Location (City, Country)")
        start = _ask("Start Date (MM/YYYY or YYYY)", validator=validate_date)
        end = _ask("End Date (MM/YYYY, YYYY, or 'Present')", validator=validate_date)

        console.print()
        achievements = _collect_achievements()

        reason = _ask("Why did you leave this role? (optional, used for recommendations)",
                      required=False)

        entries.append(
            WorkExperience(
                job_title=title,
                company=company,
                location=location,
                start_date=normalize_date(start),
                end_date=normalize_date(end),
                achievements=achievements,
                reason_for_leaving=reason or None,
            )
        )

        if not Confirm.ask("  [cyan]Add another work experience entry?[/cyan]", default=False):
            break

    return entries


# ─── Stage 4: Skills ─────────────────────────────────────────────────────────

def collect_skills() -> Skills:
    _print_stage_header(4, "Skills")

    # Technical skills
    console.print("\n  [bold]Technical Skills[/bold] [dim](proficiency: Beginner / Intermediate / Advanced / Expert)[/dim]")
    technical: list[TechnicalSkill] = []
    while True:
        skill_name = Prompt.ask(
            "  [yellow]Technical Skill[/yellow] [dim](or press Enter to finish)[/dim]",
            default="",
        ).strip()
        if not skill_name:
            break
        level = _ask_choice(
            f"  Proficiency level for '{skill_name}'",
            TECHNICAL_PROFICIENCY_LEVELS,
            default="Intermediate",
        )
        technical.append(TechnicalSkill(name=skill_name, proficiency=level))

    # Soft skills
    console.print("\n  [bold]Soft Skills[/bold]")
    soft = _ask_list("Soft Skill", hint="e.g., Communication, Leadership, Teamwork. Leave blank to finish.")

    # Languages
    console.print("\n  [bold]Languages[/bold] [dim](proficiency: Native / Fluent / Intermediate / Basic)[/dim]")
    languages: list[Language] = []
    while True:
        lang_name = Prompt.ask(
            "  [yellow]Language[/yellow] [dim](or press Enter to finish)[/dim]",
            default="",
        ).strip()
        if not lang_name:
            break
        level = _ask_choice(
            f"  Proficiency for '{lang_name}'",
            LANGUAGE_PROFICIENCY_LEVELS,
            default="Fluent",
        )
        languages.append(Language(name=lang_name, proficiency=level))

    # Certifications
    console.print("\n  [bold]Certifications[/bold]")
    certifications: list[Certification] = []
    while True:
        cert_name = Prompt.ask(
            "  [yellow]Certification Name[/yellow] [dim](or press Enter to finish)[/dim]",
            default="",
        ).strip()
        if not cert_name:
            break
        org = _ask("  Issuing Organization")
        date = _ask("  Date Obtained (MM/YYYY or YYYY)", validator=validate_date)
        expiry = _ask("  Expiry Date (MM/YYYY, optional)", required=False,
                      validator=lambda d: validate_date(d) or not d)
        certifications.append(
            Certification(
                name=cert_name,
                issuing_org=org,
                date=normalize_date(date),
                expiry_date=normalize_date(expiry) if expiry else None,
            )
        )

    return Skills(
        technical=technical,
        soft=soft,
        languages=languages,
        certifications=certifications,
    )


# ─── Stage 5: Projects ───────────────────────────────────────────────────────

def collect_projects() -> list[Project]:
    _print_stage_header(5, "Projects")

    if not Confirm.ask("  [cyan]Do you have any projects to add?[/cyan]", default=True):
        return []

    projects: list[Project] = []

    while True:
        name = _ask("Project Name")
        description = _ask("Brief Description")
        problem = _ask("What problem did this project solve?", required=False)
        technologies = _ask("Technologies Used (comma-separated)",
                            hint="e.g., Python, React, PostgreSQL")
        role = _ask("Your Role in the Project")
        outcomes = _ask("Key Outcomes / Results")
        link = _ask("Project Link (GitHub, live URL — optional)", required=False,
                    validator=lambda u: validate_url(u) or not u)

        projects.append(
            Project(
                name=name,
                description=description,
                technologies=technologies,
                role=role,
                outcomes=outcomes,
                link=link or None,
                problem_solved=problem or None,
            )
        )

        if not Confirm.ask("  [cyan]Add another project?[/cyan]", default=False):
            break

    return projects


# ─── Stage 6: Additional Information ─────────────────────────────────────────

def collect_additional_info() -> AdditionalInfo:
    _print_stage_header(6, "Additional Information")
    console.print("  [dim]All fields in this section are optional.[/dim]\n")

    volunteer = _ask("Volunteer Work (organization, role, brief description)",
                     required=False)
    publications = _ask("Publications / Conferences (title, venue, year)",
                        required=False)
    interests = _ask("Interests / Hobbies", required=False,
                     hint="e.g., Open-source contributing, Chess, Rock climbing")

    return AdditionalInfo(
        volunteer_work=volunteer or None,
        publications=publications or None,
        interests=interests or None,
    )


# ─── Stage 7: Job Preferences ────────────────────────────────────────────────

def collect_job_preferences() -> JobPreferences:
    _print_stage_header(7, "Job Preferences")
    console.print("  [dim]This information is used for job recommendations.[/dim]\n")

    desired_roles = _ask_list(
        "Desired Job Title / Role",
        hint="Enter roles you want to target (or type 'not sure'). Leave blank to finish.",
    )

    preferred_industries = _ask_list(
        "Preferred Industry",
        hint="e.g., Technology, Finance, Healthcare. Leave blank to finish.",
    )

    employment_type = _ask_choice("Employment Type", EMPLOYMENT_TYPES, default="Full-time")
    work_mode = _ask_choice("Work Mode Preference", WORK_MODES, default="Hybrid")

    preferred_locations: list[str] = []
    if work_mode in ("Hybrid", "On-site"):
        preferred_locations = _ask_list("Preferred Location",
                                        hint="e.g., London, New York. Leave blank to finish.")

    salary = _ask("Salary Expectation (optional, e.g., '£60k-£80k')", required=False)
    relocate = Confirm.ask("  [cyan]Are you willing to relocate?[/cyan]", default=False)

    return JobPreferences(
        desired_roles=desired_roles,
        preferred_industries=preferred_industries,
        employment_type=employment_type,
        work_mode=work_mode,
        preferred_locations=preferred_locations,
        salary_expectation=salary or None,
        willing_to_relocate=relocate,
    )


# ─── Summary display ─────────────────────────────────────────────────────────

def display_summary(profile: UserProfile) -> None:
    console.print("\n")
    console.print(
        Panel("[bold green]📄 Profile Summary[/bold green]", border_style="green")
    )

    pi = profile.personal_info
    if pi:
        table = Table(show_header=False, box=None)
        table.add_row("[cyan]Name[/cyan]", pi.full_name)
        table.add_row("[cyan]Email[/cyan]", pi.email)
        table.add_row("[cyan]Phone[/cyan]", pi.phone)
        table.add_row("[cyan]Location[/cyan]", pi.location)
        if pi.linkedin:
            table.add_row("[cyan]LinkedIn[/cyan]", pi.linkedin)
        console.print(table)

    if profile.education:
        console.print(f"\n  [bold]Education[/bold]: {len(profile.education)} entr(y/ies)")
        for edu in profile.education:
            console.print(f"    • {edu.degree} in {edu.field_of_study} — {edu.institution}")

    if profile.work_experience:
        console.print(f"\n  [bold]Work Experience[/bold]: {len(profile.work_experience)} role(s)")
        for exp in profile.work_experience:
            console.print(f"    • {exp.job_title} @ {exp.company}")

    if profile.skills.technical:
        skills_str = ", ".join(s.name for s in profile.skills.technical[:6])
        if len(profile.skills.technical) > 6:
            skills_str += "..."
        console.print(f"\n  [bold]Technical Skills[/bold]: {skills_str}")

    if profile.projects:
        console.print(f"\n  [bold]Projects[/bold]: {len(profile.projects)}")

    console.print()


# ─── Main questionnaire orchestrator ────────────────────────────────────────

def run_questionnaire() -> UserProfile:
    """Run the full multi-stage questionnaire and return the completed profile."""

    console.print(
        Panel(
            "[bold magenta]🚀  CV Builder & Job Recommender[/bold magenta]\n\n"
            "Welcome! I'll walk you through a series of questions to build your\n"
            "professional CV and recommend the best job roles for you.\n\n"
            "[dim]Your progress is saved automatically after each section.[/dim]",
            border_style="magenta",
        )
    )

    # Offer to resume from saved progress
    profile = UserProfile()
    saved = load_progress()
    if saved:
        if Confirm.ask(
            "  [cyan]A saved session was found. Would you like to resume?[/cyan]",
            default=True,
        ):
            profile = saved
            console.print("  [green]✅ Resumed from saved session.[/green]\n")

    # Run each stage
    if not profile.personal_info:
        profile.personal_info = collect_personal_info()
        save_progress(profile)

    if not profile.education:
        profile.education = collect_education()
        save_progress(profile)

    if not profile.work_experience and not _has_stage_been_skipped(profile, "work"):
        profile.work_experience = collect_work_experience()
        save_progress(profile)

    # Always re-collect skills if empty
    if not profile.skills.technical and not profile.skills.soft:
        profile.skills = collect_skills()
        save_progress(profile)

    if not profile.projects and not _has_stage_been_skipped(profile, "projects"):
        profile.projects = collect_projects()
        save_progress(profile)

    if (not profile.additional_info.volunteer_work and
            not profile.additional_info.interests and
            not profile.additional_info.publications):
        profile.additional_info = collect_additional_info()
        save_progress(profile)

    if not profile.job_preferences.desired_roles:
        profile.job_preferences = collect_job_preferences()
        save_progress(profile)

    return profile


def _has_stage_been_skipped(profile: UserProfile, stage: str) -> bool:
    """Heuristic to detect if a stage was deliberately skipped in a prior session."""
    # If the profile was loaded from JSON and the list is empty, we can't tell
    # definitively — so we re-ask. Return False to keep the behavior simple.
    return False
