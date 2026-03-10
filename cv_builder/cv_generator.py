"""CV/PDF generation logic using fpdf2."""

from __future__ import annotations

import os
from typing import Optional

from fpdf import FPDF

from cv_builder.models import UserProfile
from cv_builder.templates import CVTemplate, MODERN_TEMPLATE
from cv_builder.utils import build_filename, format_date_range


class CVGenerator:
    """Generates a professional CV as PDF or plain text."""

    def __init__(self, profile: UserProfile, template: CVTemplate = MODERN_TEMPLATE):
        self.profile = profile
        self.template = template

    # ─── Public API ────────────────────────────────────────────────────────

    def generate_pdf(self, output_dir: str = ".") -> str:
        """Generate a PDF CV and return the output file path."""
        pi = self.profile.personal_info
        if not pi:
            raise ValueError("Personal information is required to generate a CV")

        filename = build_filename(pi.full_name, "pdf")
        filepath = os.path.join(output_dir, filename)

        pdf = _CVDocument(self.profile, self.template)
        pdf.build()
        pdf.output(filepath)
        return filepath

    def generate_text(self, output_dir: str = ".") -> str:
        """Generate a plain-text CV and return the output file path."""
        pi = self.profile.personal_info
        if not pi:
            raise ValueError("Personal information is required to generate a CV")

        filename = build_filename(pi.full_name, "txt")
        filepath = os.path.join(output_dir, filename)

        content = _build_text_cv(self.profile)
        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write(content)
        return filepath


# ─── Internal PDF builder ────────────────────────────────────────────────────

class _CVDocument(FPDF):
    """Internal FPDF subclass for building the CV document."""

    def __init__(self, profile: UserProfile, template: CVTemplate):
        super().__init__()
        self.profile = profile
        self.tpl = template
        self.set_margins(
            template.margins.left,
            template.margins.top,
            template.margins.right,
        )
        self.set_auto_page_break(auto=True, margin=template.margins.bottom)

    def build(self) -> None:
        self.add_page()
        self._header_section()
        self._summary_section()
        self._experience_section()
        self._education_section()
        self._skills_section()
        self._projects_section()
        self._certifications_section()
        self._additional_section()

    # ─── Header ────────────────────────────────────────────────────────────

    def _header_section(self) -> None:
        pi = self.profile.personal_info
        if not pi:
            return

        c = self.tpl.colors
        f = self.tpl.fonts

        # Name
        self.set_font(f.family, "B", f.size_name)
        self.set_text_color(*c.primary)
        self.cell(0, 10, pi.full_name, ln=True, align="C")

        # Contact line
        self.set_font(f.family, "", f.size_small)
        self.set_text_color(*c.secondary)
        contact_parts = [pi.email, pi.phone, pi.location]
        if pi.linkedin:
            contact_parts.append(pi.linkedin)
        if pi.portfolio:
            contact_parts.append(pi.portfolio)
        self.cell(0, 5, "  |  ".join(contact_parts), ln=True, align="C")
        self.ln(3)
        self._horizontal_rule()

    # ─── Summary ────────────────────────────────────────────────────────────

    def _summary_section(self) -> None:
        pi = self.profile.personal_info
        if not pi or not pi.summary:
            return
        self._section_title("Professional Summary")
        self._body_text(pi.summary)
        self.ln(self.tpl.section_spacing)

    # ─── Work Experience ────────────────────────────────────────────────────

    def _experience_section(self) -> None:
        if not self.profile.work_experience:
            return
        self._section_title("Work Experience")
        for exp in self.profile.work_experience:
            self._entry_header(exp.job_title, exp.company, exp.location,
                               exp.start_date, exp.end_date)
            for ach in exp.achievements:
                parts = [ach.description]
                if ach.quantified_impact:
                    parts.append(f"Impact: {ach.quantified_impact}")
                if ach.tools_used:
                    parts.append(f"Tools: {ach.tools_used}")
                if ach.outcome:
                    parts.append(f"Outcome: {ach.outcome}")
                self._bullet(". ".join(parts))
            self.ln(2)

    # ─── Education ─────────────────────────────────────────────────────────

    def _education_section(self) -> None:
        if not self.profile.education:
            return
        self._section_title("Education")
        for edu in self.profile.education:
            degree_line = f"{edu.degree} in {edu.field_of_study}"
            self._entry_header(degree_line, edu.institution, "",
                               edu.start_date, edu.end_date)
            extras = []
            if edu.gpa:
                extras.append(f"GPA: {edu.gpa}")
            if edu.honors:
                extras.append(f"Honors: {edu.honors}")
            if edu.notable_coursework:
                extras.append(f"Notable work: {edu.notable_coursework}")
            if extras:
                self._body_text("  ".join(extras))
            self.ln(2)

    # ─── Skills ─────────────────────────────────────────────────────────────

    def _skills_section(self) -> None:
        sk = self.profile.skills
        if not (sk.technical or sk.soft or sk.languages):
            return
        self._section_title("Skills")

        if sk.technical:
            tech_str = ", ".join(
                f"{s.name} ({s.proficiency})" for s in sk.technical
            )
            self._labeled_line("Technical", tech_str)

        if sk.soft:
            self._labeled_line("Soft Skills", ", ".join(sk.soft))

        if sk.languages:
            lang_str = ", ".join(f"{l.name} ({l.proficiency})" for l in sk.languages)
            self._labeled_line("Languages", lang_str)

        self.ln(self.tpl.section_spacing)

    # ─── Projects ───────────────────────────────────────────────────────────

    def _projects_section(self) -> None:
        if not self.profile.projects:
            return
        self._section_title("Projects")
        for proj in self.profile.projects:
            self._entry_header(proj.name, proj.role, "", "", "")
            desc = proj.description
            if proj.problem_solved:
                desc += f" Problem solved: {proj.problem_solved}"
            self._body_text(desc)
            self._labeled_line("Technologies", proj.technologies)
            self._labeled_line("Outcomes", proj.outcomes)
            if proj.link:
                self._labeled_line("Link", proj.link)
            self.ln(2)

    # ─── Certifications ─────────────────────────────────────────────────────

    def _certifications_section(self) -> None:
        certs = self.profile.skills.certifications
        if not certs:
            return
        self._section_title("Certifications")
        for cert in certs:
            line = f"{cert.name} — {cert.issuing_org} ({cert.date})"
            if cert.expiry_date:
                line += f", Expires: {cert.expiry_date}"
            self._bullet(line)
        self.ln(self.tpl.section_spacing)

    # ─── Additional ─────────────────────────────────────────────────────────

    def _additional_section(self) -> None:
        ai = self.profile.additional_info
        has_content = ai.volunteer_work or ai.publications or ai.interests
        if not has_content:
            return
        self._section_title("Additional Information")
        if ai.volunteer_work:
            self._labeled_line("Volunteer", ai.volunteer_work)
        if ai.publications:
            self._labeled_line("Publications", ai.publications)
        if ai.interests:
            self._labeled_line("Interests", ai.interests)
        self.ln(self.tpl.section_spacing)

    # ─── Helpers ─────────────────────────────────────────────────────────────

    def _section_title(self, title: str) -> None:
        c = self.tpl.colors
        f = self.tpl.fonts
        self.set_font(f.family, "B", f.size_section)
        self.set_text_color(*c.primary)
        self.cell(0, 8, title.upper(), ln=True)
        self._horizontal_rule()
        self.ln(1)

    def _entry_header(self, title: str, org: str, location: str,
                      start: str, end: str) -> None:
        c = self.tpl.colors
        f = self.tpl.fonts

        self.set_font(f.family, "B", f.size_body)
        self.set_text_color(*c.text)
        left_text = title
        right_text = format_date_range(start, end) if start else ""

        # Print title on the left, date on the right
        self.cell(0, 5, left_text, ln=False)
        if right_text:
            self.set_x(-self.tpl.margins.right - 40)
            self.set_font(f.family, "", f.size_small)
            self.set_text_color(*c.secondary)
            self.cell(40, 5, right_text, ln=True, align="R")
        else:
            self.ln()

        if org:
            self.set_font(f.family, "I", f.size_small)
            self.set_text_color(*c.secondary)
            org_line = f"{org}"
            if location:
                org_line += f"  ·  {location}"
            self.cell(0, 4, org_line, ln=True)

    def _bullet(self, text: str) -> None:
        c = self.tpl.colors
        f = self.tpl.fonts
        self.set_font(f.family, "", f.size_body)
        self.set_text_color(*c.text)
        indent = self.tpl.margins.left + 4
        self.set_x(indent)
        self.multi_cell(0, self.tpl.line_height, f"•  {text}")

    def _body_text(self, text: str) -> None:
        c = self.tpl.colors
        f = self.tpl.fonts
        self.set_font(f.family, "", f.size_body)
        self.set_text_color(*c.text)
        self.multi_cell(0, self.tpl.line_height, text)

    def _labeled_line(self, label: str, value: str) -> None:
        c = self.tpl.colors
        f = self.tpl.fonts
        self.set_font(f.family, "B", f.size_body)
        self.set_text_color(*c.secondary)
        label_width = 30
        self.cell(label_width, self.tpl.line_height, f"{label}:")
        self.set_font(f.family, "", f.size_body)
        self.set_text_color(*c.text)
        self.multi_cell(0, self.tpl.line_height, value)

    def _horizontal_rule(self) -> None:
        c = self.tpl.colors
        self.set_draw_color(*c.accent)
        self.set_line_width(0.3)
        y = self.get_y()
        self.line(self.tpl.margins.left, y,
                  self.w - self.tpl.margins.right, y)
        self.ln(2)


# ─── Plain text CV builder ───────────────────────────────────────────────────

def _build_text_cv(profile: UserProfile) -> str:
    lines: list[str] = []

    def section(title: str) -> None:
        lines.append("")
        lines.append(title.upper())
        lines.append("=" * len(title))

    def bullet(text: str) -> None:
        lines.append(f"  • {text}")

    pi = profile.personal_info
    if pi:
        lines.append(pi.full_name)
        lines.append(f"Email: {pi.email}  |  Phone: {pi.phone}  |  Location: {pi.location}")
        if pi.linkedin:
            lines.append(f"LinkedIn: {pi.linkedin}")
        if pi.portfolio:
            lines.append(f"Portfolio: {pi.portfolio}")
        if pi.summary:
            section("Professional Summary")
            lines.append(pi.summary)

    if profile.work_experience:
        section("Work Experience")
        for exp in profile.work_experience:
            lines.append(f"\n{exp.job_title} @ {exp.company} ({exp.location})")
            lines.append(f"{exp.start_date} – {exp.end_date}")
            for ach in exp.achievements:
                text = ach.description
                if ach.quantified_impact:
                    text += f" | Impact: {ach.quantified_impact}"
                if ach.tools_used:
                    text += f" | Tools: {ach.tools_used}"
                bullet(text)

    if profile.education:
        section("Education")
        for edu in profile.education:
            lines.append(f"\n{edu.degree} in {edu.field_of_study}")
            lines.append(f"{edu.institution}  ({edu.start_date} – {edu.end_date})")
            if edu.gpa:
                lines.append(f"GPA: {edu.gpa}")
            if edu.honors:
                lines.append(f"Honors: {edu.honors}")

    sk = profile.skills
    if sk.technical or sk.soft or sk.languages:
        section("Skills")
        if sk.technical:
            tech = ", ".join(f"{s.name} ({s.proficiency})" for s in sk.technical)
            lines.append(f"Technical: {tech}")
        if sk.soft:
            lines.append(f"Soft Skills: {', '.join(sk.soft)}")
        if sk.languages:
            lang = ", ".join(f"{l.name} ({l.proficiency})" for l in sk.languages)
            lines.append(f"Languages: {lang}")

    if profile.projects:
        section("Projects")
        for proj in profile.projects:
            lines.append(f"\n{proj.name} ({proj.role})")
            lines.append(proj.description)
            lines.append(f"Technologies: {proj.technologies}")
            lines.append(f"Outcomes: {proj.outcomes}")
            if proj.link:
                lines.append(f"Link: {proj.link}")

    if sk.certifications:
        section("Certifications")
        for cert in sk.certifications:
            bullet(f"{cert.name} — {cert.issuing_org} ({cert.date})")

    ai = profile.additional_info
    if ai.volunteer_work or ai.publications or ai.interests:
        section("Additional Information")
        if ai.volunteer_work:
            lines.append(f"Volunteer: {ai.volunteer_work}")
        if ai.publications:
            lines.append(f"Publications: {ai.publications}")
        if ai.interests:
            lines.append(f"Interests: {ai.interests}")

    return "\n".join(lines)
