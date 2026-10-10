# Legacy 任务状态与交接预览

本参考适用于 global/current legacy 任务及其交接审查。新项目准备使用显式 project/run；纯技能维护只读必要背景，不把当前实验的 HOLD 当成维护准入。文中的 task-state、selector 与迁移都是各自声明范围的操作，预览不能转换成生产授权。

## Task-State Hygiene

使用既有全局选择器开始、恢复、重做长任务和请求下一门禁前，必须先运行仓库根目录的当前任务只读执行门；独立项目的准备期准入使用前述 project-preflight，不借用其他项目的选择器：

```powershell
python scripts/preflight_task_state_hygiene.py --current-scope
```

该入口固定从仓库根读取 `.claude/task-states/active/`，只评估唯一当前任务，输出 `scope=current_task` 的结构化 JSON，不修改任务状态。退出码 `0` 表示 `PASS`，`1` 表示 `REVIEW_REQUIRED`，`2` 表示 `HOLD`；当前任务执行门要求 `PASS` 且退出码 `0`。按当前作用域结果分流：

- `PASS`：继续读取当前任务的计划、结果和门禁证据；
- `REVIEW_REQUIRED`：停止当前任务推进；先完成人工复核，不能把它当作当前任务放行；
- `HOLD`：停止推进，先处理解析错误、多个 current 或非法状态。

仅需查看生命周期分类时，可补充运行 `python scripts/audit_task_state_inventory.py`；仅需查看 path/SHA256 引用时，可运行 `python scripts/audit_task_state_evidence.py`。统一预检的 `HOLD` 不得被拆分命令的局部 `PASS` 覆盖。

当前任务门与全库维护审计分层：全局命令无参数时严格汇总所有历史状态，输出 `scope=global_maintenance` 且 `execution_admission=false`；它是维护队列输入，不是当前任务执行授权。全局 `REVIEW_REQUIRED` 或 `HOLD` 仍要求维护审查，且不得自动迁移。水质实验写入入口和 canonical h1 admission 使用固定根的当前作用域门：

```powershell
python scripts/preflight_task_state_hygiene.py --current-scope
```

在 selector 缺失的兼容窗口内，当前作用域门只允许恰好一个 `active=true,current=true` 的 `task-state-v2` 且 `hook_enforced=true` 任务，并重新核验该任务的 evidence refs。selector 一旦存在，固定的 `.claude/task-states/current-selector.json` 才是全局任务的唯一选择真相源；它必须绑定 active 根直接子项的原始字节、`task_id`、`run_id` 和 SHA256，选中的状态可以保留 `current=false` 派生缓存。selector 损坏、漂移、重解析、multilink、目标不存在或证据不通过都直接 `HOLD`，绝不回退到 current 扫描；selector 模式下其他状态的旧 current 标记只作为维护审计信息。脚本接受无参数、精确的 `--current-scope`，或精确的 `--project-id <id> --run-id <id>` 项目准备期查询；未知参数直接 `HOLD`，不解释调用方路径或配置。项目查询的 `PASS` 仅放行已登记的 Phase 0 准备，不授权模型或留出集评价。两类只读门均不创建或改写状态、SQLite、artifact、缓存、raw 或 holdout。

保护项目根是固定路径契约，不是调用方可传入的配置：`<仓库根>/<受保护项目根 A>` 与 `<仓库根>/<受保护项目根 B>`。`preflight_task_state_hygiene.py`、`audit_task_state_evidence.py`、`preview_selector_reader_migration.py` 和 `preview_new_run_handoff.py` 必须使用同一组根；若入口把保护根解析到仓库根下的同名目录，视为审计失效，必须修复并回归，不能把 `PASS` 当作有效保护证明。

当前作用域预检还会运行固定根的规范入口审计，覆盖本技能、两份当前流程文档和 `engine/scripts`。可执行说明不得直接调用 `pytest` 或 `python -m water_workflow`；只有 `run_s7_tests.ps1` 和 `run_water_workflow.ps1` 可以拥有对应子进程。发现裸入口、包装器契约漂移、固定路径不可读或 reparse 解析时，当前任务直接 `HOLD`。历史报告与标记为 `DRAFT_ONLY` 的旧示例不作为操作入口扫描，审计不会修改历史文件。

当前作用域预检还会输出 `feedback_coverage`。对 `water-quality-progressive` task-state，缺少引擎 `FEEDBACK_BOUND` 证明时只能标为 `LEGACY_COMPAT_NO_BOUND_FEEDBACK / REVIEW_REQUIRED`，`next_gate_admission=false`；task-state 中自声明的 binding 也不能替代引擎 SQLite 和反馈校验器。该审计不自动补写 F0-F7、不迁移历史任务；结构性 `execution_admission` 与“是否可以请求下一门禁”必须分开理解。

需要单独核对当前任务的反馈覆盖时，运行固定根的 `python scripts/audit_current_task_feedback.py`。退出码 `0/1/2` 分别对应覆盖通过、需要人工复核、硬性 HOLD；只有覆盖通过才可把 task-state 作为下一门禁的过程证据。该入口只读，不扫描 raw/holdout 或历史 C 盘目录；若 task-state 带有 `feedback_binding_ref`，只会按固定根核验引擎 SQLite 绑定和 F1 反馈包。

需要判断历史任务能否继续、还是必须新建 run 时，紧接着运行固定根的 `python -B scripts/preview_current_task_continuation.py`。CLI 先执行既有的 current-scope 只读预检（包括证据哈希审计），预览模块只消费已选中的编排元数据和反馈覆盖分类，不自行跟随或暴露 `evidence_refs`，也不读取 SQLite、raw、holdout 或反馈 bundle，不写任何文件。`LEGACY_TASK_REQUIRES_NEW_RUN / STALE_FEEDBACK_REQUIRES_NEW_RUN` 表示旧 run 不能请求下一门禁；后者专门表示 F0 技能、反馈或核心文档快照哈希已漂移，agent 应自动转入“准备新 run + 新鲜 F0/F1”路径，不反复请求用户确认，也不得覆盖旧反馈。旧合同和结果最多作为父证据候选重新核验。只有 `ENGINE_BOUND_CONTINUATION_READY / PASS` 才能转入具体阶段门，`ENGINE_FEEDBACK_BOUND_EVENT_MISSING / HOLD` 只能完成 canonical admission，严禁手工回填。该预览不是迁移器、授权器或模型执行入口。

当 continuation 预览返回 `STALE_FEEDBACK_REQUIRES_NEW_RUN` 时，agent 应直接运行固定根的 `python -B scripts/prepare_fresh_child_run.py`。这是唯一的自动重做准备入口：它从当前 selector/active 状态读取父 run，只把旧合同、Phase 0 聚合证据和 lineage 作为只读父证据候选，派生递增的 child `task_id/run_id/project_id`，在新的隔离 artifact 根生成新鲜 F0/F1、重新核验 Phase 0 闭包并建立新的 lineage。它必须拒绝 caller 提供的身份、根目录、反馈目录或授权参数，并且必须具备幂等性；已有同一 child 准备结果时只读返回，不重复生成或覆盖证据。

该入口的成功状态是 `FRESH_CHILD_PREPARATION_READY`，不是“任务已开始”：

- 允许写入的范围只有新的隔离实验目录和固定 LocalAppData 下的新反馈/lineage 证据；
- `current-selector.json`、`.claude/task-states/active/`、生产 SQLite、授权、raw、holdout、模型和旧 run 均不得写入、消费、覆盖或回填；
- child task-state 只能作为 `current=false`、`allow_start_progressive=false` 的 admission 候选；
- 下一门固定为 `NEW_CHILD_TASK_STATE_ADMISSION`，必须重新运行 current-scope hygiene、feedback registration 和 trusted handoff preview，不能把准备结果当作 current promotion；
- 技术 `HOLD` 由 agent 自动保留，不需要为了“是否重做”反复请求用户确认；只有真正的 PLAN_FREEZE、HOLDOUT_UNLOCK、CLAIM_FREEZE 或技术无法判断的输入缺失才进入人工门。

若脚本返回 `FRESH_CHILD_PREPARATION_ALREADY_PRESENT`，应复用并只读复核该 child 证据；若返回 `HOLD`，必须保留父 run 和已生成证据，不得重试覆盖。旧 feedback、旧 task-state、旧 artifact 和旧授权永远只能作父证据，不能通过新 run 追认旧事实。
若某个已存在的隔离 child 的 F0 快照又因技能维护而失效，准备器必须保留该 child 并递增到下一个 sibling；
该 sibling 仍直接绑定原始父 run，不把未 admission 的 child 伪装成新的父 run。

准备结果生成后，必须运行固定根只读门 `python -B scripts/preview_new_child_task_state_admission.py`。它只读取最新
隔离 child、当前 active 状态和代码固定的 task-state admission 契约，分别输出 child 结构/仓库内证据是否通过，
以及固定根是否能实际接受该候选。`NEW_CHILD_TASK_STATE_ADMISSION_READY` 只表示可交给
`manager_guard` 登记；`NEW_CHILD_TASK_STATE_ADMISSION_BLOCKED` 必须保持 `HOLD`。历史 active 文件的
文件名/`task_id` 不一致、证据路径不合规、反馈绑定失效或 selector/当前状态不一致，都要在此门暴露，不能
通过手工改名、删除历史 JSON、聊天确认或把 child 标成 current 绕过。该预览永远不写 task-state、selector、
SQLite、feedback、raw、holdout 或授权。

当预览要求新 run 时，还必须运行固定根的 `python -B scripts/preview_new_run_handoff.py`。它只读取当前任务作用域和代码固定的 H1 设计证据，验证 child 的新身份、父 task/run、`IMPROVE_MODEL` 谱系、新 feedback/artifact 根和父资源不可复用规则。`PASS / NEW_RUN_REPLACEMENT_READY` 只表示交接候选结构完整，并把下一门固定为 `HANDOFF_DECISION`；它不构成人工审批，也不授予写入权。`HOLD` 表示当前门、设计证据或父子身份不一致。旧 `REVIEW_REQUIRED / NEW_RUN_REPLACEMENT_REQUIRED` 仅可由显式兼容映射解释为“历史候选结构完整、无授权”，不得默认通过。旧 current 的退役与 child current 的晋升必须通过未来受控的单次原子交接，禁止分别编辑两个 JSON、制造中间零 current 或双 current。该入口不登记 task-state、不写 SQLite、不触碰授权、raw、holdout、模型或 artifact。

该 CLI 还会输出独立的 `handoff_commit_readiness`。当前固定根 writer 已完成实现审查但仍未 release；因此候选预览可以是 `PASS / NEW_RUN_REPLACEMENT_READY`，提交就绪门仍必须是 `HOLD / ATOMIC_HANDOFF_WRITER_NOT_ENABLED`，`atomic_handoff_writer_status=IMPLEMENTED_NOT_ENABLED`，`handoff_commit_admission=false`，`next_gate=HANDOFF_DECISION`，命令退出码为 `2`。隔离 writer 只能在 pytest 临时仓库中验证协议，固定根生产 writer 在 release 前不得写真实 selector 或 task-state。这不是异常，也不能由人工确认覆盖；在生产 release、崩溃恢复证明、全入口一致性和单 current 不变量通过独立审查前，禁止手工编辑两个 task-state JSON、退役旧 current、创建 child current 或进入下一门禁。

生产 handoff release 还必须运行固定根只读门 `python -B scripts/preview_production_handoff_release.py`。初始、常规和恢复入口先把 candidate、current selector、generation、task-state、证据、反馈及恢复身份规范化为同一个 `HandoffObservation`，再交给代码固定的 `HandoffDecision`；现在三入口必须先经过 `.claude/hooks/trusted_handoff_observation.py`：所有输入冻结为 canonical byte images，身份角色必须绑定固定根文件，派生值必须闭合 provenance graph，bundle 只能一次性消费。缺源、部分 capture、证据漂移或 bundle 重放都返回 `CAPTURE_BLOCKED`/技术 `HOLD`，不得 fallback 到松散字典兼容层。该决策在敏感边界重验单字节镜像身份，并把最终授权交给 `AutonomyDecision`。技术条件未满足时按模式输出 `HOLD / {INITIAL|REGULAR|RECOVERY}_HANDOFF_RELEASE_BLOCKED`；全部满足时输出 `AUTO_ADMIT / {INITIAL|REGULAR|RECOVERY}_HANDOFF_RELEASE_AUTO_ADMITTED`。handoff 不是第四个人工门；旧 `REVIEW_REQUIRED` 仅是显式兼容输入且永不授予 authority，未知状态一律 `HOLD`。该预览本身永远不启用 writer，只提供结构化放行证据；后续写入边界仍须复核同一证据身份和策略裁决。selector generation 过期、反馈漂移、证据漂移、恢复证据不完整、current 歧义或其他技术阻断必须保持 `safe_to_enable_writer=false`，用户确认也不能覆盖该 `HOLD`。

预览之后还必须运行独立审查 `python -B scripts/review_trusted_handoff_release.py`。它在子进程中读取 fixed-root INITIAL/REGULAR 预览，独立检查 trusted seam 的固定模块身份、caller 参数边界、代码签发的 `ObservationImage`、one-shot replay、capture 无 fallback 和三模式覆盖。该审查输出 `status=PASS` 只表示“门禁行为可观察且保守”，绝不等于 production release；`production_release_authorized=false`、`production_writer_enabled=false` 或任一 fixed-root preview 为 `HOLD` 时，必须保持 writer 关闭。REGULAR/RECOVERY 候选证据未闭环时，审查报告必须继续列为 blocker，不得用人工确认或审查 PASS 绕过。

当 regular handoff preview 因反馈快照漂移、候选 child 未被 admission 或 lineage 证据不足而返回 `HOLD` 时，继续运行固定根只读诊断 `python -B scripts/review_handoff_candidate_evidence.py`。它只汇总 selector、active child、反馈摘要、run-creation 历史报告和 lineage 是否存在，输出稳定原因码与下一步动作；它不能刷新旧反馈、补写 lineage、创建候选、提升 current 或启用 writer。`FEEDBACK_ENGINE_BINDING_NOT_VERIFIED` 与 `F0_*_SNAPSHOT_*_HASH_MISMATCH` 表示必须创建新的 child run 并重新生成 F0/F1 快照，不能覆盖旧 `execution-checkpoints.jsonl`；`LINEAGE_EVIDENCE_MISSING` 表示必须经 canonical `prepare-lineage` 重新准备并验证；只有候选身份、反馈绑定、lineage 和 handoff preview 同时闭环后，才允许重新运行 trusted release review。该诊断通过也不构成 production release 授权。

在生产 selector writer 尚未启用前，可运行固定根的 `python -B scripts/preview_selector_migration.py` 做只读预览。若固定根尚未观察到有效 selector authority，结果仍为 `HOLD / SELECTOR_NOT_MIGRATED`；若运行时已经观察到有效 selector authority，但尚未完成旧状态、反馈、证据和 current 的一致性对账，结果必须明确为 `PASS_WITH_NOTES / SELECTOR_AUTHORITY_OBSERVED_REQUIRES_RECONCILIATION`。后者只是权威观察结果，不是迁移放行：两种结果都保持 `selector_migration_admission=false`，不分配真实 generation，不创建或替换 `current-selector.json`；该预览不能替代读取方接入、迁移对账或旧的多文件审计状态。

`.claude/hooks/task_selector_protocol.py` 是 selector 的纯协议层：只校验调用方已经读取的 canonical bytes 和状态镜像，不按路径读文件、不写 selector、不迁移 task-state，也不决定 current。它固定字段闭集、状态 SHA、task/run 身份和正整数 generation，并拒绝 `SELECTOR_NON_CANONICAL_BYTES`。当前读取方迁移切片已接入 `manager_guard`、current-scope preflight、inventory/迁移预览和 feedback registration；在 writer release、崩溃恢复和提交门仍未通过前，task-state 的 `current` 只能作为派生缓存，协议层不能把 `SELECTOR_AUTHORITY_OBSERVED_REQUIRES_RECONCILIATION` 误当作迁移完成，也不能解除 selector reconciliation 或 handoff commit 的技术 `HOLD`。

在 selector writer 实施前，可运行固定根的 `python -B scripts/preview_selector_reader_migration.py`。它只读取 current-scope 选中的状态字节，生成内存中的 preview generation `1` 并与 legacy 选择对账；未观察到有效 selector authority 时结果为 `HOLD / SELECTOR_NOT_MIGRATED` + `PREVIEW_MATCHED`；观察到有效 authority 但仍需对账时结果为 `PASS_WITH_NOTES / SELECTOR_AUTHORITY_OBSERVED_REQUIRES_RECONCILIATION`，并额外标记 `reader_consistency_status=AUTHORITY_OBSERVED_REQUIRES_RECONCILIATION`。两种结果都不创建 `current-selector.json`，不提交任何迁移，且 `production_readers_rewired=false`。若真实 selector 已存在，读取方会验证其固定路径、原始字节、generation、状态 SHA 和 task/run 身份；状态字节、task/run 身份或固定根检查失败时必须 `SELECTOR_PROTOCOL_MISMATCH`/`HOLD`，不得 fallback。

读取方迁移切片完成后，`task_selector_reader.py` 成为四类只读入口共享的选择层：`manager_guard`、current-scope preflight、task-state inventory/迁移预览和 feedback registration preflight。selector 不存在时它只报告并保留各入口原有兼容规则；selector 存在时所有入口都使用同一 selector/state 原始字节校验，`current` 仅为派生缓存，损坏或读取失败一律 `HOLD`。`task_selector_writer.py` 已增加固定根生产形态 writer，但 `PRODUCTION_WRITER_ENABLED=false`；隔离测试仍验证持久锁、create-new child、selector 原子替换、发布后复读、前后切换失败和双进程竞争，外部 watchdog 测试还必须真实终止子进程，覆盖 child 完成、selector 临时文件完成、selector 已替换三个断点，并通过只读恢复诊断确认权威和证据状态。`commit_current_handoff()` 仍是无参数的生产 facade，固定返回 `HOLD / ATOMIC_HANDOFF_WRITER_NOT_ENABLED`，不会创建真实 `current-selector.json`。在生产 release、崩溃恢复、并发和全入口一致性最终审查前，不得手工改动两个 task-state 来交接。

当前恢复实现仍只在隔离仓库受控验证。`IsolatedSelectorWriter.recover_and_finalize()` 只处理一种可证明状态：selector 已存在且有效、selector 选中的 child 仍在 active、active 中恰有一个额外的 current parent、child lineage 明确指向该 parent、parent 原始字节未漂移且 archive 目标无碰撞。它只归档该 parent，然后复读 active 集合、selector 原始字节和 child 身份；缺 selector、损坏/漂移、多个 orphan、父子身份不一致或 archive 冲突一律 `HOLD`，不猜测、不删除证据。归档已发生但最终复核失败时必须返回 `HANDOFF_RECOVERY_POST_MUTATION_HOLD` 与 `mutations_performed=true`，不能误报为零副作用。`ProductionSelectorWriter.recover_and_finalize()` 与 commit 共用 release gate；当前生产 flag 仍为 false，不解析真实根、不创建 selector、不改变当前 H1。
生产 `recover()` 只读诊断不得创建锁根；只有 commit 或已明确 release 的恢复动作才允许准备固定锁根。这样即使当前 selector 尚未迁移，做状态诊断也不会给 vault 或 LocalAppData 增加目录副作用。

回归结果必须区分“范围通过”和“全量通过”。任何 runner 硬超时、子进程被终止、输出截断或未得到最终 pytest 退出码，都统一记为 `TIMEOUT_NOT_COUNTED_AS_PASS`，不能用聚焦测试的 `PASS` 覆盖。超时后必须确认本轮测试树已终止、`TEST_TEMP_CLEANUP: OK`，并保留已观察到的进度和耗时；不得仅为得到绿灯盲目延长超时。需要继续验证时，按测试文件或明确功能域拆成多个经 runner 的 shard，每个 shard 都有自己的超时、退出码、清理结果和可追溯报告；慢 shard 单独定位后才能决定是否修复测试、调整预算或记录长期维护风险。`50x`、外部 watchdog、真实子进程和统计重型测试不得被隐式混入普通快速回归，也不得因未运行而声称全量完成。

为避免手工拼接大批测试文件，使用固定根入口 `engine/scripts/run_s7_regression_matrix.ps1`。它只调用 `run_s7_tests.ps1`，不直接拥有 pytest；`Fast`（默认）按 4 个确定性 shard 排除稳定性/watchdog/50x/统计重型文件，`Extended` 用显式 shard 覆盖所有非 50x 文件（普通文件合并为一个组，重型文件在 shard 内逐文件运行），`Heavy` 把每个重型文件单独运行并要求显式选择。先用 `-DryRun` 核对文件清单，再执行对应 profile；任何分组失败或超时都停止后续组并保持 `HOLD`。例如：

```powershell
powershell -File "<方法体系根>/engine/scripts/run_s7_regression_matrix.ps1" -Profile Fast -DryRun
powershell -File "<方法体系根>/engine/scripts/run_s7_regression_matrix.ps1" -Profile Fast -ShardIndex 0
powershell -File "<方法体系根>/engine/scripts/run_s7_regression_matrix.ps1" -Profile Extended -ShardCount 4 -ShardIndex 0
powershell -File "<方法体系根>/engine/scripts/run_s7_regression_matrix.ps1" -Profile Heavy -DryRun
```

新建的 progressive task-state 如要连接引擎反馈，只能增加精确的 `feedback_binding_ref`（schema 为
`water-quality-task-feedback-binding-ref-v1`，包含 `project_id`、`run_id`、声明的 `artifact_root` 和
`state_store_path`）。固定根审计会从 OS LocalAppData 重新推导路径，先做绝对路径/`..`/reparse 门，再只读查询
SQLite `FEEDBACK_BOUND`，最后验证由引擎派生的 F1 反馈目录。只有 `ENGINE_BOUND_AND_VERIFIED` 才会把
`next_gate_admission` 置为 `true`；引用本身不是授权，也不替代 PLAN_FREEZE 或阶段 F4/F5 门。旧的
`feedback_binding` 自声明字段、缺失引用和引擎事件缺失都不能自动迁移或 fallback；当前 H1 不因本维护切片被回写。

登记顺序固定为：`feedback-bootstrap` 生成 F0/F1 -> `validate_task_feedback_registration.py`
只读核对 -> 把返回的 `task_state_patch.feedback_binding_ref` 合并到新 task-state 并通过
`manager_guard` 写入 -> `start-progressive` 重验 F1 并在同一事务写 `FEEDBACK_BOUND`。登记后、启动前
若 `audit_current_task_feedback.py` 报告 `ENGINE_FEEDBACK_BOUND_EVENT_MISSING`，这是待启动的中间态，
不能把它当作失败修复，也不能绕过 `start-progressive` 手工写事件；启动后才应变为
`ENGINE_BOUND_AND_VERIFIED`。登记预检或启动重验失败时保留已有 F0/F1 证据，不删除、不覆盖、不重用其他 run。

`REVIEW_REQUIRED` 和 `HOLD` 都不得自动归档、删除、移动或改写任务状态。`active=true` 且 `current=true` 但缺少 `hook_enforced=true` 的记录，不能被静默当成没有任务；必须保留审计结果并由主智能体或用户明确裁决。该审计不修改 `manager_guard`，不读取 raw/holdout，也不替代 SQLite、人工门禁或独立审查。

需要判断旧状态如何处理时，只能先运行固定根只读预览 `python scripts/preview_task_state_migration.py`。它只列出 v2 缺口和人工选项：`0` 为无迁移事项，`1` 为需要人工选择升级/归档/重建，`2` 为必须停止的 HOLD。该预览不读取 `evidence_refs` 指向的文件，不接受 `--root` 等路径参数，也不执行迁移；真正升级仍须由 `manager_guard` 对完整 `task-state-v2` 候选做 admission。

task-state 的 schema 名称、终态集合、分类集合和 v2 必填字段唯一来源是仓库根 `.claude/hooks/task_state_contract.py`。inventory、admission 和迁移预览必须引用该只读契约，不得在各自模块复制近似定义；新增状态语义先更新契约和行为测试，再更新消费者。

`water_workflow` CLI 已在写入型命令 `phase0-generate`、`start-progressive`、`continue`、`approve` 进入业务逻辑前实际调用同一固定根预检；预检不是 `PASS` 时命令以 `HOLD` 退出。`status`、`gate`、`report` 保持只读可用，用于查看和取证；不得通过旧入口绕过写入门。

