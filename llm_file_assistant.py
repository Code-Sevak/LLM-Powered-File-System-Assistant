import os
import re
from typing import List, Dict, Optional

from fs_tools import read_file, list_files, write_file, search_in_file

try:
    import openai
except Exception:
    openai = None


def _simple_intent_parser(query: str) -> Dict:
    """
    Lightweight parser that recognizes a few user intents and parameters.

    Recognizes:
      - read all resumes in the X folder
      - find resumes mentioning <skill>
      - create a summary file for <filename>
    """
    q = query.lower()
    if "read all" in q and "resume" in q:
        m = re.search(r"in the ([\w\-_/\. ]+) folder", q)
        folder = m.group(1).strip() if m else "resumes"
        return {"action": "read_all", "folder": folder}

    m = re.search(r"find resumes mentioning ([\w\+\#\- ]+)", q)
    if m:
        term = m.group(1).strip()
        return {"action": "find_skill", "term": term, "folder": "resumes"}

    m = re.search(r"create a summary file for ([\w\-_. ]+\.[a-z0-9]+)", q)
    if m:
        filename = m.group(1).strip()
        return {"action": "create_summary", "filename": filename, "folder": "resumes"}

    # fallback
    return {"action": "unknown", "query": query}


def summarize_text_with_llm(text: str, max_tokens: int = 400) -> str:
    """
    Summarize using OpenAI if API key is present, otherwise return a short heuristic summary.
    """
    if openai and os.environ.get("OPENAI_API_KEY"):
        try:
            resp = openai.ChatCompletion.create(
                model=os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo"),
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes resume content."},
                    {"role": "user", "content": f"Summarize the following resume text. Be concise and list top skills and a 2-line summary.\n\n{text[:8000]}"}
                ],
                max_tokens=max_tokens,
                temperature=0.2,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            return f"[LLM summarization failed: {e}]"

    # simple heuristic: extract lines with keywords and the top 3 longest lines
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    keywords = [l for l in lines if any(k in l.lower() for k in ["skill", "experience", "python", "java", "c++", "machine learning"]) ]
    top_lines = sorted(lines, key=lambda s: len(s), reverse=True)[:3]
    parts = []
    if keywords:
        parts.append("Detected keyword lines: " + "; ".join(keywords[:5]))
    parts.append("Top lines: " + " | ".join(top_lines))
    return "\n".join(parts)


def handle_query(query: str, use_llm_for_summary: bool = False) -> Dict:
    """
    Process a user query, choose and run tools, and return structured output.
    """
    intent = _simple_intent_parser(query)
    action = intent.get("action")

    if action == "read_all":
        folder = intent.get("folder")
        files = list_files(folder)
        results = []
        for f in files:
            rf = read_file(f["path"]) if f.get("path") else read_file(os.path.join(folder, f.get("name")))
            results.append({"file": f, "read": rf})
        return {"action": action, "folder": folder, "results": results}

    if action == "find_skill":
        term = intent.get("term")
        folder = intent.get("folder")
        matches = []
        for f in list_files(folder, extension=None):
            path = f["path"]
            s = search_in_file(path, term)
            if s.get("matches"):
                matches.append({"file": f, "matches": s["matches"]})
        return {"action": action, "term": term, "matches": matches}

    if action == "create_summary":
        folder = intent.get("folder")
        filename = intent.get("filename")
        path = os.path.join(folder, filename)
        rf = read_file(path)
        if rf.get("error"):
            return {"action": action, "error": rf.get("error")}
        content = rf.get("content") or ""
        summary = summarize_text_with_llm(content) if use_llm_for_summary else summarize_text_with_llm(content)
        out_path = os.path.join(folder, f"summary_{os.path.splitext(filename)[0]}.txt")
        w = write_file(out_path, summary)
        return {"action": action, "source": path, "summary_path": w.get("path"), "write_ok": w.get("ok"), "summary": summary}

    return {"action": "unknown", "query": query}


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("query", help="User query (e.g. 'Read all resumes in the resumes folder')")
    p.add_argument("--use-llm", action="store_true", help="Use OpenAI LLM for summarization if API key present")
    args = p.parse_args()
    out = handle_query(args.query, use_llm_for_summary=args.use_llm)
    import json
    print(json.dumps(out, indent=2))
