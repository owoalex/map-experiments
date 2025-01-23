import psycopg2
import os
import json

conn_string = 'host=' + os.environ.get("POSTGRES_HOST") + ' dbname=' + os.environ.get("POSTGRES_DB") + ' user=' + os.environ.get("POSTGRES_USER") + ' password=' + os.environ.get("POSTGRES_PASSWORD") + ''

def get_postgres():
    return psycopg2.connect(conn_string)

if __name__ == "__main__":
    conn = get_postgres()

    cur = conn.cursor()
    #query = "SELECT * FROM planet_osm_nodes WHERE lat>=" + str(int(bb * 10000000)) + " AND lat<=" + str(int(bt * 10000000)) + " AND lon>=" + str(int(bl * 10000000)) + " AND lon<=" + str(int(br * 10000000))
    #print(query)
    #cur.execute(query)
    
    #nodes = cur.fetchall()
    
    query = "SELECT * FROM planet_osm_ways"
    cur.execute(query)
    rows = cur.fetchall()
    cols = cur.description
    for row in rows:
        dictrow = {
                "id": row[0],
                "nodes": row[1]
            }
        if not row[2] is None:
            if len(row[2]) % 2 == 0:
                for i in range(int(len(row[2]) / 2)):
                    dictrow[row[2][i * 2]] = row[2][(i * 2)+1]
        
        print(json.dumps(dictrow, indent=4))
        #break;
        #if not dictrow["highway"] is None:
        #    print(json.dumps(dictrow, indent=4))
        #break;
