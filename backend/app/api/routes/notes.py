"""Notes browsing endpoints."""

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.api.deps import ApiKeyDep, NotesLoaderDep
from app.models.note import ObsidianNote

router = APIRouter()


class NoteListItem(BaseModel):
    """Summary of a note for list views."""

    path: str
    title: str
    folder: str
    last_modified: str  # ISO format


class NoteListResponse(BaseModel):
    """Response for note list endpoint."""

    notes: list[NoteListItem]
    total: int
    offset: int
    limit: int


class FolderListResponse(BaseModel):
    """Response for folder list endpoint."""

    folders: list[str]
    total: int


@router.get("", response_model=NoteListResponse)
async def list_notes(
    _: ApiKeyDep,
    loader: NotesLoaderDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    folder: str | None = Query(default=None),
) -> NoteListResponse:
    """List all notes with pagination.

    Args:
        offset: Number of notes to skip
        limit: Maximum notes to return
        folder: Filter to specific folder

    Returns:
        Paginated list of notes
    """
    if folder:
        all_notes = loader.get_notes_by_folder(folder)
    else:
        all_notes = loader.load_all_notes()

    # Sort by last modified (newest first)
    all_notes.sort(key=lambda n: n.last_modified, reverse=True)

    # Paginate
    paginated = all_notes[offset : offset + limit]

    return NoteListResponse(
        notes=[
            NoteListItem(
                path=n.path,
                title=n.title,
                folder=n.folder,
                last_modified=n.last_modified.isoformat(),
            )
            for n in paginated
        ],
        total=len(all_notes),
        offset=offset,
        limit=limit,
    )


@router.get("/folders", response_model=FolderListResponse)
async def list_folders(
    _: ApiKeyDep,
    loader: NotesLoaderDep,
) -> FolderListResponse:
    """List all top-level folders.

    Returns:
        List of folder names
    """
    folders = loader.get_folders()
    return FolderListResponse(folders=folders, total=len(folders))


@router.get("/{path:path}", response_model=ObsidianNote)
async def get_note(
    path: str,
    _: ApiKeyDep,
    loader: NotesLoaderDep,
) -> ObsidianNote:
    """Get a single note by path.

    Args:
        path: Relative path to the note

    Returns:
        Full note content

    Raises:
        HTTPException: If note not found
    """
    note = loader.load_note(path)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note not found: {path}",
        )
    return note
