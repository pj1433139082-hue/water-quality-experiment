# water-quality-experiment

An agent skill for running a **water-quality time-series prediction workflow** end to end — planning a run, preparing it against a frozen contract, executing it against the real engine, reviewing the evidence, and maintaining the skill itself without ever overstating authority.

The skill exists because this class of work has two failure modes that look like success: **leakage** (a metric that is real but not honest) and **unearned authority** (a check that passed being read as permission to do something else). Most of the text below is about keeping those two apart.

## Layout

| Path | What it is |
| --- | --- |
| `SKILL.md` | The skill entrypoint: routing, the load-on-demand table, the non-negotiable science/permission constraints, and the completion conditions. It also carries the resource manifest at the end. |
| `references/experiment-execution.md` | Preparing, running, and reporting an experiment; phase-0 evidence packaging; the acquisition boundary; the feedback and skill-evolution contract. |
| `references/source-acquisition.md` | Source quality, point/unit semantics, segment plans, one-shot source authorization, and the aggregate-manifest rules. |
| `references/task-state-hygiene.md` | Task state, protected project roots, selector/handoff previews, lock roots, and the read-only preflight gates. |
| `references/test-isolation.md` | Test isolation: why `--basetemp` must never point into the vault, how the runner owns temp roots, and the `__pycache__` rules. |
| `scripts/check_resources.py` | Standalone read-only verifier: re-reads the manifest embedded in `SKILL.md` and checks every listed file's exact byte length and SHA-256. |

## Core rules it enforces

- **Fix the time semantics, sample construction, development window / CV / outer holdout, and baselines before anything else.** No random time splits, no future information. **Outer holdout never selects models.** No feature or model stage starts without source-quality evidence.
- **A new run needs an explicit `project_id` + `run_id`.** SQLite/WAL is the canonical machine state. A preparation registry is not the experiment workflow database; hand-written task JSON, an old selector, or a synthetic fixture cannot substitute for production admission.
- **Three human gates for a scientific run: `PLAN_FREEZE`, `HOLDOUT_UNLOCK`, `CLAIM_FREEZE`.** Silence, an agent recommendation, maintenance acceptance, or a Phase 0 PASS are not substitutes.
- **A gate that passed proves only its own scope.** An audit PASS, a synthetic-test PASS, and a pure byte-comparison PASS each prove exactly what they name and nothing more.
- **Real source reads need their own authorization.** A compatibility profile, a ledger entry, a source-code hash, or a callable identity is never permission to make a network request.
- **Separate facts stay separate.** An attempt being recorded, a function returning, a digest being accepted, a capture completing, and a role review passing are five different facts; a failure on one never proves anything about the others.
- **Do not convert a spoken identity claim into verifiable authorization.** A missing issuer/profile/ledger stays unconfigured; an unknown row state stays unknown.
- **Report statuses separately.** `maintenance_status`, `experiment_status`, `release_status`, and the unverified items are recorded as distinct fields. Maintenance completion is never written as `03 COMPLETE`, `04 READY`, model admission, or production release.

## Using it with an agent

Drop the directory into your agent's skills root and let the harness discover `SKILL.md` by its frontmatter:

```
<skills-root>/water-quality-experiment/
├── SKILL.md
├── references/
└── scripts/
```

Verify the shipped bytes at any time — the script imports nothing from your project and writes nothing:

```powershell
python -B -X utf8 scripts/check_resources.py
```

It prints `{"status": "PASS", ...}` and exits `0`, or prints a `HOLD` with a stable reason code and exits `2`. A `HOLD` means: stop any action that depends on the drifted resource.

## Honest boundaries

- This is the **generic edition** of a skill that was developed against a private methodology corpus, a private engine checkout, and a private data source. Paths that only made sense inside that corpus are written as placeholders — `<方法体系根>/`, `<受保护项目根 A>`, `<受保护项目根 B>`, `<外部来源项目根>`, `<skills-root>` — and you should map them onto your own layout.
- Engine module names, evidence schema names, gate names, and project slugs are kept **verbatim** on purpose: they are the concrete part of the contract, and paraphrasing them would make the skill sound more general than it is.
- The workflow this describes is enforced by a specific engine implementation. This repository ships the skill and its verifier only — **not** the engine. Where the text names an engine module or an entrypoint, that name is the contract you have to satisfy, not code you get here.
- `scripts/check_resources.py` proves **manifest identity** for the five listed files. It is not a proof of a complete protocol closure, and it is not a same-handle guarantee against a process that rewrites a file between the check and its use.

## 中文摘要

本仓库是一个**水质时间序列预测工作流**的 agent skill。它的重点是两件事：不让数据泄漏伪装成好指标，也不让一次通过的检查伪装成做某件事的授权。`SKILL.md` 是按需加载的入口，`references/` 下四份参考文件分别覆盖实验执行、来源取数、任务状态卫生与测试隔离，`scripts/check_resources.py` 用 `SKILL.md` 末尾的资源清单校验每个文件的确切字节数与 SHA-256。正文里那些只在私有语料中成立的本机路径已替换为占位符；引擎模块名、证据 schema 名与门禁名保持原样，因为它们是契约的具体部分。
