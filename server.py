import asyncio
import logging
import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastmcp import FastMCP
from notebooklm import NotebookLMClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

PROJECT_DIR = Path(__file__).parent.resolve()
COOKIE_IMPORT_SCRIPT = PROJECT_DIR / "scripts" / "import_chrome_cookies.py"

_client = None
_client_context = None
_client_lock = asyncio.Lock()


async def _refresh_cookies_from_chrome():
    """Re-import cookies from Chrome → ~/.notebooklm/storage_state.json."""
    if not COOKIE_IMPORT_SCRIPT.exists():
        logger.warning(f"Cookie refresh script not found: {COOKIE_IMPORT_SCRIPT}")
        return False
    logger.info("Refreshing cookies from Chrome...")
    proc = await asyncio.create_subprocess_exec(
        sys.executable, str(COOKIE_IMPORT_SCRIPT),
        cwd=str(PROJECT_DIR),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    ok = proc.returncode == 0
    if ok:
        logger.info("Cookies refreshed.")
    else:
        logger.error(f"Cookie refresh failed (code {proc.returncode}): {err.decode()[:500]}")
    return ok


async def _build_client():
    """Create + enter NotebookLMClient context."""
    cli = await NotebookLMClient.from_storage()
    ctx = await cli.__aenter__()
    return cli, ctx


async def _close_client_silently():
    global _client, _client_context
    if _client is not None:
        try:
            await _client.__aexit__(None, None, None)
        except Exception as e:
            logger.warning(f"Error closing stale client: {e}")
    _client = None
    _client_context = None


@asynccontextmanager
async def lifespan(_app):
    """Lazy init — DO NOT crash server if auth fails. Client built on first call."""
    logger.info("NotebookLM MCP server starting (lazy auth — client built on first tool call).")
    try:
        yield
    finally:
        await _close_client_silently()


mcp = FastMCP("NotebookLM", lifespan=lifespan)


async def get_client():
    """Lazy + auto-refresh: build client on first call, refresh cookies on auth failure."""
    global _client, _client_context
    async with _client_lock:
        if _client is not None:
            return _client
        # First attempt with current storage_state.json
        try:
            _client, _client_context = await _build_client()
            logger.info("NotebookLM client initialized.")
            return _client
        except Exception as e:
            logger.warning(f"Initial auth failed: {e}. Refreshing cookies from Chrome...")
            await _close_client_silently()
        # Refresh cookies + retry once
        await _refresh_cookies_from_chrome()
        _client, _client_context = await _build_client()
        logger.info("NotebookLM client initialized after cookie refresh.")
        return _client


async def call_with_retry(fn):
    """Run fn(client). On auth-like failure, drop client + refresh cookies + retry once."""
    global _client, _client_context
    try:
        client = await get_client()
        return await fn(client)
    except Exception as e:
        msg = str(e).lower()
        is_auth = any(x in msg for x in ("auth", "expired", "401", "403", "redirect", "signin", "login"))
        if not is_auth:
            raise
        logger.warning(f"Auth-like error, refreshing: {e}")
        await _close_client_silently()
        await _refresh_cookies_from_chrome()
        client = await get_client()
        return await fn(client)


@mcp.tool()
async def list_notebooks():
    """List all notebooks in your NotebookLM account."""
    async def _do(c):
        nbs = await c.notebooks.list()
        return [{"id": nb.id, "title": nb.title, "sources_count": nb.sources_count} for nb in nbs]
    return await call_with_retry(_do)


@mcp.tool()
async def create_notebook(title: str):
    """Create a new notebook with the given title."""
    async def _do(c):
        nb = await c.notebooks.create(title)
        return {"id": nb.id, "title": nb.title}
    return await call_with_retry(_do)


@mcp.tool()
async def add_source_url(notebook_id: str, url: str):
    """Add a website URL as a source to a notebook."""
    async def _do(c):
        s = await c.sources.add_url(notebook_id, url)
        return {"id": s.id, "title": s.title}
    return await call_with_retry(_do)


@mcp.tool()
async def add_source_text(notebook_id: str, title: str, text: str):
    """Add raw text as a source to a notebook."""
    async def _do(c):
        s = await c.sources.add_text(notebook_id, title, text)
        return {"id": s.id, "title": s.title}
    return await call_with_retry(_do)


@mcp.tool()
async def add_source_file(notebook_id: str, file_path: str, mime_type: str | None = None):
    """Add a local file (PDF, DOCX, TXT, MD, etc.) as a source. file_path is absolute or ~-relative."""
    async def _do(c):
        from pathlib import Path
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        s = await c.sources.add_file(notebook_id, path, mime_type=mime_type)
        return {"id": s.id, "title": s.title, "path": str(path)}
    return await call_with_retry(_do)


@mcp.tool()
async def add_source_drive(notebook_id: str, file_id: str, title: str, mime_type: str = "application/vnd.google-apps.document"):
    """Add a Google Drive file as a source. file_id is the Drive ID; default mime_type = Google Doc. Common types: application/pdf, application/vnd.google-apps.spreadsheet, application/vnd.google-apps.presentation."""
    async def _do(c):
        s = await c.sources.add_drive(notebook_id, file_id, title, mime_type=mime_type)
        return {"id": s.id, "title": s.title}
    return await call_with_retry(_do)


def _format_refs(refs):
    return [
        {"citation": r.citation_number, "cited_text": r.cited_text, "chunk_id": r.chunk_id}
        for r in (refs or [])
    ]


@mcp.tool()
async def ask_notebook(notebook_id: str, question: str):
    """Ask a question based on the sources in a specific notebook."""
    async def _do(c):
        r = await c.chat.ask(notebook_id, question)
        return {
            "answer": r.answer,
            "conversation_id": r.conversation_id,
            "references": _format_refs(r.references),
        }
    return await call_with_retry(_do)


@mcp.tool()
async def get_notebook_summary(notebook_id: str):
    """Get the summary and key insights of a notebook."""
    async def _do(c):
        r = await c.chat.ask(notebook_id, "Please provide a comprehensive summary and key insights of this notebook.")
        return {"summary": r.answer, "references": _format_refs(r.references)}
    return await call_with_retry(_do)


@mcp.tool()
async def generate_video_overview(notebook_id: str, instructions: str = "Create an engaging video overview of these sources."):
    """Generate a Video Overview artifact in NotebookLM."""
    async def _do(c):
        s = await c.artifacts.generate_video(notebook_id, instructions=instructions)
        return {"task_id": s.task_id, "status": "Task started. Check NotebookLM studio."}
    return await call_with_retry(_do)


@mcp.tool()
async def generate_audio_overview(notebook_id: str, instructions: str = "Create a deep dive podcast-style overview."):
    """Generate an Audio Overview (Deep Dive podcast) in NotebookLM."""
    async def _do(c):
        s = await c.artifacts.generate_audio(notebook_id, instructions=instructions)
        return {"task_id": s.task_id, "status": "Task started. Check NotebookLM studio."}
    return await call_with_retry(_do)


@mcp.tool()
async def generate_slide_deck(notebook_id: str, instructions: str = "Create a comprehensive slide deck."):
    """Generate a Slide Deck (PowerPoint style) in NotebookLM."""
    async def _do(c):
        s = await c.artifacts.generate_slide_deck(notebook_id, instructions=instructions)
        return {"task_id": s.task_id, "status": "Task started. Check NotebookLM studio."}
    return await call_with_retry(_do)


@mcp.tool()
async def generate_mind_map(notebook_id: str):
    """Generate an interactive Mind Map in NotebookLM (saved as a note)."""
    async def _do(c):
        r = await c.artifacts.generate_mind_map(notebook_id)
        return {"note_id": r.get("note_id"), "status": "Mind map generated and saved to notes."}
    return await call_with_retry(_do)


@mcp.tool()
async def generate_infographic(
    notebook_id: str,
    instructions: str = "Create an informative infographic.",
    language: str = "pl",
    orientation: str = "LANDSCAPE",
    detail_level: str = "STANDARD",
):
    """Generate an Infographic in NotebookLM. orientation: LANDSCAPE | PORTRAIT | SQUARE. detail_level: CONCISE | STANDARD | DETAILED."""
    async def _do(c):
        from notebooklm.types import InfographicOrientation, InfographicDetail
        o = InfographicOrientation[orientation.upper()]
        d = InfographicDetail[detail_level.upper()]
        s = await c.artifacts.generate_infographic(
            notebook_id, instructions=instructions, language=language,
            orientation=o, detail_level=d,
        )
        if not s.task_id:
            return {"task_id": "", "status": "failed", "error": s.error or "no artifact_id returned"}
        return {"task_id": s.task_id, "status": "Task started. Check NotebookLM studio."}
    return await call_with_retry(_do)


@mcp.tool()
async def generate_quiz(notebook_id: str, instructions: str = "Create a quiz based on these sources."):
    """Generate a Quiz in NotebookLM."""
    async def _do(c):
        s = await c.artifacts.generate_quiz(notebook_id, instructions=instructions)
        return {"task_id": s.task_id, "status": "Task started. Check NotebookLM studio."}
    return await call_with_retry(_do)


@mcp.tool()
async def generate_flashcards(notebook_id: str, instructions: str = "Create study flashcards."):
    """Generate Flashcards in NotebookLM."""
    async def _do(c):
        s = await c.artifacts.generate_flashcards(notebook_id, instructions=instructions)
        return {"task_id": s.task_id, "status": "Task started. Check NotebookLM studio."}
    return await call_with_retry(_do)


@mcp.tool()
async def generate_summary_report(notebook_id: str, instructions: str = "Create a briefing document."):
    """Generate a Summary Report (Briefing Doc) in NotebookLM."""
    async def _do(c):
        s = await c.artifacts.generate_report(notebook_id, custom_prompt=instructions)
        return {"task_id": s.task_id, "status": "Task started. Check NotebookLM studio."}
    return await call_with_retry(_do)


@mcp.tool()
async def generate_data_table(notebook_id: str, instructions: str = "Extract key data into a table."):
    """Generate a Data Table artifact in NotebookLM."""
    async def _do(c):
        s = await c.artifacts.generate_data_table(notebook_id, instructions=instructions)
        return {"task_id": s.task_id, "status": "Task started. Check NotebookLM studio."}
    return await call_with_retry(_do)


# =====================================================================
# Wait + download artifacts (v1.0)
# =====================================================================

@mcp.tool()
async def wait_for_completion(notebook_id: str, task_id: str, timeout_seconds: float = 300.0):
    """Block until artifact generation finishes (or timeout). Returns final status."""
    async def _do(c):
        s = await c.artifacts.wait_for_completion(notebook_id, task_id, timeout=timeout_seconds)
        return {"task_id": task_id, "status": s.status, "url": s.url, "error": s.error}
    return await call_with_retry(_do)


def _expand(path: str) -> str:
    from pathlib import Path
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = (Path.home() / "Desktop" / p.name).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    return str(p)


@mcp.tool()
async def download_infographic(notebook_id: str, output_path: str, artifact_id: str | None = None):
    """Download an infographic artifact as PNG to output_path."""
    async def _do(c):
        path = await c.artifacts.download_infographic(notebook_id, _expand(output_path), artifact_id)
        return {"path": path}
    return await call_with_retry(_do)


@mcp.tool()
async def download_audio(notebook_id: str, output_path: str, artifact_id: str | None = None):
    """Download an Audio Overview (podcast) as MP3 to output_path."""
    async def _do(c):
        path = await c.artifacts.download_audio(notebook_id, _expand(output_path), artifact_id)
        return {"path": path}
    return await call_with_retry(_do)


@mcp.tool()
async def download_video(notebook_id: str, output_path: str, artifact_id: str | None = None):
    """Download a Video Overview as MP4 to output_path."""
    async def _do(c):
        path = await c.artifacts.download_video(notebook_id, _expand(output_path), artifact_id)
        return {"path": path}
    return await call_with_retry(_do)


@mcp.tool()
async def download_slide_deck(notebook_id: str, output_path: str, artifact_id: str | None = None):
    """Download a Slide Deck as PPTX/PDF to output_path."""
    async def _do(c):
        path = await c.artifacts.download_slide_deck(notebook_id, _expand(output_path), artifact_id)
        return {"path": path}
    return await call_with_retry(_do)


@mcp.tool()
async def download_mind_map(notebook_id: str, output_path: str, artifact_id: str | None = None):
    """Download a Mind Map (JSON structure) to output_path."""
    async def _do(c):
        path = await c.artifacts.download_mind_map(notebook_id, _expand(output_path), artifact_id)
        return {"path": path}
    return await call_with_retry(_do)


@mcp.tool()
async def download_quiz(notebook_id: str, output_path: str, artifact_id: str | None = None):
    """Download a Quiz to output_path."""
    async def _do(c):
        path = await c.artifacts.download_quiz(notebook_id, _expand(output_path), artifact_id)
        return {"path": path}
    return await call_with_retry(_do)


@mcp.tool()
async def download_flashcards(notebook_id: str, output_path: str, artifact_id: str | None = None):
    """Download Flashcards to output_path."""
    async def _do(c):
        path = await c.artifacts.download_flashcards(notebook_id, _expand(output_path), artifact_id)
        return {"path": path}
    return await call_with_retry(_do)


@mcp.tool()
async def download_report(notebook_id: str, output_path: str, artifact_id: str | None = None):
    """Download a Summary Report (briefing) to output_path."""
    async def _do(c):
        path = await c.artifacts.download_report(notebook_id, _expand(output_path), artifact_id)
        return {"path": path}
    return await call_with_retry(_do)


@mcp.tool()
async def download_data_table(notebook_id: str, output_path: str, artifact_id: str | None = None):
    """Download a Data Table to output_path."""
    async def _do(c):
        path = await c.artifacts.download_data_table(notebook_id, _expand(output_path), artifact_id)
        return {"path": path}
    return await call_with_retry(_do)


if __name__ == "__main__":
    mcp.run()
