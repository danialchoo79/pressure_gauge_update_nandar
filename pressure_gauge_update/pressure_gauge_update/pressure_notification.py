
import arrow
import requests
import json
from requests.exceptions import ConnectionError,Timeout
from pprint import pprint

headers = {'content-type': 'application/json'}


def trigger_pressure_notify(line, pumpno, value):
    try:
        ws_address = 'http://128.53.1.156/Fb_ws/api/Facebook/SEND_GENERIC_MESSAGE'

        lineStr = "PRESSURE PUMP  Line - {} , No. - {} , Value - {} is OOS".format(line, pumpno,value)


        inputdata = {
                    "thread_id":"t_9048267778578285",
                    "message":lineStr
                }

        call_webservice_json(inputdata, ws_address,timeout_val=None)
    except Exception as e:
        raise e

def call_webservice_json(input,ws_address,timeout_val=None):
    try:
        # INIT HEADERS
        headers = {'content-type': 'application/json'}
        paramsJson = None
        print(type(input))

        # CHECK IF INPUT IS DICTIONARY
        if isinstance(input,dict):
            paramsJson = json.dumps(input)
        if isinstance(input,str):
            try:
                json_object = json.loads(input)
            except ValueError as e:
                raise ValueError("Json Load Failed : Json String Is Invalid")
            paramsJson = input

        r = requests.post(ws_address, data=paramsJson, headers=headers , verify=False,timeout=timeout_val)

        if r.status_code != 200:
            r.raise_for_status()

        result = {
                    "code"    : r.status_code,
                    "message" : r.reason
                    }

        return result
    except ValueError as e:
        raise
    except ConnectionError:
        raise ConnectionError("ConnectionError - Invalid Url Detected {}")
    except Timeout:
        raise Timeout("Connection Time out Error : Please Increase the timeout value")
    except Exception as e:
        raise

if __name__ == '__main__':
    ws_address = 'http://128.53.1.156/FB_WS/api/Facebook/TRIGGER_TDU_MESSAGE'
    inputdata = {
        "data" : {
                "LINENO" : "205",
                "TYPE" : "Error @P1 - KNN abnormal"
        }

    }

    call_webservice_json(inputdata,ws_address,timeout_val=None)
