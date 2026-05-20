"""
Unit tests for Financial Agent
"""

import pytest
from app.ai_lab.agents.financial_agent import FinancialAgent, QueryIntent


class TestFinancialAgent:
    """Test suite for FinancialAgent parsing and code generation"""
    
    def test_parse_outlier_detection_query_norwegian(self):
        """Test parsing Norwegian outlier detection query"""
        query = "Finn eiendommer med unormalt høye driftskostnader"
        result = FinancialAgent.parse_financial_query(query)
        
        assert result["intent"] == QueryIntent.OUTLIER_DETECTION
        assert "running_costs" in result["metrics"]
        assert result["confidence"] > 0.5
    
    def test_parse_comparison_query_english(self):
        """Test parsing English comparison query"""
        query = "Compare 8 properties to find outliers in maintenance costs"
        result = FinancialAgent.parse_financial_query(query)
        
        assert result["intent"] in [QueryIntent.COMPARISON, QueryIntent.OUTLIER_DETECTION]
        assert "maintenance" in result["metrics"]
        assert result["properties_mentioned"] == 8
    
    def test_parse_correlation_query(self):
        """Test parsing correlation query"""
        query = "Analyser korrelasjoner mellom leie og vedlikeholdskostnader"
        result = FinancialAgent.parse_financial_query(query)
        
        assert result["intent"] == QueryIntent.CORRELATION
        assert "rent" in result["metrics"]
        assert "maintenance" in result["metrics"]
    
    def test_extract_property_count(self):
        """Test extracting number of properties from query"""
        queries = [
            ("Sammenlign 8 eiendommer", 8),
            ("Compare 5 properties", 5),
            ("10 bygninger analyse", 10),
        ]
        
        for query, expected_count in queries:
            result = FinancialAgent.parse_financial_query(query)
            assert result["properties_mentioned"] == expected_count
    
    def test_default_metrics(self):
        """Test that default metrics are applied when none mentioned"""
        query = "Analyser eiendommene"
        result = FinancialAgent.parse_financial_query(query)
        
        assert "total_costs" in result["metrics"]
    
    def test_generate_outlier_prompt(self):
        """Test outlier detection prompt generation"""
        prompt = FinancialAgent.generate_comparison_prompt(
            properties=["prop1", "prop2", "prop3"],
            metrics=["rent", "running_costs"],
            intent=QueryIntent.OUTLIER_DETECTION
        )
        
        assert "outlier" in prompt.lower()
        assert "iqr" in prompt.lower()
        assert "z-score" in prompt.lower()
        assert "rent" in prompt
        assert "running_costs" in prompt
    
    def test_generate_correlation_prompt(self):
        """Test correlation prompt generation"""
        prompt = FinancialAgent.generate_comparison_prompt(
            properties=["prop1", "prop2"],
            metrics=["rent", "maintenance"],
            intent=QueryIntent.CORRELATION
        )
        
        assert "correlation" in prompt.lower()
        assert "pearson" in prompt.lower()
    
    def test_generate_comparison_prompt(self):
        """Test general comparison prompt generation"""
        prompt = FinancialAgent.generate_comparison_prompt(
            properties=["prop1", "prop2", "prop3", "prop4"],
            metrics=["total_costs"],
            intent=QueryIntent.COMPARISON
        )
        
        assert "compare" in prompt.lower()
        assert "properties" in prompt.lower()
        assert "4 properties" in prompt
    
    def test_confidence_calculation(self):
        """Test confidence score calculation"""
        # High confidence query
        high_conf = FinancialAgent.parse_financial_query(
            "Sammenlign leiekostnader for 8 eiendommer"
        )
        
        # Low confidence query
        low_conf = FinancialAgent.parse_financial_query(
            "Vis noe data"
        )
        
        assert high_conf["confidence"] > low_conf["confidence"]
        assert high_conf["confidence"] > 0.7
        assert low_conf["confidence"] < 0.7


class TestQueryIntentDetection:
    """Test intent detection accuracy"""
    
    @pytest.mark.parametrize("query,expected_intent", [
        ("Finn outliers i kostnader", QueryIntent.OUTLIER_DETECTION),
        ("Sammenlign eiendommer", QueryIntent.COMPARISON),
        ("Vis korrelasjoner mellom leie og drift", QueryIntent.CORRELATION),
        ("Budsjett vs faktisk", QueryIntent.VARIANCE),
        ("Lag prognose for neste år", QueryIntent.FORECAST),
    ])
    def test_intent_detection(self, query, expected_intent):
        """Test that various queries are correctly classified"""
        result = FinancialAgent.parse_financial_query(query)
        assert result["intent"] == expected_intent


class TestMetricExtraction:
    """Test metric keyword extraction"""
    
    @pytest.mark.parametrize("query,expected_metrics", [
        ("Analyser leiekostnader", ["rent"]),
        ("Driftskostnader og vedlikehold", ["running_costs", "maintenance"]),
        ("Totale kostnader for strøm og vann", ["total_costs", "utilities"]),
        ("Bokført faktisk spend", ["gl_transactions"]),
    ])
    def test_metric_extraction(self, query, expected_metrics):
        """Test that metrics are correctly extracted from queries"""
        result = FinancialAgent.parse_financial_query(query)
        for metric in expected_metrics:
            assert metric in result["metrics"]
