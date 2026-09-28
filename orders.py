def get_order(conn, order_id):
    query = "SELECT * FROM orders WHERE id = " + order_id
    return conn.execute(query).fetchone()
