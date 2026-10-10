# 代码验证与 Windows 隔离运行

维护的合成测试使用固定 runner；不因代码测试解锁真实实验。

## Test Workspace Isolation

Engine/S7 tests must run through the unified Windows runner, never with a
`--basetemp` (or `TMP`/`TEMP`) that points into the Obsidian vault or a drive
root such as `C:/`. Historical direct runs left ACL-locked vault directories
and empty `C:/pfr-*` basetemp roots after pytest cleaned their contents.

The workflow CLI has the same vault boundary. Use
`engine/scripts/run_water_workflow.ps1` for every CLI command: it establishes
the engine root and disables Python bytecode before the package is imported.
The `__main__.py` guard is defense in depth, not a replacement for the
wrapper, because package initialization can happen before `__main__.py`.

- Always run engine tests via `engine/scripts/run_s7_tests.ps1` (derives the
  engine root from `$PSScriptRoot`, pins `--basetemp` + `TMP`/`TEMP` to a unique
  `%LOCALAPPDATA%\Temp\paper-work-pytest\run-<ts>-<pid>`, adds
  `-p no:cacheprovider`, refuses elevated tokens, and rejects caller-supplied
  `--basetemp`).
- Never pass caller-selected `--basetemp`, whether under the vault, a project
  directory, or a drive root. Direct pytest hardening permits an explicit
  basetemp only below `%LOCALAPPDATA%/Temp/paper-work-pytest`; the runner owns
  the path and creates one unique child per run.
- To inspect historical runner residue without touching it, use the runner's
  read-only audit mode:
  ```powershell
  powershell -File "<方法体系根>/engine/scripts/run_s7_tests.ps1" -AuditHistorical
  ```
  The audit derives the fixed LocalAppData root itself, scans only direct
  children, and reports the `paper-work-pytest-temp-audit-v1` JSON result. It
  never creates, deletes, renames, repairs, or recursively enters old runs;
  it does not infer PID liveness or say that any historical entry is safe to
  delete. `-AuditHistorical` cannot be combined with `-DryRun`, `-Tests`, or
  `-PytestArgs`. Treat `RUN_UNBOUND_LEGACY`, `MARKER_ONLY`,
  `INVALID_MARKER`, `RUN_CONTENT_SCAN_BLOCKED`, and reparse classifications as
  manual-review evidence only. Do not use the normal cleanup helper against a
  historical entry unless a separately approved, identity-bound cleanup task
  exists.
- Example:
  ```powershell
  powershell -File "<方法体系根>/engine/scripts/run_s7_tests.ps1" `
    -Tests "tests/test_s701f_publication_fencing_red.py,tests/test_state_store.py"
  powershell -File "<方法体系根>/engine/scripts/run_s7_tests.ps1" -DryRun
  ```
- The runner has a finite wall-clock deadline (`-TimeoutSeconds`, default
  `1800`). When pytest or a descendant hangs, the runner emits
  `TEST_TIMEOUT:` and returns `124` after terminating only its own process
  tree; it then performs the normal ownership-checked cleanup. A timeout is a
  failed/incomplete run, never a PASS, and the cause must be diagnosed before
  retrying. Do not rely on an outer terminal timeout or Ctrl-C as the cleanup
  mechanism.
- Fixed-root task-state preflight subprocesses suppress Python bytecode output;
  they must not create new cache directories or temporary files inside the
  vault.
- The same rule applies to the direct read-only task-state inventory, evidence
  audit, migration preview, and `manager_guard` hook entrypoints. Each entrypoint
  must disable Python bytecode output before dynamic imports; direct invocation
  must not create or modify `__pycache__` inside the vault. Existing caches are
  historical audit evidence and must not be auto-deleted by this rule.

