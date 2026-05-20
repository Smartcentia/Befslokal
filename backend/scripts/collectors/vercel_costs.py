"""
Vercel Cost Collector

Collects usage metrics from Vercel using vercel CLI.
"""
import subprocess
import json
from typing import Dict, Any, Optional
from datetime import datetime


class VercelCostCollector:
    """Collects and calculates Vercel hosting costs."""
    
    # Vercel pricing - Hobby tier (assuming hobby plan)
    # Most features are free on hobby tier with limits
    HOBBY_TIER_COST = 0.0  # Free tier
    PRO_TIER_COST = 20.0  # USD per month
    
    # Additional usage costs (Pro tier)
    BANDWIDTH_COST_PER_GB = 0.15  # USD per GB after 100GB
    FREE_BANDWIDTH_GB = 100
    
    def __init__(self, project_name: Optional[str] = None):
        self.cli_command = "vercel"
        self.project_name = project_name
    
    def check_cli_available(self) -> bool:
        """Check if vercel CLI is available."""
        try:
            result = subprocess.run(
                [self.cli_command, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def get_project_info(self) -> Optional[Dict[str, Any]]:
        """Get project information from Vercel."""
        try:
            # List projects (without --json as it's not supported)
            result = subprocess.run(
                [self.cli_command, "ls"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                print(f"Error getting Vercel projects: {result.stderr}")
                return None
            
            # Parse output
            output = result.stdout.strip()
            
            # Try to find project info in output
            return {
                "raw_output": output,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except subprocess.TimeoutExpired:
            print("Timeout while running vercel CLI")
            return None
        except Exception as e:
            print(f"Unexpected error getting Vercel info: {e}")
            return None
    
    def get_deployments(self) -> Optional[int]:
        """Get number of recent deployments."""
        try:
            result = subprocess.run(
                [self.cli_command, "ls"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return None
            
            # Count deployments in output
            lines = result.stdout.strip().split('\n')
            # Filter out header and empty lines
            deployment_lines = [l for l in lines if l.strip() and not l.startswith('Project')]
            
            return len(deployment_lines)
            
        except Exception:
            return None
    
    def calculate_costs(self, project_info: Dict[str, Any], num_deployments: Optional[int]) -> Dict[str, Any]:
        """
        Calculate estimated costs from project data.
        
        Since Vercel hobby tier is free and we don't have access to detailed
        usage metrics via CLI, we'll assume hobby tier with $0 cost.
        
        Args:
            project_info: Project information
            num_deployments: Number of deployments
            
        Returns:
            Dictionary with cost calculations
        """
        # For hobby tier, cost is $0
        # For production apps, you'd typically use Pro tier ($20/month)
        # We'll default to hobby tier unless specified
        
        estimated_cost = self.HOBBY_TIER_COST
        tier = "hobby"
        
        # Note: We don't have bandwidth data from CLI
        # In production, you'd query Vercel API for detailed metrics
        
        return {
            "service_name": "vercel",
            "collection_date": datetime.utcnow().isoformat(),
            "raw_metrics": project_info,
            "estimated_cost_usd": round(estimated_cost, 2),
            "active_time_seconds": None,
            "cpu_used_seconds": None,
            "storage_gb": None,
            "bandwidth_gb": None,  # Not available from CLI
            "notes": f"Tier: {tier}, Deployments: {num_deployments or 'unknown'}",
            "metadata": {
                "tier": tier,
                "num_deployments": num_deployments,
                "project_name": self.project_name,
                "note": "CLI provides limited metrics. Consider using Vercel API for detailed usage data."
            }
        }
    
    def collect(self) -> Optional[Dict[str, Any]]:
        """
        Main collection method.
        
        Returns:
            Cost data dictionary or None if failed
        """
        if not self.check_cli_available():
            print("Error: vercel CLI not available")
            return None
        
        print("Collecting Vercel metrics...")
        
        project_info = self.get_project_info()
        if not project_info:
            print("Failed to get Vercel project info")
            # Continue anyway with limited data
            project_info = {}
        
        num_deployments = self.get_deployments()
        
        cost_data = self.calculate_costs(project_info, num_deployments)
        print(f"Vercel cost collected: ${cost_data['estimated_cost_usd']:.2f}")
        
        return cost_data


if __name__ == "__main__":
    # Test the collector
    collector = VercelCostCollector()
    result = collector.collect()
    
    if result:
        print("\n=== Vercel Cost Data ===")
        print(json.dumps(result, indent=2, default=str))
    else:
        print("Failed to collect Vercel cost data")
