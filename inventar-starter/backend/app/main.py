from fastapi import FastAPI, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from .db import get_conn
import paho.mqtt.client as mqtt
from fastapi import Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import os
import paho.mqtt.client as mqtt
from fastapi import FastAPI, Request, Query, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from .db import get_conn

app = FastAPI(title="Inventar Starter", version="0.1.0")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

MQTT_HOST = os.getenv("MQTT_HOST", "mqtt")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

def mqtt_client() -> mqtt.Client:
    c = mqtt.Client()
    c.connect(MQTT_HOST, MQTT_PORT, keepalive=30)
    return c

@app.get("/health")
async def health():
    db_state = "ok"
    mqtt_state = "ok"
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("select 1")
            cur.fetchone()
    except Exception as ex:
        db_state = f"error:{type(ex).__name__}"

    try:
        c = mqtt_client()
        c.disconnect()
    except Exception as ex:
        mqtt_state = f"degraded:{type(ex).__name__}"

    return {"status": "ok" if db_state == "ok" else "degraded", "db": db_state, "mqtt": mqtt_state}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "Inventar Starter"})

@app.get("/inventory", response_class=HTMLResponse)
async def inventory_page(request: Request):
    return templates.TemplateResponse("inventory.html", {"request": request, "title": "Inventar Starter"})

@app.post("/mqtt/publish")
async def mqtt_publish(topic: str = Query(...), payload: str = Query(...)):
    c = mqtt_client()
    c.publish(topic, payload, qos=0, retain=False)
    c.disconnect()
    return {"ok": True, "topic": topic, "payload": payload}

@app.get("/devices", response_class=HTMLResponse)
def devices_page(request: Request):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            select d.serial_number, 
                   dt.type_name as device_type,
                   d.device_model, 
                   l.standort
            from devices d
            join device_type dt on d.device_type = dt.device_type_id
            join location_info l on l.location_id = d.device_location
            """
        )
        devices = list(cur.fetchall())

    return templates.TemplateResponse(
        "inventory.html",
        {"request": request, "title": "Geräte", "devices": devices},
    )


@app.post("/devices", response_class=HTMLResponse)
def create_device(
    request: Request,
    serial_number: str = Form(...),
    device_type: str = Form(...),      # Muss str sein für "Laptop" etc.
    device_model: str = Form(...),
    buy_date: str = Form(...),
    net_price: float = Form(...),
    device_location: str = Form(...),  # Muss str sein für "Berlin" etc.
    return_to: str | None = Form(None),
):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("select 1 from devices where serial_number = %s", (serial_number,))
        if cur.fetchone() is not None:
            raise HTTPException(
                status_code=409, 
                detail="IR-01 Conflict: Die Seriennummer existiert bereits."
            )

        cur.execute(
            """
            insert into devices (serial_number, device_type, device_model, buy_date, net_price, device_location)
            select d.serial_number, dt.device_type_id, d.device_model, cast(d.buy_date as date), cast(d.net_price as decimal), l.location_id
            from (values
                (%s, %s, %s, %s, %s, %s)
            ) as d(serial_number, type_name, device_model, buy_date, net_price, standort)
            join device_type dt on dt.type_name = d.type_name
            join location_info l on l.standort = d.standort
            """,
            (serial_number, device_type, device_model, buy_date, net_price, device_location),
        )
    
    target = return_to or "/devices"
    return RedirectResponse(target, status_code=303)


@app.get("/assignments/active", response_class=HTMLResponse)
def active_assignments_page(request: Request):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            select a.assignment_id,
                   a.issue_date,
                   p.first_name,
                   p.last_name,
                   p.mitarbeiter_id,
                   d.serial_number,
                   d.device_model
            from assignment a
            join person p on p.person_id = a.person_id
            join devices d on d.device_id = a.device_id
            where a.return_date is null
            order by a.issue_date desc
            """
        )
        assignments = list(cur.fetchall())
        
        cur.execute("select person_id, first_name, last_name from person order by last_name")
        persons = list(cur.fetchall())
        
        cur.execute("select device_id, serial_number, device_model from devices order by serial_number")
        devices = list(cur.fetchall())

    return templates.TemplateResponse(
        "active.html",
        {
            "request": request,
            "title": "Aktive Zuweisungen",
            "assignments": assignments,
            "persons": persons,
            "devices": devices
        },
    )


@app.post("/assignments", response_class=HTMLResponse)
def create_assignment(
    request: Request,
    person_id: int = Form(...),
    serial_number: str = Form(...),
    issue_date: str = Form(...),
    return_to: str | None = Form(None),
):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            select a.issue_date from assignment a
            join devices d on  a.device_id = d.device_id
            where d.serial_number = %s and return_date is null
            """,
            (serial_number,)
        )
        if cur.fetchone() is not None:
            raise HTTPException(
                status_code=409, 
                detail="IR-02 Conflict: Das Gerät hat bereits eine aktive Ausleihe."
            )

        cur.execute(
            """
            insert into assignment (person_id, serial_number, issue_date)
            values (%s, %s, %s) as a(mitarbeiter_id, serial_number, issue_date)
            join devices d on d.serial_number = a.serial_number
            join person p on p.mitarbeiter_id = a.mitarbeiter_id;
            """,
            (person_id, serial_number, issue_date),
        )
    
    target = return_to or "/assignments/active"
    return RedirectResponse(target, status_code=303)


@app.post("/assignments/{assignment_id}/return", response_class=HTMLResponse)
def return_assignment(
    request: Request,
    assignment_id: int,
    return_date: str = Form(...),
    return_to: str | None = Form(None),
):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "select issue_date from assignment where assignment_id = %s", 
            (assignment_id,)
        )
        row = cur.fetchone()
        
        if row:
            issue_date_str = str(row[0])
            if return_date < issue_date_str:
                raise HTTPException(
                    status_code=422, 
                    detail=f"IR-03 Unprocessable Entity: Rückgabedatum ({return_date}) darf nicht vor dem Ausgabedatum ({issue_date_str}) liegen."
                )

        cur.execute(
            """
            update assignment
            set return_date = %s
            where assignment_id = %s
            """,
            (return_date, assignment_id),
        )
    
    target = return_to or "/assignments/active"
    return RedirectResponse(target, status_code=303)
