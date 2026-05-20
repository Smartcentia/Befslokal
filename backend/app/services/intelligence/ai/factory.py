class AgentFactory:
    """Legacy factory for AI agents. Currently inactive as system moved to Direct OpenAI."""
    @classmethod
    def get_agent(cls):
        return None

agent_factory = AgentFactory()

