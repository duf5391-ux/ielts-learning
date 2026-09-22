# cleaned-luna-20260921-listening：Part 1 听力逐题审阅

本批选择两份避开 Film Club 的 Part 1：Horseback-trip 与 Lifeguard Application。两份均来自 materials-index.json，题面、10 个题目对象、articleJson 转写和本地音频文件齐全。每题的 answer 是项目参考答案，按题面、转写连续证据和来源解析候选交叉整理，不称官方答案。

| sourceId | 标题 | partId | 题数 | 音频 | 用途状态 |
|---|---|---|---:|---|---|
| 2072889406625742849 | Horseback-trip | 2072884383917342722 | 10 | 本地存在；未播放 | 练习 proposed；部分短测需隔离 QA；整卷 blocked |
| 2033383348044922882 | Lifeguard Application | 2033382999737335809 | 10 | 本地存在；未播放 | 练习 proposed；部分短测需隔离 QA；整卷 blocked |

## 逐题核对结论

- Horseback-trip：1–10 均为 NO MORE THAN TWO WORDS；转写连续出现 birds、tent、mountains、swim、waterfall、cave、back、walking boots、discount、insurance。第 3 题保留 valleys→mountains 的转折，第 7 题保留 knee→back 的纠正，第 8 题保留 walking boots 与 riding boots 的对比。
- Lifeguard Application：1–10 均为 ONE WORD AND/OR A NUMBER；转写连续出现 Elsinore、cellphone number 对应的数字、waiter、baseball、beach、diving、October、Saturday、six、radio。第 7 题明确记录 November 后的自我纠正为 October；第 2 题保留座机号与 cellphone number 的区分。
- 所有 evidenceQuote 均直接来自本地 articleJson transcript 的连续字符串；没有把解析里的中文说明或题面答案当作音频证据。

## 限制与后续

audioSemanticVerification 统一为 not-listened。音频文件和 SHA-256 已核对，但本轮没有实际播放，不能声称完成原音语义核验。两份可先作为资料练习；在隔离数据中完成保存、重做和短测边界检查后，才可把其中一部分题目作为短测候选。没有独立官方答案字段，不能把两份材料包装成已核实整卷测试，也不能据此生成正式分数。

## 自查

- 两个 sourceRawPath 均存在，sourceSha256 与当前 raw/exams 文件一致；两个 audioLocalPath 均存在，audioSha256 与 media-index.json 一致。
- 每个单元 10 题，sourceQuestionId 与原始题目对象对应且题号连续 1–10。
- 词数限制逐题来自原题 group.description；题面 prompt/blankContext 保留原填空语境。
- 每条 evidenceQuote 都将在写入后再次对 articleJson 转写做连续 substring 检查。
- 本批仅写 listening-reviewed.json 与 listening-review.md，不修改下载原件、正式页、主图或其他批次文件。
