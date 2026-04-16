---
description: 完整深度分析一只股票（19 维基本面 + 50 位大佬评审团 + 杀猪盘检测 + 电影级 HTML 报告 + 社交战报 PNG）
argument-hint: "[股票名称或代码，例如 水晶光电 / 002273 / AAPL / 00700.HK]"
---

# 深度分析任务

用户输入: $ARGUMENTS

## 你的任务

加载 `deep-analysis` skill 并按照其 5 Task 工作流执行**完整**的个股深度分析。

**执行规则**:
1. 严格遵守 skill 中定义的 Task 顺序和门控规则——前序产物不存在则**拒绝**执行后续 task
2. 每个 Task 完成后将产物写入 `.cache/{ticker}/{task_name}.json`
3. 全部完成后将 HTML 报告 + 社交战报 PNG 写入 `reports/{ticker}_{YYYYMMDD}/`
4. 最后向用户汇报：报告路径、综合评分、一句话定调、是否安全（杀猪盘检测）

**禁止**:
- 跳过任何 Task
- 在没有跑 fetcher 脚本的情况下编造数据
- 用模板话术（"基本面良好"等）糊弄综合研判，必须输出有冲突感的金句

开始 Task 1。
