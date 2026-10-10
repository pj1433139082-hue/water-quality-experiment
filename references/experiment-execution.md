# 实验运行、Phase 0 与执行反馈

仅在当前任务涉及实验准备、执行或反馈时读取相应小节。状态迁移、SQLite 写入与科学人工门只适用于对应实验动作。入口的维护完成条件适用于技能/代码维护。

### Independent project preparation

Keep `project_id`, `run_id`, `target`, and `horizon_steps` distinct. A short request for `cod_in/h1` states the prediction target and horizon; it supplies project/run identities only if the frozen request/contract explicitly binds those identity fields. Resolve each field from that evidence; do not invent IDs or substitute the target/horizon shorthand as IDs.

The current project-preparation implementation is a fixed Qinhuangdao slice, not a generic preparation interface: `project_preparation_admission.py` requires `project_id=qinhuangdao-periodicity-innovation`, `run_id=qinhuangdao-tn-in-h1-*`, `target_columns=("tn-in",)`, `declared_frequency=1D`, `timezone=Asia/Shanghai`, and its code-fixed source/time boundaries. Unsupported identities/schema remain HOLD (`PROJECT_IDENTITY_NOT_SUPPORTED` or `PROJECT_SOURCE_SCHEMA_MISMATCH`). A COD request requires a separate supported contract/entrypoint before registration or source reads; do not relabel it as TN. An h1 prediction is one sample step at the frozen frequency, not automatically one hour.

The reviewed Qinhuangdao preparation path uses explicit `project_id + run_id`
without changing the global current selector. Through `run_water_workflow.ps1`,
use `register-project REQUEST --project-id PROJECT --run-id RUN` to bind a strict
Phase 0 request and the fixed read-only source in the OS LocalAppData SQLite/WAL
preparation registry. `project-preflight` with both IDs is read-only; the root
preflight script also accepts exactly `--project-id PROJECT --run-id RUN`.
The scope is `project_preparation`, not `current_task`; a PASS grants only
`phase0_preparation_admission`, never model execution or holdout access.
`phase0-generate REQUEST --project-id PROJECT --run-id RUN` uses the bound request
image and the existing canonical calculator/producer. Missing identity, evidence,
hash drift, redirected paths or interrupted registration must HOLD without
falling back to another project. The registry does not contain experiment-stage
state and does not replace a future atomically bound `workflow.db`.
Project-scoped model startup, lineage/feedback writes and approvals remain
unreleased in this slice. Do not mark task 01 complete before its actual
development contract, time boundaries and sample construction have been verified.
The legacy current-scope instructions below apply only to global legacy tasks.

- New work uses the canonical `water_workflow` engine and is addressed by explicit `project_id + run_id`.
- SQLite/WAL is the only canonical machine state. Do not create or search for a global `current=true` task.
- `READONLY_COMPAT` is mandatory when an existing project supplies data. Set `protected_project_root` to that project root and place the database, artifacts, reports, caches, and temporary copies outside it.
- Existing projects are read-only evidence sources. Do not create `.planning/`, `.claude/`, `artifacts/`, reports, caches, or repaired datasets inside them.
- Resume with both IDs, then load only the returned stage evidence and compact artifact references.
- For IoT APIs or external exports, complete `08-数据获取与来源质量门.md` before Phase 0. A successful API response is not evidence that the requested points, time coverage, units, or physical values are usable.
- Before `PLAN_FREEZE`, require explicit `evaluation`, `timecv`, `holdout`, and `baselines` protocol objects. Never let the runner infer a seasonal period, CV fold count, primary metric, or holdout interval that is absent from the contract.
- Before any model-execution entry, require a machine-validated `water-quality-phase0-gate-v3` whose evidence closure contains exactly three JSON machine records: semantic data evidence, time-series diagnostics, and a technique register. The records must bind project/run/source identity, development and holdout boundaries, the required diagnostic categories, and falsifiable candidate routes; the gate decision must agree with the top-level status and flags. `water-quality-phase0-gate-v2` is historical-read-only and cannot authorize a new executable v2 lineage. A prose report, a historical script, or a self-authored empty gate is not sufficient.
- The only canonical v3 packaging entrypoint is `water_workflow.phase0_evidence.generate_phase0_package`. It accepts already-computed machine evidence, does not read raw data or calculate statistics, writes exactly three evidence JSON files plus `phase0-gate.json` under a fixed root outside the vault, and revalidates the published gate. Source-driven generation must use `water_workflow.phase0_generation.generate_phase0_from_source` with a strict `water-quality-phase0-generation-request-v1`; it performs structural preflight, then the scientific calculator, then the canonical producer. The calculator and runner must use the file-free `water_workflow.phase0_scientific_core`; `water_workflow.scientific` is compatibility-only and must not dynamically load historical scripts. The runner code fingerprint must cover the canonical core without appending a historical CLI. The runner now requires a fixed Phase 0/lineage binding before any run-scoped write. This entrypoint does not authorize model execution or holdout access; historical diagnostic CLIs remain `DRAFT_ONLY` and cannot become canonical authority.
- If a result is weak or inconsistent, classify it through `07-失败重做与实验谱系流程.md` before changing code or parameters. Use a new `run_id` for every non-recovery redo, preserve the old run, and record the earliest affected stage and invalidated downstream evidence. New executable redo manifests use `water-quality-experiment-lineage-v2`; v1 is historical-only. Every v2 redo must bind a read-only parent SQLite, parent result manifest SHA, and recomputable parent state SHA before the child StateStore is created.
- Data acquisition must use a fixed, timezone-aware UTC window and `ceil`-planned segments no larger than the verified source limit. Never calculate segment count with floor division, let an empty segment `break` the whole history, or use a moving `datetime.now()` inside the loop. Record every segment request, every actual retry attempt in order, empty response, row count, response columns, observed cadence, time bounds, duplicate/乱序 count, gap count, and final content hash. When a source contract freezes `response_row_limit`, the response quality gate must enforce it and classify an over-limit response as `DATA_QUALITY_HOLD`; the limit is not a substitute for coverage or cadence checks. The v2 acquisition manifest must carry `SegmentAttemptEvidence` with a finite outcome, `retryable`, `retry_scheduled`, and stable quality/error codes; never persist exception messages, credentials, raw responses, or row values. v1 manifests are historical-only: the v2 publisher must reject them with `ACQUISITION_MANIFEST_LEGACY_READ_ONLY` before creating an output directory, rather than silently converting or overwriting the historical evidence.
- Historical v1 manifests may be checked only through the read-only `water_workflow.acquisition.validate_acquisition_manifest` entrypoint. It performs a legacy structural/redaction check without adding v2 fields, normalizing or writing back the input, and it is not a publication or execution authorization path. Keep v1 and v2 validation contracts separate.
- Response cadence evidence must distinguish the declared response frequency from the client request `interval`. `quality_summary` must retain the declared frequency in seconds, the positive-transition count, a deterministic seconds-to-count `observed_cadence_distribution`, and the count of transitions that differ from the declaration; `dominant_cadence_seconds` is only a convenience field and cannot hide irregularity, gaps, duplicates, or out-of-order transitions.
- Treat source points as untrusted until the response schema and returned value columns match the frozen ledger. A missing column, all-null column, unexpectedly high null rate, non-finite value (`+Inf`/`-Inf`), unresolved unit, negative/physically impossible value, long constant plateau, duplicate/conflicting timestamp, or unexplained time gap is a `DATA_QUALITY_HOLD` or an explicitly documented quality code, never an implicit clean value. Do not fill missing values with zero by default.
- Treat instantaneous and cumulative points as different measurement semantics. Never infer a totalizer from a name or suffix. When a source ledger explicitly declares a cumulative point and supplies a justified `max_increment_per_hour`, pass the quality-approved UTC frame to `water_workflow.cumulative.derive_hourly_cumulative_increments`: aggregate with the hour-end `last` value, then `diff`; a reset (`delta < 0`), jump over the declared limit, incomplete hour, cadence problem, or invalid value is `DATA_QUALITY_HOLD` and exposes no partial derived frame. A zero increment is recorded, not silently replaced. The current North-China compatibility card selects `V_LF` instantaneous flow; do not apply cumulative conversion to it. Cumulative mappings such as `V_LFQ`/`V_GFQ` require a new explicit ledger/run and a separate audit.
- Acquisition output must use an absolute run-specific isolated root outside the source project, the Obsidian vault, and drive roots. Do not write CSVs or manifests through relative paths. Preserve canonical UTC timestamps; local timezone columns are display-only derivatives. Save per-segment evidence before sorting/deduplicating, so cleanup cannot erase quality findings.
- The additive acquisition boundary `engine/water_workflow/acquisition.py` may be used after the source contract is frozen: `plan_segments` and `validate_segment_response` are pure checks; `fetch_segments` only orchestrates a caller-owned single-segment callback with bounded retry for transport failures/empty responses, no retry for typed response-quality failures, and no empty-segment early stop; `AcquisitionFetchResult.to_manifest` and `publish_acquisition_manifest` produce create-new v2 aggregate evidence outside the vault, including the ordered per-attempt trace. The publisher must revalidate the v2 attempt trace before creating the output directory or writing a file, so a hand-authored manifest cannot forge retry order or final status. It has no network client, credentials, model, or database authority. A `DATA_QUALITY_HOLD` result must stop the handoff to Phase 0, and no caller may use this boundary as an execution authorization. Keep `fetch_segments` for synthetic or explicitly controlled callbacks only; a real external ledger must use the strict one-shot source-authorization entry.
- The additive source adapter `engine/water_workflow/iot_source.py` may be used only after the point ledger is frozen: `PointBinding` must bind the complete external point ID (base point number plus signal suffix), response alias, unit, and optional physical bounds; `IotSourceContract` must freeze the factory, source timestamp field/timezone, declared frequency, row limit, request window, and request interval with no usable implicit defaults. Omitting any of those six request semantics fails closed as `IOT_SOURCE_CONTRACT_INCOMPLETE`; do not silently turn an observed `interval=15min` into `15s` or invent a response cadence. The contract-derived `response_validation_kwargs` must carry that row limit into `validate_segment_response`, where an over-limit response is a non-retryable `DATA_QUALITY_HOLD`. For an external ledger, first create an `IotSourceLedger` declaration from an already-authorized evidence mapping; `IotSourceLedger.from_mapping` is strict, rejects extra credential fields, requires an absolute parent-free artifact path and a declared artifact SHA, and performs no filesystem access. Its deterministic `sha256` excludes self-reference. `build_iot_request` emits the black-box client's argument shape without credentials or network access; `build_iot_fetch_callback_from_ledger` constructs a lazy adapter but cannot invoke its client outside an authorized execution context. The ledger, mapping, and compatibility fetch helpers are synthetic/controlled seams and require an internal source-execution capability; the only production entry for a real source is `fetch_segments_with_external_source_authorization`. `fetch_segments` snapshots its `source_identity`, and `AcquisitionFetchResult.to_manifest(run_id=...)` automatically uses it; an explicit conflicting identity is rejected. The contract-level `build_iot_fetch_callback` is reserved for synthetic or explicitly controlled internal tests, which must still provide explicit manifest identity. Both seams fix request construction before response normalization; `normalize_iot_response` explicitly normalizes UTC and renames columns but never sorts, de-duplicates, fills, or hides unknown fields. A received schema/timestamp failure is an `IotSourceResponseError`, which the acquisition orchestrator records as one non-retryable `DATA_QUALITY_HOLD`; callback contract failures are also non-retryable; ordinary transport errors and empty responses remain the only retryable cases. Always pass the bound callback through `fetch_segments` and its result through `validate_segment_response`; this adapter is not a network client, authorization gate, or model entrypoint.
- An `IotFetchCallback` exposes a pure `request_evidence(segment)` descriptor generated from the same frozen request as the client call. For IoT-bound callbacks, `SegmentFetchEvidence.request_evidence` and the v2 manifest preserve the exact credential-free client arguments (`factory_code`, full point mapping, second-precision `start_time`, `rolling_window`, `interval`) plus the canonical UTC half-open bounds. `LedgerBoundIotFetchCallback` and the external-profile wrapper must forward this evidence. The publisher revalidates its closed schema, segment-boundary match, point mapping, and absence of credential fields before creating an output directory. Generic callbacks without this capability must not invent source request evidence; their manifest retains only the generic segment boundary. Before every actual retry client call, `fetch_segments` must regenerate and validate the descriptor; any point/window/interval/boundary drift is recorded as `REQUEST_EVIDENCE_DRIFT`, blocks that call and the rest of the segment, and leaves the prior attempt evidence intact. Each new attempt carries `request_evidence_sha256`; the first attempt must bind to the saved segment descriptor, while a non-drift retry must carry the same hash. Historical v2 manifests that omit this optional field remain readable.
- Aggregate manifests are evidence artifacts, not credential sinks. Treat `source_identity` as untrusted input: reject nested credential, token, cookie, password, secret, header, or API-key field names during result construction and again before publication, while allowing non-secret audit identifiers such as `credential_binding_id` and `authorization_id`. Preserve the more specific request/attempt validation error when malformed request evidence is found first, and never create the output directory before these checks pass.
- The current black-box evidence proves `rolling_window_observed=360min` only for a full maximum window (`rolling_window_observation_scope=full_max_window_only`). Its compatibility card therefore sets `partial_segment_policy=HOLD_UNOBSERVED`: the generic `plan_segments` rule may retain a final partial segment, but the strict source-authorization entrypoint must reject that segment during preflight, before one-shot consumption and before the caller-owned client is invoked, until a new source observation proves the partial-window argument. The compatibility callback keeps a second non-retryable guard as defense in depth. Do not infer partial-window behavior from the full-window call or from the approximately 15-second response cadence; this is a source-specific compatibility gate, not a change to the generic planner.
- When a black-box audit records source-specific physical or freeze risks, keep the requirement machine-readable in `observed_data_quality_notes.required_quality_gate`: `physical_bounds_required_for` names the affected logical points and `freeze_threshold_required=true` makes the freeze check mandatory. The profile declares the need, but never invents numeric bounds; the human `IotSourceLedger` mapping must supply explicit bounds before the external callback can be bound, and both `bind_external_iot_profile_to_ledger(..., freeze_threshold=...)` and `fetch_segments_from_external_profile(..., freeze_threshold=...)` require a positive threshold shorter than the observed maximum window. The effective quality policy is carried into acquisition `source_identity`/manifest. Missing bounds or threshold is a non-retryable `HOLD` before client invocation. The bound adapter is only callable inside `fetch_segments`; a direct call is rejected with `PROFILE_ORCHESTRATION_REQUIRED` before the client, so it cannot bypass segmentation, retry classification, response-quality validation, or manifest evidence. This source-specific gate does not change the generic contract's optional bounds or threshold behavior.
- When an external Excel ledger must be inspected, use a separately authorized `LedgerReadPermit` and `read_ledger_candidate` before constructing any `IotSourceLedger`. The candidate reader may inspect only the fixed metadata columns `设施名称`, `设备名称`, `数采点位编号`, `数采信号名称`, `是否缺失` and optional `水厂`; it must never include `数采数值` or measurement rows. It rechecks the source SHA before and after parsing, rejects missing/unknown flags, empty fields, invalid or duplicate full point IDs, path escape, and parser drift, and returns a non-executable candidate that still needs human mapping for response alias, unit, and physical bounds. A candidate is evidence, not a source contract, network authorization, or model input. Real workbook reads require a new isolated authorization run; synthetic workbook tests must go through `run_s7_tests.ps1`.
- A compatibility profile, ledger, source-code evidence hash, and callable identity are never permission to make a network request. For a real external read, use the separate code-fixed `water-quality-iot-source-authorization-v1` and the strict `fetch_segments_with_external_source_authorization()` entrypoint. The one-shot authorization must bind the profile/ledger/client identities, ordered UTC segment-plan SHA, quality parameters, protected source root, non-secret credential binding ID, run ID, and a new LocalAppData artifact root; it must be validated before the first client call and consumed atomically in a separate SQLite ledger. The strict entrypoint does not accept caller-controlled authorization paths, state/consume roots, artifact/output roots, or validation objects. It receives `profile`, `ledger`, a caller-owned `client_fetch`, and frozen `segments` as runtime inputs, but first preflights and binds every one of them to the authorization, including the client callback and source evidence, before one-shot consumption; none of them is permission. Immediately before consumption it opens and holds the already-validated authorization image and source-evidence lease, consumes once, and reuses the frozen binding/callback through the client calls and aggregate publication. It must not perform a second full preflight or rebind after consumption; drift, expiry, collision, or a second use is a non-retryable `HOLD`. The strict entrypoint may publish only an aggregate acquisition manifest and never writes credentials, raw rows, or the source project. The public low-level consume function is not an execution entrypoint and rejects direct in-memory authorization objects; only the strict coordinator may use its private consume capability. The older `fetch_segments_from_external_profile()` remains a compatibility/synthetic seam and must not be presented as real network authorization. A failed real read is not repaired in place: redo with a new authorization, run, segment-plan hash, and artifact root.
- When a source comes from a black-box external project and an observation card records point-semantic ambiguity, the card is a runtime precondition rather than a prose reference. For the fixed `beikong-ps1092-fetch-iot-data-v1` profile, the semantic gate must validate the code-fixed dual-hash identity record, the historical card file bytes, selected ledger aliases, instantaneous/cumulative suffixes, and point scope before evidence verification, client invocation, one-shot consumption, or publication. `profile_canonical_sha256` is the normalized mapping identity used by `validate_external_iot_profile`, the ledger, semantic capability, and future authorization; `profile_file_sha256` is the exact evidence-file identity, and the historical card field `compatibility_profile.sha256` means the latter only. An unresolved `NH3_in`/`NH4_in` full-point conflict, a `Flow1`/`Flow2` alias substitution, a `V_LFQ`/`V_GFQ` cumulative mapping, scope expansion, or canonical profile drift is `HOLD`; never merge, substitute, convert, or widen the mapping automatically. A passing gate issues an internal capability bound to the canonical profile SHA, identity-record file SHA, card file SHA, ledger SHA, and ordered segment-plan SHA. Every low-level `semantic_capability_matches*` call must revalidate the fixed identity record, profile evidence, and card before ledger fetch or authorization consume; a capability is not a permanent pass and becomes invalid after any fixed-evidence drift. The capability must travel through the strict consume and callback context; low-level ledger/mapping entries reject a missing, forged, stale, or differently bound capability. A profile with a different ID is only `SEMANTIC_GATE_NOT_APPLICABLE`; it still needs the ordinary source authorization and quality gates. If either the canonical profile evidence or its file bytes differ from the fixed identity record, stop for identity reconciliation and do not update an old pin in place.
- The fixed semantic evidence must be checked through the bounded `trusted_evidence_io` boundary, not by resolving a path and reopening it by name. On Windows this boundary uses handle-relative `NtCreateFile` opens with `OBJ_DONT_REPARSE`, a size cap, and handles retained across the effect interval; an unavailable native runtime, missing evidence, reparse escape, non-canonical image, or hash mismatch is a stable `HOLD`. Each low-level binding or preflight must obtain a fresh evidence lease. The strict coordinator completes binding before one-shot consumption, then obtains one fresh lease immediately before the effect interval and holds the checked identity record, profile evidence, semantic card, and authorization image through consumption, client calls, and aggregate manifest publication. Do not re-enter a closed generator context or redo a full post-consume preflight; reuse the frozen binding and callback while the lease is held. A successful earlier matcher result is never reusable after evidence drift, and the lease must be acquired before any client, consume-ledger, staging, manifest, or source-project side effect. This is a same-process governance freshness boundary, not an adversarial-process guarantee.
- Before adding or changing a real external-source caller, run `tests/test_external_iot_entry_inventory.py` through `engine/scripts/run_s7_tests.ps1`. The guard must show that production code has no unapproved call or import of `fetch_segments_from_external_profile`; only the strict source-authorization coordinator may hand its already-authorized client to that compatibility-quality pipeline. A failed inventory is a `HOLD`, even when unit tests are green.


### EvidenceSession 与 IsolatedRun owner 边界

`EvidenceSession` 是证据写入 facade，不是完整运行 owner。它只允许身份/status 只读投影、
`evidence_root`/`reports_root` 和 evidence/report/review/completion-proof 写入；不得恢复
`__getattr__`、`.run` 或任何动态代理。不得从 facade 取得完整 session `root`、state/artifact/
cache/tmp 根，也不得通过 facade 调用 `finalize`、`cleanup_ephemeral` 或 redo。需要创建终态、
清理或重做时，必须在 synthetic/隔离任务中显式持有同一个 `IsolatedRun` owner，再把它传给
`EvidenceSession(owner)`。这只是公共 API 误用防线，不是防止同一 Python 进程刻意读取私有
`_run` 的操作系统安全边界；它也不代表 direct 全链已经统一接管。
`EvidenceSession.open()` 不得用于创建隐藏 owner，当前会在任何 workspace 创建前以
`EVIDENCE_SESSION_OWNER_REQUIRED` 拒绝；这样可以避免 facade 被遗忘后留下未收口的 retained
workspace。正确顺序是先显式 `IsolatedRun.open(...)`，再构造 `EvidenceSession(owner)`，最后由
owner 负责 `finalize()` 或失败收口。

Sensitive direct-entry stage changes use `StateStore.set_stage()` with an atomic expected
`stage/state/evidence_hash` triple. A mismatch writes neither a new run state nor a `STAGE_SET`
event. Failure handling may transition to `FAILED` only from the matching `*-PLAN/EXECUTING/plan
evidence` state; PREPARED or terminal states must remain unchanged.

The direct-entry state-root slice is now `PASS_WITH_NOTES` with P0/P1 cleared. Direct compatibility
runs must derive their state database from the code-fixed `%LOCALAPPDATA%/water-workflow/direct-state`
root (or an explicitly absolute `LOCALAPPDATA` override), reject reparse/junction ancestors before
filesystem work, and use the exact `<project_id>/<run_id>/workflow.sqlite3` identity. This remains a
compatibility seam for synthetic or explicitly isolated contracts; it does not authorize real model,
holdout, or Stage 7d work. The generation-aware PREPARED GC seam is now `PASS_WITH_NOTES`, but it is
not yet wired into the three direct compatibility entries. A redo must create a new run/attempt
generation, and eventual cleanup may remove only an old, ledger-backed, TTL-eligible `ABANDONED`
staging directory after lease/intent/lock/state-root gates pass. Current PREPARED, visible revisions,
unknown orphans, and same/new-generation evidence must be retained and reported, not deleted; the
remaining P2 is the direct-entry wiring and its recovery tests.

Before any direct attempt ledger transaction, derive the generation-specific staging path and run the
no-follow reparse preflight on the leaf and every existing ancestor. A missing or broken
symlink/junction must fail as `ATTEMPT_STAGING_REPARSE` before `publication_intents` or
`publication_attempts` is created; never let `Path.exists()` alone classify a broken reparse as a new
directory. Native handle-relative identity checks remain the second fence after creation. A failed
preflight retains the pre-existing filesystem evidence and performs no automatic cleanup.


## Execution Feedback Gate

`09-任务执行反馈与技能迭代闭环.md` 的 F0–F7 是水质任务的过程证据契约。步骤结果、审查裁决和阶段出口不能只存在于对话中；在请求下一阶段或关闭任务前，从引擎目录运行同一只读校验器：

```powershell
python scripts/validate_execution_feedback.py --feedback-dir <absolute-isolated-feedback-dir> --project-id <project_id> --run-id <run_id> --require-through F5_GATE_READY
python scripts/validate_execution_feedback.py --feedback-dir <absolute-isolated-feedback-dir> --project-id <project_id> --run-id <run_id> --final
```

两个只读门各有职责：`preflight_task_state_hygiene.py` 检查任务状态和 evidence refs；`validate_execution_feedback.py` 检查 F0 路由、技能快照、反馈顺序、计划变化和最终伴随文件。反馈校验器固定解析仓库技能路径、拒绝 vault 内反馈目录；退出码 `2` 或结构化 `HOLD` 必须停止受影响的实验动作。该门不授予模型执行、holdout 读取、Stage 7d 或生产部署权限。

For a new progressive run, the canonical CLI binds feedback before it writes the
objective-ladder snapshot. The derived
`<artifact_root>/<project_id>/<run_id>/feedback/` path is recorded as an
immutable `FEEDBACK_BOUND` admission event in the same SQLite transaction as
the run, context, and lineage. The new-run gate requires the latest `F1_STEP_STARTED`;
`PLAN_FREEZE` approval requires the latest `F4_REVIEW_DECISION`; an S5/S6
transition requires the latest `F5_GATE_READY`. Missing feedback, identity/path
drift, or an old checkpoint returns structured `HOLD` before state or artifact
writes. A historical run with no `FEEDBACK_BOUND` event is explicitly
`LEGACY_COMPAT`, not silently migrated; a run that already has the event cannot
fall back to the historical path. The only no-feedback fixture adapter is the
test-only `engine/tests/_legacy_runner_fixture.py`; it is outside the production
package, is not exposed by the CLI and must not be used as a new-run production entrypoint.

## Stage Discipline

Follow the stages in `05-水质预测实验管线与状态机.md`. Human approval is required only at:

- `PLAN_FREEZE`
- `HOLDOUT_UNLOCK`
- `CLAIM_FREEZE`

Do not infer approval from silence or from a subagent recommendation.

## Step Loop

For every step:

1. For a redo, validate the new lineage and Phase 0 evidence closure before reading model data or creating a model artifact.
2. Send `F1 STEP_STARTED` in Chinese with the step goal, inputs, risk, completion criteria, and expected review route.
3. Execute one registered workflow stage or checklist item.
4. Send `F2 MATERIAL_CHANGE` immediately when a material fact, risk, scope, or plan changes; stop first when the change is blocking.
5. Commit an immutable artifact revision and update canonical SQLite state.
6. Send `F3 STEP_RESULT` with facts, inferences, unresolved questions, evidence refs, and the next action.
7. Route review by risk using `04-步骤回写与子智能体审查闭环.md`.
8. Let the main agent adjudicate every finding as `ACCEPT`, `PARTIAL_ACCEPT`, `REJECT`, or `DEFER` with evidence, then send `F4 REVIEW_DECISION`.
9. Resolve all P0/P1 findings and run fresh verification.
10. Send `F5 GATE_READY` or `F6 HOLD_OR_INPUT` before requesting a transition or user decision.
11. Let the engine atomically claim an approved transition. Hooks delegate to the engine gate and must not maintain a second state machine.

For scientific execution, stop the affected transition on an unresolved P0/P1 and diagnose it in isolation. For an explicitly authorized autonomous maintenance task, use the current task acceptance criteria and require new evidence or a concrete repair each round; continue until those criteria pass. Repeated attempts with no progress require a changed approach or a concrete blocker report. Never reinterpret maintenance progress as experiment admission.

The complete feedback and skill-evolution contract, including the 20-minute long-task cadence, Chinese user-facing format, route records, skill-improvement candidates, and skill snapshot rules, is `<方法体系根>/09-任务执行反馈与技能迭代闭环.md`. A long task must not remain silent until its final report. Every completed task must include a Chinese skill-learning summary, even when it records `skill_learning=NONE`.

## Agent Routing

- Contract/design: 规划员 + 实验设计员
- Time semantics/leakage: 数据审计员
- Water/process interpretation: 水质研究智能体
- Feature/training/ablation: 特征工程师 + 训练执行员 + 消融协调员
- Code change: 代码审查员 by risk
- Result/claim: 模型评估员
- Stage/final verification: 验收员

Subagents advise; the main agent owns route decisions. Outer holdout never selects models.

## Completion

For a scientific run, completion requires the frozen plan, applicable immutable artifacts and hashes, adjudicated findings with no applicable P0/P1, source protection in `READONLY_COMPAT`, QA, applicable `F0-F7`, and evidence for the human gates reached. Declaring the whole scientific run complete requires all three human gates. Use the entrypoint maintenance criteria for skill/code-only work; do not create experiment state or demand scientific gate approvals solely to finish maintenance. State the skill-learning disposition and snapshot used.
