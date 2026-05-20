from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.domains.fdv.services.iot_service import iot_service
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class SensorCreate(BaseModel):
    property_id: str
    name: str
    type: str

class ReadingCreate(BaseModel):
    sensor_id: str
    value: float
    unit: str

@router.get("/")
async def root():
    return {"status": "IoT/Sensor MCP Server Active"}

@router.post("/sensors")
async def register_sensor(sensor: SensorCreate, db: Session = Depends(get_db)):
    """
    Agent Action: Register a new IoT device.
    """
    try:
        return await iot_service.register_sensor(db, sensor.property_id, sensor.name, sensor.type)
    except Exception as e:
        print(f"IoT Error (Register Sensor): {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/readings")
async def ingest_reading(reading: ReadingCreate, db: Session = Depends(get_db)):
    """
    Agent Action: Ingest data into the IoT service.
    """
    try:
        return await iot_service.ingest_reading(db, reading.sensor_id, reading.value, reading.unit)
    except Exception as e:
        print(f"IoT Error (Ingest Reading): {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/anomalies/{property_id}")
async def check_anomalies(property_id: str, db: Session = Depends(get_db)):
    """
    Agent Action: Check if a property has active sensor anomalies (e.g., leaks).
    """
    try:
        return await iot_service.get_property_anomalies(db, property_id)
    except Exception as e:
        print(f"IoT Error (Check Anomalies): {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
