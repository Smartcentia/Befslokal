from enum import Enum
from typing import Dict, Any, List, Optional
import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.hms.models.risk import RiskAssessment
from app.domains.core.models.property import Property

class ProcessState(Enum):
    OPPRETTET = "Opprettet"     # Created
    ANALYSE = "Analyse"         # Analysis
    TILTAK = "Tiltak"           # Measures
    KONTROLL = "Kontroll"       # Review/Control
    LUKKET = "Lukket"           # Closed

class ProcessService:
    """
    Manages the lifecycle of an Internal Control Process using the Database.
    Strictly follows the state machine: Opprettet -> Analyse -> Tiltak -> Kontroll -> Lukket.
    """

    @staticmethod
    async def get_process(deviation_id: str, db: AsyncSession) -> Dict[str, Any]:
        """
        Gets existing process (Case) for a deviation or initializes a new one.
        """
        try:
            dev_uuid = UUID(deviation_id)
        except ValueError:
            return None

        # 1. Check if Case exists for this Risk Assessment
        stmt = select(InternalControlCase).filter(InternalControlCase.risk_assessment_id == dev_uuid)
        result = await db.execute(stmt)
        case = result.scalar_one_or_none()

        if case:
            return ProcessService._format_case(case)
        
        # 2. If not, create new Case
        # We need the RiskAssessment to get property_id and details
        r_stmt = select(RiskAssessment).filter(RiskAssessment.assessment_id == dev_uuid)
        r_res = await db.execute(r_stmt)
        risk = r_res.scalar_one_or_none()
        
        if not risk:
            # Cannot create process without parent deviation
            print(f"Risk Assessment {deviation_id} not found")
            return None

        new_case = InternalControlCase(
            title=f"Behandling av avvik: {risk.risk_category}",
            description=risk.notes or "Automatisk opprettet sak fra risikovurdering",
            case_type="deviation_handling",
            property_id=risk.property_id,
            risk_assessment_id=risk.assessment_id,
            process_state=ProcessState.OPPRETTET.value,
            process_data={},
            process_history=[],
            status="open"
        )
        db.add(new_case)
        await db.commit()
        await db.refresh(new_case)
        
        return ProcessService._format_case(new_case)

    @staticmethod
    async def transition(deviation_id: str, action: str, data: Dict[str, Any] = None, db: AsyncSession = None) -> Dict[str, Any]:
        """
        Transitions the process to the next state based on action.
        """
        if not db:
            raise ValueError("Database session required")

        # Get the Case (we know it exists or we fail)
        try:
            dev_uuid = UUID(deviation_id)
        except ValueError:
            return None

        stmt = select(InternalControlCase).filter(InternalControlCase.risk_assessment_id == dev_uuid)
        result = await db.execute(stmt)
        case = result.scalar_one_or_none()

        if not case:
             # Should natively create if not found? 
             # For a transition action, strictly speaking, the process should exist or be created implicitly.
             # Let's call get_process to ensure creation.
             # But get_process returns dict. We need ORM object here.
             # Redundant lookup but simplest safe way:
             await ProcessService.get_process(deviation_id, db)
             # Re-fetch ORM object
             result = await db.execute(stmt)
             case = result.scalar_one_or_none()

        current_state_val = case.process_state or ProcessState.OPPRETTET.value
        try:
            current_state = ProcessState(current_state_val)
        except ValueError:
            current_state = ProcessState.OPPRETTET

        # Update process data
        if data:
            current_data = dict(case.process_data) if case.process_data else {}
            current_data.update(data)
            case.process_data = current_data

        # State Machine Logic
        next_state = current_state
        
        if current_state == ProcessState.OPPRETTET and action == "start_analysis":
            next_state = ProcessState.ANALYSE
        elif current_state == ProcessState.ANALYSE and action == "submit_analysis":
            next_state = ProcessState.TILTAK
        elif current_state == ProcessState.TILTAK and action == "submit_measures":
            next_state = ProcessState.KONTROLL
        elif current_state == ProcessState.KONTROLL and action == "approve":
            next_state = ProcessState.LUKKET
            case.status = "closed"
            case.completed_at = datetime.datetime.now()
            
        if next_state != current_state:
            case.process_state = next_state.value
            
            # Update History
            history_entry = {
                "from": current_state.value,
                "to": next_state.value,
                "timestamp": datetime.datetime.now().isoformat(),
                "action": action
            }
            # Copy list to mutate
            current_history = list(case.process_history) if case.process_history else []
            current_history.append(history_entry)
            case.process_history = current_history
            
        await db.commit()
        await db.refresh(case)
        return ProcessService._format_case(case)

    @staticmethod
    def _format_case(case: InternalControlCase) -> Dict[str, Any]:
        """Helper to format ORM object to expected Dict structure."""
        
        # Calculate current step index
        steps = [ProcessState.OPPRETTET, ProcessState.ANALYSE, ProcessState.TILTAK, ProcessState.KONTROLL, ProcessState.LUKKET]
        try:
            current_state = ProcessState(case.process_state)
            step_index = steps.index(current_state)
        except ValueError:
            step_index = 0

        return {
            "deviation_id": str(case.risk_assessment_id) if case.risk_assessment_id else str(case.case_id),
            "status": case.process_state,
            "process_data": case.process_data or {},
            "history": case.process_history or [],
            "current_step_index": step_index,
            "case_id": str(case.case_id)
        }

    @staticmethod
    def get_steps() -> List[Dict[str, str]]:
        """Returns the definitions of steps in Norwegian."""
        return [
            {"id": "step1", "label": "Start", "state": "Opprettet"},
            {"id": "step2", "label": "Årsaksanalyse", "state": "Analyse", "desc": "Hvorfor skjedde dette?"},
            {"id": "step3", "label": "Tiltak", "state": "Tiltak", "desc": "Hva skal gjøres?"},
            {"id": "step4", "label": "Verifisering", "state": "Kontroll", "desc": "Har tiltaket fungert?"},
            {"id": "step5", "label": "Ferdig", "state": "Lukket"}
        ]
