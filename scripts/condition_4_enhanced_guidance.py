"""
Condition 4: Enhanced Guidance Test

This script implements Condition 4 of the LLM testing framework:
- Data Type: Curated (same 49 location dataset as Condition 3)
- Guidance: Enhanced (schema discovery + config enrichment)

This bridges the gap between Condition 3 (minimal guidance) and the full 
multi-prompt agent by demonstrating the value of enhanced guidance without
the complexity of org/global benchmarks or data filtering.

Key Features:
- Uses existing 49 curated location rows (same data as Condition 3)
- Applies schema discovery with config enrichment
- Enhanced business context and field guidance
- Direct comparison capability with Condition 3 results
"""

import os
import sys
import json
import yaml
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from agents.schema_discovery import SchemaDiscoveryAgent
import anthropic
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Condition4EnhancedGuidance:
    """
    Condition 4: Enhanced Guidance Test Implementation
    
    Tests enhanced guidance approach using schema discovery and config enrichment
    on the same 49 curated location dataset used in Condition 3.
    """
    
    def __init__(self):
        """Initialize the enhanced guidance test"""
        self.project_root = project_root
        self.config_path = project_root / "config" / "agent_config.yaml"
        self.schema_agent = SchemaDiscoveryAgent(str(self.config_path))
        
        # Initialize API client
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        self.api_client = anthropic.Anthropic(api_key=api_key)
        
        # Data and results paths
        self.curated_data_dir = project_root / "data" / "curated"
        self.results_dir = project_root / "results" / "condition_4"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
        
        # Test metadata
        self.test_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def _load_config(self) -> Dict[str, Any]:
        """Load test configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning("Config file not found, using defaults")
            return {
                "api": {
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 4000,
                    "temperature": 0.1
                }
            }
    
    def discover_curated_data(self) -> List[str]:
        """Discover available curated data files"""
        if not self.curated_data_dir.exists():
            raise FileNotFoundError(f"Curated data directory not found: {self.curated_data_dir}")
        
        csv_files = list(self.curated_data_dir.glob("*.csv"))
        
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in {self.curated_data_dir}")
        
        logger.info(f"Found {len(csv_files)} curated data files")
        return [str(f) for f in csv_files]
    
    def run_schema_discovery_with_enrichment(self, data_files: List[str]) -> Dict[str, Any]:
        """
        Run schema discovery with config enrichment on curated data
        
        Args:
            data_files: List of curated data file paths
            
        Returns:
            Enhanced schema metadata
        """
        logger.info("Running schema discovery with config enrichment")
        
        # Use schema discovery agent to analyze files
        schema_output = self.schema_agent.discover_schema(data_files)
        
        # Convert to dictionary format for easier handling
        schema_dict = {
            "timestamp": schema_output.timestamp,
            "data_sources": schema_output.data_sources,
            "total_fields": schema_output.total_fields,
            "field_metadata": {
                name: {
                    "name": field.name,
                    "data_type": field.data_type,
                    "business_purpose": field.business_purpose,
                    "importance_tier": field.importance_tier,
                    "completeness": field.completeness,
                    "unique_values": field.unique_values,
                    "sample_values": field.sample_values,
                    "business_rules": field.business_rules,
                    "relationships": field.relationships
                }
                for name, field in schema_output.field_metadata.items()
            },
            "data_quality_score": schema_output.data_quality_score,
            "business_context_available": schema_output.business_context_available,
            "confidence_score": schema_output.confidence_score
        }
        
        # Save schema discovery results
        schema_file = self.results_dir / f"schema_discovery_{self.test_timestamp}.json"
        with open(schema_file, 'w') as f:
            json.dump(schema_dict, f, indent=2, default=str)
        
        logger.info(f"Schema discovery complete. Quality score: {schema_output.data_quality_score:.2f}")
        return schema_dict
    
    def load_enhanced_guidance_prompt(self) -> str:
        """Load the enhanced guidance prompt template"""
        prompt_path = project_root / "prompts" / "enhanced_guidance" / "output_generation.md"
        
        if prompt_path.exists():
            with open(prompt_path, 'r') as f:
                return f.read()
        else:
            # Fallback enhanced guidance prompt
            return """
You are a senior data analyst specializing in retail location performance analysis.

Using the provided schema context and business field definitions, analyze the curated location data to answer the user's question with comprehensive business insights and actionable recommendations.

Key Analysis Framework:
1. **Performance Assessment**: Identify locations requiring immediate attention based on priority scores, sales trends, and business metrics
2. **Business Context**: Use field metadata and business purposes to provide meaningful interpretations
3. **Actionable Recommendations**: Provide specific, implementable actions with expected impact and timelines
4. **Data-Driven Insights**: Support all recommendations with evidence from the data

Focus on delivering executive-level insights that enable immediate business decisions.
"""
    
    def run_enhanced_guidance_analysis(self, question: str, data_files: List[str], 
                                     schema_metadata: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        """
        Run enhanced guidance analysis on curated data
        
        Args:
            question: Business question to analyze
            data_files: Curated data file paths
            schema_metadata: Enhanced schema metadata
            
        Returns:
            Analysis results with enhanced guidance
        """
        logger.info("Running enhanced guidance analysis")
        
        # Load the curated data (use first file for now)
        data_df = pd.read_csv(data_files[0])
        logger.info(f"Loaded curated data: {data_df.shape}")
        
        # Load enhanced guidance prompt
        enhanced_prompt = self.load_enhanced_guidance_prompt()
        
        # Intelligent data reduction to fit context limits
        reduced_data, schema_summary = self._reduce_data_for_context(data_df, schema_metadata)
        
        # Build enhanced prompt with optimized context
        full_prompt = f"""
{enhanced_prompt}

BUSINESS QUESTION: {question}

ENHANCED SCHEMA SUMMARY:
{schema_summary}

CURATED LOCATION DATA ({len(reduced_data)} locations):
{reduced_data.to_string()}

Please provide comprehensive business analysis with actionable recommendations using the enhanced guidance framework.
"""
        
        # Estimate token usage
        estimated_tokens = len(full_prompt.split()) * 1.3  # Rough estimate
        
        if dry_run:
            logger.info("DRY RUN MODE - No API call will be made")
            logger.info(f"Estimated input tokens: {estimated_tokens:.0f}")
            logger.info(f"Prompt length: {len(full_prompt)} characters")
            
            # Save dry run prompt for review
            dry_run_file = self.results_dir / f"dry_run_prompt_{self.test_timestamp}.txt"
            with open(dry_run_file, 'w') as f:
                f.write("DRY RUN - PROMPT PREVIEW\n")
                f.write("=" * 50 + "\n\n")
                f.write(full_prompt)
            
            return {
                "dry_run": True,
                "estimated_tokens": estimated_tokens,
                "prompt_length": len(full_prompt),
                "prompt_file": str(dry_run_file),
                "message": "Dry run complete - no API call made"
            }
        
        # Save final prompt for transparency (always, not just dry run)
        final_prompt_file = self.results_dir / f"final_prompt_{self.test_timestamp}.txt"
        with open(final_prompt_file, 'w', encoding='utf-8') as f:
            f.write("FINAL PROMPT SENT TO LLM\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Model: {self.config['api']['model']}\n")
            f.write(f"Max Tokens: {self.config['api']['max_tokens']}\n")
            f.write(f"Temperature: {self.config['api']['temperature']}\n")
            f.write(f"Estimated Tokens: {estimated_tokens:.0f}\n")
            f.write(f"Prompt Length: {len(full_prompt)} characters\n")
            f.write("\n" + "=" * 50 + "\n\n")
            f.write(full_prompt)
        
        logger.info(f"Final prompt saved to {final_prompt_file}")
        logger.info(f"Prompt length: {len(full_prompt)} characters, estimated tokens: {estimated_tokens:.0f}")
        
        # Call Claude API with enhanced guidance
        try:
            response = self.api_client.messages.create(
                model=self.config["api"]["model"],
                max_tokens=self.config["api"]["max_tokens"],
                temperature=self.config["api"]["temperature"],
                messages=[{"role": "user", "content": full_prompt}]
            )
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "condition": "4_enhanced_guidance",
                "question": question,
                "data_files": data_files,
                "data_shape": list(data_df.shape),
                "schema_enrichment": {
                    "total_fields": schema_metadata["total_fields"],
                    "quality_score": schema_metadata["data_quality_score"],
                    "confidence_score": schema_metadata["confidence_score"],
                    "business_context_available": schema_metadata["business_context_available"]
                },
                "response": response.content[0].text,
                "token_usage": {
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                    "total": response.usage.input_tokens + response.usage.output_tokens
                }
            }
            
            logger.info(f"Enhanced guidance analysis complete. Tokens used: {result['token_usage']['total']}")
            return result
            
        except Exception as e:
            logger.error(f"Error in enhanced guidance analysis: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "condition": "4_enhanced_guidance",
                "question": question,
                "data_files": data_files if 'data_files' in locals() else [],
                "data_shape": list(data_df.shape) if 'data_df' in locals() else [0, 0]
            }
    
    def compare_with_condition_3(self, condition_4_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare Condition 4 results with Condition 3 baseline
        
        Args:
            condition_4_result: Results from Condition 4 enhanced guidance
            
        Returns:
            Comparison analysis
        """
        logger.info("Comparing with Condition 3 baseline")
        
        # Look for most recent Condition 3 results
        condition_3_dir = project_root / "results" / "condition_3"
        
        if not condition_3_dir.exists():
            logger.warning("No Condition 3 results found for comparison")
            return {"comparison_available": False, "message": "No Condition 3 baseline found"}
        
        # Find most recent Condition 3 result
        condition_3_files = list(condition_3_dir.glob("condition_3_result_*.json"))
        
        if not condition_3_files:
            logger.warning("No Condition 3 JSON results found")
            return {"comparison_available": False, "message": "No Condition 3 JSON results found"}
        
        # Load most recent Condition 3 result
        latest_c3_file = max(condition_3_files, key=lambda f: f.stat().st_mtime)
        
        try:
            with open(latest_c3_file, 'r') as f:
                condition_3_result = json.load(f)
            
            logger.info(f"Loaded Condition 3 baseline from {latest_c3_file}")
            
            comparison = {
                "comparison_available": True,
                "condition_3_baseline": {
                    "file": str(latest_c3_file),
                    "timestamp": condition_3_result.get("timestamp", "unknown"),
                    "token_usage": condition_3_result.get("token_usage", {}),
                    "guidance_type": "minimal"
                },
                "condition_4_enhanced": {
                    "timestamp": condition_4_result.get("timestamp", "unknown"),
                    "token_usage": condition_4_result.get("token_usage", {}),
                    "guidance_type": "enhanced",
                    "schema_enrichment": condition_4_result.get("schema_enrichment", {})
                },
                "improvements": {
                    "schema_context_added": condition_4_result.get("schema_enrichment", {}).get("business_context_available", False),
                    "field_enrichment": condition_4_result.get("schema_enrichment", {}).get("total_fields", 0),
                    "data_quality_score": condition_4_result.get("schema_enrichment", {}).get("quality_score", 0)
                }
            }
            
            # Calculate token efficiency if both have token usage
            c3_tokens = condition_3_result.get("token_usage", {}).get("total", 0)
            c4_tokens = condition_4_result.get("token_usage", {}).get("total", 0)
            
            if c3_tokens > 0 and c4_tokens > 0:
                comparison["token_efficiency"] = {
                    "condition_3_tokens": c3_tokens,
                    "condition_4_tokens": c4_tokens,
                    "efficiency_ratio": c4_tokens / c3_tokens,
                    "additional_tokens": c4_tokens - c3_tokens
                }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error loading Condition 3 results: {e}")
            return {"comparison_available": False, "error": str(e)}
    
    def _reduce_data_for_context(self, data_df: pd.DataFrame, 
                               schema_metadata: Dict[str, Any]) -> tuple[pd.DataFrame, str]:
        """
        Intelligently reduce data and schema context to fit within token limits
        
        Args:
            data_df: Full curated dataset
            schema_metadata: Complete schema discovery results
            
        Returns:
            Tuple of (reduced_dataframe, schema_summary)
        """
        # Estimate current sizes
        full_data_size = len(data_df.to_string())
        full_schema_size = len(json.dumps(schema_metadata, indent=2, default=str))
        
        logger.info(f"Original data size: {full_data_size:,} chars, Schema size: {full_schema_size:,} chars")
        
        # Target limits (rough token estimation: 1 token ≈ 4 characters)
        # More conservative limits to preserve most of the 49 locations
        max_total_chars = 80000   # ~20000 tokens for data + schema
        max_data_chars = 60000    # ~15000 tokens for location data (should keep ~40-45 locations)
        max_schema_chars = 20000  # ~5000 tokens for schema context
        
        # Step 1: Create condensed schema summary
        schema_summary = self._create_schema_summary(schema_metadata, max_schema_chars)
        
        # Step 2: Reduce location data if needed
        if full_data_size > max_data_chars:
            reduced_data = self._reduce_location_data(data_df, max_data_chars)
            logger.info(f"Reduced locations from {len(data_df)} to {len(reduced_data)} rows")
        else:
            reduced_data = data_df
            logger.info(f"Using all {len(data_df)} locations (within size limits)")
        
        # Final size check
        final_data_size = len(reduced_data.to_string())
        final_schema_size = len(schema_summary)
        total_size = final_data_size + final_schema_size
        
        logger.info(f"Final sizes - Data: {final_data_size:,}, Schema: {final_schema_size:,}, Total: {total_size:,} chars")
        
        return reduced_data, schema_summary
    
    def _create_schema_summary(self, schema_metadata: Dict[str, Any], max_chars: int) -> str:
        """
        Create a condensed schema summary focusing on key business context
        """
        field_metadata = schema_metadata.get("field_metadata", {})
        
        # Prioritize fields by importance tier
        critical_fields = []
        important_fields = []
        supplementary_fields = []
        
        for field_name, field_info in field_metadata.items():
            tier = field_info.get("importance_tier", 3)
            field_summary = {
                "name": field_name,
                "purpose": field_info.get("business_purpose", ""),
                "type": field_info.get("data_type", ""),
                "completeness": field_info.get("completeness", 0)
            }
            
            if tier == 1:
                critical_fields.append(field_summary)
            elif tier == 2:
                important_fields.append(field_summary)
            else:
                supplementary_fields.append(field_summary)
        
        # Build condensed summary
        summary = f"""SCHEMA DISCOVERY SUMMARY:
Total Fields: {schema_metadata.get('total_fields', 0)}
Data Quality: {schema_metadata.get('data_quality_score', 0):.2f}
Confidence: {schema_metadata.get('confidence_score', 0):.2f}

CRITICAL FIELDS ({len(critical_fields)}):"""
        
        for field in critical_fields:
            summary += f"\n• {field['name']}: {field['purpose']} ({field['type']}, {field['completeness']:.1%} complete)"
        
        if important_fields and len(summary) < max_chars * 0.7:
            summary += f"\n\nIMPORTANT FIELDS ({len(important_fields)}):"
            for field in important_fields[:5]:  # Limit to top 5
                summary += f"\n• {field['name']}: {field['purpose']}"
        
        # Truncate if still too long
        if len(summary) > max_chars:
            summary = summary[:max_chars-50] + "\n... [Schema summary truncated for context efficiency]"
        
        return summary
    
    def _reduce_location_data(self, data_df: pd.DataFrame, max_chars: int) -> pd.DataFrame:
        """
        Intelligently reduce location data while maintaining representativeness
        """
        # Strategy: Select diverse, high-priority locations
        
        # Step 1: Try to use priority score for selection
        if "priority_score" in data_df.columns:
            # Sort by priority and take top performers + some lower performers for diversity
            sorted_df = data_df.sort_values("priority_score", ascending=False)
            
            # Start with top priority locations
            selected_rows = []
            current_size = 0
            
            # Add high priority locations first
            high_priority = sorted_df.head(20)
            for idx, row in high_priority.iterrows():
                row_size = len(str(row.to_dict()))
                if current_size + row_size < max_chars * 0.8:  # Leave some buffer
                    selected_rows.append(idx)
                    current_size += row_size
                else:
                    break
            
            # Add some lower priority for diversity if space allows
            low_priority = sorted_df.tail(10)
            for idx, row in low_priority.iterrows():
                if idx not in selected_rows:
                    row_size = len(str(row.to_dict()))
                    if current_size + row_size < max_chars:
                        selected_rows.append(idx)
                        current_size += row_size
                    else:
                        break
            
            reduced_df = data_df.loc[selected_rows]
            
        else:
            # Fallback: Take first N rows that fit
            selected_rows = []
            current_size = 0
            
            for idx, row in data_df.iterrows():
                row_size = len(str(row.to_dict()))
                if current_size + row_size < max_chars:
                    selected_rows.append(idx)
                    current_size += row_size
                else:
                    break
            
            reduced_df = data_df.loc[selected_rows]
        
        return reduced_df
    
    def save_results(self, schema_metadata: Dict[str, Any], analysis_result: Dict[str, Any], 
                    comparison: Dict[str, Any]):
        """Save all Condition 4 results"""
        
        # Complete results package
        complete_results = {
            "condition": "4_enhanced_guidance",
            "timestamp": self.test_timestamp,
            "description": "Enhanced guidance test using schema discovery and config enrichment on 49 curated locations",
            "schema_discovery": schema_metadata,
            "analysis_result": analysis_result,
            "comparison_with_condition_3": comparison
        }
        
        # Save complete results
        results_file = self.results_dir / f"condition_4_result_{self.test_timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(complete_results, f, indent=2, default=str)
        
        # Save human-readable response
        if "response" in analysis_result:
            response_file = self.results_dir / f"condition_4_response_{self.test_timestamp}.txt"
            with open(response_file, 'w') as f:
                f.write(f"Question: {analysis_result.get('question', 'Unknown')}\n")
                f.write(f"Timestamp: {analysis_result.get('timestamp', 'Unknown')}\n")
                f.write(f"Condition: 4 - Enhanced Guidance (Schema Discovery + Config Enrichment)\n")
                f.write("=" * 80 + "\n\n")
                f.write(analysis_result["response"])
        
        logger.info(f"Results saved to {results_file}")
        return results_file
    
    def run_complete_test(self, question: str = None, dry_run: bool = False) -> Dict[str, Any]:
        """
        Run complete Condition 4 enhanced guidance test
        
        Args:
            question: Business question to analyze (uses default if not provided)
            
        Returns:
            Complete test results
        """
        if question is None:
            question = "Which of my locations need immediate attention and what specific actions should I take?"
        
        logger.info(f"Starting Condition 4: Enhanced Guidance Test")
        logger.info(f"Question: {question}")
        
        try:
            # Step 1: Discover curated data
            data_files = self.discover_curated_data()
            
            # Step 2: Run schema discovery with enrichment
            schema_metadata = self.run_schema_discovery_with_enrichment(data_files)
            
            # Step 3: Run enhanced guidance analysis
            analysis_result = self.run_enhanced_guidance_analysis(question, data_files, schema_metadata, dry_run)
            
            # Step 4: Compare with Condition 3 baseline
            comparison = self.compare_with_condition_3(analysis_result)
            
            # Step 5: Save results
            results_file = self.save_results(schema_metadata, analysis_result, comparison)
            
            logger.info("Condition 4 test complete!")
            
            return {
                "success": True,
                "results_file": str(results_file),
                "schema_metadata": schema_metadata,
                "analysis_result": analysis_result,
                "comparison": comparison
            }
            
        except Exception as e:
            logger.error(f"Condition 4 test failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Condition 4: Enhanced Guidance Test")
    parser.add_argument("--question", "-q",
                       default="Which of my locations need immediate attention and what specific actions should I take?",
                       help="Business question to analyze")
    parser.add_argument("--dry-run", action="store_true",
                       help="Preview prompt and estimate tokens without making API call")
    
    args = parser.parse_args()
    
    # Run Condition 4 test
    test = Condition4EnhancedGuidance()
    results = test.run_complete_test(args.question, args.dry_run)
    
    # Print summary
    if results["success"]:
        print("\n" + "="*80)
        print("CONDITION 4: ENHANCED GUIDANCE TEST RESULTS")
        print("="*80)
        
        schema_meta = results["schema_metadata"]
        analysis = results["analysis_result"]
        comparison = results["comparison"]
        
        print(f"Data Quality Score: {schema_meta['data_quality_score']:.2f}")
        print(f"Schema Confidence: {schema_meta['confidence_score']:.2f}")
        print(f"Fields Analyzed: {schema_meta['total_fields']}")
        print(f"Business Context Available: {schema_meta['business_context_available']}")
        
        if analysis.get('dry_run'):
            print(f"Estimated Token Usage: {analysis['estimated_tokens']:.0f}")
            print(f"Prompt Length: {analysis['prompt_length']:,} characters")
            print(f"Dry Run Prompt File: {analysis['prompt_file']}")
        elif 'error' in analysis:
            print(f"Analysis Error: {analysis['error']}")
        elif 'token_usage' in analysis:
            print(f"Token Usage: {analysis['token_usage']['total']}")
        else:
            print("Token usage information not available")
        
        if comparison.get("comparison_available"):
            print(f"\nComparison with Condition 3:")
            if "token_efficiency" in comparison:
                ratio = comparison["token_efficiency"]["efficiency_ratio"]
                print(f"  Token Efficiency Ratio: {ratio:.2f}x")
            print(f"  Schema Enhancement: {comparison['improvements']['schema_context_added']}")
        
        print(f"\nResults saved to: {results['results_file']}")
    else:
        print(f"Test failed: {results['error']}")


if __name__ == "__main__":
    main()
