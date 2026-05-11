-- Local dynamic store schema. Static JSON/Markdown content is intentionally not stored here.
CREATE TABLE IF NOT EXISTS users (
  user_id TEXT PRIMARY KEY,
  login_status TEXT NOT NULL CHECK (login_status IN ('guest', 'login', 'vip')),
  subject_id TEXT NOT NULL DEFAULT 'high_itpmp',
  exam_date TEXT,
  weekly_days INTEGER CHECK (weekly_days BETWEEN 0 AND 7),
  daily_minutes INTEGER CHECK (daily_minutes > 0),
  updated_at TEXT NOT NULL,
  synced INTEGER NOT NULL DEFAULT 0
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
  task_date TEXT NOT NULL,
  task_type TEXT NOT NULL CHECK (task_type IN ('learn', 'practice', 'wrong_review')),
  target_id TEXT,
  target_count INTEGER NOT NULL DEFAULT 0,
  completed_count INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL CHECK (status IN ('pending', 'doing', 'done', 'skipped')),
  updated_at TEXT NOT NULL,
  synced INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_records_user ON user_records(user_id);
CREATE INDEX IF NOT EXISTS idx_wrong_book_user ON wrong_book(user_id);
CREATE INDEX IF NOT EXISTS idx_wrong_book_question ON wrong_book(question_id);
CREATE INDEX IF NOT EXISTS idx_daily_tasks_user_date ON daily_tasks(user_id, task_date);
