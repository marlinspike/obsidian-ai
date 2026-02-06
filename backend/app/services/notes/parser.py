"""Markdown note parser for Obsidian notes."""

import re
from datetime import date, datetime
from pathlib import Path

import frontmatter
from markdown_it import MarkdownIt

from app.models.note import NoteChunk, ObsidianNote


class NoteParser:
    """Parses Obsidian markdown notes into structured data."""

    # Regex patterns
    WIKILINK_PATTERN = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
    TAG_PATTERN = re.compile(r"(?:^|\s)#([a-zA-Z][a-zA-Z0-9_/-]*)")
    DATE_PATTERNS = [
        re.compile(r"\b(\d{4}-\d{2}-\d{2})\b"),  # YYYY-MM-DD
        re.compile(r"\bDate:\s*(\d{4}-\d{2}-\d{2})\b", re.IGNORECASE),
    ]
    HEADER_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

    # Pattern for entry delimiter: horizontal rule followed by frontmatter-like content
    # Matches: ------ or more dashes, followed by newline and Key: Value pairs
    ENTRY_DELIMITER_PATTERN = re.compile(
        r"(?:^|\n)(-{3,})\s*\n((?:[A-Za-z_][A-Za-z0-9_]*:\s*[^\n]*\n?)+)",
        re.MULTILINE
    )

    # Pattern for inline frontmatter fields (Key: Value format)
    INLINE_FRONTMATTER_PATTERN = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", re.MULTILINE)

    def __init__(self, notes_root: Path):
        """Initialize parser with notes root directory.

        Args:
            notes_root: Root directory containing Obsidian notes
        """
        self.notes_root = notes_root
        self.md = MarkdownIt()

    def parse_file(self, file_path: Path) -> ObsidianNote:
        """Parse a markdown file into an ObsidianNote.

        Args:
            file_path: Path to the markdown file

        Returns:
            Parsed ObsidianNote
        """
        content = file_path.read_text(encoding="utf-8")
        relative_path = str(file_path.relative_to(self.notes_root))

        # Parse frontmatter
        post = frontmatter.loads(content)
        fm = dict(post.metadata) if post.metadata else {}
        body = post.content

        # Extract components
        title = self._extract_title(file_path, body, fm)
        headers = self._extract_headers(body)
        links = self._extract_links(body)
        tags = self._extract_tags(body, fm)
        dates = self._extract_dates(body, fm)
        people = self._extract_people(body)
        folder = self._extract_folder(relative_path)

        return ObsidianNote(
            path=relative_path,
            title=title,
            content=body,
            headers=headers,
            links=links,
            tags=tags,
            dates=dates,
            people=people,
            folder=folder,
            last_modified=datetime.fromtimestamp(file_path.stat().st_mtime),
            frontmatter=fm,
        )

    def chunk_note(
        self,
        note: ObsidianNote,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> list[NoteChunk]:
        """Split a note into overlapping chunks for embedding.

        Handles notes with multiple entries separated by horizontal rules
        followed by inline frontmatter (Date:, Title:, People:, etc.).

        Args:
            note: The note to chunk
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks

        Returns:
            List of NoteChunks
        """
        chunks: list[NoteChunk] = []
        chunk_index = 0

        # First, split by entries (horizontal rule + frontmatter delimiter)
        entries = self._split_by_entries(note.content)

        for entry_metadata, entry_content in entries:
            # Build context string from entry metadata
            entry_context = self._format_entry_context(entry_metadata)

            # Split entry by headers
            sections = self._split_by_headers(entry_content)

            for header, section_content in sections:
                # Combine entry context with header
                full_context = entry_context
                if header:
                    full_context = f"{entry_context} > {header}" if entry_context else header

                # If section is small enough, use as-is
                if len(section_content) <= chunk_size:
                    if section_content.strip():
                        chunks.append(
                            NoteChunk(
                                note_path=note.path,
                                chunk_index=chunk_index,
                                content=section_content.strip(),
                                header_context=full_context,
                                folder=note.folder,
                            )
                        )
                        chunk_index += 1
                else:
                    # Split large sections into overlapping chunks
                    section_chunks = self._split_text(section_content, chunk_size, chunk_overlap)
                    for text in section_chunks:
                        if text.strip():
                            chunks.append(
                                NoteChunk(
                                    note_path=note.path,
                                    chunk_index=chunk_index,
                                    content=text.strip(),
                                    header_context=full_context,
                                    folder=note.folder,
                                )
                            )
                            chunk_index += 1

        return chunks

    def _split_by_entries(self, content: str) -> list[tuple[dict[str, str], str]]:
        """Split content by entry delimiters (horizontal rule + inline frontmatter).

        Each entry starts with a horizontal rule (---) followed by metadata lines
        like Date:, Title:, People:, Group:, etc.

        Args:
            content: The full note content

        Returns:
            List of (metadata_dict, entry_content) tuples
        """
        entries: list[tuple[dict[str, str], str]] = []

        # Find all entry delimiters
        delimiter_matches = list(self.ENTRY_DELIMITER_PATTERN.finditer(content))

        if not delimiter_matches:
            # No entry delimiters found, treat entire content as single entry
            # Check if there's frontmatter-style content at the very beginning
            first_metadata = self._extract_inline_frontmatter(content[:500])
            return [(first_metadata, content)]

        # Handle content before first delimiter (initial entry with file frontmatter)
        first_delim_start = delimiter_matches[0].start()
        if first_delim_start > 0:
            initial_content = content[:first_delim_start].strip()
            if initial_content:
                # Extract any inline frontmatter from the beginning
                initial_metadata = self._extract_inline_frontmatter(initial_content[:500])
                entries.append((initial_metadata, initial_content))

        # Process each entry delimiter
        for i, match in enumerate(delimiter_matches):
            # Extract the frontmatter block from the delimiter match
            frontmatter_block = match.group(2)
            metadata = self._extract_inline_frontmatter(frontmatter_block)

            # Get content after this delimiter until next delimiter or end
            content_start = match.end()
            if i + 1 < len(delimiter_matches):
                content_end = delimiter_matches[i + 1].start()
            else:
                content_end = len(content)

            entry_content = content[content_start:content_end].strip()
            if entry_content or metadata:
                entries.append((metadata, entry_content))

        return entries if entries else [({}), content]

    def _extract_inline_frontmatter(self, text: str) -> dict[str, str]:
        """Extract Key: Value pairs from inline frontmatter.

        Only extracts lines that look like metadata (Key: Value format)
        and stops when encountering non-metadata content.

        Args:
            text: Text that may contain inline frontmatter

        Returns:
            Dictionary of extracted key-value pairs
        """
        metadata: dict[str, str] = {}

        # Process line by line, stopping when we hit non-frontmatter content
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue

            match = self.INLINE_FRONTMATTER_PATTERN.match(line)
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                if value:  # Only include non-empty values
                    metadata[key] = value
            elif metadata:
                # We've started seeing frontmatter but hit a non-frontmatter line
                # Stop processing (we're now in content)
                break

        return metadata

    def _format_entry_context(self, metadata: dict[str, str]) -> str:
        """Format entry metadata into a context string.

        Args:
            metadata: Dictionary of entry metadata

        Returns:
            Formatted context string (e.g., "2026-02-06 | People: John, Jane")
        """
        parts: list[str] = []

        # Date is most important - put first
        if "Date" in metadata:
            parts.append(metadata["Date"])

        # Title if present
        if "Title" in metadata:
            parts.append(metadata["Title"])

        # People if present
        if "People" in metadata:
            parts.append(f"People: {metadata['People']}")

        # Group if present
        if "Group" in metadata:
            parts.append(f"Group: {metadata['Group']}")

        return " | ".join(parts)

    def _extract_title(
        self, file_path: Path, content: str, frontmatter: dict[str, str | list[str] | None]
    ) -> str:
        """Extract title from frontmatter, H1, or filename."""
        # Try frontmatter title
        if "title" in frontmatter:
            title = frontmatter["title"]
            if isinstance(title, str):
                return title

        # Try first H1
        h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()

        # Fall back to filename
        return file_path.stem

    def _extract_headers(self, content: str) -> list[str]:
        """Extract all headers from content."""
        matches = self.HEADER_PATTERN.findall(content)
        return [match[1].strip() for match in matches]

    def _extract_links(self, content: str) -> list[str]:
        """Extract [[wiki-style]] links."""
        return list(set(self.WIKILINK_PATTERN.findall(content)))

    def _extract_tags(
        self, content: str, frontmatter: dict[str, str | list[str] | None]
    ) -> list[str]:
        """Extract tags from content and frontmatter."""
        tags = set()

        # Tags from content
        tags.update(self.TAG_PATTERN.findall(content))

        # Tags from frontmatter
        if "tags" in frontmatter:
            fm_tags = frontmatter["tags"]
            if isinstance(fm_tags, list):
                tags.update(str(t) for t in fm_tags)
            elif isinstance(fm_tags, str):
                tags.add(fm_tags)

        return list(tags)

    def _extract_dates(
        self, content: str, frontmatter: dict[str, str | list[str] | None]
    ) -> list[date]:
        """Extract dates from content and frontmatter.

        Handles:
        - YAML frontmatter date field
        - Inline Date: fields (common in entry delimiters)
        - ISO dates in content (YYYY-MM-DD)
        """
        dates: set[date] = set()

        # From YAML frontmatter
        if "date" in frontmatter:
            fm_date = frontmatter["date"]
            if isinstance(fm_date, str):
                try:
                    dates.add(date.fromisoformat(fm_date))
                except ValueError:
                    pass
        if "Date" in frontmatter:
            fm_date = frontmatter["Date"]
            if isinstance(fm_date, str):
                try:
                    dates.add(date.fromisoformat(fm_date))
                except ValueError:
                    pass

        # From content (including inline Date: fields)
        for pattern in self.DATE_PATTERNS:
            for match in pattern.findall(content):
                try:
                    dates.add(date.fromisoformat(match))
                except ValueError:
                    pass

        return sorted(dates)

    # Common frontmatter/metadata field names to exclude from people detection
    FRONTMATTER_FIELDS = {
        "Date", "Title", "People", "Group", "Tags", "Type", "Status",
        "Created", "Modified", "Updated", "Author", "Category", "Project",
        "Priority", "Due", "Start", "End", "Location", "Summary", "Description",
    }

    def _extract_people(self, content: str) -> list[str]:
        """Extract likely person names from content.

        This is a simple heuristic - looks for capitalized words
        after common patterns like "with", "from", etc.
        Also extracts from People: frontmatter fields within entries.
        """
        people: set[str] = set()

        # Pattern: "People: Name1, Name2, Name3" in inline frontmatter
        people_field = re.compile(r"^People:\s*(.+)$", re.MULTILINE)
        for match in people_field.findall(content):
            # Split by comma and clean up each name
            for name in match.split(","):
                name = name.strip()
                if name and name not in self.FRONTMATTER_FIELDS:
                    people.add(name)

        # Pattern: "Name Name: " at start of line (common in meeting notes)
        # Excludes common frontmatter field names
        name_colon = re.compile(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*):(?:\s|$)", re.MULTILINE)
        for name in name_colon.findall(content):
            if name not in self.FRONTMATTER_FIELDS:
                people.add(name)

        # Pattern: "with Name Name" or "from Name Name"
        with_pattern = re.compile(r"\b(?:with|from|by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b")
        for name in with_pattern.findall(content):
            if name not in self.FRONTMATTER_FIELDS:
                people.add(name)

        return list(people)

    def _extract_folder(self, relative_path: str) -> str:
        """Extract folder path from note path (excludes the filename)."""
        parts = relative_path.split("/")
        if len(parts) > 1:
            # Return full folder path (all parts except the filename)
            return "/".join(parts[:-1])
        return ""

    def _split_by_headers(self, content: str) -> list[tuple[str, str]]:
        """Split content by headers, returning (header, content) pairs."""
        sections: list[tuple[str, str]] = []

        # Find all headers
        header_matches = list(self.HEADER_PATTERN.finditer(content))

        if not header_matches:
            # No headers, return entire content
            return [("", content)]

        # Content before first header
        first_header_start = header_matches[0].start()
        if first_header_start > 0:
            preamble = content[:first_header_start].strip()
            if preamble:
                sections.append(("", preamble))

        # Content for each header
        for i, match in enumerate(header_matches):
            header = match.group(2).strip()
            start = match.end()
            end = header_matches[i + 1].start() if i + 1 < len(header_matches) else len(content)
            section_content = content[start:end].strip()
            if section_content:
                sections.append((header, section_content))

        return sections

    def _split_text(self, text: str, chunk_size: int, overlap: int) -> list[str]:
        """Split text into overlapping chunks."""
        chunks: list[str] = []

        if len(text) <= chunk_size:
            return [text]

        start = 0
        while start < len(text):
            end = start + chunk_size

            # Try to break at a sentence or paragraph boundary
            if end < len(text):
                # Look for paragraph break
                para_break = text.rfind("\n\n", start, end)
                if para_break > start + chunk_size // 2:
                    end = para_break
                else:
                    # Look for sentence break
                    sentence_break = max(
                        text.rfind(". ", start, end),
                        text.rfind("! ", start, end),
                        text.rfind("? ", start, end),
                    )
                    if sentence_break > start + chunk_size // 2:
                        end = sentence_break + 1

            chunks.append(text[start:end])
            start = end - overlap

            # Avoid tiny final chunks
            if len(text) - start < overlap:
                break

        return chunks
