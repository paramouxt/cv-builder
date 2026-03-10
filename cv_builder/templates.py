"""CV template style definitions for the PDF generator."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FontConfig:
    family: str = "Helvetica"
    size_name: int = 22
    size_section: int = 13
    size_body: int = 10
    size_small: int = 9


@dataclass
class ColorConfig:
    # RGB tuples
    primary: tuple = (30, 64, 175)      # deep blue
    secondary: tuple = (75, 85, 99)     # grey
    text: tuple = (17, 24, 39)          # near-black
    light: tuple = (243, 244, 246)      # very light grey
    white: tuple = (255, 255, 255)
    accent: tuple = (59, 130, 246)      # lighter blue for rules


@dataclass
class MarginConfig:
    left: float = 15.0
    right: float = 15.0
    top: float = 15.0
    bottom: float = 15.0


@dataclass
class CVTemplate:
    name: str = "Modern"
    fonts: FontConfig = field(default_factory=FontConfig)
    colors: ColorConfig = field(default_factory=ColorConfig)
    margins: MarginConfig = field(default_factory=MarginConfig)
    line_height: float = 6.0
    section_spacing: float = 4.0


# Available templates
MODERN_TEMPLATE = CVTemplate(name="Modern")
