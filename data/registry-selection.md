# CT.gov ALS 精选登记范围

本清单是中文 ALS 药物监测站使用的**精选子集，并非 ClinicalTrials.gov 的全部 ALS 研究**。本次通过 ClinicalTrials.gov API v2 `/api/v2/studies` 查询 `query.cond=Amyotrophic Lateral Sclerosis` 与 `filter.overallStatus=RECRUITING,ACTIVE_NOT_RECRUITING,NOT_YET_RECRUITING`，使用分页令牌完整读取 3 页（100、100、82 条；共 282 条），而不是仅用首批结果。随后优先保留明确涉及 ALS、`INTERVENTIONAL` 且包含药物或生物制品干预的研究，排除观察研究、单纯器械/手术或诊断示踪剂研究；对多疾病研究检查其登记条件及干预相关性。

初始收录 31 条：包含 SOD1（如 tofersen、ALN-SOD、AMT-162、RAG-17）、FUS（ION363、RAG-21）、个体化 ASO/基因与细胞疗法、HEALEY 平台和其他代表性临床开发项目，并涵盖 2026 年更新的登记记录。另按补充要求纳入 BANYAN（NCT07688239）：CT.gov 的 2026-10-21 更新显示 `NOT_YET_RECRUITING`，保留该登记状态；外部临床进展公告不覆盖注册局字段，页面可另行说明差异。另逐一核对预选的 NCT04297683、NCT05021536、NCT06307301、NCT02166944、NCT04993755、NCT04768972、NCT05633459、NCT06665165、NCT06556394、NCT06973629、NCT07174492；全部在本次读取时可查且与 ALS 药物/生物干预相关，故保留。它们并非全都已结束：API 当前将部分登记为招募中、尚未招募或进行中。NCT05021536 的登记状态为 `UNKNOWN`；忠实保留注册状态值，不据此推断研究结果。

数据字段直接映射 API 登记内容；`hasResults` 仅表示登记记录是否带有结果模块，不代表疗效有效、结果已判读或临床获益。`refresh_trials.py` 只刷新 `trials.json` 已跟踪的 NCT ID，不自动增删精选成员；所有记录通过校验后才以同目录临时文件原子替换目标文件。

整合研究卡片时，补充读取其关联的 13 项登记（包括已完成试验与 ATLAS），现收录 44 项。另将已登记的新 pridopidine III 期试验作为独立登记进度卡片，不改变早期阴性试验结果。
