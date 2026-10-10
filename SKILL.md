---
name: water-quality-experiment
description: Use when planning, preparing, running, reviewing, resuming, reporting, or maintaining a water-quality time-series prediction workflow, including source quality, leakage-safe validation, workflow evidence, skill maintenance, and paper-claim gates.
---

# Water Quality Experiment

先确定当前任务和验收范围，再按需读取证据。实验运行使用受测引擎；技能维护完成后，应交付可用的实际技能和验证结果。

## 首步：保持用户当前目标

记录任务类型、已授权动作、只读/写入边界、证据来源、完成条件和尚待决定事项。从当前任务的冻结合同、交接和实际代码核实状态；旧报告中的测试数属于那次报告，不是本轮验证。

- **维护技能/代码/文档**：继续已授权的可逆维护，固定计划和源文件基线，做必要复现、修复、反馈、审查与新鲜验证。即使实验状态是 `03 partial / 04 blocked / HOLD`，仍可完成本次维护。明确交付实际源文件；历史票据的下一阶段仅作为背景。实验执行门禁只约束涉及它的动作。
- **新项目准备**：分别核实 `project_id`、`run_id`、`target`、`horizon_steps` 四个字段。单独的 `cod_in / h1` 是目标/步长简称，不能据此认定 project/run 身份；身份从冻结请求/合同的对应字段定位，缺失时不猜测。读取00入口、来源门08和当前合同，走 project preparation；PASS只准 Phase 0 preparation，不能启动模型或读取 holdout。
- **运行/恢复/重做实验**：定位明确的 project/run 和冻结合同，再读取05状态机、09反馈及当前步骤证据；重做加07谱系。缺失身份或证据保持 HOLD，先只读诊断。
- **结果/论文声称**：读取冻结评估协议和实际结果证据；跨工况/跨厂结论须有注册协议和对应验证。原始指标、显著性和效果量不能凭空补齐。

执行准备前，先核对实际已实现的项目/目标/时间口径。当前 `register-project / project-preflight` 只支持 `qinhuangdao-periodicity-innovation`、`qinhuangdao-tn-in-h1-*`、`tn-in`、`1D` 及代码固定来源和时间窗（`engine/water_workflow/project_preparation_admission.py`）。秦皇岛 COD 或其他组合只能先做只读合同/能力缺口审查，不能通过换名成 TN、猜 ID 或回退 current 取得准入。`h1` 是一个预测步，实际时长由冻结频率决定；`1D` 下不是一小时。

使用 `ask-matt` 的路由思想：已有目标采用已有文档与具体验收；失败先最小复现；实现先固定规格再逐片修复；大未知才做探索。它位于 `<skills-root>/ask-matt/SKILL.md`，缺失时说明并直接采用以上路线。在 F0 或目标/权限/协议出现实质变化时记录 `route`、`route_reason`、`destination`、`unresolved_decisions`、`next_frontier`。用户既有“按推荐/确认/继续”的授权持续有效；可从代码核实的事实由代理查明。需要新的真实授权时才请求人类决定。

## 按需加载

方法体系根目录：`<方法体系根>/`，所有下述00–09文件名都相对此根目录。先读 `00-水质预测实验总入口.md` 的当前场景路由；通常一次只加载4–6份当前必需文件，证据索引用于定位，不展开整个 vault。

| 当前动作 | 本技能参考 | 体系证据 |
| --- | --- | --- |
| 准备、科学运行、反馈、EvidenceSession owner | [实验与反馈](references/experiment-execution.md) | 当前合同、05状态机、09反馈；选型才读03，目标阶梯才读06，重做才读07 |
| API、外部导出、历史快照、来源授权与测点语义 | [来源与取数](references/source-acquisition.md) | 08来源门、当前冻结请求/来源证据；本轮没有真实取数授权就只读 |
| 修改代码、执行合成回归或检查 CLI | [测试隔离](references/test-isolation.md) | 所改代码和必要测试；使用固定 Windows runner |
| 操作 legacy current task、交接、selector 预览 | [任务状态](references/task-state-hygiene.md) | 只读任务状态/证据审查；新项目准备和纯技能维护不继承 global current 的执行准入 |

资源完整性用 [只读校验脚本](scripts/check_resources.py)。从仓库根运行：

```powershell
python -B -X utf8 .agents/skills/water-quality-experiment/scripts/check_resources.py
python -B -X utf8 scripts/audit_operational_entrypoints.py
```

入口末尾清单绑定每个参考文件与脚本的精确字节。新增/修改资源必须同步更新清单并重新验证；不直接执行参考文件。资源校验失败时，停止依赖该资源的动作，报告具体缺失或漂移并修复维护候选。文件适配器会在 F0 创建/核验时检查绑定资源；当前 `water-quality-skill-snapshot-v1` **仍只有固定五个角色：SKILL.md、09、00、04、05**，纯五文件捕获校验不证明参考文件的实际字节、完整协议闭包或 native 租约。06/07、方法模块、合同/计划/Gate/代码指纹在各自适用证据中记录。清单与运行时读取校验也不构成对抗进程的同句柄保证。

## 不可省略的科学与权限约束

- 时间预测先固定时间语义、样本构造、开发窗/CV/outer holdout 和 baseline；避免随机时间切分、未来信息泄漏、在 holdout 上选模。**Outer holdout never selects models.** 没有来源质量证据不能开始特征或模型阶段。
- 新运行显式 `project_id + run_id`，SQLite/WAL 是规范机器状态。准备 registry 不等于实验 workflow.db；不能用手写 task JSON、旧 selector 或合成 fixture 代替生产准入。
- 历史项目提供数据时使用 `READONLY_COMPAT`，受保护项目内不得落数据库、模型、报告、缓存或临时副本。审计/预览 PASS、合成测试 PASS、纯字节比较 PASS 各自只证明其声明范围。
- 不把“我是数据所有者”这类口头身份声明转换为签名者身份、配置或可验证授权。缺失 issuer/profile/ledger 保持未配置；未知 DB/行状态保持未知。真实取数、模型、holdout、生产切换各自需要相应授权和实际引擎支持。
- 科学运行的人工门为 `PLAN_FREEZE`、`HOLDOUT_UNLOCK`、`CLAIM_FREEZE`。沉默、代理推荐、维护验收或 Phase 0 PASS 不能替代这些批准。旧运行使用其冻结规则；技能源文件更新不重新授权旧运行。

## 执行与反馈

每片先列完成条件，执行后区分事实、推断、未验证项；把证据和路径记录到本片拥有的输出位置。实验运行按09保存适用的 `F0–F7` 与固定 skill snapshot，按引擎原子状态迁移；维护候选记录计划、基线、真实修复、测试/审查裁决和技能学习，不为了维护另起真实实验或写旧 run 状态。

代码/文档改变时，审查规格是否满足当前任务、行为是否符合真实引擎。独立前向测试只提供用户请求、技能及最小必要材料，不给预期答案或已猜到的缺陷。主代理逐条裁决 `ACCEPT / PARTIAL_ACCEPT / REJECT / DEFER`；子代理提供建议，主代理负责最后决定。

每轮应新增有效证据或完成一个修复。用户明确要求自主迭代时，持续完成已授权范围，直到本次验收通过；只有实际缺失的决定/权限、不可恢复错误或重复无进展才停止相关动作并说明原因。P0/P1 不得带入发布；可继续隔离诊断和修复。不要因为历史 repair loop 的轮次数或未发行的下一阶段停掉当前已授权维护，也不要反复测试已有充分证据的低风险改动。

## 完成条件

**技能维护**：实际入口与按需参考可用；资源身份和操作入口审查通过；改动所需回归及独立行为验收完成；本次适用的 P0/P1 已解决；报告变化、理由、测试、技能学习、回滚基线和仍未发行边界。只读设计/审查按约定产物与证据范围完成。未实施的建议不能当成已完成。

**实验运行**：完成冻结计划与当前阶段的适用证据、不可变产物/哈希、来源保护、QA、反馈与人工门。只有声明完成整个科学运行时，三个科学人工门均须有实际证据。不要将维护完成写成 `03 COMPLETE`、`04 READY`、模型准入或生产放行。

最终状态分别记录 `maintenance_status`、`experiment_status`、`release_status` 和未验证项；给出用户可直接复用的技能与验证记录。

<!-- water-quality-skill-resources-v1
{
  "schema": "water-quality-skill-resources-v1",
  "files": [
    {
      "path": "references/experiment-execution.md",
      "bytes": 32562,
      "sha256": "fafa8f003820528d149fd5690f0edc1095ee078542b7e3fb5ee5428cea61e231"
    },
    {
      "path": "references/source-acquisition.md",
      "bytes": 22763,
      "sha256": "313de531eb5ad00d29420a2f0aafecea3ee4e2034d4bda3d164e8ee9410e815d"
    },
    {
      "path": "references/task-state-hygiene.md",
      "bytes": 23585,
      "sha256": "bf604fef3e6fce588d073c74d45ed4fd9941fefbb5070365621080f26e77123c"
    },
    {
      "path": "references/test-isolation.md",
      "bytes": 3583,
      "sha256": "977c8457ea8a7d44bdd57d27b8ec180e6334ff4bd55bbfe5f5ff8560d837b27a"
    },
    {
      "path": "scripts/check_resources.py",
      "bytes": 6145,
      "sha256": "d984e080772a9aea3c15c780ffab36cd9a61914c0e06be7a9ac5bafac0e52911"
    }
  ]
}
-->
