"""
Jira Integration Service

Provides integration with Jira Cloud for creating and managing issues.
Uses the atlassian-python-api library for API communication.
"""

from typing import Optional, List, Dict, Any
from atlassian import Jira
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class JiraService:
    """Service for interacting with Jira Cloud API."""
    
    def __init__(self):
        """Initialize Jira service with configuration from settings."""
        self.jira_url = settings.JIRA_URL
        self.jira_email = settings.JIRA_EMAIL
        self.jira_api_token = settings.JIRA_API_TOKEN
        self.default_project = settings.JIRA_DEFAULT_PROJECT
        self._client: Optional[Jira] = None
    
    def is_configured(self) -> bool:
        """Check if Jira integration is properly configured."""
        return all([
            self.jira_url,
            self.jira_email,
            self.jira_api_token
        ])
    
    def get_client(self) -> Jira:
        """
        Get or create Jira client instance.
        
        Returns:
            Jira: Authenticated Jira client
            
        Raises:
            ValueError: If Jira is not configured
        """
        if not self.is_configured():
            raise ValueError(
                "Jira integration is not configured. Please set JIRA_URL, "
                "JIRA_EMAIL, and JIRA_API_TOKEN environment variables."
            )
        
        if self._client is None:
            try:
                if not self.jira_url:
                    raise ValueError("JIRA_URL is not set")
                
                logger.info(f"Connecting to Jira at {self.jira_url} for {self.jira_email}")
                self._client = Jira(
                    url=self.jira_url,
                    username=self.jira_email,
                    password=self.jira_api_token,
                    cloud=True,
                    timeout=10
                )
                # Test connection immediately to verify credentials
                self._client.myself()
                logger.info(f"Successfully connected to Jira at {self.jira_url}")
            except Exception as e:
                self._client = None
                logger.error(f"Failed to connect to Jira: {str(e)}")
                raise ValueError(f"Jira connection failed: {str(e)}")
        
        return self._client
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Jira and return status.
        
        Returns:
            Dict with status, user info, or error
        """
        if not self.is_configured():
            return {"success": False, "message": "Jira Integration not configured"}
            
        try:
            client = self.get_client()
            user = client.myself()
            return {
                "success": True, 
                "message": f"Connected as {user.get('displayName')} ({user.get('emailAddress')})",
                "user": user.get("displayName")
            }
        except Exception as e:
            logger.error(f"Jira connection test failed: {str(e)}")
            return {"success": False, "message": f"Connection failed: {str(e)}"}
    
    def create_issue(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Task",
        priority: Optional[str] = None,
        labels: Optional[List[str]] = None,
        assignee: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new Jira issue.
        
        Args:
            project_key: Jira project key (e.g., "BEFS")
            summary: Issue title/summary
            description: Detailed description of the issue
            issue_type: Type of issue (Task, Bug, Story, Epic, etc.)
            priority: Priority level (Highest, High, Medium, Low, Lowest)
            labels: List of labels to add to the issue
            assignee: Username or account ID of assignee
            **kwargs: Additional fields to include in the issue
            
        Returns:
            Dict containing the created issue details including key and URL
            
        Raises:
            Exception: If issue creation fails
        """
        client = self.get_client()
        
        # Build the issue fields
        fields = {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type},
        }
        
        # Add optional fields
        if priority:
            fields["priority"] = {"name": priority}
        
        if labels:
            fields["labels"] = labels
        
        if assignee:
            fields["assignee"] = {"name": assignee}
        
        # Add any additional custom fields
        fields.update(kwargs)
        
        try:
            logger.info(f"Creating Jira issue in project {project_key}: {summary}")
            issue = client.create_issue(fields=fields)
            
            issue_key = issue.get("key")
            issue_url = f"{self.jira_url}/browse/{issue_key}"
            
            logger.info(f"Successfully created Jira issue: {issue_key}")
            
            return {
                "key": issue_key,
                "url": issue_url,
                "id": issue.get("id"),
                "self": issue.get("self"),
            }
        except Exception as e:
            logger.error(f"Failed to create Jira issue: {str(e)}")
            raise Exception(f"Failed to create Jira issue: {str(e)}")
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """
        Get list of all accessible Jira projects.
        
        Returns:
            List of project dictionaries with key, name, and id
            
        Raises:
            Exception: If fetching projects fails
        """
        client = self.get_client()
        
        try:
            logger.info("Fetching Jira projects")
            projects = client.projects()
            
            # Extract relevant project information
            project_list = [
                {
                    "key": project.get("key"),
                    "name": project.get("name"),
                    "id": project.get("id"),
                    "projectTypeKey": project.get("projectTypeKey"),
                }
                for project in projects
            ]
            
            logger.info(f"Found {len(project_list)} Jira projects")
            return project_list
        except Exception as e:
            logger.error(f"Failed to fetch Jira projects: {str(e)}")
            raise Exception(f"Failed to fetch Jira projects: {str(e)}")
    
    def get_issue_types(self, project_key: str) -> List[Dict[str, Any]]:
        """
        Get available issue types for a specific project.
        
        Args:
            project_key: Jira project key
            
        Returns:
            List of issue type dictionaries with id, name, and description
            
        Raises:
            Exception: If fetching issue types fails
        """
        client = self.get_client()
        
        try:
            logger.info(f"Fetching issue types for project {project_key}")
            
            # Get project metadata to find issue types
            project = client.project(project_key)
            issue_types = project.get("issueTypes", [])
            
            # Extract relevant issue type information
            type_list = [
                {
                    "id": issue_type.get("id"),
                    "name": issue_type.get("name"),
                    "description": issue_type.get("description", ""),
                    "subtask": issue_type.get("subtask", False),
                }
                for issue_type in issue_types
                if not issue_type.get("subtask", False)  # Exclude subtasks by default
            ]
            
            logger.info(f"Found {len(type_list)} issue types for project {project_key}")
            return type_list
        except Exception as e:
            logger.error(f"Failed to fetch issue types: {str(e)}")
            raise Exception(f"Failed to fetch issue types: {str(e)}")
    
    def get_issue(self, issue_key: str) -> Dict[str, Any]:
        """
        Get details of a specific Jira issue.
        
        Args:
            issue_key: Jira issue key (e.g., "BEFS-123")
            
        Returns:
            Dict containing issue details
            
        Raises:
            Exception: If fetching issue fails
        """
        client = self.get_client()
        
        try:
            logger.info(f"Fetching Jira issue {issue_key}")
            issue = client.issue(issue_key)
            
            fields = issue.get("fields", {})
            
            return {
                "key": issue.get("key"),
                "id": issue.get("id"),
                "summary": fields.get("summary"),
                "description": fields.get("description"),
                "status": fields.get("status", {}).get("name"),
                "priority": fields.get("priority", {}).get("name"),
                "assignee": fields.get("assignee", {}).get("displayName"),
                "reporter": fields.get("reporter", {}).get("displayName"),
                "created": fields.get("created"),
                "updated": fields.get("updated"),
                "url": f"{self.jira_url}/browse/{issue.get('key')}",
            }
        except Exception as e:
            logger.error(f"Failed to fetch Jira issue {issue_key}: {str(e)}")
            raise Exception(f"Failed to fetch Jira issue: {str(e)}")


# Singleton instance
jira_service = JiraService()
