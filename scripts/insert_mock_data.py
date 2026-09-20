"""插入模拟历史数据，让趋势图能看到真正的折线变化"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from datetime import datetime, timedelta
import pymysql

# 配置
conn = pymysql.connect(
    host='localhost', port=3306,
    user='root', password='root',
    database='health', charset='utf8mb4'
)
cur = conn.cursor()

# 先查 user_id
cur.execute("SELECT id FROM health_user LIMIT 1")
row = cur.fetchone()
if not row:
    print("❌ 没有用户，请先注册")
    sys.exit(1)
user_id = row[0]
print(f"✅ user_id = {user_id}")

# 查当前已有的指标（不重复插入）
cur.execute("SELECT name, DATE(measured_at) FROM health_indicator WHERE user_id=%s", (user_id,))
existing = {(r[0], str(r[1])) for r in cur.fetchall()}
print(f"已有 {len(existing)} 条记录")

# 模拟数据：血糖、血压、血脂、肝功能，近 14 天各 3-4 个时间点
mock = [
    # 空腹血糖（3 个时间点：偏高→正常→偏高）
    ("空腹血糖", "blood_sugar", 6.5, "2026-09-08 08:00:00", "average", "mmol/L", 3.9, 6.0, "manual"),
    ("空腹血糖", "blood_sugar", 5.7, "2026-09-12 08:00:00", "average", "mmol/L", 3.9, 6.0, "manual"),
    ("空腹血糖", "blood_sugar", 6.2, "2026-09-20 08:00:00", "average", "mmol/L", 3.9, 6.0, "ocr"),

    # 收缩压 / 舒张压（每天一组，5 天变化）
    ("收缩压", "blood_pressure", 145, "2026-09-10 09:00:00", "average", "mmHg", 0, 130, "manual"),
    ("舒张压", "blood_pressure", 92,  "2026-09-10 09:00:00", "average", "mmHg", 0, 80,  "manual"),
    ("收缩压", "blood_pressure", 138, "2026-09-14 09:00:00", "average", "mmHg", 0, 130, "manual"),
    ("舒张压", "blood_pressure", 85,  "2026-09-14 09:00:00", "average", "mmHg", 0, 80,  "manual"),
    ("收缩压", "blood_pressure", 142, "2026-09-17 09:00:00", "average", "mmHg", 0, 130, "manual"),
    ("舒张压", "blood_pressure", 88,  "2026-09-17 09:00:00", "average", "mmHg", 0, 80,  "manual"),
    ("收缩压", "blood_pressure", 136, "2026-09-20 09:00:00", "average", "mmHg", 0, 130, "ocr"),
    ("舒张压", "blood_pressure", 73,  "2026-09-20 09:00:00", "average", "mmHg", 0, 80,  "ocr"),

    # 甘油三酯 + 总胆固醇（2 次对比，改善中）
    ("甘油三酯", "blood_fat", 5.8, "2026-09-06 10:00:00", "single", "mmol/L", 0.565, 1.96, "manual"),
    ("甘油三酯", "blood_fat", 7.8, "2026-09-20 10:00:00", "single", "mmol/L", 0.565, 1.96, "ocr"),
    ("总胆固醇", "blood_fat", 5.12, "2026-09-06 10:00:00", "single", "mmol/L", 2.9, 6.0, "manual"),
    ("总胆固醇", "blood_fat", 4.44, "2026-09-20 10:00:00", "single", "mmol/L", 2.9, 6.0, "ocr"),
    ("高密度脂蛋白", "blood_fat", 1.05, "2026-09-06 10:00:00", "single", "mmol/L", 1.1, 1.7, "manual"),  # 偏低
    ("高密度脂蛋白", "blood_fat", 1.20, "2026-09-20 10:00:00", "single", "mmol/L", 1.1, 1.7, "ocr"),

    # 谷丙转氨酶 / 谷草转氨酶（2 次）
    ("谷丙转氨酶", "liver", 32.5, "2026-09-05 11:00:00", "single", "U/L", 5.0, 40.0, "manual"),
    ("谷丙转氨酶", "liver", 20.6, "2026-09-20 11:00:00", "single", "U/L", 5.0, 40.0, "ocr"),
    ("谷草转氨酶", "liver", 28.0, "2026-09-05 11:00:00", "single", "U/L", 8.0, 41.0, "manual"),
    ("谷草转氨酶", "liver", 31.4, "2026-09-20 11:00:00", "single", "U/L", 8.0, 41.0, "ocr"),
]

inserted = 0
skipped = 0
for row in mock:
    name, cat, val, measured_at, stype, unit, rmin, rmax, src = row
    key = (name, measured_at[:10])
    if key in existing:
        skipped += 1
        continue
    cur.execute("""
        INSERT INTO health_indicator
        (user_id, name, category, value, measured_at, statistic_type, unit,
         reference_min, reference_max, source, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
    """, (user_id, name, cat, val, measured_at, stype, unit, rmin, rmax, src))
    inserted += 1

conn.commit()
print(f"\n✅ 插入 {inserted} 条，跳过 {skipped} 条已存在")

# 验证
cur.execute("SELECT category, name, DATE(measured_at), value FROM health_indicator WHERE user_id=%s ORDER BY measured_at", (user_id,))
print(f"\n📊 当前所有指标 ({cur.rowcount} 条):")
for r in cur.fetchall():
    print(f"  {r[0]:15s} {r[1]:12s} {r[2]}  {r[3]}")

conn.close()
