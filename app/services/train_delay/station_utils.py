import pymysql

def get_station_name_by_coords(lng, lat, conn=None):
    """
    根据经纬度查找站点名。假设经纬度唯一，且表名为 station_table，字段为 lng, lat, name。
    """
    close_conn = False
    if conn is None:
        conn = pymysql.connect(host='localhost', user='root', password='qwe123', database='train', charset='utf8')
        close_conn = True
    try:
        with conn.cursor() as cursor:
            sql = "SELECT en_name FROM jinghu_station WHERE ABS(longitude - %s) < 1e-5 AND ABS(latitude - %s) < 1e-5 LIMIT 1"
            cursor.execute(sql, (lng, lat))
            row = cursor.fetchone()
            return row[0] if row else f"{lng},{lat}"
    finally:
        if close_conn:
            conn.close()