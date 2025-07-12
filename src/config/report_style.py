from enum import Enum


class ReportStyle(Enum):
    """
    Enumeration of available report writing styles.

    This enum defines the different writing styles that can be used
    when generating reports, each optimized for specific audiences
    and contexts.

    Attributes:
        ACADEMIC: Formal, research-oriented style with citations and technical language
        POPULAR_SCIENCE: Accessible scientific writing for general audiences
        NEWS: Journalistic style with clear, concise reporting
        SOCIAL_MEDIA: Brief, engaging format optimized for social platforms

    Example:
        >>> style = ReportStyle.ACADEMIC
        >>> print(style.value)
        'academic'
        >>> print(str(style))
        'Academic Report Style'
    """

    ACADEMIC = "academic"
    POPULAR_SCIENCE = "popular_science"
    NEWS = "news"
    SOCIAL_MEDIA = "social_media"

    def __str__(self) -> str:
        """
        Return a human-readable string representation of the report style.

        Returns:
            str: Formatted display name of the report style
        """
        # Convert enum name to title case with spaces
        return self.name.replace("_", " ").title() + " Report Style"

    @classmethod
    def get_all_styles(cls) -> list["ReportStyle"]:
        """
        Get a list of all available report styles.

        Returns:
            list[ReportStyle]: List containing all report style enum values
        """
        return list(cls)

    @classmethod
    def from_string(cls, style_str: str) -> "ReportStyle":
        """
        Create a ReportStyle from a string value.

        Args:
            style_str (str): String representation of the style

        Returns:
            ReportStyle: Corresponding enum value

        Raises:
            ValueError: If the style string is not recognized
        """
        # Handle case-insensitive lookup
        style_str = style_str.lower().strip()

        for style in cls:
            if style.value == style_str:
                return style

        # If direct match fails, try mapping common variations
        style_mapping = {
            "academic": cls.ACADEMIC,
            "scientific": cls.ACADEMIC,
            "research": cls.ACADEMIC,
            "popular": cls.POPULAR_SCIENCE,
            "science": cls.POPULAR_SCIENCE,
            "news": cls.NEWS,
            "journalism": cls.NEWS,
            "article": cls.NEWS,
            "social": cls.SOCIAL_MEDIA,
            "media": cls.SOCIAL_MEDIA,
            "twitter": cls.SOCIAL_MEDIA,
            "facebook": cls.SOCIAL_MEDIA,
        }

        if style_str in style_mapping:
            return style_mapping[style_str]

        # Raise error with helpful message
        valid_styles = [style.value for style in cls]
        raise ValueError(
            f"Unknown report style: '{style_str}'. "
            f"Valid styles are: {', '.join(valid_styles)}"
        )
