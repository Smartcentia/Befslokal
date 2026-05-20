"""Fullverdig domeneagenter."""

from app.services.intelligence.fullverdig.agents.internkontroll import internkontroll_agent_node
from app.services.intelligence.fullverdig.agents.kontrakter import kontrakter_agent_node
from app.services.intelligence.fullverdig.agents.eiendommer import eiendommer_agent_node
from app.services.intelligence.fullverdig.agents.oekonomi import oekonomi_agent_node

__all__ = ["internkontroll_agent_node", "kontrakter_agent_node", "eiendommer_agent_node", "oekonomi_agent_node"]
