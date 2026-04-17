"""Utilities for parsing and normalising Bible references."""

import re

from bibleverseparser import (
    ParsedReference,
)
from bibleverseparser.parsing import (
    bible_reference_parser_for_lang,
    normalize_reference_input,
)

_parser = bible_reference_parser_for_lang("en", strict=False)

# Abbreviation map: abbreviations used in sources -> full book names.
# Only needed for abbreviations that the non-strict parser doesn't handle correctly.
_ABBREVIATIONS = {
    "Deu": "Deuteronomy",
    "Eccl": "Ecclesiastes",
    # "Psa" -> already works, "Gen" -> already works, etc.
}

# Build regex for abbreviation replacement (case-insensitive, word boundary)
_ABBREV_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in sorted(_ABBREVIATIONS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)


def _expand_abbreviations(text: str) -> str:
    """Expand known abbreviations to full book names."""
    def _replace(m):
        key = m.group(0)
        # Try exact match first, then case-insensitive
        if key in _ABBREVIATIONS:
            return _ABBREVIATIONS[key]
        for k, v in _ABBREVIATIONS.items():
            if k.lower() == key.lower():
                return v
        return key
    return _ABBREV_PATTERN.sub(_replace, text)


def _fix_single_chapter_book(ref: ParsedReference) -> ParsedReference:
    """Fix references to single-chapter books.

    The parser may interpret 'Jude 9' as chapter 9 (no verse) instead of chapter 1 verse 9.
    For single-chapter books, if start_verse is None, reinterpret start_chapter as start_verse.
    """
    if ref.book_info.chapter_count == 1 and ref.start_verse is None and ref.start_chapter is not None:
        return ParsedReference(
            language_code=ref.language_code,
            book_name=ref.book_name,
            start_chapter=1,
            start_verse=ref.start_chapter,
            end_chapter=1,
            end_verse=ref.end_chapter if ref.end_chapter else ref.start_chapter,
        )
    return ref


def parse_reference_from_start(text: str) -> tuple[ParsedReference, str]:
    """Parse a Bible reference from the beginning of text.

    Returns (parsed_ref, remaining_text).
    """
    text = _expand_abbreviations(text.strip())
    normalized = normalize_reference_input("en", text)
    ref, remaining = _parser.parse_partial(normalized)
    # Validate that we got chapter/verse info
    if ref.start_chapter is None:
        raise ValueError(f"Parsed book only (no chapter/verse) from '{text}'")
    ref = _fix_single_chapter_book(ref)
    return ref, remaining


def expand_to_single_verses(ref: ParsedReference) -> list[str]:
    """Expand a ParsedReference (possibly a range) to a list of canonical single-verse strings."""
    return [r.canonical_form() for r in ref.to_list()]


def normalise_reference(text: str) -> list[str]:
    """Parse a reference string and return a list of canonical single-verse references."""
    ref, remaining = parse_reference_from_start(text)
    if remaining.strip():
        raise ValueError(f"Unexpected trailing text: {remaining!r} from input {text!r}")
    return expand_to_single_verses(ref)


def normalise_reference_from_start(text: str) -> list[str]:
    """Parse a reference from the start of text and return canonical single-verse references."""
    ref, _ = parse_reference_from_start(text)
    return expand_to_single_verses(ref)
