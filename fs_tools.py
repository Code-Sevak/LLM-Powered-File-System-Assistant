import os
from typing import List, Dict, Optional
from datetime import datetime

try:
    import importlib
    pdf_module = importlib.import_module("PyPDF2")
    PdfReader = getattr(pdf_module, "PdfReader", None)
except Exception:
    PdfReader = None

try:
    import importlib
    docx = importlib.import_module("docx")
except Exception:
    docx = None


def _file_metadata(path: str) -> Dict:
    st = os.stat(path)
    return {
        "name": os.path.basename(path),
        "path": os.path.abspath(path),
        "size": st.st_size,
        "modified": datetime.fromtimestamp(st.st_mtime).isoformat(),
    }


def read_file(filepath: str) -> Dict:
    """
    Read a resume file (PDF, TXT, DOCX) and return a dict with content and metadata.

    Returns:
      {"content": str, "metadata": {...}, "error": Optional[str]}
    """
    if not os.path.exists(filepath):
        return {"content": None, "metadata": None, "error": f"File not found: {filepath}"}

    _, ext = os.path.splitext(filepath)
    ext = ext.lower()
    metadata = _file_metadata(filepath)

    try:
        if ext == ".pdf":
            if PdfReader is None:
                return {"content": None, "metadata": metadata, "error": "PyPDF2 not installed"}
            text_parts: List[str] = []
            with open(filepath, "rb") as f:
                reader = PdfReader(f)
                for page in reader.pages:
                    try:
                        text = page.extract_text() or ""
                    except Exception:
                        # older PyPDF2 versions may raise on some pages
                        text = ""
                    text_parts.append(text)
            content = "\n".join(text_parts).strip()
            return {"content": content, "metadata": metadata, "error": None}

        elif ext in (".docx", ".doc"):
            if docx is None:
                return {"content": None, "metadata": metadata, "error": "python-docx not installed"}
            try:
                doc = docx.Document(filepath)
                paragraphs = [p.text for p in doc.paragraphs]
                content = "\n".join(paragraphs).strip()
                return {"content": content, "metadata": metadata, "error": None}
            except Exception as e:
                return {"content": None, "metadata": metadata, "error": str(e)}

        else:
            # treat as text file
            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                return {"content": content, "metadata": metadata, "error": None}
            except Exception as e:
                return {"content": None, "metadata": metadata, "error": str(e)}

    except Exception as e:
        return {"content": None, "metadata": metadata, "error": str(e)}


def list_files(directory: str, extension: Optional[str] = None) -> List[Dict]:
    """
    List all files in a directory. Optionally filter by extension (e.g., '.pdf', '.txt').

    Returns a list of metadata dicts for each file.
    """
    if not os.path.isdir(directory):
        raise FileNotFoundError(f"Not a directory: {directory}")

    ext = None
    if extension:
        ext = extension.lower()
        if not ext.startswith('.'): 
            ext = '.' + ext

    results = []
    for entry in os.scandir(directory):
        if not entry.is_file():
            continue
        if ext and os.path.splitext(entry.name)[1].lower() != ext:
            continue
        results.append(_file_metadata(entry.path))

    return results


def write_file(filepath: str, content: str) -> Dict:
    """
    Write content to file, creating directories if needed.

    Returns: {"ok": bool, "path": str, "error": Optional[str]}
    """
    try:
        dirpath = os.path.dirname(filepath)
        if dirpath and not os.path.exists(dirpath):
            os.makedirs(dirpath, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return {"ok": True, "path": os.path.abspath(filepath), "error": None}
    except Exception as e:
        return {"ok": False, "path": filepath, "error": str(e)}


def search_in_file(filepath: str, keyword: str, context_chars: int = 50) -> Dict:
    """
    Search for keyword in file content. Case-insensitive.

    Returns: {"matches": [{"start": int, "end": int, "match": str, "context": str}], "metadata": {...}, "error": Optional[str]}
    """
    res = read_file(filepath)
    if res.get("error"):
        return {"matches": [], "metadata": res.get("metadata"), "error": res.get("error")}

    content = res.get("content") or ""
    lowered = content.lower()
    term = (keyword or "").lower()
    matches = []
    if term == "":
        return {"matches": [], "metadata": res.get("metadata"), "error": "Empty keyword"}

    start = 0
    while True:
        idx = lowered.find(term, start)
        if idx == -1:
            break
        end = idx + len(term)
        before = max(0, idx - context_chars)
        after = min(len(content), end + context_chars)
        context = content[before:after]
        matches.append({"start": idx, "end": end, "match": content[idx:end], "context": context})
        start = end

    return {"matches": matches, "metadata": res.get("metadata"), "error": None}


if __name__ == "__main__":
    # quick manual test
    print("fs_tools quick test")
    import sys
    if len(sys.argv) > 1:
        path = sys.argv[1]
        print(read_file(path))
    else:
        print("Usage: python fs_tools.py <path-to-file>")
