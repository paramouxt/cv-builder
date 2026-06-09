"""Pydantic data models for the CV Builder application."""

from __future__ import annotations

import re

from pydantic import BaseModel, field_validator


class PersonalInfo(BaseModel):
    full_name: str
    email: str
    phone: str
    location: str
    linkedin: str | None = None
    portfolio: str | None = None
    summary: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid email address format")
        return v


class Education(BaseModel):
    degree: str
    field_of_study: str
    institution: str
    start_date: str
    end_date: str
    gpa: str | None = None
    honors: str | None = None
    notable_coursework: str | None = None


class Achievement(BaseModel):
    description: str
    quantified_impact: str | None = None
    tools_used: str | None = None
    outcome: str | None = None


class WorkExperience(BaseModel):
    job_title: str
    company: str
    location: str
    start_date: str
    end_date: str
    achievements: list[Achievement] = []
    reason_for_leaving: str | None = None


class TechnicalSkill(BaseModel):
    name: str
    proficiency: str  # Beginner / Intermediate / Advanced / Expert


class Language(BaseModel):
    name: str
    proficiency: str  # Native / Fluent / Intermediate / Basic


class Certification(BaseModel):
    name: str
    issuing_org: str
    date: str
    expiry_date: str | None = None


class Skills(BaseModel):
    technical: list[TechnicalSkill] = []
    soft: list[str] = []
    languages: list[Language] = []
    certifications: list[Certification] = []


class Project(BaseModel):
    name: str
    description: str
    technologies: str
    role: str
    outcomes: str
    link: str | None = None
    problem_solved: str | None = None


class AdditionalInfo(BaseModel):
    volunteer_work: str | None = None
    publications: str | None = None
    interests: str | None = None


class JobPreferences(BaseModel):
    desired_roles: list[str] = []
    preferred_industries: list[str] = []
    employment_type: str = "Full-time"
    work_mode: str = "Hybrid"
    preferred_locations: list[str] = []
    salary_expectation: str | None = None
    willing_to_relocate: bool = False


class UserProfile(BaseModel):
    personal_info: PersonalInfo | None = None
    education: list[Education] = []
    work_experience: list[WorkExperience] = []
    skills: Skills = Skills()
    projects: list[Project] = []
    additional_info: AdditionalInfo = AdditionalInfo()
    job_preferences: JobPreferences = JobPreferences()
