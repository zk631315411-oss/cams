<!--
  用途：项目交接文档模板，用于项目移交、人员离职/转岗时完整传递项目上下文。
  使用方式：复制本文件，将 {{placeholder}} 替换为实际内容。
-->

# 项目交接文档 — 生成日期：{{date}}

<!-- date: 文档生成日期，格式 YYYY-MM-DD -->

## 项目概况
- 项目名称：{{project_name}}
- 当前状态：{{status}}
- 技术栈：{{tech_stack}}

<!--
  project_name: 项目全称
  status: 当前状态，如"开发中/测试中/已上线/维护中"
  tech_stack: 核心技术栈，如"Python 3.11 + FastAPI + Vue 3 + PostgreSQL"
-->

## 当前完成的功能
{{completed_features}}

<!-- completed_features: 已实现的功能列表，建议按模块分类列出，说明完成度 -->

## 关键决策记录
{{key_decisions}}

<!-- key_decisions: 项目过程中做出的关键决策，说明决策背景、内容与影响 -->

## 技术债务/已知问题
{{tech_debt}}

<!-- tech_debt: 尚未解决的技术债务或已知 bug，说明影响范围与建议修复时间 -->

## 待办事项
{{todo_list}}

<!-- todo_list: 交接后仍需完成的工作，建议按优先级排列 -->

## 关键文件索引
{{file_index}}

<!-- file_index: 项目核心文件/目录的路径与作用说明，帮助接手人快速定位 -->

## 移交说明
{{handover_notes}}

<!-- handover_notes: 其他需要特别说明的移交事项，如环境配置、依赖说明、联系人等 -->