# Version
1

# Coding Rules (Pointer)

This project's coding rules live in `CODING_RULES.md` in the project root. They are
BINDING for all code work in this repository.

MANDATORY: Before writing or editing ANY code, you MUST Read `CODING_RULES.md`
in full **in the current session**. Do not rely on memory of a previous session,
a summary, or partial reads.

If you are about to make a code change and have not read `CODING_RULES.md` in
this session: STOP, read it, then continue.

Do not inline rules back into this file and do not use `@import` for
`CODING_RULES.md` — it is intentionally referenced, not imported.

## Testing

After changing Core plugin code (`src/main/resources/base/Plugins/Core/core/**`),
run:

```bash
powershell -Command "cd 'D:\GIT\BenjaminKobjolke\fman'; cmd /c '.\tools\run_core_tests.bat'"
```

Fast (~0.4s), covers all of `core`'s own tests. Do **not** use `python build.py test`
for this — it also runs fbs's bundled `fman_unittest`/`fman_integrationtest` suites,
which have a known intermittent hang (Qt/thread state leaking from
`fman_integrationtest.test_qt` into a later widget test — unrelated to Core plugin
changes, not yet root-caused).

If you touched the zip/7-Zip filesystem code (`core/fs/zip.py` or
`core/tests/fs/zip_test.py`), also run:

```bash
powershell -Command "cd 'D:\GIT\BenjaminKobjolke\fman'; cmd /c '.\tools\run_zip_tests.bat'"
```

These are excluded from `run_core_tests.bat` (filename doesn't match `test*.py`)
because they spawn `7za.exe` as a real subprocess and can hang under
AV/EDR interference.

How fman drives 7-Zip (the `-bsp1` progress protocol, canceling, why there is
no pseudo-terminal on Windows) is documented in `docs/ARCHIVES.md`.

## Code Analysis

Two analysis modes — pick by situation:

**Changed-files run (default after implementing a feature, finishing a plan, or
fixing a bug):**

```bash
powershell -Command "cd 'D:\GIT\BenjaminKobjolke\fman'; cmd /c '.\tools\analyze_changed_and_new_files.bat'"
```

Uses `--only-changed`: the report is filtered to files new/modified vs git `HEAD`
(includes untracked). Project-wide analyzers still run; only the report is
filtered. Fast feedback, no noise from pre-existing violations elsewhere.

**Full run (whole-project audits):**

```bash
powershell -Command "cd 'D:\GIT\BenjaminKobjolke\fman'; cmd /c '.\tools\analyze_code.bat'"
```

Use the full run for: an explicit audit request (`/analyze:run-and-fix`),
exception maintenance (`/analyze:improve-exceptions`), before a release/merge,
after refactors that touch shared code, or when the working tree is clean vs
`HEAD` (a changed-files run would report nothing).

Results are written to `code_analysis_results/` as **per-rule CSV files** (e.g.
`flutter_analyze.csv`, `line_count_report.csv`, `duplicate_code.csv`) — there is
no `.md` report, and a missing CSV means that rule found nothing. Fix any
reported issues before committing.

## Knowledge Graph (graphify)

This project's graph is built from the **repository root**, never from `src/`:

```bash
/graphify . --directed
```

The graph deliberately covers `docs/`, `tools/`, `build.py` and the root
`*.md` files as well as `src/` — roughly 480 of its ~4000 nodes, and the half
that answers "how does X work" rather than "where is X defined". Rebuilding
with a narrower path deletes them. graphify's shrink guard catches that and
refuses the write; **do not force past it** — re-run with `.` instead.

Excluding `docs/` from `.graphifyignore` is the same mistake in another form,
and it has been tried: a code-only graph answers symbol lookups that grep
already answered, and loses every "how does X work" question. Keep docs in.

This overrides the generic `/graphify <code-dir> --directed` line in
`CODING_RULES.md`, whose `# e.g. src/ app/ lib/` comment is what makes `src/`
look right here. It isn't.

Two things that make the wrong scope easy to hit:

- `graphify-out/` is gitignored, so the scan-root sidecar
  (`graphify-out/.graphify_root`) never travels with a clone — and it holds an
  absolute path, so it *cannot* be committed either. A fresh checkout has no
  memory of the scope; the first rebuild must pass `.` explicitly.
- Any `/graphify <path>` run overwrites that sidecar, so a single
  wrong-path invocation leaves it pointing at the wrong root and a later bare
  `graphify update` rescans only that subtree — reading every file outside it
  as deleted.

Before rebuilding, confirm the scope: group `graphify-out/graph.json` nodes by
the first path segment of their `source_file`. If you see `docs`, `tools` and
`build.py` alongside `src`, the graph is root-scoped — keep it that way.
