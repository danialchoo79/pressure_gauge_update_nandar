
import arrow
import psycopg2
import pandas as pd
import datetime


############
## HELPER ##
############

def getpgconnection(sqlparam):
    '''Sql Connection Parameters



    Parameters
    ----------
    Param : {[1dARRAY]}
    [databasename,user,password,host]



    Returns
    -------
    [psycopg2 Connection Obj]



    '''
    try:



        conn = psycopg2.connect("dbname='"+sqlparam[0] + "' user='"+sqlparam[1]+"' password='"+sqlparam[2]+"' host='"+ sqlparam[3] +"'" )



        return conn
    except Exception as e:
        raise



## MAIN METHOD ## 
################# 

def create_pressure_header_main(params, spt_db_connections):
    try:

        pgConn = None
        pgConn = getpgconnection((spt_db_connections['DATABASE'],
                         spt_db_connections['USER'],
                         spt_db_connections['PASSWORD'],
                         spt_db_connections['HOST']
        ))

        run_id = create_pressure_header(pgConn,params)
        return run_id
    except Exception as e:
        raise e
    finally:
        if (pgConn is not None):
            pgConn.close()

def create_run_data_main(params, spt_db_connections):
    try:
        pgConn = None
        pgConn = getpgconnection((spt_db_connections['DATABASE'],
                         spt_db_connections['USER'],
                         spt_db_connections['PASSWORD'],
                         spt_db_connections['HOST']
        ))

        run_id = create_run_data(pgConn,params)
        return run_id
    except Exception as e:
        raise e
    finally:
        if (pgConn is not None):
            pgConn.close()


## Database Method ##
#####################

def create_pressure_header(pgConn,data):
    try:
        cur = pgConn.cursor()
        cur.execute("SELECT * FROM cryro_pump_uat.cryro_pump_pressure_header( %s,%s,%s,%s,%s,%s,%s) ;", data)
        result = cur.fetchall()[0]
        run_id = result[0]
        error_code = result[1]

        if (error_code == "1") :
            raise Exception("Error create_pressure_header due to  - " , result[2])
        pgConn.commit()
        return run_id
    except Exception as e:
        raise e

def create_run_data(pgConn,data):
    try:
        cur = pgConn.cursor()
        cur.execute("SELECT * FROM cryro_pump_uat.create_cryro_pump_run_data( %s,%s,%s,%s,%s,%s) ;", data)
        result = cur.fetchall()[0] # grabs first row of results
        error_code = result[0] # gets error / status code

        if (error_code == "1") :
            raise Exception("Error create_run_data due to  - " , result[1])
        pgConn.commit() # finalize the changes

    except Exception as e:
        raise e
