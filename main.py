from fastapi import FastAPI
import psycopg2.extras as extras
from fastapi.middleware.cors import CORSMiddleware
from core.common_db import get_conn
from starlette.responses import Response
import subprocess
import logging
import json
from datetime import date
from decimal import Decimal
from core.config import Config

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=Config.LOG_LEVEL, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%a, %d %b %Y %H:%M:%S', filename=Config.LOG_PATH, filemode='a')

# Funzione per convertire oggetti non serializzabili
def default_converter(obj):
    if isinstance(obj, Decimal):
        return float(obj)  # Converte Decimal in float
    if isinstance(obj, date):
        return obj.isoformat()  # Converte date in stringa 'YYYY-MM-DD'
    raise TypeError(f"Type {type(obj)} not serializable")


@app.get("/chargeability", tags=['Chargeability Manager'])
async def get_chargeability():
    return execute_query("chargeability_manager", """
            SELECT eid, work_hh, chg, hh_no_chg_to_assign 
            FROM check_forecast
            """)


@app.get("/time-reports", tags=['Chargeability Manager'])
async def get_time_reports():
    return execute_query("chargeability_manager", """
    SELECT * FROM report_tr_mm
    """)


def execute_query(schema_name: str, query: str, params: tuple = None) -> Response:
    """
        Esegue una query SQL su uno schema specifico e restituisce una risposta JSON.
    """
    conn = None
    try:
        conn = get_conn(Config.DB_HOST, Config.DB_NAME, Config.DB_USER, Config.DB_PWD,
                        Config.DB_PORT)
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute(f"SET search_path = {schema_name};")
            cur.execute(query, params)

            result = cur.fetchall()

            conn.commit()

        return Response(json.dumps(result, default=default_converter), media_type="application/json")
    except Exception as e:
        logging.error(f'Errore {str(e)}')
        return Response(status_code=500)
    finally:
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()


def execute_webhook(repo_path: str, service_name: str):
    try:
        subprocess.run(['git', '-C', repo_path, 'pull'])
        # Riavvia il servizio delle API
        subprocess.run(['echo', Config.UBUNTU_PWD, '|', 'sudo', '-S', 'systemctl', 'restart', service_name])
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Errore durante il webhook: {e}")
        return Response(f"Errore: {str(e)}", status_code=500)


@app.post("/chargeability-manager-api-webhook", tags=['WebHook'])
async def chargeability_manager():
    return execute_webhook('/home/miky2184/Documents/Workspace/chargeability_manager_api', 'chargeabilitymanagerapi.service')
