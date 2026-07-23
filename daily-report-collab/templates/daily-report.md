<!--
  用途：日报模板，用于记录每日工作总结，包括 Git 活动、关键决策、问题与计划。
  使用方式：复制本文件，将 {{placeholder}} 替换为实际内容。
-->

# 日报 — {{date}}

<!-- date: 日期，格式 YYYY-MM-DD，如 2025-07-23 -->

## 今日工作概况
{{overview}}

<!-- overview: 今日工作总述，2-5 句话概括核心进展 -->

## Git 活动
{{git_activity}}

<!-- git_activity: 当日 Git 提交清单，建议用 - commit message 列表形式呈现 -->

## 人工补充

### 关键决策
{{key_decisions}}

<!-- key_decisions: 今日做出的重要技术/业务决策，说明决策内容与原因 -->

### 遇到的问题与解决
{{problems}}

<!-- problems: 遇到的问题及解决思路/方案，格式：问题描述 -> 解决方式 -->

### 明日计划
{{tomorrow_plan}}

<!-- tomorrow_plan: 次日计划开展的工作项，建议用 - 列表逐条列出 -->

### 需要协助
{{help_needed}}

<!-- help_needed: 需要他人配合或解决的问题，否则留空或写"无" -->

## 统计概览
- 涉及项目：{{project_count}} 个
- 提交次数：{{commit_count}} 次
- 涉及文件：{{file_count}} 个

<!--
  project_count: 当日涉及的项目数量
  commit_count: 当日提交次数
  file_count: 当日变更涉及的文件数量
-->