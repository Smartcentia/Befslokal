from typing import List, Optional
from sqlalchemy.orm import Session
from app.domains.fdv.models.iot import Sensor, SensorReading, Anomaly
from app.services.base import BaseService
from datetime import datetime
import logging

logger = logging.getLogger("IoTService")

class IoTService(BaseService):
    """
    Service for managing IoT sensors and data.
    """
    async def register_sensor(self, db: Session, property_id: str, name: str, type: str) -> dict:
        """
        Registers a new sensor.
        """
        self.log_info(f"Registering sensor {name} for property {property_id}")
        sensor = Sensor(property_id=property_id, name=name, type=type)
        db.add(sensor)
        db.commit()
        db.refresh(sensor)
        return {"sensor_id": str(sensor.sensor_id), "status": "active"}

    async def ingest_reading(self, db: Session, sensor_id: str, value: float, unit: str) -> dict:
        """
        Ingests a reading and checks for anomalies.
        """
        reading = SensorReading(sensor_id=sensor_id, value=value, unit=unit)
        db.add(reading)
        
        # Anomaly detection logic
        anomaly_detected = False
        if (unit == "C" and value > 30) or (unit == "leak_status" and value > 0):
             anomaly_detected = True
             self.log_warning(f"Anomaly detected on sensor {sensor_id}: Value {value} {unit}")
             anomaly = Anomaly(
                 sensor_id=sensor_id,
                 description=f"High value detected: {value} {unit}",
                 severity="high"
             )
             db.add(anomaly)

        db.commit()
        
        return {
            "status": "ingested", 
            "anomaly": anomaly_detected
        }

    async def get_property_anomalies(self, db: Session, property_id: str) -> List[dict]:
        """
        Lists active anomalies for a property (via sensor join).
        """
        # This requires a join, simplified here for now:
        # In real impl: join Anomaly -> Sensor -> Property
        anomalies = db.query(Anomaly).join(Sensor).filter(Sensor.property_id == property_id).all()
        return [
            {"description": a.description, "severity": a.severity, "date": str(a.detected_at)}
            for a in anomalies
        ]

iot_service = IoTService()
