# AtomQ Data

当前目录采用新结构：

- `.old/`：旧脚本、旧样例、旧 SQLite，保留作参考但不再作为可发布数据源。
- `content_package/public/`：唯一可发布静态内容包，包含科目索引、章节元数据、知识卡片 JSON/Markdown、章节题目 JSON；所有卡片和题目均为公开免费内容，可直接上传到阿里 OSS 公共读目录。
- `local_store/`：客户端本地动态库 schema，存用户学习记录、错题、掌握度和每日任务。
- `sources/`：内容来源与抽取说明。
- `scripts/`：内容构建与校验脚本。

静态内容继续使用 JSON + Markdown；动态用户数据进入 SQLite。后续同步到云端时，只发布 `content_package/public` 到阿里 OSS，备案通过后切到阿里 CDN。`local_store` 对应表走 Supabase/Postgres。

知识卡正文 `.md` 只保留正文阅读内容。高频考点、记忆口诀、易错提示统一放在同名 `.json` 中：

- `key_points`：原 `:::key` 内容
- `mnemonics`：原 `:::tip` 内容
- `warnings`：原 `:::warning` 内容
