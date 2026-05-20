
from app.db.base_class import Base

# Import all the models, so that Base has them before being
# imported by Alembic
# Import all models here for Alembic

# VIKTIG: Import rekkefølge er kritisk for SQLAlchemy relationships!
# Modeller som andre modeller har relationship til MÅ importeres FØR.
# Property har relationships til: Center, RiskAssessment, InternalControlCase

# 1. Grunnleggende modeller (ingen relationships til andre domener)
from app.domains.core.models.organisation import Organisation  # Fase 6 — må importeres FØR User/Property
from app.domains.core.models.user import User
from app.domains.core.models.party import Party
from app.domains.core.models.center import Center

# 2. HMS-modeller (Property har relationship til disse)
from app.domains.hms.models.risk import RiskAssessment, RiskFactor
from app.domains.hms.models.internal_control import InternalControlCase, Notification
from app.domains.hms.models.checklist import ChecklistTemplate, ChecklistExecution
from app.domains.hms.models.scheduled_activity import ScheduledActivity, ActivityTemplate

# 3. Nå kan Property importeres (etter at alle dens relationships er definert)
from app.domains.core.models.lokasjon import Lokasjon  # Må komme FØR Property (Property.lokasjon_id FK)
from app.domains.core.models.property import Property
# Import NS 3451 Code (referenced by BuildingComponent)
from app.domains.core.models.ns3451 import NS3451Code

# 4. Modeller som avhenger av Property
# Building hierarchy (Fase 4): Building → Floor → Space (must come before Unit)
from app.domains.core.models.building import Building, Floor, Space
from app.domains.core.models.unit import Unit
from app.domains.core.models.contract import Contract
from app.domains.core.models.email_verification import EmailVerificationCode
from app.domains.core.models.mfa_token import MFAToken
from app.domains.core.models.property_annual_cost import PropertyAnnualCost
from app.domains.core.models.property_husleie_csv import PropertyHusleieCsv
# Temporarily disabled: from app.domains.core.models.api_usage import APIUsage
from app.models.crisis_center import CrisisCenter
from app.models.financial_models import Budget, GLTransaction, FinanceBudget

from app.domains.fdv.models.action import WorkOrder, Task
from app.domains.fdv.models.fdv import BuildingComponent, MaintenanceRecord
from app.domains.fdv.models.iot import Sensor, SensorReading, Anomaly
from app.domains.fdv.models.bim import BIMModel, BIMObject
from app.domains.fdv.models.compliance import FdvuSection  # noqa: F401 — required for Property mapper

from app.domains.innsikt.models.memory import UserPreference, ContextHistory

# Legacy/Shared/Not Migrated Yet
from app.models.file_meta import FileMeta
from app.models.text_content import TextContent
from app.models.external_api_data import ExternalApiData
from app.models.api_call_logs import ApiCallLog
from app.models.proximity import ProximityService
from app.models.geo import GeologicalData, NaturalHazardEvent
from app.models.environmental import EnvironmentalData
from app.models.gdpr import DataSubjectRequest, AnonymizationLog
from app.models.ai_tool import AITool
from app.models.agent_memory import AgentMemory
from app.models.data_governance import DataFieldMetadata
from app.models.master_data_crosswalk import MasterDataCrosswalk
from app.models.agresso_budget import AgressoBudget
from app.models.institution_plasser import InstitusjonPlasser
