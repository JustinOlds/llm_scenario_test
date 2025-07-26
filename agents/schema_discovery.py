"""
Schema Discovery Agent - Stage 1 of Multi-Prompt Pipeline

This agent performs intelligent schema discovery and metadata enrichment
for the available data sources, providing business context and data quality
assessment for downstream analysis.

Key Responsibilities:
- Discover and catalog all available data fields
- Enrich fields with business context and metadata
- Assess data quality and completeness
- Identify relationships between data elements
- Generate machine-readable schema output for next stage
"""

import os
import yaml
import pandas as pd
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class FieldMetadata:
    """Metadata container for a single data field"""
    name: str
    data_type: str
    business_purpose: str
    importance_tier: int  # 1=Critical, 2=Important, 3=Supplementary
    completeness: float  # 0.0 to 1.0
    unique_values: int
    sample_values: List[str]
    business_rules: List[str]
    relationships: List[str]


@dataclass
class SchemaDiscoveryOutput:
    """Machine-readable output from schema discovery stage"""
    timestamp: str
    data_sources: List[str]
    total_fields: int
    field_metadata: Dict[str, FieldMetadata]
    data_quality_score: float
    business_context_available: bool
    recommended_next_stage: str
    confidence_score: float


class SchemaDiscoveryAgent:
    """
    Stage 1 Agent: Schema Discovery and Metadata Enrichment
    
    This agent analyzes available data sources and generates comprehensive
    metadata including business context, data quality metrics, and field
    relationships to guide subsequent analysis stages.
    """
    
    def __init__(self, config_path: str = None):
        """Initialize the schema discovery agent"""
        self.config = self._load_config(config_path)
        self.field_catalog = {}
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load agent configuration"""
        # TODO: Implement configuration loading
        # Placeholder for configuration loading logic
        return {
            "max_tokens": 2000,
            "temperature": 0.1,
            "include_business_rules": True,
            "include_data_quality": True,
            "include_relationships": True
        }
    
    def discover_schema(self, data_paths: List[str]) -> SchemaDiscoveryOutput:
        """
        Main entry point for dynamic schema discovery with config enrichment
        
        Args:
            data_paths: List of paths to data files to analyze
            
        Returns:
            SchemaDiscoveryOutput: Machine-readable schema metadata
        """
        logger.info(f"Starting dynamic schema discovery for {len(data_paths)} data sources")
        
        # Step 1: Discover fresh schema from actual files
        discovered_fields = self._discover_fresh_schema(data_paths)
        
        # Step 2: Load existing config knowledge
        config_knowledge = self._load_config_knowledge()
        
        # Step 3: Merge discovered schema with config enrichment
        enriched_metadata = self._merge_discovery_with_config(discovered_fields, config_knowledge)
        
        # Step 4: Assess data quality across all sources
        quality_score = self._assess_data_quality(enriched_metadata, data_paths)
        
        # Step 5: Identify learning opportunities for config updates
        learning_insights = self._identify_config_learning_opportunities(discovered_fields, config_knowledge)
        
        # Step 6: Generate machine-readable output
        output = SchemaDiscoveryOutput(
            timestamp=datetime.now().isoformat(),
            data_sources=data_paths,
            total_fields=len(enriched_metadata),
            field_metadata=enriched_metadata,
            data_quality_score=quality_score,
            business_context_available=len(config_knowledge) > 0,
            recommended_next_stage="question_analysis",
            confidence_score=self._calculate_discovery_confidence(discovered_fields, config_knowledge)
        )
        
        # Step 7: Save learning insights for config updates
        self._save_learning_insights(learning_insights)
        
        logger.info(f"Dynamic schema discovery complete. Found {len(enriched_metadata)} fields")
        logger.info(f"Config enrichment available for {len([f for f in enriched_metadata.values() if f.business_purpose])} fields")
        
        return output
    
    def _discover_fresh_schema(self, data_paths: List[str]) -> Dict[str, FieldMetadata]:
        """Discover schema from fresh data files"""
        discovered_fields = {}
        
        for file_path in data_paths:
            try:
                df = pd.read_csv(file_path)
                logger.info(f"Analyzing {file_path}: {df.shape}")
                
                for column in df.columns:
                    if column not in discovered_fields:
                        # Calculate field statistics
                        completeness = 1 - (df[column].isnull().sum() / len(df))
                        unique_values = df[column].nunique()
                        sample_values = df[column].dropna().astype(str).head(5).tolist()
                        
                        # Determine data type
                        if pd.api.types.is_numeric_dtype(df[column]):
                            data_type = "numeric"
                        elif pd.api.types.is_datetime64_any_dtype(df[column]):
                            data_type = "datetime"
                        else:
                            data_type = "categorical" if unique_values < len(df) * 0.5 else "text"
                        
                        discovered_fields[column] = FieldMetadata(
                            name=column,
                            data_type=data_type,
                            business_purpose="",  # To be enriched from config
                            importance_tier=3,  # Default to supplementary
                            completeness=completeness,
                            unique_values=unique_values,
                            sample_values=sample_values,
                            business_rules=[],
                            relationships=[]
                        )
                        
            except Exception as e:
                logger.warning(f"Could not analyze {file_path}: {e}")
        
        return discovered_fields
    
    def _load_config_knowledge(self) -> Dict[str, Any]:
        """Load existing configuration knowledge"""
        import os
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "field_metadata.yaml")
        
        if os.path.exists(config_path):
            try:
                import yaml
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                field_defs = config.get('field_definitions', {})
                logger.info(f"Loaded config knowledge with {len(field_defs)} field definitions")
                return config
            except Exception as e:
                logger.warning(f"Could not load config: {e}")
        else:
            logger.info(f"No config file found at {config_path}")
        
        return {}
    
    def _merge_discovery_with_config(self, discovered_fields: Dict[str, FieldMetadata], 
                                   config_knowledge: Dict[str, Any]) -> Dict[str, FieldMetadata]:
        """Merge discovered schema with existing config knowledge"""
        enriched_fields = discovered_fields.copy()
        
        config_fields = config_knowledge.get('field_definitions', {})
        
        for field_name, field_metadata in enriched_fields.items():
            # Check if we have config knowledge for this field
            if field_name in config_fields:
                config_field = config_fields[field_name]
                
                # Enrich with config knowledge
                field_metadata.business_purpose = config_field.get('purpose', field_metadata.business_purpose)
                field_metadata.importance_tier = config_field.get('tier', field_metadata.importance_tier)
                field_metadata.business_rules = config_field.get('business_rules', field_metadata.business_rules)
                field_metadata.relationships = config_field.get('relationships', field_metadata.relationships)
                
                logger.debug(f"Enriched {field_name} with config knowledge")
            else:
                # New field not in config - opportunity for learning
                logger.info(f"New field discovered: {field_name} (not in config)")
        
        return enriched_fields
    
    def _assess_data_quality(self, field_metadata: Dict[str, FieldMetadata], data_paths: List[str]) -> float:
        """Assess overall data quality score"""
        if not field_metadata:
            return 0.0
        
        # Calculate quality based on completeness and field coverage
        completeness_scores = [field.completeness for field in field_metadata.values()]
        avg_completeness = sum(completeness_scores) / len(completeness_scores)
        
        # Bonus for having business context
        context_coverage = len([f for f in field_metadata.values() if f.business_purpose]) / len(field_metadata)
        
        # Combined quality score
        quality_score = (avg_completeness * 0.7) + (context_coverage * 0.3)
        
        return min(quality_score, 1.0)
    
    def _identify_config_learning_opportunities(self, discovered_fields: Dict[str, FieldMetadata], 
                                              config_knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Identify opportunities to update config based on new discoveries"""
        config_fields = config_knowledge.get('fields', {})
        
        learning_insights = {
            "new_fields": [],
            "updated_statistics": [],
            "potential_relationships": [],
            "data_quality_insights": []
        }
        
        for field_name, field_metadata in discovered_fields.items():
            if field_name not in config_fields:
                learning_insights["new_fields"].append({
                    "field_name": field_name,
                    "data_type": field_metadata.data_type,
                    "completeness": field_metadata.completeness,
                    "unique_values": field_metadata.unique_values,
                    "sample_values": field_metadata.sample_values
                })
            else:
                # Check for updated statistics
                config_field = config_fields[field_name]
                if abs(field_metadata.completeness - config_field.get('completeness', 1.0)) > 0.1:
                    learning_insights["updated_statistics"].append({
                        "field_name": field_name,
                        "old_completeness": config_field.get('completeness', 1.0),
                        "new_completeness": field_metadata.completeness
                    })
        
        return learning_insights
    
    def _calculate_discovery_confidence(self, discovered_fields: Dict[str, FieldMetadata], 
                                      config_knowledge: Dict[str, Any]) -> float:
        """Calculate confidence in schema discovery"""
        if not discovered_fields:
            return 0.0
        
        # Base confidence from data quality
        avg_completeness = sum(f.completeness for f in discovered_fields.values()) / len(discovered_fields)
        
        # Bonus for config enrichment coverage
        config_fields = config_knowledge.get('fields', {})
        enriched_count = len([f for f in discovered_fields.keys() if f in config_fields])
        enrichment_ratio = enriched_count / len(discovered_fields) if discovered_fields else 0
        
        # Combined confidence
        confidence = (avg_completeness * 0.6) + (enrichment_ratio * 0.4)
        
        return min(confidence, 0.95)  # Cap at 95%
    
    def _save_learning_insights(self, learning_insights: Dict[str, Any]):
        """Save learning insights for future config updates"""
        if not any(learning_insights.values()):
            return
        
        import os
        import json
        from datetime import datetime
        
        # Save to learning directory
        project_root = os.path.dirname(os.path.dirname(__file__))
        learning_dir = os.path.join(project_root, "config", "learning")
        os.makedirs(learning_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        learning_file = os.path.join(learning_dir, f"schema_learning_{timestamp}.json")
        
        with open(learning_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "insights": learning_insights
            }, f, indent=2)
        
        logger.info(f"Learning insights saved to {learning_file}")
    
    def save_output(self, output: SchemaDiscoveryOutput, output_path: str):
        """Save schema discovery output for next stage"""
        # TODO: Implement output saving
        logger.info(f"Saving schema discovery output to {output_path}")


# Entry point for standalone execution
if __name__ == "__main__":
    # TODO: Implement CLI interface for standalone testing
    agent = SchemaDiscoveryAgent()
    # Example usage would go here
    pass
