from pyspatialite import dbapi2 as db
import os

sqlite_path = "./data/bikes.sqlite"

if os.path.isfile(sqlite_path):
    print "Error: Database %s already initialised" % (sqlite_path)

else:
    # Create and connect
    conn = db.connect(sqlite_path)
    cur = conn.cursor()

    # Initialising Spatial MetaData
    # using v.2.4.0 this will automatically create
    # GEOMETRY_COLUMNS and SPATIAL_REF_SYS
    cur.execute("SELECT InitSpatialMetadata()")

    # Create `bikes` table
    cur.execute("CREATE TABLE 'bikes' ( ogc_fid INTEGER PRIMARY KEY, 'bikeid' INTEGER, 'timestamp' INTEGER)")

    # Register our `bikes` geometry column
    # cur.execute("SELECT AddGeometryColumn('bikes', 'geom', 4326, 'POINT', 'XY')")
    cur.execute("SELECT AddGeometryColumn('bikes', 'geom', 4326, 'LINESTRING', 'XY')")

    # Use Write Ahead Logging (WAL) mode to allow simultaneous read/write on tables
    # http://stackoverflow.com/a/22708807
    # https://sqlite.org/wal.html
    cur.execute('PRAGMA journal_mode=wal')
    
    conn.close()
    print "Table `bikes` initialised succesfully."