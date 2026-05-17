-- Local dynamic store schema. Static JSON/Markdown content is intentionally not stored here.
CREATE TABLE IF NOT EXISTS users (
  user_id TEXT PRIMARY KEY,
  login_status TEXT NOT NULL CHECK (login_status IN ('guest', 'login', 'vip')),
  subject_id TEXT NOT NULL DEFAULT 'high_itpmp',
  exam_date TEXT,
  daily_minutes INTEGER CHECK (daily_minutes > 0),
  active_plan_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  synced INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS study_plans (
  plan_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  subject_id TEXT NOT NULL DEFAULT 'high_itpmp',
  exam_date TEXT NOT NULL,
  start_date TEXT NOT NULL,
  daily_minutes INTEGER NOT NULL CHECK (daily_minutes > 0),
  total_card_count INTEGER NOT NULL DEFAULT 0,
  total_question_count INTEGER NOT NULL DEFAULT 0,
  remaining_card_count INTEGER NOT NULL DEFAULT 0,
  remaining_question_count INTEGER NOT NULL DEFAULT 0,
  daily_card_target INTEGER NOT NULL DEFAULT 0,
  daily_question_target INTEGER NOT NULL DEFAULT 0,
  plan_pressure TEXT NOT NULL DEFAULT 'normal'
    CHECK (plan_pressure IN ('normal', 'tight', 'impossible')),
  status TEXT NOT NULL DEFAULT 'active'
    CHECK (status IN ('active', 'archived', 'completed')),
  generated_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  synced INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS user_records (
  record_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  target_type TEXT NOT NULL CHECK (target_type IN ('point', 'question', 'paper')),
  target_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('not_start', 'doing', 'done')),
  last_position TEXT,
  answer_time_ms INTEGER,
  updated_at TEXT NOT NULL,
  synced INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS wrong_book (
  wrong_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  question_id TEXT NOT NULL,
  wrong_count INTEGER NOT NULL DEFAULT 1,
  right_streak INTEGER NOT NULL DEFAULT 0,
  priority TEXT NOT NULL CHECK (priority IN ('high', 'normal', 'archived')),
  last_wrong_at TEXT NOT NULL,
  next_review_at TEXT,
  updated_at TEXT NOT NULL,
  synced INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS mastery_scores (
  user_id TEXT NOT NULL,
  subject_id TEXT NOT NULL DEFAULT 'high_itpmp',
  chapter_id TEXT NOT NULL,
  section_id TEXT NOT NULL,
  point_id TEXT NOT NULL,
  score INTEGER NOT NULL CHECK (score BETWEEN 0 AND 100),
  updated_at TEXT NOT NULL,
  synced INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, subject_id, chapter_id, section_id, point_id),
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS daily_tasks (
  task_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  plan_id TEXT,
  task_date TEXT NOT NULL,
  task_type TEXT NOT NULL CHECK (task_type IN ('learn', 'practice', 'wrong_review')),
  target_scope TEXT CHECK (
    target_scope IS NULL
    OR target_scope IN ('subject', 'chapter', 'section', 'point', 'question_set')
  ),
  target_id TEXT,
  target_count INTEGER NOT NULL DEFAULT 0,
  completed_count INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL CHECK (status IN ('pending', 'doing', 'done', 'skipped')),
  updated_at TEXT NOT NULL,
  synced INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS daily_study_stats (
  stat_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  subject_id TEXT NOT NULL DEFAULT 'high_itpmp',
  stat_date TEXT NOT NULL,
  study_seconds INTEGER NOT NULL DEFAULT 0,
  learned_card_count INTEGER NOT NULL DEFAULT 0,
  mastered_card_count INTEGER NOT NULL DEFAULT 0,
  answered_question_count INTEGER NOT NULL DEFAULT 0,
  correct_question_count INTEGER NOT NULL DEFAULT 0,
  wrong_question_count INTEGER NOT NULL DEFAULT 0,
  completed_task_count INTEGER NOT NULL DEFAULT 0,
  total_task_count INTEGER NOT NULL DEFAULT 0,
  checkin_status TEXT NOT NULL DEFAULT 'none'
    CHECK (checkin_status IN ('none', 'partial', 'done')),
  checkin_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  synced INTEGER NOT NULL DEFAULT 0,
  UNIQUE(user_id, subject_id, stat_date),
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_study_plans_user_status ON study_plans(user_id, status);
CREATE INDEX IF NOT EXISTS idx_user_records_user ON user_records(user_id);
CREATE INDEX IF NOT EXISTS idx_wrong_book_user ON wrong_book(user_id);
CREATE INDEX IF NOT EXISTS idx_wrong_book_question ON wrong_book(question_id);
CREATE INDEX IF NOT EXISTS idx_daily_tasks_user_date ON daily_tasks(user_id, task_date);
CREATE INDEX IF NOT EXISTS idx_daily_tasks_plan_date ON daily_tasks(plan_id, task_date);
CREATE INDEX IF NOT EXISTS idx_daily_study_stats_user_date ON daily_study_stats(user_id, stat_date);
