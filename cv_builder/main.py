"""CLI entry point for CV Builder: build, score, and tailor a CV.

Usage:
    cv-builder                      Interactive questionnaire (build a CV + tools)
    cv-builder demo                 Run a bundled, no-input demo (score + tailor)
    cv-builder score  --profile p.json --jd jd.txt
    cv-builder tailor --profile p.json --jd jd.txt -o out/
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from cv_builder import __version__
from cv_builder.cv_generator import CVGenerator
from cv_builder.cv_tailor import tailor as tailor_cv
from cv_builder.docx_generator import DocxGenerator
from cv_builder.fit_scorer import score_fit
from cv_builder.jd_analyzer import analyze_jd
from cv_builder.jd_models import FitScore, JobDescription, TailoredCV
from cv_builder.job_recommender import recommend_jobs, suggest_industries
from cv_builder.llm import get_provider
from cv_builder.models import UserProfile
from cv_builder.questionnaire import display_summary, run_questionnaire
from cv_builder.utils import PROGRESS_FILE, load_progress

console = Console()

SAMPLE_DIR = Path(__file__).resolve().parent / "sample_data"
_BAND_COLOR = {"Strong": "green", "Competitive": "cyan", "Stretch": "yellow", "Poor": "red"}


# ─── Shared rendering ────────────────────────────────────────────────────────

def _print_welcome() -> None:
    console.print(
        Panel(
            f"[bold magenta]CV Builder[/bold magenta]  [dim]v{__version__}[/dim]\n\n"
            "[dim]Build an ATS-ready CV, score it against a job description, "
            "and tailor it to the role.[/dim]",
            border_style="magenta",
        )
    )


def render_fit_score(fit: FitScore, jd: JobDescription) -> None:
    color = _BAND_COLOR.get(fit.band.value, "white")
    title = jd.title or "this role"
    console.print(
        Panel(
            f"[bold {color}]Fit: {fit.overall}/100 - {fit.band.value}[/bold {color}]"
            f"\n[dim]{title}[/dim]",
            border_style=color,
        )
    )
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Category", min_width=20)
    table.add_column("Score", width=8)
    table.add_column("Notes", min_width=40)
    for c in fit.categories:
        table.add_row(c.name, f"{c.score}/{c.max_score}", c.note)
    console.print(table)
    console.print(f"\n  [bold]Summary:[/bold] {fit.summary}")
    if fit.missing_keywords:
        console.print(
            f"  [bold yellow]Gaps to address:[/bold yellow] "
            f"[dim]{', '.join(fit.missing_keywords[:10])}[/dim]"
        )
    console.print()


def render_tailor_changes(tailored: TailoredCV) -> None:
    console.print(
        Panel("[bold cyan]Tailoring change-log[/bold cyan]", border_style="cyan")
    )
    for ch in tailored.changes:
        console.print(f"  [green]*[/green] {ch.change}")
        console.print(f"    [dim]{ch.reason}[/dim]")
    console.print()


def _provider_banner(provider) -> None:
    name = type(provider).__name__
    if name == "ClaudeProvider":
        console.print("  [green]Claude API enrichment active.[/green]\n")
    else:
        console.print(
            "  [dim]Running deterministically (set ANTHROPIC_API_KEY + install "
            "the ai extra for Claude-enriched output).[/dim]\n"
        )


def _read_jd(jd_path: str | None, jd_text: str | None) -> str:
    if jd_text:
        return jd_text
    if jd_path:
        return Path(jd_path).read_text(encoding="utf-8")
    raise ValueError("A job description is required (--jd PATH or --jd-text TEXT).")


def _load_profile_or_exit(path: str) -> UserProfile:
    profile = load_progress(path)
    if profile is None:
        console.print(f"  [red]Could not load a profile from:[/red] {path}")
        raise SystemExit(1)
    return profile


# ─── Subcommands ─────────────────────────────────────────────────────────────

def cmd_score(args: argparse.Namespace) -> int:
    profile = _load_profile_or_exit(args.profile)
    jd = analyze_jd(_read_jd(args.jd, args.jd_text))
    provider = get_provider()
    _provider_banner(provider)
    fit = score_fit(profile, jd, provider)
    render_fit_score(fit, jd)
    return 0


def cmd_tailor(args: argparse.Namespace) -> int:
    profile = _load_profile_or_exit(args.profile)
    jd = analyze_jd(_read_jd(args.jd, args.jd_text))
    provider = get_provider()
    _provider_banner(provider)

    fit = score_fit(profile, jd, provider)
    render_fit_score(fit, jd)

    tailored = tailor_cv(profile, jd, provider)
    render_tailor_changes(tailored)

    out_dir = args.output or "."
    path = DocxGenerator(tailored.profile).generate(out_dir)
    console.print(f"  [green]Tailored CV saved:[/green] {path}\n")
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    _print_welcome()
    profile = _load_profile_or_exit(str(SAMPLE_DIR / "sample_profile.json"))
    jd_text = (SAMPLE_DIR / "sample_jd.txt").read_text(encoding="utf-8")
    jd = analyze_jd(jd_text)

    console.print(
        Panel(
            f"[bold]Demo:[/bold] scoring [cyan]{profile.personal_info.full_name}[/cyan] "
            f"against [cyan]{jd.title}[/cyan]",
            border_style="magenta",
        )
    )
    provider = get_provider()
    _provider_banner(provider)

    fit = score_fit(profile, jd, provider)
    render_fit_score(fit, jd)

    tailored = tailor_cv(profile, jd, provider)
    render_tailor_changes(tailored)

    out_dir = args.output or "cv_builder_demo_output"
    path = DocxGenerator(tailored.profile).generate(out_dir)
    console.print(f"  [green]Tailored CV saved:[/green] {path}")
    console.print(
        "\n  [dim]This whole run was offline and free. "
        "Try it with your own files: [/dim][cyan]cv-builder tailor --profile p.json --jd jd.txt[/cyan]\n"
    )
    return 0


# ─── Interactive flow ────────────────────────────────────────────────────────

def _show_job_recommendations(profile: UserProfile) -> None:
    recommendations = recommend_jobs(profile)
    industries = suggest_industries(profile)
    if not recommendations:
        console.print("\n  [yellow]Not enough profile data for recommendations.[/yellow]")
        return

    console.print(Panel("[bold cyan]Job Role Recommendations[/bold cyan]", border_style="cyan"))
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("Role", min_width=24)
    table.add_column("Match", width=7)
    table.add_column("Reasons", min_width=36)
    table.add_column("Skill Gaps", min_width=26)
    for i, rec in enumerate(recommendations, start=1):
        if rec.match_score >= 70:
            score_str = f"[green]{rec.match_score}%[/green]"
        elif rec.match_score >= 40:
            score_str = f"[yellow]{rec.match_score}%[/yellow]"
        else:
            score_str = f"[red]{rec.match_score}%[/red]"
        reasons = "\n".join(f"- {r}" for r in rec.reasons[:3])
        gaps = "\n".join(f"- {g}" for g in rec.skill_gaps[:3]) or "[dim]none[/dim]"
        table.add_row(str(i), rec.title, score_str, reasons, gaps)
    console.print(table)
    if industries:
        console.print(f"\n  [bold]Suggested Industries:[/bold] [cyan]{', '.join(industries)}[/cyan]")
    console.print()


def _offer_jd_tools(profile: UserProfile) -> None:
    """Interactive: score and optionally tailor the CV against a pasted JD."""
    if not Confirm.ask(
        "  [cyan]Score your CV against a specific job description?[/cyan]", default=True
    ):
        return

    console.print(
        "  [dim]Paste the job description below. Finish with a line containing only "
        "[/dim][bold]END[/bold][dim]:[/dim]"
    )
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)
    jd_text = "\n".join(lines).strip()
    if not jd_text:
        console.print("  [yellow]No job description entered - skipping.[/yellow]\n")
        return

    jd = analyze_jd(jd_text)
    provider = get_provider()
    _provider_banner(provider)
    fit = score_fit(profile, jd, provider)
    render_fit_score(fit, jd)

    if Confirm.ask("  [cyan]Generate a tailored CV for this role?[/cyan]", default=True):
        tailored = tailor_cv(profile, jd, provider)
        render_tailor_changes(tailored)
        out_dir = Prompt.ask("  [yellow]Output directory[/yellow]", default=".").strip() or "."
        path = DocxGenerator(tailored.profile).generate(out_dir)
        console.print(f"  [green]Tailored CV saved:[/green] {path}\n")


def _generate_outputs(profile: UserProfile) -> None:
    console.print(Panel("[bold green]Generate Your CV[/bold green]", border_style="green"))
    output_dir = Prompt.ask("  [yellow]Output directory[/yellow]", default=".").strip() or "."
    os.makedirs(output_dir, exist_ok=True)

    if Confirm.ask("  [cyan]Generate a .docx version (recommended, ATS-friendly)?[/cyan]", default=True):
        try:
            path = DocxGenerator(profile).generate(output_dir)
            console.print(f"  [green]DOCX saved:[/green] {path}")
        except Exception as exc:  # noqa: BLE001
            console.print(f"  [red]DOCX generation failed:[/red] {exc}")

    gen = CVGenerator(profile)
    if Confirm.ask("  [cyan]Also generate a PDF?[/cyan]", default=False):
        try:
            path = gen.generate_pdf(output_dir)
            console.print(f"  [green]PDF saved:[/green] {path}")
        except Exception as exc:  # noqa: BLE001
            console.print(f"  [red]PDF generation failed:[/red] {exc}")

    if Confirm.ask("  [cyan]Also generate a plain-text version?[/cyan]", default=False):
        try:
            path = gen.generate_text(output_dir)
            console.print(f"  [green]Text CV saved:[/green] {path}")
        except Exception as exc:  # noqa: BLE001
            console.print(f"  [red]Text generation failed:[/red] {exc}")
    console.print()


def _cleanup_progress() -> None:
    if os.path.exists(PROGRESS_FILE):
        if Confirm.ask("  [cyan]Delete the saved progress file?[/cyan]", default=True):
            try:
                os.remove(PROGRESS_FILE)
                console.print("  [dim]Progress file removed.[/dim]")
            except OSError:
                pass


def cmd_interactive(_args: argparse.Namespace) -> int:
    _print_welcome()
    try:
        profile = run_questionnaire()
        display_summary(profile)

        if Confirm.ask(
            "  [cyan]See personalised job recommendations?[/cyan]", default=True
        ):
            _show_job_recommendations(profile)

        _offer_jd_tools(profile)
        _generate_outputs(profile)
        _cleanup_progress()

        console.print(
            Panel(
                "[bold green]All done! Good luck with your job search![/bold green]",
                border_style="green",
            )
        )
        return 0
    except KeyboardInterrupt:
        console.print("\n\n  [yellow]Interrupted. Your progress has been saved.[/yellow]")
        return 130
    except Exception as exc:  # noqa: BLE001
        console.print(f"\n  [red]Unexpected error:[/red] {exc}")
        return 1


# ─── Argument parsing ────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cv-builder",
        description="Build an ATS-ready CV, score it against a job description, and tailor it.",
    )
    parser.add_argument("--version", action="version", version=f"cv-builder {__version__}")
    parser.set_defaults(func=cmd_interactive)
    sub = parser.add_subparsers(dest="command")

    p_demo = sub.add_parser("demo", help="Run a bundled no-input demo (score + tailor).")
    p_demo.add_argument("-o", "--output", help="Output directory for the demo CV.")
    p_demo.set_defaults(func=cmd_demo)

    p_score = sub.add_parser("score", help="Score a profile against a job description.")
    p_score.add_argument("--profile", required=True, help="Path to a profile JSON file.")
    p_score.add_argument("--jd", help="Path to a job-description text file.")
    p_score.add_argument("--jd-text", help="Job-description text inline.")
    p_score.set_defaults(func=cmd_score)

    p_tailor = sub.add_parser("tailor", help="Tailor a CV to a job description (.docx).")
    p_tailor.add_argument("--profile", required=True, help="Path to a profile JSON file.")
    p_tailor.add_argument("--jd", help="Path to a job-description text file.")
    p_tailor.add_argument("--jd-text", help="Job-description text inline.")
    p_tailor.add_argument("-o", "--output", help="Output directory for the tailored CV.")
    p_tailor.set_defaults(func=cmd_tailor)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
