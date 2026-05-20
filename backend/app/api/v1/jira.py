"""
Jira Integration API Endpoints

Provides REST API endpoints for Jira integration including:
- Issue creation
- Project listing
- Issue type retrieval
- Configuration status
"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.api.deps import get_current_user, get_db
from app.schemas.jira import (
    JiraConfigResponse,
    JiraProjectResponse,
    JiraIssueTypeResponse,
    CreateJiraIssueRequest,
    JiraIssueResponse,
    JiraIssueDetailResponse,
)
from app.services.jira_service import jira_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/config", response_model=JiraConfigResponse)
async def get_jira_config(
    current_user = Depends(get_current_user),
) -> JiraConfigResponse:
    """
    Get Jira configuration status.
    
    Returns configuration status without exposing sensitive credentials.
    """
    try:
        is_configured = jira_service.is_configured()
        
        return JiraConfigResponse(
            configured=is_configured,
            url=jira_service.jira_url if is_configured else None,
            default_project=jira_service.default_project if is_configured else None,
            connection_test=None  # Don't test connection automatically to avoid blocking
        )
    except Exception as e:
        logger.error(f"Error checking Jira configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check Jira configuration: {str(e)}"
        )


@router.get("/test-connection", response_model=JiraConfigResponse)
async def test_jira_connection(
    current_user = Depends(get_current_user),
) -> JiraConfigResponse:
    """
    Test the Jira connection and return status.
    """
    try:
        is_configured = jira_service.is_configured()
        if not is_configured:
            return JiraConfigResponse(configured=False)
            
        connection_test = jira_service.test_connection()
        
        return JiraConfigResponse(
            configured=is_configured,
            url=jira_service.jira_url,
            default_project=jira_service.default_project,
            connection_test=connection_test
        )
    except Exception as e:
        logger.error(f"Error testing Jira connection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test Jira connection: {str(e)}"
        )


@router.get("/projects", response_model=List[JiraProjectResponse])
def list_jira_projects(
    current_user = Depends(get_current_user),
) -> List[JiraProjectResponse]:
    """
    List all accessible Jira projects.
    
    Requires Jira to be configured with valid credentials.
    """
    try:
        if not jira_service.is_configured():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Jira integration is not configured. Please set JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN."
            )
        
        projects = jira_service.get_projects()
        return [JiraProjectResponse(**project) for project in projects]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Jira projects: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch Jira projects: {str(e)}"
        )


@router.get("/projects/{project_key}/issue-types", response_model=List[JiraIssueTypeResponse])
def get_project_issue_types(
    project_key: str,
    current_user = Depends(get_current_user),
) -> List[JiraIssueTypeResponse]:
    """
    Get available issue types for a specific Jira project.
    
    Args:
        project_key: Jira project key (e.g., "BEFS")
    """
    try:
        if not jira_service.is_configured():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Jira integration is not configured."
            )
        
        issue_types = jira_service.get_issue_types(project_key)
        return [JiraIssueTypeResponse(**issue_type) for issue_type in issue_types]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching issue types for project {project_key}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch issue types: {str(e)}"
        )


@router.post("/issues", response_model=JiraIssueResponse, status_code=status.HTTP_201_CREATED)
def create_jira_issue(
    request: CreateJiraIssueRequest,
    current_user = Depends(get_current_user),
) -> JiraIssueResponse:
    """
    Create a new Jira issue.
    
    Creates an issue in the specified project with the provided details.
    Returns the created issue key and URL.
    """
    try:
        if not jira_service.is_configured():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Jira integration is not configured. Please set JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN."
            )
        
        # Create the issue
        issue = jira_service.create_issue(
            project_key=request.project_key,
            summary=request.summary,
            description=request.description,
            issue_type=request.issue_type,
            priority=request.priority,
            labels=request.labels,
            assignee=request.assignee,
        )
        
        logger.info(f"Created Jira issue {issue['key']} for user {current_user.email}")
        
        return JiraIssueResponse(**issue)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating Jira issue: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Jira issue: {str(e)}"
        )


@router.get("/issues/{issue_key}", response_model=JiraIssueDetailResponse)
def get_jira_issue(
    issue_key: str,
    current_user = Depends(get_current_user),
) -> JiraIssueDetailResponse:
    """
    Get details of a specific Jira issue.
    
    Args:
        issue_key: Jira issue key (e.g., "BEFS-123")
    """
    try:
        if not jira_service.is_configured():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Jira integration is not configured."
            )
        
        issue = jira_service.get_issue(issue_key)
        return JiraIssueDetailResponse(**issue)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Jira issue {issue_key}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch Jira issue: {str(e)}"
        )
