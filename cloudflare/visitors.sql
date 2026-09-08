CREATE TABLE IF NOT EXISTS daily_visitors (
 day TEXT NOT NULL, visitor TEXT NOT NULL, PRIMARY KEY (day, visitor)
) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS daily_totals (
 day TEXT PRIMARY KEY, visitors INTEGER NOT NULL DEFAULT 0
);
CREATE TRIGGER IF NOT EXISTS count_new_visitor AFTER INSERT ON daily_visitors
BEGIN
 INSERT INTO daily_totals(day, visitors) VALUES (NEW.day, 1)
 ON CONFLICT(day) DO UPDATE SET visitors = visitors + 1;
END;
