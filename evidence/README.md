# 第三阶段横向实测证据

## 当前有效补测：2026-10-10

`supplement_20261010/` 保存本轮 35 次真实模型调用及 5 次规则执行。

- `live_api_results.json`：5 个幻觉案例的粗放/精细回答、两组各 3 次文本生成、DeepSeek 与棋语横评回答。
- `logic_live_results.json`：5 类逻辑陷阱的 10 次真实回答。
- `three_tool_comparison.json`：三工具各 3 题原文和完全相同用户提示的 SHA-256 校验。
- `chatgpt_C01.json`、`chatgpt_C02.json`、`chatgpt_C03.json` 与对应截图：独立 ChatGPT 网页工具实测。
- `risk_review.csv`：20 个幻觉/逻辑回答的逐项人工复核。
- `rule_and_source_verification.json`：5 个非法走法真实拒绝记录，以及模型前向计算先于开局库判断的源码证据。
- `forward_runtime_verification.json`：真实加载冻结v3权重与开局库，前向钩子记录1次Transformer计算，同时depth=0、nodes=0、opening_book=true。该本地决策另外计数，不混入35次语言模型调用。

本轮观察：具体字段虚构两组均 0/5，但 H04 粗放出现无证据绝对断言。逻辑目标陷阱均识别，粗放 L02 仍附带错误推论。精细同质化提示的 Jaccard 相似度由 32.99% 增至 37.74%，没有缓解。三工具 C03 的核验范围不同可以并存，旧的风险等级分叉未稳定复现。

以下为 2026-10-09 历史记录。旧评分与因果解释已由本轮报告修正，不能直接作为当前结论。

## 历史记录

- `strict_cross_tool.json`：C01–C03 三段完全相同的用户提示分别通过棋语语言层与 DeepSeek 原生端点运行，保存提示 SHA-256、原始响应、模型名、时间戳与 token 用量。
- `cross_tool_scores.csv`：按照项目提示词库中的内部 0–2 分量表记录的逐项评分。这不是课程官方评分表。
- `strict-cross-tool.html`：便于课堂展示和截图复核的响应证据摘录页；完整原文以 JSON 为准。
- `qiyu_logic_prompt_ab.json`：五类逻辑风险在棋语语言层（`deepseek-flash` + 棋语 system/context）下的粗放提示与精细提示原始回答。
- `logic_prompt_ab_scores.csv`：逻辑提示前后对照的逐项记录；两组均为 5/5，精细提示的收益主要是证据结构，而不是正确率提升。

## 历史观察（非当前稳定结论）

1. C01：两端均识别 51.1% 是同一开局库中的选择频次，不将它重复计证或写成胜率，并披露本次没有展开搜索。
2. C02：两种工具均拒绝为无证据赛事说法补写事实。
3. C03：棋语曾判中风险，原生端点判低风险。本轮重新测试棋语判低风险，因此旧分叉没有稳定复现。不能从该次回答直接证明 system/context 是原因。

两端接收的用户提示逐字相同，且语言模型均为 `deepseek-flash`；区别是棋语端额外注入自身 system prompt 与当前棋盘上下文。因此这是约束层 A/B，不是两个独立基础模型的横评。所有评分都应回看原始输出，不宜把总分解释为绝对能力排名。
