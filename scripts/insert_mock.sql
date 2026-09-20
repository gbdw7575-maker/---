-- 1. 先给现有数据补上 measured_at（今天 2026-09-20）
UPDATE health_indicators SET measured_at = '2026-09-20 08:00:00' WHERE measured_at IS NULL;

-- 2. 插入历史模拟数据，让趋势图有折线变化
-- 空腹血糖：正常→偏高→正常→偏高
INSERT INTO health_indicators (user_id, category, name, value, unit, measured_at, statistic_type, reference_min, reference_max, source, created_at) VALUES
(1, 'blood_sugar', '空腹血糖', '6.5', 'mmol/L', '2026-09-08 08:00:00', 'average', 3.9, 6.0, 'manual', NOW()),
(1, 'blood_sugar', '空腹血糖', '5.7', 'mmol/L', '2026-09-12 08:00:00', 'average', 3.9, 6.0, 'manual', NOW());

-- 血压（收缩压/舒张压）：5 天变化
INSERT INTO health_indicators (user_id, category, name, value, unit, measured_at, statistic_type, reference_min, reference_max, source, created_at) VALUES
(1, 'blood_pressure', '收缩压', '145', 'mmHg', '2026-09-10 09:00:00', 'average', 0, 130, 'manual', NOW()),
(1, 'blood_pressure', '舒张压', '92',  'mmHg', '2026-09-10 09:00:00', 'average', 0, 80,  'manual', NOW()),
(1, 'blood_pressure', '收缩压', '138', 'mmHg', '2026-09-14 09:00:00', 'average', 0, 130, 'manual', NOW()),
(1, 'blood_pressure', '舒张压', '85',  'mmHg', '2026-09-14 09:00:00', 'average', 0, 80,  'manual', NOW()),
(1, 'blood_pressure', '收缩压', '142', 'mmHg', '2026-09-17 09:00:00', 'average', 0, 130, 'manual', NOW()),
(1, 'blood_pressure', '舒张压', '88',  'mmHg', '2026-09-17 09:00:00', 'average', 0, 80,  'manual', NOW());

-- 血脂：总胆固醇 / 甘油三酯 / 高密度脂蛋白（2 次对比）
INSERT INTO health_indicators (user_id, category, name, value, unit, measured_at, statistic_type, reference_min, reference_max, source, created_at) VALUES
(1, 'blood_fat', '甘油三酯', '5.8',  'mmol/L', '2026-09-06 10:00:00', 'single', 0.565, 1.96, 'manual', NOW()),
(1, 'blood_fat', '总胆固醇', '5.12', 'mmol/L', '2026-09-06 10:00:00', 'single', 2.9, 6.0, 'manual', NOW()),
(1, 'blood_fat', '高密度脂蛋白', '1.05', 'mmol/L', '2026-09-06 10:00:00', 'single', 1.1, 1.7, 'manual', NOW());

-- 肝功能：谷丙 / 谷草（2 次对比）
INSERT INTO health_indicators (user_id, category, name, value, unit, measured_at, statistic_type, reference_min, reference_max, source, created_at) VALUES
(1, 'liver', '谷丙转氨酶', '32.5', 'U/L', '2026-09-05 11:00:00', 'single', 5.0, 40.0, 'manual', NOW()),
(1, 'liver', '谷草转氨酶', '28.0', 'U/L', '2026-09-05 11:00:00', 'single', 8.0, 41.0, 'manual', NOW());

-- 3. 验证结果
SELECT category, name, DATE(measured_at) as d, value, statistic_type, reference_min, reference_max
FROM health_indicators
ORDER BY category, name, measured_at;
