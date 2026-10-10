# 来源质量、外部取数与授权边界

仅对涉及外部来源的任务加载相应小节。已有执行许可的边界必须从冻结证据核实；历史说明不替代本轮授权。真实数据和凭据不能因维护任务而自动读取。

### 外部黑盒取数操作卡（来自 `learn-model` 的取数迁移）

- 外部入口里的“数据确认”必须落成四类可交接证据：测点/单位/瞬时或累计口径确认、固定 UTC 请求计划、逐段响应质量摘要、质量通过后的参数图与分工况摘要。只有接口返回 `DataFrame` 而没有这四类证据时，保持 `DATA_QUALITY_HOLD`，不得进入特征或模型步骤；所有输出放隔离根，不把原始行或凭据写回 vault。
- 将 `fetch_iot_data` 只当作已观察的客户端接口：请求由 `factory_code`、完整 point ID 到返回列别名、固定 `start_time`、`rolling_window` 和 `interval` 组成；真实实现中的 OIDC/网络凭据仍由受控外部环境持有，不能写入技能、授权或 manifest。不要把 `start_time=''` 的“当前时间减窗口”默认行为带入实验。
- 对该类已观察来源，约 1500 行上限、约 15 秒返回节奏和最多 6 小时完整窗口必须写进 profile/ledger；分段数使用 `ceil`，固定一次 UTC `[start, end)`，保留最后不足一段，不能用 `floor` 或空段 `break` 截断历史。`interval` 只是请求参数，`data_time` 才按来源合同解释为 UTC，实际频率必须从返回时间戳重算。
- 返回列别名必须与冻结映射逐字匹配；本来源优先使用英文返回别名，中文列名曾造成云端 schema 对不上。每段先保存请求、响应列、行数、时间范围、重复/乱序、半开频率网格的期望行数、首端/尾端缺槽、最大断点、空值、物理范围和冻结证据，再排序、去重、重采样或建模。合法的非整频率尾段按 `[segment_start_utc, segment_end_utc)` 网格判断，不得把 `segment_end_utc` 本身强行当成采样点；首端或尾端缺槽必须 `HOLD`。
- 外部来源的别名语义冲突必须先查隔离卡 `_isolated_experiments/beikong-learn-model-point-semantic-audit-r1/preflight/point-semantic-ambiguity-card.json`：同一完整点位出现 `NH3_in(mg/L)` 与 `NH4_in(mg/L)` 时，状态为 `UNRESOLVED_SEMANTIC_CONFLICT`，不能自动合并，必须人工确认测量定义；`Flow1(m3h)`/`Flow1_inst(m3h)` 等返回别名变化必须新建映射和 run，不能静默替换。`V_LF`/`V_GF` 瞬时量与 `V_LFQ`/`V_GFQ` 累计量不能按名称自动推断或互换；点位范围变化必须停在来源门。
- 如果选用累计量，先按合同确定“小时末值差分”口径；回零、负差分或异常大跳变必须保留为质量异常/`HOLD`，不能对累计量直接取均值，也不能把缺失填成 0。取数质量门通过后，才为每个实际使用的参数生成带单位的时序图和分工况摘要，图和摘要写入隔离根，不把原始行写进 vault。
- 真实来源仍必须走独立的一次性 source authorization 和 `fetch_segments_with_external_source_authorization()`；兼容卡、`fetch_segments_from_external_profile()` 或客户端成功返回 DataFrame 都不能替代授权和质量门。失败重做必须新建 authorization、`run_id`、计划摘要和隔离输出根。

### 当前外部取数治理口径

- 从 `learn-model` 学到的是取数契约和质量证据的组织方式，不是可直接复用的生产客户端：完整测点 ID 与返回别名必须逐项绑定，`interval` 与返回频率分开核验，时间计划固定为 UTC 半开区间并用 `ceil` 保留尾段；每段响应先留请求/列/行数/覆盖/频率/缺口/异常摘要，再进入规范化、重采样或建模。
- 唯一生产路径固定为：`OBSERVATION_ONLY` → 人工测点语义确认 → 新 `IotSourceLedger` → 固定 UTC 分段计划 → 来源质量门 → 新的一次性 source authorization → `fetch_segments_with_external_source_authorization()` → 仅聚合 manifest。旧审计中出现的 `fetch_segments_from_ledger`、`fetch_segments_from_external_profile` 和历史脚本只能作为 `SUPERSEDED_HISTORICAL` 或合成/受控测试材料，不能启动真实网络调用。
- 证据范围必须分层书写：本轮实现硬化没有访问 `<外部来源项目根>` 的 raw 文件或网络；早期隔离审计曾对代表性 CSV 做流式/聚合质量核查，但没有复制或导出行级数据；点位语义卡、来源 profile 和历史聚合质量记录都不是授权。若范围无法区分，直接标记 `HOLD`。
- 当前北控 profile 仍是观察型兼容证据，`NH3_in`/`NH4_in`、`Flow1`/`Flow1_inst`、瞬时/累计量和点位范围扩展的冲突没有自动解释。任何新别名、新测点、新时间范围或新客户端都必须创建新的 mapping、run、证据和授权，不能更新旧 pin 来“修绿”。

- Convert a `LedgerCandidate` to an in-memory `IotSourceLedger` through a `LedgerMappingDeclaration` for any traceable run: create it with fully populated `LedgerContractSettings` and explicit `PointBinding` list/tuple, store its non-self `mapping_sha256` in external review evidence, then call `build_iot_ledger_from_mapping(..., expected_mapping_sha256=...)`. The declaration carries candidate SHA and source identity, is strict/file-free/non-executable, and the conversion rechecks the candidate image and identity before construction. All settings have no implicit defaults; `factory_code` must match the candidate, every binding must name an eligible candidate point, and response alias, unit, physical bounds, timestamp, timezone, frequency, request window, row limit, and interval must be supplied by the caller. The compatibility bridge `build_iot_ledger_from_candidate` remains synthetic/in-memory only; it must not be used as evidence that a mapping was approved. For a traceable synthetic/controlled acquisition, `fetch_segments_from_mapping` carries `candidate_sha256` and `mapping_sha256` into the aggregate manifest but requires the internal source-execution capability. No declaration or ledger constructor reads the source path, calls a network client, accesses credentials, writes authorization/manifest, or infers semantics; real workbook/API execution must use a separate isolated source-authorization run and the strict entry.
- Keep `requested_interval` and `declared_frequency` semantically independent. The former is only the frozen black-box query argument; the latter is the expected response cadence used by the quality gate. A request parameter or successful call never proves cadence; compute observed cadence from returned timestamps and record mismatches as quality evidence.
- To make a mapping redoable across restarts, publish it only with `publish_iot_mapping_declaration` into a new absolute run directory outside the vault, source project, and protected roots; the parent must already exist and the output is create-new. The record contains only the non-executable declaration, `run_id`, and `mapping_sha256`, never measurement values, credentials, or authorization. Restore only with `load_iot_mapping_declaration`, which verifies the record schema, run identity, declaration hash, and reparse-safe path without reopening the candidate workbook. Collisions, `..`, reparse escape, and atomic-write failure are fail-closed; old records are never overwritten.
- For every new modeling ladder, require a companion `objective_ladder.yaml`. One ladder has one target; one run has one `horizon_steps`. Never run an unregistered `targets` or `horizons` loop inside one contract.
- Default new feasibility work to the `EXPLORATION` track: start with the smallest explicitly frozen business-actionable horizon, fixed strong baselines, development-only TimeCV, and a limited evidence-triggered candidate set. Do not choose a shorter horizon merely because it scores better.
- Extend only one registered horizon rung at a time. The next run must pin the predecessor run, horizon and Development Gate decision. A development result may allow creation of the next plan, but cannot execute it automatically or unlock holdout.
- Keep extension execution fail-closed until the engine first publishes an immutable `DevelopmentEvaluationBundle` containing the inner-selected pipeline manifest, per-outer-fold metrics, coverage/failure audit and source hashes, then recomputes and atomically publishes the Gate record from that bundle. `WF-S6` frozen-baseline output alone is not a candidate-pipeline Gate. Never accept a hand-authored `development_gate.json` as authority.
- Do not trust predecessor fields by declaration. Require the predecessor ladder snapshot, terminal SQLite run state, and matching `development_gate.json` with the same evidence hash before starting an extension rung.
- Local configuration selection belongs only inside each outer-train inner TimeCV. Outer folds evaluate the selected full pipeline and may rank only preregistered routes; they must never feed back into alpha/window/lag/threshold tuning. A route proposed after seeing outer results is `EXPLORATORY_ONLY` and needs a new preregistered run.
- Use a new `CONFIRMATION` run, contract and one-shot authorization only after one target, one horizon and one pipeline are frozen. All residual-driven enhancement must finish before confirmation; confirmation loads and verifies the pinned pipeline and never selects a route. Never upgrade an exploration run in place or reuse a consumed authorization/holdout.
- Keep confirmation execution fail-closed until the engine has a project-level atomic single-use holdout registry. Per-ladder declarations are not sufficient because multiple ladders could otherwise reuse the same final period.
- Reuse the already verified shared engine in exploration. Do not rerun production authorization or 50x filesystem/publication gates for every model candidate unless relevant infrastructure code changed or the current risk review explicitly requires it.
- If a longer horizon misses the frozen gate, keep the prior rung and emit `STOP_AT_CURRENT` or `REFRAME_TASK`; do not search an unlimited model zoo. Reframe to interval, exceedance-risk or trend prediction only through a new frozen plan.
- Use a positive fixed-width `time_axis.declared_frequency` to map horizon steps to `origin_time`; reject zero, negative and calendar-dependent offsets, and never substitute an observed modal interval or row position.
- Treat affine transforms of `y(t+h)` as future-target leakage and `HOLD`. If current and future mappings are both plausible, emit `AMBIGUOUS_CURRENT_AND_FUTURE_MAPPING/HOLD` and require lineage/availability evidence. Only an exact current-target signal with a trend-induced non-exact future affine relation may remain `WARN`.
- Granger screening must use stationary representations, test cointegration only for verified I(1)-I(1) pairs, and correct the complete feature-by-direction-by-lag hypothesis family while reporting its hypothesis count. It is predictive precedence only.
- In `WF-S5`, execute only frozen baseline/evaluation work. Record TimeCV as frozen but not executed and holdout as locked; never turn a serialized protocol snapshot into a false execution claim.
- Block `WF-S5` with `NO_EVALUABLE_BASELINE` unless at least one frozen baseline produces finite predictions and a finite primary metric.
- In `WF-S6`, split only by target-time windows anchored at `development_end`. Require explicit train/test grid coverage and `min_evaluable_coverage`; a baseline enters fold evidence only when its primary metric is finite, prediction coverage passes, and `causality_status=PASS`.
- Load and hash only the physical development snapshot. Post-development rows may be inspected only through the timestamp column to locate the boundary; never load holdout labels/features into the workflow frame. Keep `holdout_accessed=false`, `holdout_values_used=false`, and `allow_enter_wf_s7=false`.
- Publish artifact revisions atomically from short-path staging. A failed WF-S6 artifact write must leave no visible partial revision and may be retried only while frozen evidence is unchanged.
- Run `WF-S6` on demand after a completed `WF-S5`; do not schedule it as a recurring service. A `PASS` proves the frozen baseline TimeCV mechanics only, not model superiority or paper readiness.
- Legacy per-task JSON files and v1 lineage manifests may be read only for historical inspection or explicitly supported recovery. They are not authoritative for new runs, v1 redo is blocked, and neither may be silently converted in place.
- `status`, `gate`, and `report` are read-only operations. They must use the read-only SQLite admission/status readers and must not create a missing database, parent directory, migration, cache, or artifact.
- `StateStore.create_run()` and `bind_lineage()` are legacy/manual compatibility APIs only. They require an explicit `StateStore.legacy()` instance and are forbidden in the canonical runner; new admissions must use the atomic `create_bound_run()` path that writes `RUN_CREATED`, context, and `LINEAGE_BOUND` together.
- Evidence bundle publication must treat every existing directory entry at the final bundle name as a collision, including a dangling symlink/junction. Check with `os.path.lexists()` before creating the temporary bundle; never let `Path.exists()` classify a broken reparse entry as absent, and never overwrite or replace it.

Progressive invocation for every new experiment from `<方法体系根>/engine`:

```powershell
.\scripts\run_water_workflow.ps1 feedback-bootstrap <experiment_contract.yaml>
.\scripts\run_water_workflow.ps1 start-progressive <experiment_contract.yaml> <objective_ladder.yaml>
.\scripts\run_water_workflow.ps1 status --project-id <project_id> --run-id <run_id>
.\scripts\run_water_workflow.ps1 approve PLAN_FREEZE --project-id <project_id> --run-id <run_id>
.\scripts\run_water_workflow.ps1 continue --project-id <project_id> --run-id <run_id>  # WF-S5
.\scripts\run_water_workflow.ps1 continue --project-id <project_id> --run-id <run_id>  # WF-S6
```

For a new progressive run, execute `feedback-bootstrap` first. It creates only the
fixed-root F0/F1 initialization bundle and prints a `task_state_patch`; it does
not write task-state, SQLite, a ladder snapshot, raw data, holdout data, or model
outputs. The orchestrator must submit that patch through the normal
`task-state-v2`/`manager_guard` admission, then invoke `start-progressive`.
Bootstrap success is not a WF-S0 result, a plan approval, or a stage gate.

Before submitting the patch, pipe the exact JSON emitted by `feedback-bootstrap`
through the fixed-root registration preflight:

```powershell
.\scripts\run_water_workflow.ps1 feedback-bootstrap <experiment_contract.yaml> |
    python -B scripts\validate_task_feedback_registration.py
```

The registration preflight reads the fixed active-root current task (using the
selector when present) and stdin only;
it accepts no caller-selected state path and never writes task-state, SQLite or
feedback evidence. A `PASS` with classification `FEEDBACK_REGISTRATION_READY` means that the bootstrap reference is ready to be
merged into a new `task-state-v2` record. The normal `manager_guard` admission
remains the only state writer: a newly created `water-quality-progressive`
record without `feedback_binding_ref`, with the legacy `feedback_binding`, or
with an identity/path mismatch is rejected. Existing historical records are
not backfilled by this check. `start-progressive` must still revalidate the
F1 bundle and create the authoritative `FEEDBACK_BOUND` event; registration
`PASS` is not engine binding proof.

When the target task-state does not exist yet, do not use the raw-bootstrap
mode above as a substitute for a candidate. Submit a single JSON envelope on
stdin instead:

```json
{
  "schema": "water-quality-task-feedback-registration-input-v1",
  "task_state_candidate": {
    "schema": "task-state-v2",
    "workflow": "water-quality-progressive",
    "task_id": "<task_id>",
    "run_id": "<same run_id as bootstrap>"
  },
  "bootstrap_result": {
    "schema": "water-quality-feedback-bootstrap-v1",
    "status": "PASS",
    "binding_ref": "<the exact object from task_state_patch>"
  }
}
```

The real envelope contains the complete candidate and the exact bootstrap
object, not placeholder strings. The fixed script checks
the candidate's progressive identity and the bootstrap reference without
writing it; `manager_guard` then remains the only writer and also checks the
single-current-task rule. Raw-bootstrap mode is explicitly `CURRENT_TASK`
mode for an already existing current record; envelope mode is
`NEW_TASK_CANDIDATE` mode. Neither mode proves engine `FEEDBACK_BOUND`.

`run_water_workflow.ps1` is the bytecode-safe CLI entrypoint. It changes to
the engine root, sets `PYTHONDONTWRITEBYTECODE=1`, and invokes `python -B`
before importing `water_workflow`. Do not run bare `python -m water_workflow`
from the vault; if the wrapper cannot be used, the minimum fallback is
`python -B -m water_workflow`.

Before writing a next-rung plan, run the read-only extension preflight:

```powershell
.\scripts\run_water_workflow.ps1 preflight-progressive-extension <objective_ladder.json>
```

It returns only `PLAN_ELIGIBLE` or `HOLD` and must not write governance, SQLite, authorization,
artifacts, or model outputs. `PLAN_ELIGIBLE` permits drafting in a new isolated directory only; it
does not authorize extension execution or holdout access. A historical Bundle/Gate without the
code-fixed predecessor `workflow.db` admission is `HOLD`, even when its files and hashes verify.
Never repair that gap by writing a synthetic admission or by changing the old run in place.

For a redo of a historical h1 anchor, create a new run and run the read-only canonical anchor preflight
before generating Phase 0 or starting the runner:

```powershell
.\scripts\run_water_workflow.ps1 preflight-canonical-anchor <experiment_contract.json> <objective_ladder.json>
```

It checks contract/ladder identity, the fixed progressive runtime root, the fixed Phase 0 gate, the new
run's lineage binding, and task-state hygiene. It returns only `READY_FOR_START_PROGRESSIVE` or `HOLD`
and performs no writes or raw/holdout reads. `READY_FOR_START_PROGRESSIVE` is only permission to enter the
normal `start-progressive` admission path; it never authorizes model execution or holdout access. A
historical result, Bundle, or hand-authored Gate cannot satisfy this preflight by itself.

The legacy `start <experiment_contract>` command is disabled. Historical runs resume only through `status` / `continue`, and only if a persisted `LINEAGE_BOUND` matches the fixed Phase 0 package. After the explicit feedback bootstrap, `start-progressive` validates both contracts, checks protected-root separation and predecessor evidence, proves the fixed Phase 0/lineage binding and F1 feedback before writing any run-scoped governance file, then atomically freezes a no-replace ladder snapshot before the runner starts. The snapshot SHA is part of run evidence. The two explicit `continue` calls preserve stage observability: inspect WF-S5 before requesting WF-S6. Neither call opens holdout.

When consulting `02-标准实验执行SOP.md`, treat only its explicitly marked `EXECUTABLE_ENTRYPOINT` block as a command reference. The SOP also preserves legacy implementation examples under `DRAFT_ONLY` markers for historical reasoning; those blocks are non-executable and must never be copied into a new run. If a legacy example conflicts with the current CLI or engine contract, the current entrypoint and this skill win.

`WorkflowRunner(...)` uses the hard feedback entry by default: its constructor has no public
`require_execution_feedback` switch, and `start()` itself rechecks the feedback bundle and
ladder snapshot; calling the Python API cannot bypass the CLI gate. The production package has
no historical no-feedback factory. Existing historical/test fixtures use the explicit
test-only adapter `engine/tests/_legacy_runner_fixture.py`; it is not part of the
`water_workflow` package, is absent from the CLI and must never be imported by a new run.
For progressive runs, deletion or byte drift after S0 is a hard failure, not a new evidence
revision that can be re-approved. Only pre-progressive historical S0 artifacts without an
`objective_ladder` field may resume without one. `WorkflowRunner.status()` is a read-only
inspection path and cannot initialize state.

The direct-entry trust-root remediation is now `PASS_WITH_NOTES` with P0/P1 cleared. The three
compatibility APIs (`development_improvement_run`, `development_stability_run`, and
`development_horizon_screen_run`) use code-fixed Phase 0 Gate/lineage paths, read-only admission,
atomic `create_bound_run()`, repeated binding validation, and a cooperative publication fence.
They may be used only for synthetic or explicitly isolated contracts while the P2 backlog is open;
the canonical `start-progressive`/`WorkflowRunner` path remains the preferred route for new work.

Their public historical `execute_run()` functions are machine-blocked with
`LEGACY_R2_ENTRY_DRAFT_ONLY` before state-path resolution, SQLite access, snapshot reads, model
calculation, or artifact writes. Historical synthetic regression uses only the test adapter
`engine/tests/_legacy_r2_entry_fixture.py`, which is outside the production package and is not a
new experiment entrypoint. The private compatibility body also requires that explicit test-only
adapter context; there is no environment or caller flag that reopens the public entry.

The same machine boundary applies to the historical `prepare_run()` and
`approve_plan_freeze()` functions: public calls are blocked before contract reads, path resolution,
SQLite access, or admission writes with `LEGACY_R2_ENTRY_DRAFT_ONLY`. Their old implementations are
private compatibility bodies and may be reached only through the named prepare/approval helpers in
`engine/tests/_legacy_r2_entry_fixture.py`. Do not call the production module functions directly,
and do not add an environment variable, CWD rule, or boolean opt-out. This preserves historical
synthetic tests without leaving a plan/approval route that can seed state before the canonical
workflow.

If a direct run detects lineage drift or publication uncertainty, it may retain a visible
`PREPARED` directory as non-authoritative evidence, but it must not write a terminal/authoritative
state without post-rename binding validation. Generic legacy APIs remain historical/DRAFT_ONLY and
must not become a new experiment entrypoint. This remediation does not authorize real model
execution, holdout access, or Stage 7d.

