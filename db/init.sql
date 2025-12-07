CREATE TABLE IF NOT EXISTS test_table (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_test_table_name ON test_table(name);
CREATE INDEX IF NOT EXISTS idx_test_table_created_at ON test_table(created_at DESC);

INSERT INTO test_table (name, value) VALUES
    ('test1', 'Тестовое значение 1'),
    ('test2', 'Тестовое значение 2'),
    ('test3', 'Тестовое значение 3')
ON CONFLICT DO NOTHING;

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_test_table_updated_at ON test_table;
CREATE TRIGGER update_test_table_updated_at 
BEFORE UPDATE ON test_table 
FOR EACH ROW 
EXECUTE FUNCTION update_updated_at_column();

GRANT ALL ON test_table TO testuser;
GRANT USAGE ON SEQUENCE test_table_id_seq TO testuser;
