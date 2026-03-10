"""Main CLI entry point for the CV Builder & Job Recommender application."""

from __future__ import annotations

import os
import sys

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from cv_builder import __version__
from cv_builder.cv_generator import CVGenerator
from cv_builder.job_recommender import recommend_jobs, suggest_industries
from cv_builder.questionnaire import display_summary, run_questionnaire
from cv_builder.utils import PROGRESS_FILE

console = Console()


def _print_welcome() -> None:
    console.print(
        Panel(
            f"[bold magenta]CV Builder & Job Recommender[/bold magenta]  "
            f"[dim]v{__version__}[/dim]\n\n"
            "[dim]Build a professional CV and get personalised job role recommendations.[/dim]",
            border_style="magenta",
        )
    )


def _show_job_recommendations(profile) -> None:
    """Display job recommendations and skill gaps."""
    recommendations = recommend_jobs(profile)
    industries = suggest_industries(profile)

    if not recommendations:
        console.print("\n  [yellow]⚠ Not enough profile data to generate job recommendations.[/yellow]")
        return

    console.print(
        Panel(
            "[bold cyan]🎯  Job Role Recommendations[/bold cyan]",
            border_style="cyan",
        )
    )

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("Role", min_width=28)
    table.add_column("Match", width=7)
    table.add_column("Reasons", min_width=40)
    table.add_column("Skill Gaps", min_width=30)

    for i, rec in enumerate(recommendations, start=1):
        # Colour the score: green ≥70, yellow ≥40, red <40
        if rec.match_score >= 70:
            score_str = f"[green]{rec.match_score}%[/green]"
        elif rec.match_score >= 40:
            score_str = f"[yellow]{rec.match_score}%[/yellow]"
        else:
            score_str = f"[red]{rec.match_score}%[/red]"

        reasons_str = "\n".join(f"• {r}" for r in rec.reasons[:3])
        gaps_str = "\n".join(f"• {g}" for g in rec.skill_gaps[:3]) or "[dim]none identified[/dim]"

        table.add_row(str(i), rec.title, score_str, reasons_str, gaps_str)

    console.print(table)

    if industries:
        console.print(
            f"\n  [bold]Suggested Industries:[/bold] "
            f"[cyan]{', '.join(industries)}[/cyan]"
        )
    console.print()


def _generate_outputs(profile) -> None:
    """Ask the user which output formats they want and generate them."""
    console.print(
        Panel(
            "[bold green]📄  Generate Your CV[/bold green]",
            border_style="green",
        )
    )

    output_dir = Prompt.ask(
        "  [yellow]Output directory[/yellow]",
        default=".",
    ).strip() or "."

    os.makedirs(output_dir, exist_ok=True)

    gen = CVGenerator(profile)

    # PDF
    if Confirm.ask("  [cyan]Generate a PDF version of your CV?[/cyan]", default=True):
        try:
            path = gen.generate_pdf(output_dir)
            console.print(f"  [green]✅ PDF saved:[/green] {path}")
        except Exception as exc:  # noqa: BLE001
            console.print(f"  [red]❌ PDF generation failed:[/red] {exc}")

    # Plain text
    if Confirm.ask("  [cyan]Generate a plain-text version of your CV?[/cyan]", default=True):
        try:
            path = gen.generate_text(output_dir)
            console.print(f"  [green]✅ Text CV saved:[/green] {path}")
        except Exception as exc:  # noqa: BLE001
            console.print(f"  [red]❌ Text generation failed:[/red] {exc}")

    console.print()


def _cleanup_progress() -> None:
    """Optionally remove the saved progress file."""
    if os.path.exists(PROGRESS_FILE):
        if Confirm.ask(
            "  [cyan]Delete the saved progress file?[/cyan]", default=True
        ):
            try:
                os.remove(PROGRESS_FILE)
                console.print("  [dim]Progress file removed.[/dim]")
            except OSError:
                pass


def main() -> int:
    """Run the CV Builder CLI. Returns an exit code (0 = success)."""
    _print_welcome()

    try:
        # Step 1 — collect user data through the interactive questionnaire
        profile = run_questionnaire()

        # Step 2 — show a profile summary
        display_summary(profile)

        # Step 3 — show job recommendations
        if Confirm.ask(
            "  [cyan]Would you like to see personalised job recommendations?[/cyan]",
            default=True,
        ):
            _show_job_recommendations(profile)

        # Step 4 — generate CV files
        _generate_outputs(profile)

        # Step 5 — tidy up
        _cleanup_progress()

        console.print(
            Panel(
                "[bold green]🎉  All done! Good luck with your job search![/bold green]",
                border_style="green",
            )
        )
        return 0

    except KeyboardInterrupt:
        console.print("\n\n  [yellow]⚠  Interrupted. Your progress has been saved.[/yellow]")
        return 130
    except Exception as exc:  # noqa: BLE001
        console.print(f"\n  [red]❌ Unexpected error:[/red] {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
