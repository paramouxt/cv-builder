"""Pydantic data models for the CV Builder application."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, EmailStr, field_validator
import re


class PersonalInfo(BaseModel):
    full_name: str
    email: str
    phone: str
    location: str
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None
    summary: Optional[str] = None

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
    gpa: Optional[str] = None
    honors: Optional[str] = None
    notable_coursework: Optional[str] = None


class Achievement(BaseModel):
    description: str
    quantified_impact: Optional[str] = None
    tools_used: Optional[str] = None
    outcome: Optional[str] = None


class WorkExperience(BaseModel):
    job_title: str
    company: str
    location: str
    start_date: str
    end_date: str
    achievements: List[Achievement] = []
    reason_for_leaving: Optional[str] = None


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
    expiry_date: Optional[str] = None


class Skills(BaseModel):
    technical: List[TechnicalSkill] = []
    soft: List[str] = []
    languages: List[Language] = []
    certifications: List[Certification] = []


class Project(BaseModel):
    name: str
    description: str
    technologies: str
    role: str
    outcomes: str
    link: Optional[str] = None
    problem_solved: Optional[str] = None


class AdditionalInfo(BaseModel):
    volunteer_work: Optional[str] = None
    publications: Optional[str] = None
    interests: Optional[str] = None


class JobPreferences(BaseModel):
    desired_roles: List[str] = []
    preferred_industries: List[str] = []
    employment_type: str = "Full-time"
    work_mode: str = "Hybrid"
    preferred_locations: List[str] = []
    salary_expectation: Optional[str] = None
    willing_to_relocate: bool = False


class UserProfile(BaseModel):
    personal_info: Optional[PersonalInfo] = None
    education: List[Education] = []
    work_experience: List[WorkExperience] = []
    skills: Skills = Skills()
    projects: List[Project] = []
    additional_info: AdditionalInfo = AdditionalInfo()
    job_preferences: JobPreferences = JobPreferences()
