import sqlite3
from pathlib import Path

# 数据库路径
db_path = Path('data/rag_web.db')

if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    
    # 检查 graphs 表是否存在
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='graphs'")
    if cursor.fetchone():
        # 查询所有图谱记录
        rows = conn.execute("SELECT * FROM graphs").fetchall()
        print('数据库中的知识图谱记录：')
        if rows:
            for row in rows:
                print(dict(row))
        else:
            print('暂无知识图谱记录')
    else:
        print('graphs 表不存在，数据库可能未初始化')
    
    conn.close()
else:
    print('数据库文件不存在')