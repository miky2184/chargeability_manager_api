from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from typing import Optional
from core.auth_config import create_access_token, verify_password, get_password_hash
import psycopg2.extras as extras
from fastapi.middleware.cors import CORSMiddleware
from core.common_db import get_conn, create_user, get_user_by_username, get_current_user
from starlette.responses import Response
import subprocess
import logging
import json
from datetime import date
from decimal import Decimal
from core.config import Config
from model.request import schemas
from core.auth_config import SECRET_KEY, ALGORITHM

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambia con i domini permessi
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=Config.LOG_LEVEL, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%a, %d %b %Y %H:%M:%S', filename=Config.LOG_PATH, filemode='a')

# OAuth2 schema
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db_connection():
    return get_conn(Config.DB_HOST, Config.DB_NAME, Config.DB_USER, Config.DB_PWD,
                        Config.DB_PORT)

# Funzione per convertire oggetti non serializzabili
def default_converter(obj):
    if isinstance(obj, Decimal):
        return float(obj)  # Converte Decimal in float
    if isinstance(obj, date):
        return obj.isoformat()  # Converte date in stringa 'YYYY-MM-DD'
    raise TypeError(f"Type {type(obj)} not serializable")

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db_connection()
    user = get_user_by_username(conn, form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register")
async def register(user: schemas.UserRegister):
    conn = get_db_connection()
    hashed_password = get_password_hash(user.password)
    user_id = create_user(conn, user.username, user.email, hashed_password, user.full_name)
    return {"id": user_id, "message": "User created successfully"}

@app.get("/users/me")
async def read_users_me(token: str = Depends(oauth2_scheme)):
    conn = get_db_connection()
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = get_user_by_username(conn, username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.get("/forecast", tags=['Chargeability Manager'])
async def get_forecast(current_user: dict = Depends(get_current_user)):
    return execute_query("chargeability_manager", """
            SELECT fiscal_year, yy_cal, mm_cal, fortnight, eid, work_hh, tot_hour, chg, hh_chg, hh_no_chg, calc_meeting_time, hh_no_chg_to_assign
             FROM chargeability_manager.check_forecast;
            """, exec_ddl=False)


@app.get("/chargeability", tags=['Chargeability Manager'])
async def get_chargeability(current_user: dict = Depends(get_current_user)):
    return execute_query("chargeability_manager", """
            SELECT eid, fiscal_year, yy_cal, mm_cal, tot_hours, work_hh, work_hh_chg, work_hh_nochg, work_hh_no_impact, chg_mm, chg_yy
              FROM chg_all;
            """, exec_ddl=False)


@app.get("/time-reports", tags=['Chargeability Manager'])
async def get_time_reports(current_user: dict = Depends(get_current_user)):
    return execute_query("chargeability_manager", """
    SELECT eid, wbs, fiscal_year, yy_cal, mm_cal, fortnight, work_hh, fl_forecast 
      FROM time_report
    """, exec_ddl=False)

@app.get("/wbs", tags=['Chargeability Manager'])
async def get_wbs(current_user: dict = Depends(get_current_user)):
    return execute_query("chargeability_manager", """
    SELECT wbs, wbs_type, project_name, budget_mm, budget_tot, true as salvata FROM wbs
    """, exec_ddl=False)

@app.post("/wbs", tags=['Chargeability Manager'])
async def post_wbs(wbs: schemas.WbsCreate, current_user: dict = Depends(get_current_user)):
    return execute_query("chargeability_manager", """
    INSERT INTO wbs (wbs, wbs_type, project_name, budget_mm, budget_tot) VALUES (%s, %s, %s, %s, %s)
    """, (wbs.wbs, wbs.wbs_type, wbs.project_name, wbs.budget_mm, wbs.budget_tot))

@app.put("/wbs/{wbs_id}", tags=['Chargeability Manager'])
async def put_wbs(wbs_id: str, wbs: schemas.WbsUpdate, current_user: dict = Depends(get_current_user)):
    return execute_query("chargeability_manager", """
    UPDATE wbs set wbs_type = %s , project_name = %s, budget_mm = %s, budget_tot = %s 
     where wbs = %s
    """, (wbs.wbs_type, wbs.project_name, wbs.budget_mm, wbs.budget_tot, wbs_id))

@app.delete("/wbs/{wbs_id}", tags=['Chargeability Manager'])
async def delete_wbs(wbs_id: str, current_user: dict = Depends(get_current_user)):
    return execute_query("chargeability_manager", """
    DELETE FROM wbs WHERE wbs = %s
    """, (wbs_id,))

@app.get("/resources", tags=['Chargeability Manager'])
async def get_resources(current_user: dict = Depends(get_current_user)):
    return execute_query("chargeability_manager", """
    select eid, last_name , first_name , "level" , loaded_cost , office , dte , true as salvata from resources r 
    """, exec_ddl=False)

@app.post("/resources", tags=['Chargeability Manager'])
async def post_resources(resource: schemas.ResourceCreate, current_user: dict = Depends(get_current_user)):
    return execute_query("chargeability_manager", """
    INSERT INTO resources (eid, last_name , first_name , "level" , loaded_cost , office , dte) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (resource.eid, resource.last_name, resource.first_name, resource.level, resource.loaded_cost,
          resource.office, resource.dte))

@app.put("/resources/{resources_id}", tags=['Chargeability Manager'])
async def put_resources(resources_id: str, resource: schemas.ResourceUpdate, current_user: dict = Depends(get_current_user)):
    return execute_query("chargeability_manager", """
    UPDATE resources set last_name = %s , first_name = %s, level = %s, loaded_cost = %s, office = %s, dte = %s 
     where eid = %s
    """, (resource.last_name, resource.first_name, resource.level, resource.loaded_cost,
          resource.office, resource.dte, resources_id))

@app.delete("/resources/{resources_id}", tags=['Chargeability Manager'])
async def delete_resources(resources_id: str, current_user: dict = Depends(get_current_user)):
    return execute_query("chargeability_manager", """
    DELETE FROM resources WHERE eid = %s
    """, (resources_id,))


def execute_query(schema_name: str, query: str, params: tuple = None, exec_ddl: bool = True) -> Response:
    """
        Esegue una query SQL su uno schema specifico e restituisce una risposta JSON.
    """
    conn = None
    result = None
    try:
        conn = get_conn(Config.DB_HOST, Config.DB_NAME, Config.DB_USER, Config.DB_PWD,
                        Config.DB_PORT)
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute(f"SET search_path = {schema_name};")
            cur.execute(query, params)

            if not exec_ddl:
                result = cur.fetchall()
            else:
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
