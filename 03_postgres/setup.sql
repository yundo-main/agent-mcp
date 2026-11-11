-- 03_postgres 실습용 샘플 데이터와 읽기 전용 롤 (슈퍼유저로 한 번만 실행)
CREATE TABLE IF NOT EXISTS orders (
    id         SERIAL PRIMARY KEY,
    customer   TEXT NOT NULL,
    amount     INTEGER NOT NULL,
    ordered_at DATE NOT NULL
);
-- 테이블이 비어 있을 때만 넣는다 (다시 실행해도 5건 유지)
INSERT INTO orders (customer, amount, ordered_at)
SELECT * FROM (VALUES
    ('김민수', 12000, current_date - 40),
    ('이서연', 8500,  current_date - 35),
    ('박지훈', 23000, current_date - 20),
    ('최유진', 4500,  current_date - 12),
    ('정하늘', 15000, current_date - 3)
) AS v(customer, amount, ordered_at)
WHERE NOT EXISTS (SELECT 1 FROM orders);

-- 읽기 전용 롤: SELECT만 허용 (비밀번호는 실습용 자리표시자 — .env의 DATABASE_URI와 맞출 것)
DO $$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_ro') THEN
        CREATE ROLE app_ro LOGIN PASSWORD 'app_ro_pw';
    END IF;
END $$;
GRANT CONNECT ON DATABASE postgres TO app_ro;
GRANT USAGE ON SCHEMA public TO app_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_ro;
