"""Notes loader service for scanning and loading Obsidian notes."""

from pathlib import Path
from typing import Iterator

from app.models.note import ObsidianNote
from app.services.notes.parser import NoteParser


class NotesLoader:
    """Loads and manages Obsidian notes from the filesystem."""

    # Directories to skip
    SKIP_DIRS = {
        ".obsidian",
        ".smart-connections",
        ".smart-env",
        ".trash",
        ".git",
        "img",
        "img-old",
        "smart-chats",
    }

    # Files to skip (by extension or pattern)
    SKIP_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".svg", ".webp"}

    def __init__(self, notes_path: Path):
        """Initialize loader with notes directory.

        Args:
            notes_path: Root directory containing Obsidian notes
        """
        self.notes_path = notes_path
        self.parser = NoteParser(notes_path)

    def scan_notes(self) -> Iterator[Path]:
        """Scan for all markdown files in the notes directory.

        Yields:
            Paths to markdown files
        """
        for path in self.notes_path.rglob("*.md"):
            # Skip directories
            if any(skip_dir in path.parts for skip_dir in self.SKIP_DIRS):
                continue

            # Skip hidden files
            if path.name.startswith("."):
                continue

            # Skip empty files
            if path.stat().st_size == 0:
                continue

            yield path

    def load_all_notes(self) -> list[ObsidianNote]:
        """Load all notes from the directory.

        Returns:
            List of parsed ObsidianNote objects
        """
        notes: list[ObsidianNote] = []
        for path in self.scan_notes():
            try:
                note = self.parser.parse_file(path)
                notes.append(note)
            except Exception as e:
                # Log but don't fail on individual file errors
                print(f"Warning: Failed to parse {path}: {e}")
                continue
        return notes

    def load_note(self, relative_path: str) -> ObsidianNote | None:
        """Load a single note by its relative path.

        Args:
            relative_path: Path relative to notes root

        Returns:
            Parsed note or None if not found
        """
        full_path = self.notes_path / relative_path
        if not full_path.exists() or not full_path.is_file():
            return None
        return self.parser.parse_file(full_path)

    def get_folders(self) -> list[str]:
        """Get all folder paths in the notes directory (including subfolders).

        Returns:
            List of folder paths relative to notes root
        """
        folders: set[str] = set()

        for path in self.notes_path.rglob("*"):
            if not path.is_dir():
                continue

            # Skip hidden and system directories
            if any(skip_dir in path.parts for skip_dir in self.SKIP_DIRS):
                continue
            if path.name.startswith("."):
                continue

            # Get relative path
            relative = path.relative_to(self.notes_path)
            folders.add(str(relative))

        return sorted(folders)

    def get_note_count(self) -> int:
        """Get total number of markdown notes.

        Returns:
            Count of notes
        """
        return sum(1 for _ in self.scan_notes())

    def get_notes_by_folder(self, folder: str) -> list[ObsidianNote]:
        """Get all notes in a specific folder.

        Args:
            folder: Folder name

        Returns:
            List of notes in that folder
        """
        folder_path = self.notes_path / folder
        if not folder_path.exists():
            return []

        notes: list[ObsidianNote] = []
        for path in folder_path.rglob("*.md"):
            if any(skip_dir in path.parts for skip_dir in self.SKIP_DIRS):
                continue
            if path.name.startswith("."):
                continue
            if path.stat().st_size == 0:
                continue
            try:
                note = self.parser.parse_file(path)
                notes.append(note)
            except Exception:
                continue
        return notes
