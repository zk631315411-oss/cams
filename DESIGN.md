---
name: CAMS V7 教研工作台
description: 以教材为中心的教研证据追溯工具
colors:
  primary: "#0071e3"
  neutral-bg: "#f5f5f7"
  neutral-surface: "#ffffff"
  neutral-soft: "#fafafa"
  neutral-line: "#e5e5e7"
  neutral-line-strong: "#d4d4d8"
  neutral-text: "#1d1d1f"
  neutral-text-soft: "#6e6e73"
  neutral-text-muted: "#aeaeb2"
  amber: "#ff9f0a"
  green: "#30d158"
  danger: "#ff453a"
typography:
  display:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'PingFang SC', 'Segoe UI', sans-serif"
    fontSize: "26px"
    fontWeight: 700
    lineHeight: 1.3
  headline:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'PingFang SC', 'Segoe UI', sans-serif"
    fontSize: "20px"
    fontWeight: 600
    lineHeight: 1.4
  title:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'PingFang SC', 'Segoe UI', sans-serif"
    fontSize: "16px"
    fontWeight: 600
    lineHeight: 1.5
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'PingFang SC', 'Segoe UI', sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.7
  label:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'PingFang SC', 'Segoe UI', sans-serif"
    fontSize: "13px"
    fontWeight: 500
    lineHeight: 1.5
rounded:
  sm: "8px"
  md: "12px"
  lg: "16px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
  xxl: "32px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "10px 20px"
  button-primary-hover:
    backgroundColor: "#0077ed"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "10px 20px"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.neutral-text-soft}"
    rounded: "{rounded.sm}"
    padding: "6px 12px"
  card:
    backgroundColor: "{colors.neutral-surface}"
    rounded: "{rounded.md}"
    padding: "{spacing.xl}"
  input:
    backgroundColor: "{colors.neutral-soft}"
    textColor: "{colors.neutral-text}"
    rounded: "{rounded.md}"
    padding: "8px 14px"
  segmented-control:
    backgroundColor: "#e5e5e7"
    rounded: "8px"
    padding: "3px"
  segmented-control-active:
    backgroundColor: "{colors.neutral-surface}"
    rounded: "6px"
    padding: "0 12px"
---

# 历史设计说明

本文是旧前端原型的视觉与交互设计稿，不再约束正式工作台。正式界面位于 `D:/守正公司工作区/cams考试工作台（正式版）/`；本文只保留为已采用设计思路的历史来源。

# Design System: CAMS V7 教研工作台

## 1. Overview

**Creative North Star: "The Reading Room"**

这是一间以教材为中心的安静阅览室。界面像一张干净的书桌——内容摊开在面前，工具在伸手可及的地方，但从不喧宾夺主。暖白基调、大圆角卡片、毛玻璃导航栏，整体氛围是 Apple 式的简约与克制，让教研员和教师专注于教材原文和证据链的追溯，而不是与 UI 本身搏斗。

**Key Characteristics:**
- 暖白背景（`#f5f5f7`）降低视觉疲劳，适合长时间阅读和教研工作
- Apple 蓝（`#0071e3`）作为唯一语义色，用于可交互元素和选中状态，使用 ≤10% 的界面面积
- 大圆角（`12px` 卡片、`8px` 元素）系统传递温和、可靠的感觉
- 毛玻璃顶部导航栏，提供纵深层次感而不增加视觉重量
- 微阴影（`0 2px 12px`）代替边框，区分层级而非切割空间
- 明确拒绝：厚重边框、嵌套卡片、渐变文字、玻璃拟态装饰

## 2. Colors

暖白基底，Apple 蓝点睛。色彩使用克制，90% 的面积由中性色覆盖。

### Primary
- **Apple Blue** (`#0071e3`): 所有可交互元素（按钮、链接、选中指示器）。仅用于需要用户注意的地方，不用于装饰。

### Neutral
- **Warm Paper** (`#f5f5f7`): 页面背景色。暖白基调，降低长时间使用的视觉疲劳。
- **Pure White** (`#ffffff`): 卡片、面板、搜索下拉等浮于背景之上的表面。
- **Near White** (`#fafafa`): 柔和表面，用于输入框、hover 状态、次要容器。
- **Subtle Line** (`#e5e5e7`): 分割线、边框。极淡，只有必要时才出现。
- **Stronger Line** (`#d4d4d8`): 强调分割线，用于需要更清晰分离的场景。
- **Deep Ink** (`#1d1d1f`): 主文字色。接近纯黑但带一丝暖意，比纯黑更柔和。
- **Muted Ink** (`#6e6e73`): 辅助文字。说明性文本、次要信息。
- **Faint Ink** (`#aeaeb2`): 弱化文字。占位符、禁用状态。

### Semantic
- **iOS Amber** (`#ff9f0a`): 警告、待审核状态。
- **iOS Green** (`#30d158`): 正确、已确认、通过状态。
- **iOS Red** (`#ff453a`): 错误、危险、拒绝状态。

### Named Rules
**The Rarity Rule.** 主色（Apple Blue）的使用面积不超过任何给定屏幕的 10%。它的稀缺性就是它的力量。如果某个页面上蓝色太多，视觉层次就失效了。

## 3. Typography

**Display/Body Font:** `-apple-system, BlinkMacSystemFont, "PingFang SC", "Segoe UI", sans-serif`

系统原生字体栈。在 macOS/iOS 上使用 San Francisco，在 Windows 上回退到 Segoe UI，中文字体使用 PingFang SC。不需要加载外部字体——系统原生字体性能最优，且与操作系统视觉语言一致。

**Character:** 干净、直接、不喧哗。没有装饰性衬线，没有极端的字重对比。信息层级通过字号和字重区分，而非字体切换。

### Hierarchy
- **Display** (700, 26px, 1.3): 工作台标题（`CAMS V7 教研工作台`）。仅出现在顶部品牌区域。
- **Headline** (600, 20px, 1.4): 面板标题（`教材知识单元`、`题目证据`）。每个内容区块的主标题。
- **Title** (600, 16px, 1.5): 区块内小标题（`选项分析`、`盲判结论`）。卡片或 section 的次级标题。
- **Body** (400, 15px, 1.7): 正文。教材内容、题目题干、解析说明。行高 1.7 确保长时间阅读舒适。
- **Label** (500, 13px, 1.5): 标签、元数据、统计数字、辅助说明。小且清晰，不干扰正文阅读流。

### Named Rules
**The Single-Voice Rule.** 全站使用同一字体家族。不同层级通过字号和字重区分，不引入第二种字体。单一字体保证视觉一致性，消除字体切换带来的杂乱感。

## 4. Elevation

系统采用 **轻阴影 + 毛玻璃** 混合方案。大多数表面是平的（无阴影），阴影只在需要区分层级时使用。

### Shadow Vocabulary
- **Surface Lift** (`0 2px 12px rgba(0,0,0,0.08)`): 卡片、面板、下拉菜单的默认阴影。轻而散，让浮起的表面感觉是自然悬浮而非硬切割。
- **Hover Lift** (`0 4px 20px rgba(0,0,0,0.12)`): 可交互元素（按钮、卡片）的 hover 状态。配合 `translateY(-1px)` 微上移动画。

### Named Rules
**The Flat-By-Default Rule.** 表面在静止状态下是平的。阴影仅在响应状态（hover、选中、浮层）时出现。不要给所有卡片都加阴影——那样视觉上就变成了"一堆浮着的方块"，而不是"内容在纸面上"。

## 5. Components

### Buttons
- **Shape:** 大圆角（12px），简洁无边框。
- **Primary Button:** Apple Blue 背景，白色文字，hover 加深至 `#0077ed` 并 `translateY(-1px)` 微上浮。Padding 12px 24px。
- **Ghost Button:** 无背景色，灰色文字，hover 时出现蓝色文字和浅蓝底色。用于次要操作。

### Segmented Control
- **Style:** iOS 原生分段控件风格。浅灰背景（`#e5e5e7`），选中项白色浮起加微阴影。
- **Padding:** 容器 3px，选项 0 12px。
- **使用场景:** 工作模式切换（看书备课 / 新题解析 / 学生答疑）、语言切换（中文 / English / 对照）。

### Cards
- **Corner Style:** 大圆角（12px）。
- **Background:** 纯白（`#ffffff`）。
- **Shadow Strategy:** 默认无阴影，hover 时出现 Surface Lift 阴影。
- **Border:** 默认无边框，仅在需要分组时使用 `1px solid #e5e5e7`。
- **Internal Padding:** 24px。给予内容足够的呼吸空间。

### Input / Search
- **Style:** 浅灰背景（`#fafafa`），`1px` 淡灰边框。
- **Focus:** 边框变 Apple Blue，外发光 `box-shadow: 0 0 0 3px rgba(0,113,227,0.15)`。
- **Radius:** 8px。

### Navigation (Topbar)
- **Style:** 毛玻璃效果（`backdrop-filter: saturate(180%) blur(20px)`），底部无分割线，靠阴影与内容区自然分离。
- **Height:** 56px，紧凑不浪费空间。

### Evidence Cards
- **Style:** 白底，左边框语义色条（3px）作为状态指示。绿色=直接支持，琥珀=间接支持，蓝色=关联，红色=需审核。
- **Hover:** 浅蓝底色（`#e8f0fe`）。
- **Internal Padding:** 16px。

## 6. Do's and Don'ts

### Do:
- **Do** 使用暖白背景（`#f5f5f7`）作为页面底色，保持阅读舒适度。
- **Do** 使用 Apple Blue（`#0071e3`）作为唯一的交互语义色，且使用面积 ≤10%。
- **Do** 使用大圆角（12px 卡片，8px 元素）传递温和、可靠的感觉。
- **Do** 使用毛玻璃效果（`backdrop-filter: blur(20px)`）为导航栏增加层次感。
- **Do** 使用 `translateY(-1px)` + 阴影加深作为 hover 反馈，让交互感觉自然。

### Don't:
- **Don't** 使用灰色文字放在彩色背景上——看起来褪色且难以阅读。
- **Don't** 使用嵌套卡片——卡片内嵌卡片永远是错误的结构。
- **Don't** 使用渐变文字（`background-clip: text` + gradient）——装饰性且无意义。
- **Don't** 使用边框左侧色条（`border-left > 1px`）作为卡片装饰——这是 AI 生成的典型特征。
- **Don't** 使用 bounce/elastic 缓动曲线——感觉过时。
- **Don't** 使用厚重的后台管理风格（深色侧边栏、密集表格、小字号数据面板）。
- **Don't** 使用纯黑（`#000`）或纯灰（`#808080`）——永远使用带色调的深色。
- **Don't** 使用 `Letter-spacing` 过大的小写标题——这是 AI 生成的典型特征。
