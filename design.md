# AtomQ 设计规范（基于 Figma `IJ94IJOoh9DN4D8dAGEAoi` / Node `7689:2191`）

## 1. 文档范围
本规范基于 AtomQ 画布 `UI`（node `7689:2191`）中现有页面与组件整理，目标是为后续 UI 实现提供统一的页面结构、组件规则与设计 Token 参考。

## 2. 画布与端规格
- 主要端形态：iOS 移动端
- 典型页面尺寸：`390 x 844`
- 页面常见左右边距：`24`
- 底部主按钮常见尺寸：`342 x 56`
- 顶部状态区与底部 Home Indicator 通过 `IOS components` 统一复用

## 3. 页面信息架构

### 3.1 欢迎页（`7689:2192`）
- 结构：品牌区 + 3 条核心价值点 + 主 CTA 按钮
- 价值点卡片结构统一：图标容器（48）+ 标题 + 说明文案
- 底部使用主按钮进入下一步流程

### 3.2 选择考试科目-高级（`7689:2253`）
- 标题区：页面标题 + 引导说明
- 筛选区：`tabs`（科目层级）
- 列表区：`Tile_item` 列表（支持横向分页容器）
- 底部：主按钮确认

### 3.3 选择考试科目-中级（`7689:2325`）
- 与高级页结构一致
- `tabs` 在中级场景下使用更宽布局

### 3.4 选择考试时间（`7689:2397`）
- 顶部：标题 + 说明文案
- 信息卡：已选科目、考试倒计时、建议学习量
- 参数选择区：两组 `Segmented`（考试年份/考试时间）
- 底部操作区：主按钮

### 3.5 首页 / Home v1（`7766:135`）
- 头部问候区（Greeting + Notification）
- Today Progress Card（目标进度、倒计时、进度条）
- Continue Practice Card（继续练习）
- Quick Actions（4 个快捷入口）
- Today Plan（任务列表 + 状态标签）
- Tab Bar（首页/题库/计划/我的）

### 3.6 答题页（`7769:594`）
- 题干与选项区，核心使用 `Option` 组件
- 选项容器按固定间距垂直排布（4 条选项）

### 3.7 答题记录（`7769:640`）
- 答题回顾宫格：`答题回顾_item`
- 统计/说明区
- 底部双按钮操作区

## 4. 组件体系

### 4.1 Button（`7591:250`）
- 变体维度：
  - `Type`: `primary | secondary | tertiary`
  - `State`: `default | pressed | disabled`
- 常见尺寸：`342 x 56`
- 使用场景：页面主流程推进、次级动作、弱化动作

### 4.2 选择控件
- `Radios`（`7595:269`）: `Selected=true/false`
- `Checklist`（`7595:280`）: `Selected=true/false`
- `Toggle`（`7595:291`）: `Opened=true/false`
- `Segmented`（`7611:569`）: `Number=2/3`

### 4.3 业务组件
- `Option`（`7611:3019`）: `default | correct | wrong`
- `答题回顾_item`（`7622:614`）: `答对 | 答错 | 已答 | 未答`
- `Tile_item`（`7664:2136`）: `Active=true/false`
- `tabs_item`（`7664:2115`）: `Active=true/false`
- `tabs`（`7664:2121`）: 由 `tabs_item` 组合

### 4.4 输入与图表
- `input`（`7660:1168`）: `default | active | typing | fill`
- `Chart`（`7611:605`）: 两种图表变体（Light）

### 4.5 平台组件
- `IOS components`（`7784:2834`）
  - `Status bar`
  - `Home Indicator`
  - `Top`

## 5. 设计 Token（来自 Figma Variables）

### 5.1 Color
- `--ios-color-bg-canvas: #ffffff`
- `--ios-color-bg-surface: #ffffff`
- `--ios-color-bg-subtle: #fafbfc`
- `--ios-color-bg-brand: #1355ff`
- `--ios-color-bg-brand-subtle: #ecf4ff`
- `--ios-color-text-primary: #121b26`
- `--ios-color-text-secondary: #404c63`
- `--ios-color-text-tertiary: #6e7e94`
- `--ios-color-text-disabled: #c2ccd8`
- `--ios-color-text-white: #ffffff`
- `--ios-color-text-brand: #1355ff`
- `--ios-color-border-default: #e9edf2`
- `--ios-color-border-strong: #d9e0e8`（组件场景中也出现深色边框值 `#1b2533`）
- `--ios-color-fg-success: #12a58c`
- `--ios-color-fg-danger: #f6285f`
- `--ios-color-fg-warning: #ffde6e`

### 5.2 Typography
- 主要中文字体：`PingFang SC`
- 数据字体：`DIN`（例如 Data/xxlg）
- 常用文本层级：
  - `Heading/h4`: 24/36, 600
  - `Heading/h5`: 20/30, 600
  - `Heading/h6`: 16/24, 600
  - `Text/lg/regular`: 16/24, 400
  - `Text/lg/medium`: 16/24, 500
  - `Text/md/regular`: 14/22, 400
  - `Text/md/medium`: 14/22, 500
  - `Text/md/semibold`: 14/22, 600
  - `Text/sm/regular`: 12/20, 400
  - `Text/sm/medium`: 12/20, 500
  - `Text/sm/semibold`: 12/20, 600
  - `Data/xxlg`: 32/48, 700

### 5.3 Radius
- `--ios-radius-sm: 12`
- `--ios-radius-md: 16`
- `--ios-radius-lg: 20`
- `--ios-radius-xl: 24`
- `--ios-radius-full: 999`

### 5.4 Spacing（已观测）
- `--ios-spacing-8: 8`
- `--ios-spacing-16: 16`
- `--ios-spacing-24: 24`
- `--ios-spacing-56: 56`

## 6. 交互与状态约定
- 所有主交互组件均采用显式状态建模（如 `default/pressed/disabled`、`selected/unselected`）。
- 列表型组件优先通过 `Active` 或语义状态（`correct/wrong`）表达业务反馈，而不是仅靠颜色变化。
- 首页、答题、回顾等关键路径页面均依赖卡片化分组与中高对比文本层级提升可读性。

## 7. 前端实现建议
- 将上述变量统一映射到 design token 文件（如 CSS Variables / JSON Tokens），避免页面内硬编码。
- 组件开发按“基础组件（Button/Input/Select）-> 业务组件（Option/Tile）-> 页面模板”分层。
- 先搭建 `390` 宽度基线与 `24` 页面边距规则，再做响应式扩展。
- 对 `Button`、`Option`、`input`、`tabs_item` 优先补齐状态快照测试，确保 UI 状态一致性。

## 8. 溯源
- Figma 文件：`https://www.figma.com/design/IJ94IJOoh9DN4D8dAGEAoi/AtomQ`
- 根节点：`7689:2191`
- 文档生成时间：`2026-04-30`
