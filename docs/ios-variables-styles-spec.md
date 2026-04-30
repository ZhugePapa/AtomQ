# iOS Variables & Styles 文档（AtomQ / 软考 App）

- 导出时间：2026-04-25T06:17:00.075Z
- 目标文件：`IJ94IJOoh9DN4D8dAGEAoi`
- 说明：本文件基于已落地在 Figma 的 `iOS/*` 变量与样式生成，供组件库搭建和研发对齐使用。

## 1. Variables 总览

- `iOS/Primitives`：56（基础色阶）
- `iOS/Semantic Colors`：29（Light / Dark 语义色）
- `iOS/Spacing`：17（间距）
- `iOS/Radius`：8（圆角）

## 2. iOS/Primitives（基础色）

| 变量名 | 值（Base） | 描述 | 使用场景 |
| --- | --- | --- | --- |
| neutral/0 | #FFFFFF | 中性色阶（灰阶） | 用于页面底色、分割线、主次文案的基础色来源 |
| neutral/25 | #FAFBFC | 中性色阶（灰阶） | 用于页面底色、分割线、主次文案的基础色来源 |
| neutral/50 | #F4F6F8 | 中性色阶（灰阶） | 用于页面底色、分割线、主次文案的基础色来源 |
| neutral/100 | #E9EDF2 | 中性色阶（灰阶） | 用于页面底色、分割线、主次文案的基础色来源 |
| neutral/200 | #D9E0E8 | 中性色阶（灰阶） | 用于页面底色、分割线、主次文案的基础色来源 |
| neutral/300 | #C2CCD8 | 中性色阶（灰阶） | 用于页面底色、分割线、主次文案的基础色来源 |
| neutral/400 | #97A6B8 | 中性色阶（灰阶） | 用于页面底色、分割线、主次文案的基础色来源 |
| neutral/500 | #6E7E94 | 中性色阶（灰阶） | 用于页面底色、分割线、主次文案的基础色来源 |
| neutral/600 | #536279 | 中性色阶（灰阶） | 用于页面底色、分割线、主次文案的基础色来源 |
| neutral/700 | #3D495F | 中性色阶（灰阶） | 用于页面底色、分割线、主次文案的基础色来源 |
| neutral/800 | #2A3446 | 中性色阶（灰阶） | 用于页面底色、分割线、主次文案的基础色来源 |
| neutral/900 | #182031 | 中性色阶（灰阶） | 用于页面底色、分割线、主次文案的基础色来源 |
| neutral/950 | #0F1524 | 中性色阶（灰阶） | 用于页面底色、分割线、主次文案的基础色来源 |
| brand/50 | #EAF3FF | 品牌主色阶 | 用于品牌强调、主按钮、关键状态色 |
| brand/100 | #D2E5FF | 品牌主色阶 | 用于品牌强调、主按钮、关键状态色 |
| brand/200 | #A7CBFF | 品牌主色阶 | 用于品牌强调、主按钮、关键状态色 |
| brand/300 | #7CAFFF | 品牌主色阶 | 用于品牌强调、主按钮、关键状态色 |
| brand/400 | #4C8DFF | 品牌主色阶 | 用于品牌强调、主按钮、关键状态色 |
| brand/500 | #216CFF | 品牌主色阶 | 用于品牌强调、主按钮、关键状态色 |
| brand/600 | #1454DB | 品牌主色阶 | 用于品牌强调、主按钮、关键状态色 |
| brand/700 | #1342B0 | 品牌主色阶 | 用于品牌强调、主按钮、关键状态色 |
| brand/800 | #13378A | 品牌主色阶 | 用于品牌强调、主按钮、关键状态色 |
| brand/900 | #132F73 | 品牌主色阶 | 用于品牌强调、主按钮、关键状态色 |
| success/50 | #ECFBF4 | 成功语义基础色阶 | 用于正确、通过、已掌握等正向状态 |
| success/100 | #D6F5E6 | 成功语义基础色阶 | 用于正确、通过、已掌握等正向状态 |
| success/200 | #AEEBCF | 成功语义基础色阶 | 用于正确、通过、已掌握等正向状态 |
| success/300 | #7EDEB3 | 成功语义基础色阶 | 用于正确、通过、已掌握等正向状态 |
| success/400 | #49CD95 | 成功语义基础色阶 | 用于正确、通过、已掌握等正向状态 |
| success/500 | #1FB977 | 成功语义基础色阶 | 用于正确、通过、已掌握等正向状态 |
| success/600 | #15985F | 成功语义基础色阶 | 用于正确、通过、已掌握等正向状态 |
| success/700 | #12774D | 成功语义基础色阶 | 用于正确、通过、已掌握等正向状态 |
| success/900 | #0B4730 | 成功语义基础色阶 | 用于正确、通过、已掌握等正向状态 |
| warning/50 | #FFF8E8 | 警告语义基础色阶 | 用于提醒、待处理、风险提示 |
| warning/100 | #FFEFC8 | 警告语义基础色阶 | 用于提醒、待处理、风险提示 |
| warning/200 | #FFE19A | 警告语义基础色阶 | 用于提醒、待处理、风险提示 |
| warning/300 | #FFD068 | 警告语义基础色阶 | 用于提醒、待处理、风险提示 |
| warning/400 | #FFBC3C | 警告语义基础色阶 | 用于提醒、待处理、风险提示 |
| warning/500 | #F3A314 | 警告语义基础色阶 | 用于提醒、待处理、风险提示 |
| warning/600 | #C8840D | 警告语义基础色阶 | 用于提醒、待处理、风险提示 |
| warning/700 | #9E680D | 警告语义基础色阶 | 用于提醒、待处理、风险提示 |
| warning/900 | #5D3C0B | 警告语义基础色阶 | 用于提醒、待处理、风险提示 |
| danger/50 | #FFF0F3 | 错误语义基础色阶 | 用于错误、失败、删除、危险操作 |
| danger/100 | #FFDCE4 | 错误语义基础色阶 | 用于错误、失败、删除、危险操作 |
| danger/200 | #FFBACB | 错误语义基础色阶 | 用于错误、失败、删除、危险操作 |
| danger/300 | #FF8CA8 | 错误语义基础色阶 | 用于错误、失败、删除、危险操作 |
| danger/400 | #FF5F87 | 错误语义基础色阶 | 用于错误、失败、删除、危险操作 |
| danger/500 | #F63568 | 错误语义基础色阶 | 用于错误、失败、删除、危险操作 |
| danger/600 | #D81D50 | 错误语义基础色阶 | 用于错误、失败、删除、危险操作 |
| danger/700 | #AB1A42 | 错误语义基础色阶 | 用于错误、失败、删除、危险操作 |
| danger/900 | #651229 | 错误语义基础色阶 | 用于错误、失败、删除、危险操作 |
| alpha/black-05 | #000000 @ 0.05 | 透明叠加色 | 用于遮罩、弱化态、阴影颜色基底 |
| alpha/black-10 | #000000 @ 0.10 | 透明叠加色 | 用于遮罩、弱化态、阴影颜色基底 |
| alpha/black-20 | #000000 @ 0.20 | 透明叠加色 | 用于遮罩、弱化态、阴影颜色基底 |
| alpha/black-40 | #000000 @ 0.40 | 透明叠加色 | 用于遮罩、弱化态、阴影颜色基底 |
| alpha/white-08 | #FFFFFF @ 0.08 | 透明叠加色 | 用于遮罩、弱化态、阴影颜色基底 |
| alpha/white-16 | #FFFFFF @ 0.16 | 透明叠加色 | 用于遮罩、弱化态、阴影颜色基底 |

## 3. iOS/Semantic Colors（语义色）

| 变量名 | Light | Dark | 描述 | 使用场景 |
| --- | --- | --- | --- | --- |
| bg/canvas | alias:neutral/0 | alias:neutral/950 | App 主画布背景色 | 页面根容器、列表大背景 |
| bg/surface | alias:neutral/0 | alias:neutral/900 | 内容面板背景色 | 卡片、单元格、弹层主体 |
| bg/subtle | alias:neutral/50 | alias:neutral/800 | 弱强调背景色 | 分区底色、次级容器背景 |
| bg/elevated | alias:neutral/0 | alias:neutral/700 | 抬升层背景色 | 浮层、悬浮卡片 |
| bg/brand | alias:brand/500 | alias:brand/400 | 品牌实色背景 | 主按钮、品牌标签底色 |
| bg/brand-subtle | alias:brand/50 | alias:brand/900 | 品牌弱化背景 | 品牌提醒条、浅色品牌徽标底 |
| text/primary | alias:neutral/950 | alias:neutral/50 | 主文本色 | 正文、标题、关键可读信息 |
| text/secondary | alias:neutral/700 | alias:neutral/300 | 次级文本色 | 说明文案、辅助信息 |
| text/tertiary | alias:neutral/500 | alias:neutral/400 | 三级文本色 | 占位文案、最弱信息层 |
| text/inverse | alias:neutral/0 | alias:neutral/950 | 反色文本 | 深色背景上的文本 |
| text/brand | alias:brand/600 | alias:brand/300 | 品牌文本色 | 品牌强调链接/文本 |
| text/on-brand | alias:neutral/0 | alias:neutral/0 | 品牌底上的文本色 | 主按钮文案、品牌块上的文字 |
| icon/primary | alias:neutral/800 | alias:neutral/100 | 主图标色 | 导航图标、操作图标默认态 |
| icon/secondary | alias:neutral/500 | alias:neutral/400 | 次级图标色 | 弱化图标、提示图标 |
| icon/inverse | alias:neutral/0 | alias:neutral/950 | 反色图标色 | 深色背景上的图标 |
| border/default | alias:neutral/200 | alias:neutral/700 | 默认边框色 | 输入框、卡片、分割线 |
| border/strong | alias:neutral/400 | alias:neutral/500 | 强调边框色 | 选中态、重点模块边界 |
| border/brand | alias:brand/500 | alias:brand/400 | 品牌边框色 | 品牌强调边框、焦点替代线 |
| state/success/fg | alias:success/700 | alias:success/300 | 成功前景色 | 成功图标、成功文字 |
| state/success/bg | alias:success/50 | alias:success/900 | 成功背景色 | 成功标签/提示底色 |
| state/warning/fg | alias:warning/700 | alias:warning/300 | 警告前景色 | 警告图标、警告文字 |
| state/warning/bg | alias:warning/50 | alias:warning/900 | 警告背景色 | 警告标签/提示底色 |
| state/danger/fg | alias:danger/700 | alias:danger/300 | 错误前景色 | 错误图标、错误文字 |
| state/danger/bg | alias:danger/50 | alias:danger/900 | 错误背景色 | 错误标签/提示底色 |
| overlay/scrim | alias:alpha/black-40 | alias:alpha/black-40 | 强遮罩色 | 全屏弹窗背景遮罩 |
| overlay/soft | alias:alpha/black-10 | alias:alpha/black-20 | 轻遮罩色 | 局部悬浮层、状态覆盖层 |
| control/disabled-bg | alias:neutral/100 | alias:neutral/800 | 禁用控件背景色 | 禁用按钮、禁用输入容器 |
| control/disabled-fg | alias:neutral/400 | alias:neutral/500 | 禁用控件前景色 | 禁用文字、禁用图标 |
| focus/ring | alias:brand/500 | alias:brand/300 | 焦点环色 | 键盘焦点、可访问性高亮外框 |

## 4. iOS/Spacing（间距）

| 变量名 | 值（pt） | 描述 | 使用场景 |
| --- | --- | --- | --- |
| 0 | 0 | 超小间距 | 图标与文字微调、紧凑排版 |
| 2 | 2 | 超小间距 | 图标与文字微调、紧凑排版 |
| 4 | 4 | 超小间距 | 图标与文字微调、紧凑排版 |
| 6 | 6 | 小间距 | 按钮内部、表单项内间距 |
| 8 | 8 | 小间距 | 按钮内部、表单项内间距 |
| 10 | 10 | 中间距 | 列表项/卡片标准间距 |
| 12 | 12 | 中间距 | 列表项/卡片标准间距 |
| 14 | 14 | 中间距 | 列表项/卡片标准间距 |
| 16 | 16 | 中间距 | 列表项/卡片标准间距 |
| 20 | 20 | 大间距 | 区块内层级分组 |
| 24 | 24 | 大间距 | 区块内层级分组 |
| 28 | 28 | 特大间距 | 模块之间留白 |
| 32 | 32 | 特大间距 | 模块之间留白 |
| 40 | 40 | 特大间距 | 模块之间留白 |
| 48 | 48 | 超大间距 | 页面级分隔和首屏留白 |
| 56 | 56 | 超大间距 | 页面级分隔和首屏留白 |
| 64 | 64 | 超大间距 | 页面级分隔和首屏留白 |

## 5. iOS/Radius（圆角）

| 变量名 | 值（pt） | 描述 | 使用场景 |
| --- | --- | --- | --- |
| none | 0 | 直角 | 分割线容器、硬边界模块 |
| xs | 4 | 小圆角 | 输入框、小按钮 |
| sm | 6 | 小圆角 | 输入框、小按钮 |
| md | 8 | 中圆角 | 卡片、常规按钮 |
| lg | 12 | 中圆角 | 卡片、常规按钮 |
| xl | 16 | 大圆角 | 大卡片、底部浮层、弹窗 |
| 2xl | 20 | 大圆角 | 大卡片、底部浮层、弹窗 |
| full | 999 | 胶囊圆角 | 标签、胶囊按钮、头像裁切 |

## 6. Text Styles（ios/*）

| 样式名 | 字体 | 字重 | 字号 | 行高 | 描述 | 使用场景 |
| --- | --- | --- | --- | --- | --- | --- |
| ios/large-title/bold | Inter | Bold | 34 | 41 | 页面大标题层级 | 首页/章节主标题 |
| ios/title-1/semibold | Inter | Semi Bold | 28 | 34 | 一级标题层级 | 页面区块标题 |
| ios/title-2/semibold | Inter | Semi Bold | 22 | 28 | 二级标题层级 | 模块标题 |
| ios/title-3/semibold | Inter | Semi Bold | 20 | 25 | 三级标题层级 | 卡片标题 |
| ios/headline/semibold | Inter | Semi Bold | 17 | 22 | 强调标题层级 | 关键行标题、重点文本 |
| ios/body/regular | Inter | Regular | 17 | 24 | 正文层级 | 主要阅读内容 |
| ios/body/medium | Inter | Medium | 17 | 24 | 正文层级 | 主要阅读内容 |
| ios/callout/regular | Inter | Regular | 16 | 22 | 提示正文层级 | 提示信息、次重点正文 |
| ios/subheadline/regular | Inter | Regular | 15 | 20 | 强调标题层级 | 关键行标题、重点文本 |
| ios/footnote/regular | Inter | Regular | 13 | 18 | 脚注层级 | 注释、辅助解释 |
| ios/caption-1/regular | Inter | Regular | 12 | 16 | 说明层级 1 | 标签、小字说明 |
| ios/caption-2/regular | Inter | Regular | 11 | 14 | 说明层级 2 | 最弱辅助信息 |
| ios/tab-label/medium | Inter | Medium | 10 | 12 | 导航标签层级 | Tab 文案 |
| ios/button/semibold | Inter | Semi Bold | 16 | 22 | 按钮文案层级 | 主次按钮文案 |

## 7. Effect Styles（ios/elevation/*）

| 样式名 | 阴影参数（x,y,blur） | 颜色（rgba） | 描述 / 使用场景 |
| --- | --- | --- | --- |
| ios/elevation/level-1 | 0,1,3 | 0,0,0,0.12 | 基础悬浮层级，适用于轻量卡片 |
| ios/elevation/level-2 | 0,4,12 | 0,0,0,0.14 | 中等悬浮层级，适用于可点击卡片/悬浮按钮 |
| ios/elevation/level-3 | 0,8,24 | 0,0,0,0.18 | 高悬浮层级，适用于弹出层 |
| ios/elevation/level-4 | 0,12,32 | 0,0,0,0.24 | 最高悬浮层级，适用于模态/强调层 |

## 8. Paint Styles（ios/color/*）

| 样式名 | 绑定变量 | 描述 | 使用场景 |
| --- | --- | --- | --- |
| ios/color/bg/canvas | bg/canvas | 绑定语义色：App 主画布背景色 | 页面根容器、列表大背景 |
| ios/color/bg/surface | bg/surface | 绑定语义色：内容面板背景色 | 卡片、单元格、弹层主体 |
| ios/color/bg/subtle | bg/subtle | 绑定语义色：弱强调背景色 | 分区底色、次级容器背景 |
| ios/color/bg/brand | bg/brand | 绑定语义色：品牌实色背景 | 主按钮、品牌标签底色 |
| ios/color/text/primary | text/primary | 绑定语义色：主文本色 | 正文、标题、关键可读信息 |
| ios/color/text/secondary | text/secondary | 绑定语义色：次级文本色 | 说明文案、辅助信息 |
| ios/color/text/tertiary | text/tertiary | 绑定语义色：三级文本色 | 占位文案、最弱信息层 |
| ios/color/text/inverse | text/inverse | 绑定语义色：反色文本 | 深色背景上的文本 |
| ios/color/border/default | border/default | 绑定语义色：默认边框色 | 输入框、卡片、分割线 |
| ios/color/border/strong | border/strong | 绑定语义色：强调边框色 | 选中态、重点模块边界 |
| ios/color/state/success-bg | state/success/bg | 绑定语义色：成功背景色 | 成功标签/提示底色 |
| ios/color/state/warning-bg | state/warning/bg | 绑定语义色：警告背景色 | 警告标签/提示底色 |
| ios/color/state/danger-bg | state/danger/bg | 绑定语义色：错误背景色 | 错误标签/提示底色 |
| ios/color/focus/ring | focus/ring | 绑定语义色：焦点环色 | 键盘焦点、可访问性高亮外框 |

## 9. 使用建议

1. 组件优先绑定 `iOS/Semantic Colors`，避免直接使用 `Primitives`。
2. 视觉稿里优先用 `ios/color/*`、`ios/*` 文本样式，减少手工样式漂移。
3. 新增业务状态色（如“待复习/已掌握/易错”）时，优先扩展 Semantic 层，不改 Primitives。
4. 若后续切换品牌色，只需改 `iOS/Primitives` 对应色阶即可联动语义层。
