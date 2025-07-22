"""
Schema discovery module for the LLM Prototype.

This module contains functions for discovering and enriching schema
information from available data, supporting Step 0 of the LLM pipeline.

UPDATED: Now uses an exclude-list approach to allow for dynamic schema discovery
while still providing guidance for established columns.
"""

import os
import yaml
import logging
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Set

# Import utilities from our modular structure
from .utils.field_metadata import (
    get_business_purpose,
    get_importance_tier,
    get_business_description,
    get_truncation_priority,
    get_filter_capability
)
from .utils.question_types import identify_supported_question_types

logger = logging.getLogger(__name__)


class SchemaDiscovery:
    """
    Schema discovery class for detecting and enriching field metadata
    from available data sources.
    
    Updated to use an exclude-list approach where all columns are discovered
    except those explicitly excluded, while still providing guidance for
    established columns.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the schema discovery with configuration
        
        Args:
            config_path: Path to field configuration YAML file
        """
        self.field_config = self._load_field_config(config_path)
        
    def _load_field_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load field configuration from YAML files. Ignores deprecated 'fields' list for schema discovery—fields are always discovered from the DataFrame.
        Config is used only for enrichment (exclude_columns, field_descriptions, etc.), not as a whitelist.
        
        Args:
            config_path: Path to field configuration YAML file
            
        Returns:
            Dictionary containing field configuration
        """
        config = {}
        
        # Use provided config path or default locations
        config_paths = [
            config_path,
            'llm_columns_canonical.yaml', # Our canonical config with exclude-list approach
            '../llm_columns_canonical.yaml',
            'llm_prototype/llm_columns_canonical.yaml',
            'llm_columns_final.yaml',    # Final exclude-list structure with enhanced guidance
            'llm_columns_revised.yaml',  # Earlier revision of exclude-list structure
            'llm_columns.yaml',          # Legacy structure
            'llm_columns_fixed.yaml',    # Temporary fixed structure
            '../llm_columns_final.yaml',
            '../llm_columns.yaml'
        ]
        
        # Try each path until we find a valid config
        config_loaded = False
        for path in [p for p in config_paths if p]:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        yaml_config = yaml.safe_load(f)
                        logger.info(f"Loaded YAML config from {path}")
                        
                        # Ignore legacy 'fields' list for schema discovery; always use DataFrame columns
                        if 'fields' in yaml_config:
                            logger.warning("'fields' list found in config but is deprecated and ignored. Schema discovery is always data-driven.")
                            config['explicit_fields'] = yaml_config.get('fields', [])  # Retained for legacy compatibility, not used
                            config['is_legacy_format'] = False
                        else:
                            # Handle new exclude-list format
                            logger.info("Using exclude-list format for dynamic schema discovery")
                            config['exclude_columns'] = yaml_config.get('exclude_columns', [])
                            
                            # Map field groups to help with classification and context building
                            field_groups = {}
                            for group_name, group_dict in yaml_config.get('field_groups', {}).items():
                                field_groups[group_name] = group_dict
                            config['field_groups'] = field_groups
                            
                            # Store field descriptions for enrichment
                            config['field_descriptions'] = yaml_config.get('field_descriptions', {})
                            config['field_type_mappings'] = yaml_config.get('field_type_mappings', {})
                            config['is_legacy_format'] = False
                        
                        # Question types guidance is consistent across formats
                        config['question_types'] = yaml_config.get('question_types', {})
                        config['novel_fallback'] = yaml_config.get('novel_question_fallback', {})
                        
                        logger.info(f"Config loaded with {len(config.get('exclude_columns', []))} excluded columns")
                        config_loaded = True
                        break
                except Exception as e:
                    logger.warning(f"Failed to load config from {path}: {e}")
                    continue
        
        # Default exclude columns if no config was found
        if not config_loaded:
            logger.warning("Using default exclude-list configuration")
            config['exclude_columns'] = [
                'ROW_ID', 'REPORT_DATE', 'DATA_DATE', 'SOURCE_SYSTEM', 'IS_TEST_DATA',
                'CREATED_BY', 'CREATED_AT', 'UPDATED_BY', 'UPDATED_AT', 'DELETED_AT',
                'IS_DELETED', 'VERSION'
            ]
            config['field_descriptions'] = {}
            config['question_types'] = {}
            config['novel_fallback'] = {}
            config['is_legacy_format'] = True
        
        return config
    
    def _map_pandas_dtype_to_json_type(self, dtype: str) -> str:
        """Map pandas dtype to simplified JSON-compatible type"""
        dtype = str(dtype).lower()
        
        if 'int' in dtype or 'float' in dtype:
            return 'number'
        elif 'bool' in dtype:
            return 'boolean'
        elif 'datetime' in dtype or 'timestamp' in dtype:
            return 'datetime'
        else:
            return 'string'  # Default to string for object and other types
    
    def _get_field_type_fallback(self, field_name: str) -> str:
        """Get field type when no data is available"""
        field_name = field_name.upper()
        
        if any(x in field_name for x in ['SALES', 'PRICE', 'SCORE', 'PCT', 'RANK', 'COUNT', 'QTY']):
            return 'number'
        elif field_name.startswith('IS_'):
            return 'boolean'
        elif 'DATE' in field_name or 'WEEK' in field_name or 'TIME' in field_name:
            return 'datetime'
        else:
            return 'string'
    
    def _get_field_interpretation(self, field_name: str) -> str:
        """Get interpretation guidance for numeric fields"""
        field_name = field_name.upper()
        
        if 'SALES' in field_name:
            return "Dollar value. Higher values indicate better sales performance."
        elif 'WOW' in field_name or 'PCT' in field_name:
            return "Percentage change. Positive values indicate growth, negative values indicate decline."
        elif 'PRIORITY' in field_name:
            return "Priority score from 0-100. Higher values indicate more urgent attention needed."
        elif 'SCORE' in field_name:
            return "Confidence score from 0-100. Higher values indicate more confidence."
        elif 'RANK' in field_name:
            return "Ranking position. Lower values (closer to 1) indicate higher importance."
        else:
            return "Numeric value. Higher values generally indicate stronger performance."
    
    def _get_field_description(self, field_name: str) -> str:
        """
        Get description for a field, falling back to sensible defaults
        
        Args:
            field_name: Field name to get description for
            
        Returns:
            Description string
        """
        field_name = field_name.upper()
        
        # Check for YAML enrichment first
        field_descs = self.field_config.get('field_descriptions', {})
        if field_name in field_descs:
            desc = field_descs[field_name].get('description', '')
            if desc:
                return desc
        
        # Fall back to pattern-based defaults
        if 'SALES' in field_name:
            return "Sales metric in dollars"
        elif 'WOW' in field_name:
            return "Week over week comparison"
        elif 'PCT' in field_name:
            return "Percentage metric"
        elif 'RANK' in field_name:
            return "Ranking position"
        elif 'TOP' in field_name:
            return "Top-performing item or category"
        elif field_name.startswith('IS_'):
            return f"Flag indicating if the location {field_name[3:].lower().replace('_', ' ')}"
        else:
            return f"Metric related to {field_name.lower().replace('_', ' ')}"
    
    def _get_predefined_field_ranges(self, mode: str) -> Dict[str, Dict[str, Any]]:
        """Get predefined field ranges from config"""
        ranges_key = f"{mode}_field_ranges"
        return self.field_config.get(ranges_key, {})
    
    def _get_question_type_field_guidance(self, mode: str) -> Dict[str, Any]:
        """Get question type field guidance from config"""
        return self.field_config.get('question_types', {})
    
    def _get_novel_question_strategy(self, mode: str) -> Dict[str, Any]:
        """Get novel question strategy from config"""
        return self.field_config.get('novel_fallback', {})
    
    def _get_all_available_fields(self, df: pd.DataFrame) -> List[str]:
        """
        Get all available fields from dataframe, excluding those in exclude_columns from config.
        Args:
            df: DataFrame to get columns from
        Returns:
            List of field names to include in schema discovery
        Raises:
            ValueError if DataFrame is None or empty
        """
        if df is None or df.empty:
            logger.error("DataFrame is None or empty during schema discovery. Cannot discover fields.")
            raise ValueError("DataFrame is None or empty during schema discovery")
            
        # Get all columns from DataFrame
        all_df_columns = set(df.columns)
        
        # Get exclude columns from config
        exclude_columns_from_config = set(self.field_config.get('exclude_columns', []))
        
        # Log what we're doing for transparency
        logger.info(f"DataFrame has {len(all_df_columns)} columns")
        logger.info(f"Exclude list has {len(exclude_columns_from_config)} columns")
        
        # Remove excluded columns
        excluded_columns = set()
        for exclude_pattern in exclude_columns_from_config:
            # Handle exact match
            if exclude_pattern in all_df_columns:
                excluded_columns.add(exclude_pattern)
                continue
                
            # Handle pattern with wildcards
            if '*' in exclude_pattern:
                import fnmatch
                for col in all_df_columns:
                    if fnmatch.fnmatch(col, exclude_pattern):
                        excluded_columns.add(col)
        
        # Get final set of available columns (all minus excluded)
        available_fields = sorted(list(all_df_columns - excluded_columns))
        
        # Log for debugging
        logger.info(f"After excluding {len(excluded_columns)} columns, {len(available_fields)} columns remain")
        logger.debug(f"Available fields: {', '.join(available_fields[:20])}{'...' if len(available_fields) > 20 else ''}")
        
        return available_fields
                
    def build_schema_context(self, df: Optional[pd.DataFrame] = None, mode: str = 'small') -> Dict[str, Any]:
        """
        Build schema context with continuous variable ranges and interpretation guides
        
        Args:
            df: Optional DataFrame to use for schema discovery
            mode: 'small' or 'big' field configuration
            
        Returns:
            Schema context with field ranges and interpretation
        """
        logger.info(f"Building schema context in {mode} mode")
        field_metadata = []
        raw_field_count = 0
        excluded_field_count = 0
        
        if df is not None and not df.empty:
            # Use the DataFrame columns as the source of truth, excluding any in exclude_columns
            # This is the data-driven approach with an exclude-list
            raw_field_count = len(df.columns)
            available_fields = self._get_all_available_fields(df)
            excluded_field_count = raw_field_count - len(available_fields)
            
            # Build field metadata with range information
            for field in available_fields:
                series = df[field].dropna()
                
                if series.empty:
                    continue
                
                dtype = str(series.dtype)
                field_type = self._map_pandas_dtype_to_json_type(dtype)
                
                # Calculate range statistics for continuous variables
                field_info = {
                    'field': field,
                    'type': field_type,
                    'available': True
                }
                
                # Add range information for numeric fields
                if field_type == 'number':
                    try:
                        field_info.update({
                            'min': float(series.min()),
                            'max': float(series.max()),
                            'mean': float(series.mean()),
                            'std': float(series.std()),
                            'p25': float(series.quantile(0.25)),
                            'p50': float(series.quantile(0.50)),
                            'p75': float(series.quantile(0.75)),
                            'range_interpretation': self._get_field_interpretation(field)
                        })
                    except Exception as e:
                        logger.warning(f"Error calculating statistics for {field}: {e}")
                        field_info.update({
                            'min': None, 'max': None, 'mean': None, 'std': None,
                            'p25': None, 'p50': None, 'p75': None,
                            'error': str(e)
                        })
                else:
                    try:
                        value_counts = series.value_counts()
                        field_info.update({
                            'unique_values': len(value_counts),
                            'top_values': value_counts.head(3).to_dict(),
                            'sample_values': series.head(3).tolist()
                        })
                    except Exception as e:
                        logger.warning(f"Error getting value counts for {field}: {e}")

                # Enrich using field_descriptions if available
                field_descs = self.field_config.get('field_descriptions', {})
                desc = field_descs.get(field, {})
                if desc:
                    # Use YAML enrichment values if present
                    field_info.update({
                        'description': desc.get('description', ''),
                        'importance': desc.get('importance', ''),
                        'business_purpose': desc.get('business_purpose', ''),
                        'type': desc.get('type', field_type),
                        'sample_values': desc.get('sample_values', field_info.get('sample_values', [])),
                        'range': desc.get('range', None),
                        'semantic_tags': desc.get('semantic_tags', []),
                    })
                else:
                    # Fallback to code-based enrichment
                    business_purpose = get_business_purpose(field)
                    importance = get_importance_tier(field, business_purpose)
                    description = self._get_field_description(field)
                    field_info.update({
                        'business_purpose': business_purpose,
                        'importance_tier': importance,
                        'description': description,
                        'filter_capability': get_filter_capability(dtype),
                        'truncation_priority': get_truncation_priority(field, importance)
                    })
                field_metadata.append(field_info)

        else:
            # Fail loudly if DataFrame is None or empty
            logger.error("[SCHEMA DISCOVERY] DataFrame is None or empty during schema discovery. Cannot proceed.")
            raise ValueError("DataFrame is None or empty during schema discovery. Cannot proceed.")

        # Identify supported question types
        supported_question_types = []
        if df is not None:
            supported_question_types = identify_supported_question_types(df.columns)
        
        # Add question type guidance for context
        question_type_guidance = self._get_question_type_field_guidance(mode)
        
        # Determine which approach we used for discovery
        discovery_approach = 'dynamic_exclude_list' 
        if self.field_config.get('is_legacy_format', True):
            discovery_approach = 'legacy_fields_list'
        
        schema_context = {
            'mode': mode,
            'available_fields': field_metadata,
            'field_count': len(field_metadata),
            'raw_field_count': raw_field_count,
            'excluded_field_count': excluded_field_count,
            'supported_question_types': supported_question_types,
            'question_type_guidance': question_type_guidance,
            'novel_question_strategy': self._get_novel_question_strategy(mode),
            'data_source': 'real_location_data' if df is not None else 'config_defaults',
            'discovery_approach': discovery_approach,
            'timestamp': pd.Timestamp.now().isoformat()
        }
        
        return schema_context
