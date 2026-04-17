"""Utilities for parsing and normalising Bible references."""

from bibleverseparser import (
    ParsedReference,
)
from bibleverseparser.parsing import (
    bible_reference_parser_for_lang,
    normalize_reference_input,
)

_parser = bible_reference_parser_for_lang("en", strict=False)


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
    normalized = normalize_reference_input("en", text.strip())
    ref, remaining = _parser.parse_partial(normalized)
    # Validate that we got chapter/verse info
    if ref.start_chapter is None:
        raise ValueError(f"Parsed book only (no chapter/verse) from '{text}'")
    ref = _fix_single_chapter_book(ref)
    return ref, remaining


def expand_to_single_verses(ref: ParsedReference) -> list[str]:
    """Expand a ParsedReference (possibly a range) to a list of canonical single-verse strings."""
    return [r.canonical_form() for r in ref.to_list()]


def to_range_string(ref: ParsedReference) -> str:
    """Return the canonical form of a reference, preserving ranges."""
    return ref.canonical_form()


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


def range_reference(text: str) -> str:
    """Parse a reference string and return a single canonical range string."""
    ref, remaining = parse_reference_from_start(text)
    if remaining.strip():
        raise ValueError(f"Unexpected trailing text: {remaining!r} from input {text!r}")
    return to_range_string(ref)


def range_reference_from_start(text: str) -> str:
    """Parse a reference from the start of text and return a canonical range string."""
    ref, _ = parse_reference_from_start(text)
    return to_range_string(ref)
