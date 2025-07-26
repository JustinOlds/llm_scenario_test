"""
Output Generation Agent - Stage 4 of Multi-Prompt Pipeline

This agent generates the final human-readable output based on the filtered
data and analysis specifications from previous stages.

Key Responsibilities:
- Generate actionable insights from filtered data
- Create structured recommendations with business context
- Format output for human consumption
- Include confidence indicators and data quality notes
- Provide clear action items and next steps
"""

import logging
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class OutputGenerationResult:
    """Final output from the multi-prompt pipeline"""
    timestamp: str
    question: str
    analysis_type: str
    key_insights: List[str]
    recommendations: List[Dict[str, Any]]
    data_summary: Dict[str, Any]
    confidence_score: float
    limitations: List[str]
    next_steps: List[str]
    formatted_output: str


class OutputGeneratorAgent:
    """
    Stage 4 Agent: Human-Readable Output Generation
    
    This agent creates the final human-readable analysis output with
    actionable insights, recommendations, and business context.
    """
    
    def __init__(self, config_path: str = None):
        """Initialize the output generator agent"""
        self.config = self._load_config(config_path)
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load agent configuration"""
        # TODO: Implement configuration loading
        return {
            "max_tokens": 4000,
            "temperature": 0.2,
            "max_recommendations": 10,
            "include_action_items": True,
            "include_confidence": True,
            "output_format": "structured_text"
        }
    
    def generate_output(self, filtered_data: pd.DataFrame, question_analysis: Dict[str, Any],
                       schema_metadata: Dict[str, Any], filter_metadata: Dict[str, Any]) -> OutputGenerationResult:
        """
        Main entry point for output generation
        
        Args:
            filtered_data: Filtered dataset from previous stage
            question_analysis: Question analysis results
            schema_metadata: Schema discovery results
            filter_metadata: Data filtering metadata
            
        Returns:
            OutputGenerationResult: Final human-readable output
        """
        logger.info("Starting output generation")
        
        original_question = question_analysis.get("original_question", "")
        analysis_type = question_analysis.get("question_type", "")
        
        # Step 1: Generate key insights from data
        insights = self._generate_key_insights(filtered_data, question_analysis)
        
        # Step 2: Create actionable recommendations
        recommendations = self._generate_recommendations(filtered_data, question_analysis, insights)
        
        # Step 3: Summarize data characteristics
        data_summary = self._create_data_summary(filtered_data, filter_metadata)
        
        # Step 4: Calculate overall confidence
        confidence = self._calculate_output_confidence(insights, recommendations, filter_metadata)
        
        # Step 5: Identify limitations and caveats
        limitations = self._identify_limitations(filter_metadata, schema_metadata)
        
        # Step 6: Generate next steps
        next_steps = self._generate_next_steps(recommendations, question_analysis)
        
        # Step 7: Format final output
        formatted_output = self._format_final_output(
            original_question, insights, recommendations, data_summary, 
            confidence, limitations, next_steps
        )
        
        result = OutputGenerationResult(
            timestamp=datetime.now().isoformat(),
            question=original_question,
            analysis_type=analysis_type,
            key_insights=insights,
            recommendations=recommendations,
            data_summary=data_summary,
            confidence_score=confidence,
            limitations=limitations,
            next_steps=next_steps,
            formatted_output=formatted_output
        )
        
        logger.info("Output generation complete")
        return result
    
    def _generate_key_insights(self, data: pd.DataFrame, question_analysis: Dict[str, Any]) -> List[str]:
        """Generate key insights from the filtered data"""
        # TODO: Implement intelligent insight generation
        # This would analyze the data based on question type and generate insights
        
        insights = []
        
        # Placeholder insights based on common patterns
        if len(data) > 0:
            insights.append(f"Analysis based on {len(data)} representative locations")
            
            # Example: Performance insights
            if "priority_score" in data.columns:
                high_priority = data[data["priority_score"] > data["priority_score"].median()]
                insights.append(f"{len(high_priority)} locations require immediate attention")
            
            # Example: Geographic insights
            if "location_name" in data.columns:
                insights.append(f"Analysis covers diverse geographic locations")
        
        return insights
    
    def _generate_recommendations(self, data: pd.DataFrame, question_analysis: Dict[str, Any], 
                                insights: List[str]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        # TODO: Implement intelligent recommendation generation
        
        recommendations = []
        max_recs = self.config["max_recommendations"]
        
        # Placeholder recommendations
        if len(data) > 0:
            recommendations.append({
                "priority": "HIGH",
                "action": "Focus on underperforming locations",
                "details": "Review locations with declining trends",
                "expected_impact": "Improve overall performance",
                "timeline": "Immediate"
            })
            
            recommendations.append({
                "priority": "MEDIUM", 
                "action": "Analyze successful location patterns",
                "details": "Study top-performing locations for best practices",
                "expected_impact": "Identify replicable strategies",
                "timeline": "1-2 weeks"
            })
        
        return recommendations[:max_recs]
    
    def _create_data_summary(self, data: pd.DataFrame, filter_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of data characteristics"""
        return {
            "total_locations": len(data),
            "data_coverage": filter_metadata.get("data_coverage_score", 0.85),
            "selection_method": filter_metadata.get("selection_rationale", {}).get("selection_method", ""),
            "quality_score": filter_metadata.get("efficiency_score", 0.90)
        }
    
    def _calculate_output_confidence(self, insights: List[str], recommendations: List[Dict[str, Any]], 
                                   filter_metadata: Dict[str, Any]) -> float:
        """Calculate overall confidence in the output"""
        # TODO: Implement confidence calculation based on data quality and analysis depth
        base_confidence = 0.85
        
        # Adjust based on data coverage
        coverage_score = filter_metadata.get("data_coverage_score", 0.85)
        adjusted_confidence = base_confidence * coverage_score
        
        return min(adjusted_confidence, 0.95)  # Cap at 95%
    
    def _identify_limitations(self, filter_metadata: Dict[str, Any], 
                            schema_metadata: Dict[str, Any]) -> List[str]:
        """Identify analysis limitations and caveats"""
        limitations = []
        
        # Data limitations
        original_count = filter_metadata.get("original_row_count", 0)
        filtered_count = filter_metadata.get("filtered_row_count", 0)
        
        if original_count > 0:
            reduction_pct = (1 - filtered_count / original_count) * 100
            if reduction_pct > 50:
                limitations.append(f"Analysis based on {reduction_pct:.0f}% data reduction for efficiency")
        
        # Schema limitations
        data_quality = schema_metadata.get("data_quality_score", 1.0)
        if data_quality < 0.9:
            limitations.append("Some data quality issues may affect precision")
        
        return limitations
    
    def _generate_next_steps(self, recommendations: List[Dict[str, Any]], 
                           question_analysis: Dict[str, Any]) -> List[str]:
        """Generate suggested next steps"""
        next_steps = []
        
        if recommendations:
            next_steps.append("Prioritize high-priority recommendations for immediate action")
            next_steps.append("Monitor implementation progress and measure impact")
        
        # Add question-specific next steps
        question_type = question_analysis.get("question_type", "")
        if "performance" in question_type:
            next_steps.append("Schedule follow-up analysis to track performance improvements")
        
        return next_steps
    
    def _format_final_output(self, question: str, insights: List[str], 
                           recommendations: List[Dict[str, Any]], data_summary: Dict[str, Any],
                           confidence: float, limitations: List[str], 
                           next_steps: List[str]) -> str:
        """Format the final human-readable output"""
        
        output = f"""Question: {question}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Data Coverage: {data_summary['total_locations']} locations analyzed
==================================================

KEY INSIGHTS:
"""
        
        for i, insight in enumerate(insights, 1):
            output += f"{i}. {insight}\n"
        
        output += "\nRECOMMENDATIONS:\n"
        
        for i, rec in enumerate(recommendations, 1):
            output += f"\n{i}. [{rec['priority']}] {rec['action']}\n"
            output += f"   Details: {rec['details']}\n"
            output += f"   Expected Impact: {rec['expected_impact']}\n"
            output += f"   Timeline: {rec['timeline']}\n"
        
        if limitations:
            output += "\nLIMITATIONS:\n"
            for limitation in limitations:
                output += f"• {limitation}\n"
        
        output += "\nNEXT STEPS:\n"
        for i, step in enumerate(next_steps, 1):
            output += f"{i}. {step}\n"
        
        output += f"\nConfidence Score: {confidence:.1%}\n"
        
        return output
    
    def save_output(self, result: OutputGenerationResult, output_path: str):
        """Save final output to file"""
        # TODO: Implement output saving
        logger.info(f"Saving final output to {output_path}")


# Entry point for standalone execution
if __name__ == "__main__":
    # TODO: Implement CLI interface for standalone testing
    agent = OutputGeneratorAgent()
    # Example usage would go here
    pass
