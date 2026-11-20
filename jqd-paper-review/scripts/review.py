#!/usr/bin/env python3
"""jqd-paper-review: single entry point of the script-driven pipeline.

Usage: python review.py [--workdir DIR] <command> …
Commands: init, next, show, find, submit, status, redo, preview, finish, render.
Every command prints a status line (OK, ERROR or WARNING) first and `NEXT COMMAND:` last.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import secrets
import shutil
import sys
from pathlib import Path

if sys.version_info < (3, 10):
    print("ERROR\nPython 3.10 or newer is required; this is Python %d.%d.\n"
          "NEXT COMMAND: read references/manual-mode.md and follow only that file" % sys.version_info[:2])
    sys.exit(2)

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jqd import anon, extract, metrics, ops, refs, render, schemas, tasks, validate  # noqa: E402
from jqd import state as st  # noqa: E402
from jqd.common import (ROW_ORDER, SKILL_VERSION, Problem, clip, dump_json, errors_of,  # noqa: E402
                        page_sentences, read_json, read_text, warnings_of, write_text)

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def out(*lines):
    print("\n".join(str(x) for x in lines))


def fail(msg, fix, next_cmd):
    out("ERROR", msg, f"FIX: {fix}", f"NEXT COMMAND: {next_cmd}")
    return 1


def self_cmd(rest):
    exe = "python3" if Path(sys.executable).name.lower().startswith("python3") else "python"
    return f'{exe} "{Path(__file__).resolve()}" {rest}'


# ---------------------------------------------------------------- working directory

def find_workdir(arg):
    if arg:
        return Path(arg)
    env = os.environ.get("JQD_REVIEW_DIR")
    if env:
        return Path(env)
    if Path("state.json").is_file():
        return Path(".")
    cands = [p for p in Path(".").glob("jqd-review-*") if (p / "state.json").is_file()]
    if len(cands) == 1:
        return cands[0]
    return None


def open_run(args):
    wd = find_workdir(getattr(args, "workdir", None))
    if wd is None or not (wd / "state.json").is_file():
        fail("No working directory with a state.json was found.",
             "Pass the directory that `init` created with --workdir, or run `init` first.",
             self_cmd("--workdir <directory> next"))
        return None
    return tasks.Run(wd)


def next_line(run):
    step = st.first_open(run.state)
    if step is None:
        return "NEXT COMMAND: none. The run is complete; give the user the file path printed by `finish`."
    if step["kind"] == "finish":
        return "NEXT COMMAND: " + run.cmd("finish")
    return "NEXT COMMAND: " + run.cmd("next")


# ---------------------------------------------------------------- init

def cmd_init(args):
    run_id = secrets.token_hex(3)
    workdir = Path(args.workdir) if args.workdir else Path(f"jqd-review-{run_id}")
    if (workdir / "state.json").exists():
        return fail(f"The directory {workdir} already holds a run.",
                    "Choose another --workdir, or continue the existing run.",
                    self_cmd(f'--workdir "{workdir}" next'))
    inputs = {"manuscript": args.manuscript, "loi": args.loi, "appendix": args.appendix}
    docs, warnings = {}, []
    for name, path in inputs.items():
        if not path:
            continue
        try:
            docs[name] = extract.extract_file(path)
        except extract.ExtractError as exc:
            return fail(f"{name}: {exc.msg}", exc.fix,
                        self_cmd("init --manuscript <file> [--loi <file>] [--appendix <file>]"))
        warnings += [f"{name}: {w}" for w in docs[name]["warnings"]
                     if name == "manuscript" or "page breaks" not in w]
    ms = docs["manuscript"]
    sections = extract.detect_sections(ms["pages"])
    mt = metrics.compute(ms["pages"], sections, docs.get("appendix", {}).get("pages"))
    cand = anon.detect_candidates(ms["pages"])
    state = st.new_state(run_id, datetime.date.today().isoformat(), args.depth,
                         {k: bool(v) for k, v in inputs.items()})
    state["meta"].update(
        skill_version=SKILL_VERSION, page_offset=ms["page_offset"], synthetic_pages=ms["synthetic"],
        extraction=ms["tool"], pages={k: len(d["pages"]) for k, d in docs.items()},
        private={"input_names": [Path(p).name for p in inputs.values() if p], "emails": cand["emails"]})
    state["metrics"], state["sections"] = mt, sections
    for name, doc in docs.items():
        write_text(workdir / "text" / f"{name}.txt", extract.to_marked(doc["pages"]))
    write_text(workdir / "metrics.json", dump_json(mt))
    (workdir / "answers").mkdir(parents=True, exist_ok=True)
    (workdir / "out").mkdir(parents=True, exist_ok=True)
    st.mark(state, 0, "done", attempts=1)
    if not sections:
        warnings.append("No section headings were found; use `show --pages` instead of `show --section`.")
    state["warnings"] = [{"step": 0, "rule": "INIT", "text": w} for w in warnings]
    notes = st.advance(state)
    st.save(workdir, state)
    run = tasks.Run(workdir, state)
    out("WARNING" if warnings else "OK",
        f"Working directory: {workdir} (run {run_id}, depth {args.depth}, {st.get_plan(state)[-1]['no']} steps)",
        f"Inputs: manuscript ({len(ms['pages'])} pages, extracted with {ms['tool']})"
        + (f", LOI ({len(docs['loi']['pages'])} pages)" if "loi" in docs else ", no LOI")
        + (f", appendix ({len(docs['appendix']['pages'])} pages)" if "appendix" in docs else ", no appendix file"),
        f"Main text: {mt['words_main']} words · " + (f"abstract: {mt['abstract_words']} words" if mt['abstract_words'] else "abstract: not found") + " · "
        f"{mt['figures']} figures · {mt['tables']} tables · appendix: {mt['appendix'].replace('_', ' ')}",
        f"Headings found: {len(sections)} · possible broken cross-references: {len(mt['broken_crossrefs'])}"
        + (f" · references shown as ??: {len(mt['unresolved_markers'])}" if mt.get("unresolved_markers") else ""),
        "Page markers ⟨p.N⟩ count the pages of the file"
        + (f"; printed page = marker {ms['page_offset']:+d}." if ms["page_offset"] else "."))
    out(*[f"WARNING: {w}" for w in warnings], *notes, next_line(run))
    return 0


# ---------------------------------------------------------------- next / status / redo

def cmd_next(args):
    run = open_run(args)
    if run is None:
        return 1
    notes = st.advance(run.state)
    if notes:
        st.save(run.workdir, run.state)
    step = st.first_open(run.state)
    if step is None:
        out("OK", "All steps are done.", next_line(run))
        return 0
    out("OK", *notes, tasks.block(run, step))
    return 0


def cmd_status(args):
    run = open_run(args)
    if run is None:
        return 1
    out("OK", f"Run {run.state['meta']['run_id']} · depth {run.state['meta'].get('depth', 'full')}",
        "step | status  | attempts | title")
    for s in st.get_plan(run.state):
        entry = run.state["steps"].get(str(s["no"]), {})
        out(f"{s['no']:>4} | {entry.get('status', 'open'):<7} | {entry.get('attempts', 0):>8} | {s['title']}")
    out(next_line(run))
    return 0


def cmd_redo(args):
    run = open_run(args)
    if run is None:
        return 1
    plan = st.get_plan(run.state)
    if not 1 <= args.step < len(plan):
        return fail(f"Step {args.step} does not exist or cannot be redone.",
                    f"Use a step number from 1 to {len(plan) - 1}; see `status`.", run.cmd("status"))
    affected = st.reset(run.state, args.step)
    notes = st.advance(run.state)
    st.save(run.workdir, run.state)
    out("OK", "Reset steps: " + ", ".join(f"{n} ({plan[n]['title']})" for n in affected), *notes, next_line(run))
    return 0


# ---------------------------------------------------------------- show / find

def _doc_pages(run, doc):
    pages = run.pages(doc)
    if pages is None:
        fail(f"No {doc} text is available in this run.", "Use --doc manuscript, or pass the file to `init`.",
             run.cmd("next"))
    return pages


def cmd_show(args):
    run = open_run(args)
    if run is None:
        return 1
    pages = _doc_pages(run, args.doc)
    if pages is None:
        return 1
    n, title = len(pages), ""
    if args.section:
        sections = run.state.get("sections", []) if args.doc == "manuscript" else extract.detect_sections(pages)
        span = extract.section_span(pages, sections, args.section)
        if not span:
            heads = " | ".join(clip(h["title"], 40) for h in sections if not h["weak"])[:900]
            return fail(f"No section title contains \"{args.section}\".",
                        f"Use one of these titles, or --pages: {heads or '(no headings found)'}", run.cmd("next"))
        title, text = f"Section \"{span[0]}\"", span[2]
    elif args.figure or args.table:
        num = (args.figure or args.table).upper().replace(".", "")
        label = ("Fig " if args.figure else "Tab ") + num
        item = next((x for x in run.state["metrics"].get("items", []) if x["label"].startswith(label)), None)
        word = r"(?:Figure|Fig\.?|Abbildung|Abb\.?)" if args.figure else r"(?:Table|Tab\.?|Tabelle)"
        rx = re.compile(rf"\b{word}\s+{re.escape(num)}\b", re.I)
        parts = []
        if item:
            parts.append(f"Caption (p.{item['page']}): {item['caption']}")
        for pno, page in enumerate(pages, 1):
            sents = [x[1] for x in page_sentences(page)]
            for i, sent in enumerate(sents):
                if rx.search(sent) and not (item and sent[:60] in item["caption"]):
                    parts.append(f"⟨p.{pno}⟩ " + " ".join(sents[max(0, i - 1):i + 2]))
        if not parts:
            return fail(f"{label} was not found.", "Check the number against the figure list (`next` for step 5), "
                        "or search with `find`.", run.cmd("next"))
        title, text = label, "\n".join(parts)
    else:
        m = re.fullmatch(r"\s*(\d+)(?:\s*[-–]\s*(\d+))?\s*", args.pages or "1")
        if not m:
            return fail(f"\"{args.pages}\" is not a page range.", "Write --pages 7-9 or --pages 7.", run.cmd("next"))
        lo, hi = int(m.group(1)), int(m.group(2) or m.group(1))
        if lo > n or lo < 1:
            return fail(f"Page {lo} does not exist; the {args.doc} has {n} pages.",
                        f"Use pages from 1 to {n}.", run.cmd("next"))
        hi = min(max(hi, lo), n)
        title = f"Pages {lo}–{hi} of {n}"
        text = "\n".join(f"⟨p.{i}⟩\n{pages[i - 1]}" for i in range(lo, hi + 1))
    chunks = [text[i:i + tasks.MAX_SHOW] for i in range(0, max(len(text), 1), tasks.MAX_SHOW)]
    if not 1 <= args.part <= len(chunks):
        return fail(f"Part {args.part} does not exist; this text has {len(chunks)} part"
                    + ("s." if len(chunks) > 1 else " and was shown in full."),
                    f"Use --part 1 to {len(chunks)}, or a different --pages range." if len(chunks) > 1
                    else "Use --pages to read further.", run.cmd("next"))
    part = args.part
    out("OK", f"{title} · {args.doc}" + (f" · part {part} of {len(chunks)}" if len(chunks) > 1 else ""), chunks[part - 1])
    if part < len(chunks):
        out(f"(Text continues. Repeat the same command with --part {part + 1}.)")
    out(next_line(run).replace("NEXT COMMAND: ", "NEXT COMMAND (when you have read enough): "))
    return 0


def cmd_find(args):
    run = open_run(args)
    if run is None:
        return 1
    pages = _doc_pages(run, args.doc)
    if pages is None:
        return 1
    try:
        rx, how = re.compile(args.pattern, re.I), "regular expression, case-insensitive"
    except re.error:
        rx, how = re.compile(re.escape(args.pattern), re.I), "not a valid regular expression, searched as plain text"
    hits = []
    for pno, page in enumerate(pages, 1):
        sents = [x[1] for x in page_sentences(page)]
        for i, sent in enumerate(sents):
            if rx.search(sent):
                hits.append(f"p.{pno} · " + clip(" ".join(sents[max(0, i - 1):i + 2]), 420))
    out("OK", f"{len(hits)} hits for \"{args.pattern}\" ({how}) in the {args.doc}"
        + (" (first 20 shown)" if len(hits) > 20 else ""), *hits[:20])
    out(next_line(run).replace("NEXT COMMAND: ", "NEXT COMMAND (when you have read enough): "))
    return 0


# ---------------------------------------------------------------- submit

def load_answer(path):
    """Read an answer file. Tolerates a Markdown code fence around the JSON."""
    try:
        raw = read_text(path)
    except OSError:
        return None, Problem("V01", "", f"The answer file {path} does not exist.",
                             "Write your answer to exactly this path, then submit again.")
    raw = raw.strip()
    fence = re.match(r"^```[a-zA-Z]*\s*\n(.*?)\n```\s*$", raw, re.S)
    if fence:
        raw = fence.group(1)
    try:
        data = json.loads(raw)
    except ValueError as exc:
        return None, Problem("V01", "", f"The file is not valid JSON: {exc}.",
                             "Write one JSON object: double quotes around keys and texts, commas between entries, "
                             "no comments, no text before or after the object.")
    if not isinstance(data, dict):
        return None, Problem("V01", "", "The answer must be one JSON object { … }.", "Wrap the answer in curly braces.")
    return data, None


def check_step(run, step, ans):
    """Validate an answer. Returns (problems, extra) where extra feeds state.apply."""
    s, ctx, kind = run.state, validate.Ctx(run.docs()), step["kind"]
    if kind == "orientation":
        return validate.check_orientation(s, ans, ctx), None
    if kind == "loi":
        return validate.check_loi(s, ans, ctx), None
    if kind == "claims":
        return validate.check_claims(s, ans, ctx), None
    if kind == "data":
        return validate.check_data(s, ans, ctx), None
    if kind == "figures":
        return validate.check_figures(s, ans, ctx), None
    if kind == "row":
        return validate.check_row(s, step["rows"][0], ans, ctx), None
    if kind == "group":
        codes = [c for c in step["rows"] if not (c == "L1" and not s["meta"]["inputs"].get("loi"))]
        probs = validate.check_group(s, ans, ctx, codes)
        if "L1" in step["rows"] and "L1" not in codes:
            ans.setdefault("rows", {})["L1"] = s["rows"].get("L1")
        return probs, None
    if kind == "consistency":
        return validate.check_consistency(s, ans)
    if kind == "synthesis":
        return validate.check_synthesis_answer(s, ans), None
    if kind == "sentence":
        return validate.check_sentence(s, ans), None
    if kind == "readback":
        return validate.check_readback(s, ans)
    if kind == "inventory":
        probs = schemas.check(ans, schemas.INVENTORY)
        if errors_of(probs):
            return probs, None
        has_loi = s["meta"]["inputs"].get("loi")
        trial = json.loads(json.dumps(s))
        probs += validate.check_orientation(trial, ans["orientation"], ctx, "orientation")
        st._apply_orientation(trial, ans["orientation"])
        if has_loi and not ans.get("loi"):
            probs.append(Problem("V01", "loi", "A Letter of Inquiry was provided, but the part \"loi\" is missing.",
                                 "Add \"loi\": {\"promises\": [ … ]}."))
        elif has_loi:
            probs += validate.check_loi(trial, ans["loi"], ctx, "loi")
        elif ans.get("loi"):
            ans.pop("loi")
        probs += validate.check_claims(trial, ans["claims"], ctx, "claims")
        trial["headline_claims"] = ans["claims"].get("claims", [])
        probs += validate.check_data(trial, ans["data"], ctx, "data")
        probs += validate.check_figures(trial, ans["figures"], ctx, "figures")
        return probs, None
    return [Problem("V01", "", "This step takes no answer.", "Run the next command.")], None


def cmd_submit(args):
    run = open_run(args)
    if run is None:
        return 1
    s, plan = run.state, st.get_plan(run.state)
    if not 0 <= args.step < len(plan):
        return fail(f"Step {args.step} does not exist.", "Use the step number from the task block.", run.cmd("next"))
    step, current = plan[args.step], st.first_open(run.state)
    if st.status(s, step["no"]) != "open":
        return fail(f"Step {step['no']} is already {st.status(s, step['no'])}.",
                    f"Continue with the next open step. To change this step, run `redo {step['no']}` first.",
                    next_line(run).replace("NEXT COMMAND: ", ""))
    if current is None or current["no"] != step["no"]:
        return fail(f"Step {step['no']} is not the next open step; step {current['no']} is.",
                    "Work on the steps in order.", run.cmd("next"))
    if step["who"] == "script":
        return fail(f"Step {step['no']} is done by the script and takes no answer.", "Run the next command.",
                    next_line(run).replace("NEXT COMMAND: ", ""))
    path = Path(args.file) if args.file else run.answer_path(step["no"])
    entry = s["steps"].setdefault(str(step["no"]), {"status": "open"})
    entry["attempts"] = entry.get("attempts", 0) + 1
    ans, problem = load_answer(path)
    problems, extra = ([problem], None) if problem else check_step(run, step, ans)
    errors, warns = errors_of(problems), warnings_of(problems)
    stats = entry.setdefault("stats", {"submit_errors": 0, "quotes_not_found": 0, "quotes_page_corrected": 0})
    stats["quotes_not_found"] += sum(1 for p in errors if p.rule == "V09")
    shown = tasks.show_path(path)
    if errors:
        stats["submit_errors"] += len(errors)
        st.save(run.workdir, s)
        out("ERROR", f"Step {step['no']} was not accepted: {len(errors)} error(s). Fix them in {shown} and submit again.")
        for i, p in enumerate(errors, 1):
            out(f"ERROR {i} of {len(errors)} · {shown} · {p.path or '(file)'} · {p.rule}", p.msg, f"FIX: {p.fix}")
        if entry["attempts"] >= 3:
            kind = step["kind"]
            out(f"SIMPLIFY (attempt {entry['attempts']}): Give a shorter answer. Leave out every optional field "
                "(quote, affects, topic, minor) and keep one strength and one gap per criterion. Minimal valid shape:")
            if kind in ("row", "group"):
                codes = step["rows"]
                mini = schemas.minimal(tasks.row_example(codes[0]), schemas.ROW)
                out(json.dumps(mini if kind == "row" else {"rows": {codes[0]: mini}}, ensure_ascii=False))
            elif kind in schemas.BY_KIND and kind != "inventory":
                out(json.dumps(schemas.minimal(refs.example(kind), schemas.BY_KIND[kind]), ensure_ascii=False))
        out("NEXT COMMAND: " + run.cmd(f"submit {step['no']}"))
        return 1
    stats["quotes_page_corrected"] += sum(1 for p in warns if p.rule == "V09")
    st.apply(s, step, ans, extra)
    st.mark(s, step["no"], "done")
    s["warnings"] = [w for w in s.get("warnings", []) if w.get("step") != step["no"]]
    s["warnings"] += [{"step": step["no"], "rule": p.rule, "text": p.msg} for p in warns]
    write_text(run.answer_path(step["no"]), dump_json(ans))
    notes = st.advance(s)
    st.save(run.workdir, s)
    out("WARNING" if warns else "OK", f"Step {step['no']} accepted.")
    out(*[f"WARNING · {p.path} · {p.rule}: {p.msg}" for p in warns], *notes, next_line(run))
    return 0


# ---------------------------------------------------------------- preview / finish / render

def cmd_preview(args):
    run = open_run(args)
    if run is None:
        return 1
    out("OK", render.render_text(render.build_view(run.state)), next_line(run))
    return 0


def _free_path(folder: Path, stem: str) -> Path:
    path, n = folder / f"{stem}.html", 1
    while path.exists():
        n += 1
        path = folder / f"{stem}-{n}.html"
    return path


def _finish(state, folder: Path, cmd_again: str, redo_hint: str):
    """Validate (E rules), then render. Returns exit code."""
    view = render.build_view(state)
    page = render.render_html(view)
    problems = validate.end_problems(state, view, render.html_to_text(page))
    errors, warns = errors_of(problems), warnings_of(problems)
    if errors:
        out("ERROR", f"The criteria evaluation was not written: {len(errors)} error(s).")
        for i, p in enumerate(errors, 1):
            out(f"ERROR {i} of {len(errors)} · {p.path} · {p.rule}", p.msg, f"FIX: {p.fix}")
        out(redo_hint, f"NEXT COMMAND: {cmd_again}")
        return 1, None
    state["end_warnings"] = [{"rule": p.rule, "text": p.msg} for p in warns]
    view = render.build_view(state)
    page = render.render_html(view)
    path = _free_path(folder, f"criteria-evaluation-{state['meta']['run_id']}")
    write_text(path, page)
    all_warn = view["footer"]["warnings"]
    n_crit = len(view["critical"])
    out("WARNING" if all_warn else "OK", f"Criteria evaluation written: {path.resolve()}")
    out(*[f"WARNING · {w}" for w in all_warn])
    out("CHAT SUMMARY (use it as it is; add at most one sentence of your own):",
        f"The criteria evaluation is saved at {path.resolve()}. It lists "
        + (f"{n_crit} critical issue{'s' if n_crit != 1 else ''}" if n_crit else "no critical issues")
        + " and scores 16 criteria without an overall score. "
        + (f"The validator logged {len(all_warn)} warning{'s' if len(all_warn) != 1 else ''}; "
           "they are listed in the footer of the file. " if all_warn else "The validator logged no warnings. ")
        + "The criteria evaluation is input for the author, reviewers and editors, not a decision.",
        "Do not paste the criteria evaluation into the chat. Do not upload or share the file.")
    return 0, path


def cmd_finish(args):
    run = open_run(args)
    if run is None:
        return 1
    s = run.state
    st.advance(s)
    step = st.first_open(s)
    if step is not None and step["kind"] != "finish":
        return fail(f"Step {step['no']} ({step['title']}) is still open.", "Complete the open steps first.", run.cmd("next"))
    code, _ = _finish(s, run.workdir / "out", run.cmd("finish"),
                      "To change an entry, run `" + run.cmd("redo <step>") + "` for the step that wrote it "
                      "(see `status`), then continue with `next`.")
    if code == 0:
        st.mark(s, st.get_plan(s)[-1]["no"], "done", attempts=1)
        st.save(run.workdir, s)
        out("NEXT COMMAND: none. Give the user the file path and the chat summary.")
    return code


def cmd_render(args):
    """Render a registry written in manual mode: validate everything, then write the HTML."""
    src = Path(args.source)
    try:
        state = read_json(src)
    except (OSError, ValueError) as exc:
        return fail(f"The registry file could not be read: {exc}.", "Pass a JSON file in registry format.",
                    self_cmd("render --from <state.json>"))
    meta = state.setdefault("meta", {})
    meta.setdefault("inputs", {"manuscript": True, "loi": bool(state.get("loi_promises")), "appendix": False})
    meta.setdefault("mode", "manual")
    meta.setdefault("run_id", secrets.token_hex(3))
    meta.setdefault("created", datetime.date.today().isoformat())
    meta["skill_version"] = meta.get("skill_version") or SKILL_VERSION
    state.setdefault("rows", {})
    state.setdefault("synthesis", {})
    docs, problems = {}, []
    if args.manuscript:
        try:
            doc = extract.extract_file(args.manuscript)
        except extract.ExtractError as exc:
            return fail(exc.msg, exc.fix, self_cmd("render --from <state.json> [--manuscript <file>]"))
        docs["manuscript"] = doc["pages"]
        sections = extract.detect_sections(doc["pages"])
        state["metrics"], state["sections"] = metrics.compute(doc["pages"], sections), sections
        meta["page_offset"], meta["quotes_checked"] = doc["page_offset"], True
        meta.setdefault("private", {})["input_names"] = [Path(args.manuscript).name]
    ctx = validate.Ctx(docs)
    if state.get("orientation"):
        o = dict(state["orientation"], model=meta.get("model") or "unknown", redact=meta.get("redact", []))
        problems += validate.check_orientation(state, o, ctx, "orientation")
    else:
        problems.append(Problem("V01", "orientation", "The registry has no \"orientation\".",
                                "Add title, layout, paper_type, primary_aim and secondary_aims."))
    claims = [{k: v for k, v in c.items() if k != "figures"} for c in state.get("headline_claims", [])]
    problems += validate.check_claims(state, {"claims": claims}, ctx, "headline_claims")
    if state.get("loi_promises"):
        problems += validate.check_loi(state, {"promises": state["loi_promises"]}, ctx, "loi_promises")
    if state.get("data_sources") and state.get("design"):
        problems += validate.check_data(state, {k: state.get(k, []) for k in ("data_sources", "measures", "subsets")}
                                        | {"design": state["design"]}, ctx, "")
    for code in ROW_ORDER:
        if code in state["rows"]:
            problems += validate.check_row(state, code, state["rows"][code], ctx, f"rows.{code}")
    problems = [p for p in problems if not (p.rule == "V12" and p.level == "warning")]
    errors = errors_of(problems)
    if errors:
        out("ERROR", f"The registry has {len(errors)} error(s). Fix them in {src} and render again.")
        for i, p in enumerate(errors, 1):
            out(f"ERROR {i} of {len(errors)} · {src.name} · {p.path} · {p.rule}", p.msg, f"FIX: {p.fix}")
        out("NEXT COMMAND: " + self_cmd(f'render --from "{src}"'))
        return 1
    state["warnings"] = [{"step": "render", "rule": p.rule, "text": p.msg} for p in warnings_of(problems)]
    folder = Path(args.out) if args.out else src.resolve().parent / "out"
    code, _ = _finish(state, folder, self_cmd(f'render --from "{src}"'), f"Edit {src} and render again.")
    if code == 0:
        out("NEXT COMMAND: none. Give the user the file path.")
    return code


# ---------------------------------------------------------------- main

def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--workdir", default=argparse.SUPPRESS, help="working directory of the run")
    p = argparse.ArgumentParser(prog="review.py", description="jqd-paper-review pipeline")
    p.add_argument("--version", action="store_true", help="check that Python and the scripts run")
    p.add_argument("--workdir", default=None)
    sub = p.add_subparsers(dest="command")
    a = sub.add_parser("init", parents=[common])
    a.add_argument("--manuscript", required=True)
    a.add_argument("--loi")
    a.add_argument("--appendix")
    a.add_argument("--depth", choices=["full", "compact"], default="full")
    sub.add_parser("next", parents=[common])
    a = sub.add_parser("show", parents=[common])
    g = a.add_mutually_exclusive_group()
    g.add_argument("--pages")
    g.add_argument("--section")
    g.add_argument("--figure")
    g.add_argument("--table")
    a.add_argument("--doc", choices=["manuscript", "loi", "appendix"], default="manuscript")
    a.add_argument("--part", type=int, default=1)
    a = sub.add_parser("find", parents=[common])
    a.add_argument("pattern")
    a.add_argument("--doc", choices=["manuscript", "loi", "appendix"], default="manuscript")
    a = sub.add_parser("submit", parents=[common])
    a.add_argument("step", type=int)
    a.add_argument("--file")
    sub.add_parser("status", parents=[common])
    a = sub.add_parser("redo", parents=[common])
    a.add_argument("step", type=int)
    sub.add_parser("preview", parents=[common])
    sub.add_parser("finish", parents=[common])
    a = sub.add_parser("render")
    a.add_argument("--from", dest="source", required=True)
    a.add_argument("--manuscript")
    a.add_argument("--out")
    return p


COMMANDS = {"init": cmd_init, "next": cmd_next, "show": cmd_show, "find": cmd_find, "submit": cmd_submit,
            "status": cmd_status, "redo": cmd_redo, "preview": cmd_preview, "finish": cmd_finish,
            "render": cmd_render}


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version:
        out("OK", f"jqd-paper-review {SKILL_VERSION} · Python {sys.version_info[0]}.{sys.version_info[1]}",
            "NEXT COMMAND: " + self_cmd("init --manuscript <file> [--loi <file>] [--appendix <file>]"))
        return 0
    if not args.command:
        parser.print_help()
        return 2
    return COMMANDS[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
