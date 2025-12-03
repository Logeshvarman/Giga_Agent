from fastmcp import FastMCP
import pymysql

DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_USER = "root"
DB_PASS = "root"
DB_NAME = "production"

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
    )

mcp = FastMCP("db-mcp-server")

@mcp.tool()
def get_product_info(product_name: str, grade: str):
    """Fetch product and request data."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, name, price, quantity, grade, demand_level
            FROM products
            WHERE name = %s AND grade = %s
            """,
            (product_name, grade),
        )
        product = cursor.fetchone()

        cursor.execute(
            """
            SELECT needed_supply_count
            FROM product_requests
            WHERE product_name = %s AND grade = %s
            ORDER BY request_time DESC
            LIMIT 1
            """,
            (product_name, grade),
        )
        request = cursor.fetchone()

    conn.close()
    return {"product": product, "request": request}

if __name__ == "__main__":
     mcp.run(transport="http", host="0.0.0.0", port=8001)
