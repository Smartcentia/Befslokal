"""
Pydantic schemas for Jira integration API.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class JiraConfigResponse(BaseModel):
    """Response model for Jira configuration status."""
    configured: bool
    url: Optional[str] = None
    default_project: Optional[str] = None
    connection_test: Optional[Dict[str, Any]] = None


class JiraProjectResponse(BaseModel):
    """Response model for Jira project."""
    key: str
    name: str
    id: str
    projectTypeKey: Optional[str] = None


class JiraIssueTypeResponse(BaseModel):
    """Response model for Jira issue type."""
    id: str
    name: str
    description: str
    subtask: bool = False


class CreateJiraIssueRequest(BaseModel):
    """Request model for creating a Jira issue."""
    project_key: str = Field(..., description="Jira project key (e.g., 'BEFS')")
    summary: str = Field(..., min_length=1, max_length=255, description="Issue title/summary")
    description: str = Field(..., description="Detailed description of the issue")
    issue_type: str = Field(default="Task", description="Type of issue (Task, Bug, Story, etc.)")
    priority: Optional[str] = Field(None, description="Priority level (Highest, High, Medium, Low, Lowest)")
    labels: Optional[List[str]] = Field(None, description="List of labels to add")
    assignee: Optional[str] = Field(None, description="Username or account ID of assignee")


class JiraIssueResponse(BaseModel):
    """Response model for created Jira issue."""
    key: str
    url: str
    id: str
    self: str


class JiraIssueDetailResponse(BaseModel):
    """Response model for Jira issue details."""
    key: str
    id: str
    summary: str
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    url: str
