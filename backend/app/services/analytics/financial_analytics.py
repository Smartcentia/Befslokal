from typing import Dict, List, Any, Optional
import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest
import logging

from app.domains.core.models.property import Property

logger = logging.getLogger(__name__)

class FinancialAnalyticsService:
    async def get_property_financial_history(self, db: Session, property_id: str) -> Dict[str, Any]:
        """
        Extracts financial history for a property from its external_data.
        Returns a sorted list of years and their total costs.
        """
        stmt = select(Property).where(Property.property_id == property_id)
        result = await db.execute(stmt)
        prop = result.scalar_one_or_none()
        
        if not prop or not prop.external_data:
            return None

        history = prop.external_data.get('financial_history', {})
        if not history:
            return None
            
        # Format: [{'year': 2020, 'total_costs': 50000}, ...]
        data_points = []
        for year, data in history.items():
            if isinstance(data, dict) and 'total_costs' in data:
                data_points.append({
                    'year': int(year),
                    'amount': float(data['total_costs'])
                })
        
        return sorted(data_points, key=lambda x: x['year'])

    async def forecast_future_costs(self, db: Session, property_id: str, years_ahead: int = 3) -> Dict[str, Any]:
        """
        Predicts future costs using Linear Regression on historical data.
        """
        history = await self.get_property_financial_history(db, property_id)
        
        if not history or len(history) < 2:
            return {"error": "Insufficient historical data for forecasting (need at least 2 years)."}

        # Prepare data for ML
        X = np.array([[d['year']] for d in history])
        y = np.array([d['amount'] for d in history])

        # Train Model
        model = LinearRegression()
        model.fit(X, y)

        # Predict
        last_year = history[-1]['year']
        future_years = np.array([[last_year + i] for i in range(1, years_ahead + 1)])
        predictions = model.predict(future_years)

        forecast = []
        for year, amount in zip(future_years.flatten(), predictions):
            forecast.append({
                "year": int(year),
                "predicted_cost": round(float(amount), 2)
            })
            
        # Calculate trend (slope)
        trend = "Stable"
        slope = model.coef_[0]
        if slope > 1000: trend = "Increasing"
        elif slope < -1000: trend = "Decreasing"

        return {
            "property_id": property_id,
            "forecast": forecast,
            "trend": trend,
            "annual_change_estimate": round(float(slope), 2)
        }

    async def detect_spending_anomalies(self, db: Session, property_id: str) -> Dict[str, Any]:
        """
        Uses Isolation Forest to detect anomalous expense years or categories provided in history.
        """
        history = await self.get_property_financial_history(db, property_id)
        
        if not history or len(history) < 3:
             return {"error": "Insufficient data for anomaly detection (need at least 3 years)."}

        # basic anomaly detection on total annual costs
        X = np.array([[d['amount']] for d in history])
        
        # Isolation Forest
        clf = IsolationForest(contamination=0.2, random_state=42)
        preds = clf.fit_predict(X)
        
        anomalies = []
        for idx, is_anomaly in enumerate(preds):
            if is_anomaly == -1: # -1 indicates anomaly
                anomalies.append({
                    "year": history[idx]['year'],
                    "amount": history[idx]['amount'],
                    "reason": "Unusual total cost deviation from norm"
                })
                
        return {
            "property_id": property_id,
            "anomaly_count": len(anomalies),
            "anomalies": anomalies,
            "status": "Anomalies Detected" if anomalies else "Normal"
        }

financial_analytics_service = FinancialAnalyticsService()
