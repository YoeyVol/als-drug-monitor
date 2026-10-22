# ALS 新药观察

中文 ALS 药物研发与临床试验监测静态网站。

- 网站：https://yoeyvol.github.io/als-drug-monitor/
- 仓库：https://github.com/yoeyvol/als-drug-monitor
- 独立于 `neals-archive`；不得修改那个仓库或站点。

本项目不含自动计时器、定时 workflow 或新的更新任务。更新执行由已存在的外部任务负责；这里只提供安全可编辑的数据和更新步骤。网页展示已发布的静态快照，不会自动抓取最新研究。

## 文件

| 文件 | 作用 |
|---|---|
| `index.html`、`styles.css`、`app.js` | 无框架的响应式页面与筛选逻辑 |
| `data/updates.json` | 人工核查的研究结果与监管记录 |
| `data/trials.json` | ClinicalTrials.gov 精选登记快照 |
| `data/changelog.json` | 每轮发布的日期、变化摘要 |
| `scripts/refresh_trials.py` | 只刷新已跟踪 NCT 记录，失败时不覆盖旧文件 |
| `scripts/validate.py` | 发布前的本地数据与页面结构校验 |

## 本地预览与校验

```bash
python3 -m http.server 8765
# 浏览 http://localhost:8765；不要直接以 file:// 打开。
python3 scripts/validate.py
```

无构建依赖，无外部字体、追踪脚本或图片。

## 每次研究更新

1. 从本仓库最新 `main` 开始；只编辑本仓库。阅读最近 changelog，不重复新增已有事项。
2. 运行 `python3 scripts/refresh_trials.py`。此步骤只改变登记快照，**不**更新研究结果或“最近研究核查”日期。API 读取时间在 `retrievedAt`，登记方更新时间在每条 `lastUpdatePosted`。
3. 通过 ClinicalTrials.gov、FDA、同行评审文章、官方研究机构或申办方核查新进展。必须阅读来源正文；搜索摘要不是证据。补充重要新 NCT 时需先核实疾病和干预，精选列表不是完整清单。
4. 编辑 `data/updates.json`。每条保留稳定的 `id`、药物、阶段、来源日期 `sourceDate`、实际核查日期 `checkedAt`、结论、限制、监管范围、NCT 和直达来源。没有日期的来源使用 `null`，不拿读取日期冒充发表日期。未来计划不能写成已发生。申办方新闻稿须标为申办方，不能标成同行评审。
5. 将 `lastUpdated` 设为真正完成本轮研究核查的日期；单纯重跑脚本不改该字段。没有发现可靠的新变化时，保留原研究结论，更新实际检查过项目的 `checkedAt`，并在 changelog 记录“未发现可验证的新变化”。未核查的项目不要批量刷新 `checkedAt`。
6. `data/changelog.json` 追加一轮记录，保留历史；按日期由近到远。不要把登记状态变更当成疗效进展。
7. 运行校验、预览桌面与手机宽度，确认筛选可用。检查 diff，不提交密钥、个人健康信息或原始网页里的无关内容。
8. 提交并推送到 `main`，GitHub Pages 从 `main` 根目录发布。确认 Pages build 成功、线上 JSON 及首页对应新版本后再报告完成。

## 数据约定

`updates.json` 顶层：`schemaVersion`（1）、`lastUpdated`（YYYY-MM-DD）、`coverage`（中文范围说明）、`items`（数组）。每条：

```json
{
  "id": "stable-drug-event-id",
  "drug": "药物 / 干预名称",
  "category": "pipeline",
  "phase": "II 期",
  "regulatoryStatus": "地区、适用范围与批准限制",
  "findings": "已核查的研究发现或事件，不把计划写成事实",
  "evidenceType": "申办方 · 新闻稿 / 同行评审 / FDA 等",
  "sourceDate": "2026-10-22",
  "checkedAt": "2026-10-22",
  "nctIds": ["NCT00000000"],
  "caveat": "证据限制或来源差异",
  "sources": [{"title": "明确的原始来源名称", "url": "https://example.org/source"}]
}
```

`category` 只能是 `pipeline` 或 `regulatory`。同一药物可有不同时间的重要事件，但不要把一个事件拆成重复卡片。`phase` 为研究事件当时的描述；最新注册分期以试验区域为准。已上市药物可继续有研究，不能据此扩大获批适用人群。

`trials.json` 保留注册库枚举，不自行把公告里的入组信息覆盖 `status`；冲突要在相关研究卡片 `caveat` 中说明。`hasResults` 仅表示注册库存在结构化结果，不表示主要终点达成。

## 重要限制

精选记录不代表全球全部试验。美国 FDA 的批准不等于中国或其他地区批准，快速通道、孤儿药资格和递交申请也不是上市批准。研究网站不构成用药建议或个人入组资格判断。
