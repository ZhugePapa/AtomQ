#!/usr/bin/env python3
"""搭建动态库（SQLite）—— 按数据设计文档 1.7 + 数据字典 V1.1 建表并插入示例数据。"""

import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.db')

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# 删旧建新
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cur = conn.cursor()

# ──────────────────────────────────────────────
# 1. users（数据字典 V1.1 新增，PRD 12.1）
# ──────────────────────────────────────────────
cur.execute("""
CREATE TABLE users (
    user_id       TEXT PRIMARY KEY,
    login_status  TEXT NOT NULL CHECK (login_status IN ('guest', 'login', 'vip')),
    subject_id    TEXT NOT NULL DEFAULT 'subj_high_level',
    exam_date     TEXT NOT NULL,
    weekly_days   INTEGER NOT NULL CHECK (weekly_days BETWEEN 0 AND 7),
    daily_minutes INTEGER NOT NULL CHECK (daily_minutes > 0)
)
""")

# ──────────────────────────────────────────────
# 2. user_records（设计文档 1.7 / 数据字典）
# ──────────────────────────────────────────────
cur.execute("""
CREATE TABLE user_records (
    record_id      TEXT PRIMARY KEY,
    user_id        TEXT NOT NULL,
    target_type    TEXT NOT NULL CHECK (target_type IN ('point', 'question', 'paper')),
    target_id      TEXT NOT NULL,
    status         TEXT NOT NULL CHECK (status IN ('not_start', 'doing', 'done')),
    last_position  TEXT,
    answer_time_ms INTEGER,
    updated_at     TEXT NOT NULL,
    synced         INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
""")
cur.execute("CREATE INDEX idx_records_user ON user_records(user_id)")

# ──────────────────────────────────────────────
# 3. wrong_book（设计文档 1.7 / 数据字典）
# ──────────────────────────────────────────────
cur.execute("""
CREATE TABLE wrong_book (
    wrong_id       TEXT PRIMARY KEY,
    user_id        TEXT NOT NULL,
    question_id    TEXT NOT NULL,
    wrong_count    INTEGER DEFAULT 1,
    right_streak   INTEGER DEFAULT 0,
    priority       TEXT NOT NULL CHECK (priority IN ('high', 'normal', 'archived')),
    last_wrong_at  TEXT NOT NULL,
    next_review_at TEXT,
    synced         INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
""")
cur.execute("CREATE INDEX idx_wrong_user ON wrong_book(user_id)")
cur.execute("CREATE INDEX idx_wrong_question ON wrong_book(question_id)")

# ──────────────────────────────────────────────
# 4. mastery_scores（设计文档 1.7 / 数据字典）
# ──────────────────────────────────────────────
cur.execute("""
CREATE TABLE mastery_scores (
    user_id    TEXT NOT NULL,
    point_id   TEXT NOT NULL,
    score      INTEGER NOT NULL CHECK (score BETWEEN 0 AND 100),
    updated_at TEXT NOT NULL,
    synced     INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, point_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
""")

# ──────────────────────────────────────────────
# 5. daily_tasks（设计文档 1.7 / 数据字典）
# ──────────────────────────────────────────────
cur.execute("""
CREATE TABLE daily_tasks (
    task_id         TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL,
    task_date       TEXT NOT NULL,
    task_type       TEXT NOT NULL CHECK (task_type IN ('learn', 'practice', 'wrong_review')),
    target_id       TEXT,
    target_count    INTEGER,
    completed_count INTEGER DEFAULT 0,
    status          TEXT NOT NULL CHECK (status IN ('pending', 'doing', 'done', 'skipped')),
    synced          INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
""")
cur.execute("CREATE INDEX idx_tasks_user ON daily_tasks(user_id)")
cur.execute("CREATE INDEX idx_tasks_date ON daily_tasks(task_date)")

# ──────────────────────────────────────────────
# 示例数据
# ──────────────────────────────────────────────

cur.execute("""
INSERT INTO users VALUES
    ('u_demo_001', 'vip',    'subj_high_level', '2026-11-07', 5, 60),
    ('u_demo_002', 'login',  'subj_high_level', '2026-11-07', 3, 30),
    ('u_demo_003', 'guest',  'subj_high_level', '2026-11-07', 0, 30)
""")

cur.execute("""
INSERT INTO user_records VALUES
    ('rec_001', 'u_demo_001', 'point',    'kp_ch04_001', 'doing',      '## 概述',       NULL, '2026-05-09T10:00:00Z', 0),
    ('rec_002', 'u_demo_001', 'question', 'q_ch04_001',  'done',       NULL,             45000, '2026-05-09T10:05:00Z', 0),
    ('rec_003', 'u_demo_002', 'point',    'kp_ch04_001', 'not_start',  NULL,              NULL, '2026-05-09T08:00:00Z', 0)
""")

cur.execute("""
INSERT INTO wrong_book VALUES
    ('w_001', 'u_demo_001', 'q_ch04_001', 1, 0, 'high',   '2026-05-09T10:05:00Z', '2026-05-10T10:00:00Z', 0),
    ('w_002', 'u_demo_001', 'q_ch04_005', 2, 1, 'normal', '2026-05-08T15:00:00Z', '2026-05-11T15:00:00Z', 0)
""")

cur.execute("""
INSERT INTO mastery_scores VALUES
    ('u_demo_001', 'kp_ch04_001', 65, '2026-05-09T10:05:00Z', 0),
    ('u_demo_002', 'kp_ch04_001', 20, '2026-05-09T08:00:00Z', 0)
""")

cur.execute("""
INSERT INTO daily_tasks VALUES
    ('task_001', 'u_demo_001', '2026-05-10', 'learn',        'ch_04', 5, 3, 'doing',  0),
    ('task_002', 'u_demo_001', '2026-05-10', 'practice',     'ch_04', 10, 0, 'pending', 0),
    ('task_003', 'u_demo_001', '2026-05-10', 'wrong_review', NULL,    3,  0, 'pending', 0)
""")

conn.commit()

# ──────────────────────────────────────────────
# 输出验证
# ──────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"  动态库（SQLite）已创建: {DB_PATH}")
print(f"{'='*60}\n")

cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print(f"表 ({len(tables)}):")
for t in tables:
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    count = cur.fetchone()[0]
    cur.execute(f"PRAGMA table_info({t})")
    cols = [c[1] for c in cur.fetchall()]
    print(f"  {t:20s}  {len(cols):2d} 列, {count:2d} 行   字段: {', '.join(cols[:6])}{'...' if len(cols) > 6 else ''}")

print(f"\n索引:")
cur.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%' ORDER BY name")
for r in cur.fetchall():
    print(f"  {r[0]:30s} → {r[1]}")

conn.close()
