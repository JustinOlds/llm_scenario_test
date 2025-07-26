"""
Multi-Prompt Agent Pipeline

This script orchestrates the complete 4-stage multi-prompt agent pipeline:
1. Schema Discovery - Analyze data and enrich with business context
2. Question Analysis - Classify question and determine approach
3. Data Filtering - Select representative subset efficiently
4. Output Generation - Create actionable business insights

Key Features:
- Dynamic schema discovery with config enrichment
- Machine-readable intermediate outputs between stages
- Intelligent data filtering for efficiency
- Comprehensive business-focused final output
"""

import os
import sys
import yaml
import json
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from agents.schema_discovery import SchemaDiscoveryAgent
from agents.question_analyzer import QuestionAnalyzerAgent
from agents.data_filter import DataFilterAgent
from agents.output_generator import OutputGeneratorAgent
from config.claude_api_config import get_api_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MultiPromptAgent:
    """
    Complete multi-prompt agent pipeline for retail analytics
    
    Orchestrates the 4-stage process from raw data discovery through
    final actionable business recommendations.
    """
    
    def __init__(self, config_path: str = None):
        """Initialize the multi-prompt agent pipeline"""
        self.project_root = project_root
        self.config_path = config_path or str(project_root / "config" / "agent_config.yaml")
        self.config = self._load_config()
        
        # Initialize stage agents
        self.schema_agent = SchemaDiscoveryAgent(self.config_path)
        self.question_agent = QuestionAnalyzerAgent(self.config_path)
        self.filter_agent = DataFilterAgent(self.config_path)
        self.output_agent = OutputGeneratorAgent(self.config_path)
        
        # API client for LLM calls
        self.api_client = get_api_client()
        
        # Data discovery paths
        self.data_paths = {
            "curated": project_root / "data" / "curated",
            "org": project_root / "data" / "org",
            "global": project_root / "data" / "global"
        }
        
        # Results storage
        self.results_dir = project_root / "results" / "multi_prompt"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Session tracking
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.results_dir / f"session_{self.session_id}"
        self.session_dir.mkdir(exist_ok=True)
        
    def _load_config(self) -> Dict[str, Any]:
        """Load pipeline configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {self.config_path}. Using defaults.")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Provide default pipeline configuration"""
        return {
            "pipeline": {
                "stages": {
                    "schema_discovery": {"enabled": True, "max_tokens": 2000},
                    "question_analysis": {"enabled": True, "max_tokens": 1500},
                    "data_filtering": {"enabled": True, "max_tokens": 1000},
                    "output_generation": {"enabled": True, "max_tokens": 4000}
                }
            },
            "data_filtering": {
                "max_rows": 25,
                "selection_weights": {
                    "representative": 0.4,
                    "priority_score": 0.4,
                    "sales_volume": 0.2
                }
            },
            "api": {
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.1
            }
        }
    
    def discover_data_sources(self) -> Dict[str, List[str]]:
        """
        Dynamically discover all available data files
        
        Returns:
            Dictionary mapping data types to file paths
        """
        logger.info("Discovering available data sources...")
        
        discovered_files = {}
        
        for data_type, path in self.data_paths.items():
            if path.exists():
                csv_files = list(path.glob("*.csv"))
                discovered_files[data_type] = [str(f) for f in csv_files]
                logger.info(f"Found {len(csv_files)} {data_type} files")
            else:
                discovered_files[data_type] = []
                logger.info(f"No {data_type} directory found")
        
        # Save discovery results
        discovery_file = self.session_dir / "data_discovery.json"
        with open(discovery_file, 'w') as f:
            json.dump(discovered_files, f, indent=2)
        
        return discovered_files
    
    def stage_1_schema_discovery(self, data_files: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Stage 1: Schema Discovery with Config Enrichment
        
        Args:
            data_files: Discovered data files by type
            
        Returns:
            Enhanced schema metadata
        """
        logger.info("=== STAGE 1: SCHEMA DISCOVERY ===")
        
        if not self.config["pipeline"]["stages"]["schema_discovery"]["enabled"]:
            logger.info("Schema discovery stage disabled")
            return {}
        
        # Get all files for analysis
        all_files = []
        for file_list in data_files.values():
            all_files.extend(file_list)
        
        if not all_files:
            logger.warning("No data files available for schema discovery")
            return {}
        
        # Load enhanced guidance prompt
        prompt_path = self.project_root / "prompts" / "enhanced_guidance" / "schema_discovery.md"
        
        try:
            with open(prompt_path, 'r') as f:
                schema_prompt = f.read()
        except FileNotFoundError:
            logger.warning("Schema discovery prompt not found, using basic prompt")
            schema_prompt = "Analyze the data schema and provide field metadata."
        
        # Load existing config knowledge for enrichment
        config_knowledge = self._load_existing_config_knowledge()
        
        # Analyze first curated file as sample
        sample_data = None
        curated_files = data_files.get("curated", [])
        if curated_files:
            try:
                sample_data = pd.read_csv(curated_files[0])
                logger.info(f"Loaded sample data: {sample_data.shape}")
            except Exception as e:
                logger.error(f"Error loading sample data: {e}")
        
        # Create schema discovery prompt
        data_summary = ""
        if sample_data is not None:
            data_summary = f"""
Sample Data Shape: {sample_data.shape}
Columns: {list(sample_data.columns)}
Data Types: {sample_data.dtypes.to_dict()}
Sample Records:
{sample_data.head(3).to_string()}
"""
        
        config_context = json.dumps(config_knowledge, indent=2) if config_knowledge else "No existing config available"
        
        full_prompt = f"""
{schema_prompt}

Available Data Files:
{json.dumps(data_files, indent=2)}

Sample Data Analysis:
{data_summary}

Existing Configuration Knowledge:
{config_context}

Please provide comprehensive schema discovery output in the specified JSON format.
"""
        
        # Call LLM for schema discovery
        try:
            response = self.api_client.messages.create(
                model=self.config["api"]["model"],
                max_tokens=self.config["pipeline"]["stages"]["schema_discovery"]["max_tokens"],
                temperature=self.config["api"]["temperature"],
                messages=[{"role": "user", "content": full_prompt}]
            )
            
            schema_result = {
                "timestamp": datetime.now().isoformat(),
                "stage": "schema_discovery",
                "data_files": data_files,
                "response": response.content[0].text,
                "token_usage": {
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                    "total": response.usage.input_tokens + response.usage.output_tokens
                },
                "config_enrichment": config_knowledge
            }
            
            # Save stage results
            stage_file = self.session_dir / "stage_1_schema_discovery.json"
            with open(stage_file, 'w') as f:
                json.dump(schema_result, f, indent=2, default=str)
            
            logger.info("Stage 1 complete: Schema discovery")
            return schema_result
            
        except Exception as e:
            logger.error(f"Error in schema discovery stage: {e}")
            return {"error": str(e)}
    
    def stage_2_question_analysis(self, question: str, schema_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stage 2: Question Analysis and Approach Selection
        
        Args:
            question: User's question to analyze
            schema_result: Output from schema discovery stage
            
        Returns:
            Question analysis and filtering specifications
        """
        logger.info("=== STAGE 2: QUESTION ANALYSIS ===")
        
        if not self.config["pipeline"]["stages"]["question_analysis"]["enabled"]:
            logger.info("Question analysis stage disabled")
            return {}
        
        # Load enhanced guidance prompt
        prompt_path = self.project_root / "prompts" / "enhanced_guidance" / "question_analysis.md"
        
        try:
            with open(prompt_path, 'r') as f:
                question_prompt = f.read()
        except FileNotFoundError:
            logger.warning("Question analysis prompt not found, using basic prompt")
            question_prompt = "Analyze the question and determine the analytical approach."
        
        # Create question analysis prompt
        schema_context = json.dumps(schema_result, indent=2, default=str)
        
        full_prompt = f"""
{question_prompt}

User Question: {question}

Schema Discovery Context:
{schema_context}

Please provide question analysis output in the specified JSON format.
"""
        
        # Call LLM for question analysis
        try:
            response = self.api_client.messages.create(
                model=self.config["api"]["model"],
                max_tokens=self.config["pipeline"]["stages"]["question_analysis"]["max_tokens"],
                temperature=self.config["api"]["temperature"],
                messages=[{"role": "user", "content": full_prompt}]
            )
            
            question_result = {
                "timestamp": datetime.now().isoformat(),
                "stage": "question_analysis",
                "original_question": question,
                "schema_context": schema_result,
                "response": response.content[0].text,
                "token_usage": {
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                    "total": response.usage.input_tokens + response.usage.output_tokens
                }
            }
            
            # Save stage results
            stage_file = self.session_dir / "stage_2_question_analysis.json"
            with open(stage_file, 'w') as f:
                json.dump(question_result, f, indent=2, default=str)
            
            logger.info("Stage 2 complete: Question analysis")
            return question_result
            
        except Exception as e:
            logger.error(f"Error in question analysis stage: {e}")
            return {"error": str(e)}
    
    def stage_3_data_filtering(self, data_files: Dict[str, List[str]], 
                              question_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stage 3: Intelligent Data Filtering
        
        Args:
            data_files: Available data files
            question_result: Output from question analysis stage
            
        Returns:
            Filtered data and selection metadata
        """
        logger.info("=== STAGE 3: DATA FILTERING ===")
        
        if not self.config["pipeline"]["stages"]["data_filtering"]["enabled"]:
            logger.info("Data filtering stage disabled")
            return {}
        
        # Load data for filtering
        curated_files = data_files.get("curated", [])
        if not curated_files:
            logger.error("No curated data files available for filtering")
            return {"error": "No curated data available"}
        
        try:
            # Load the primary data file
            data_df = pd.read_csv(curated_files[0])
            logger.info(f"Loaded data for filtering: {data_df.shape}")
        except Exception as e:
            logger.error(f"Error loading data for filtering: {e}")
            return {"error": str(e)}
        
        # Load enhanced guidance prompt
        prompt_path = self.project_root / "prompts" / "enhanced_guidance" / "data_filtering.md"
        
        try:
            with open(prompt_path, 'r') as f:
                filter_prompt = f.read()
        except FileNotFoundError:
            logger.warning("Data filtering prompt not found, using basic prompt")
            filter_prompt = "Filter the data to select the most representative subset."
        
        # Apply basic filtering logic (placeholder for now)
        max_rows = self.config["data_filtering"]["max_rows"]
        
        # Simple filtering: take top rows by priority score if available
        if "priority_score" in data_df.columns:
            filtered_df = data_df.nlargest(max_rows, "priority_score")
        else:
            # Fallback: take first N rows
            filtered_df = data_df.head(max_rows)
        
        # Create filtering prompt for LLM guidance
        question_context = json.dumps(question_result, indent=2, default=str)
        
        full_prompt = f"""
{filter_prompt}

Original Data Shape: {data_df.shape}
Filtered Data Shape: {filtered_df.shape}

Question Analysis Context:
{question_context}

Filtered Data Sample:
{filtered_df.head().to_string()}

Please provide data filtering analysis and rationale in the specified JSON format.
"""
        
        # Call LLM for filtering analysis
        try:
            response = self.api_client.messages.create(
                model=self.config["api"]["model"],
                max_tokens=self.config["pipeline"]["stages"]["data_filtering"]["max_tokens"],
                temperature=self.config["api"]["temperature"],
                messages=[{"role": "user", "content": full_prompt}]
            )
            
            filter_result = {
                "timestamp": datetime.now().isoformat(),
                "stage": "data_filtering",
                "original_row_count": len(data_df),
                "filtered_row_count": len(filtered_df),
                "filtering_method": "priority_score_ranking",
                "filtered_data_file": str(self.session_dir / "filtered_data.csv"),
                "response": response.content[0].text,
                "token_usage": {
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                    "total": response.usage.input_tokens + response.usage.output_tokens
                }
            }
            
            # Save filtered data
            filtered_df.to_csv(self.session_dir / "filtered_data.csv", index=False)
            
            # Save stage results
            stage_file = self.session_dir / "stage_3_data_filtering.json"
            with open(stage_file, 'w') as f:
                json.dump(filter_result, f, indent=2, default=str)
            
            logger.info("Stage 3 complete: Data filtering")
            return filter_result
            
        except Exception as e:
            logger.error(f"Error in data filtering stage: {e}")
            return {"error": str(e)}
    
    def stage_4_output_generation(self, question: str, schema_result: Dict[str, Any],
                                 question_result: Dict[str, Any], 
                                 filter_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stage 4: Human-Readable Output Generation
        
        Args:
            question: Original user question
            schema_result: Schema discovery output
            question_result: Question analysis output
            filter_result: Data filtering output
            
        Returns:
            Final business insights and recommendations
        """
        logger.info("=== STAGE 4: OUTPUT GENERATION ===")
        
        if not self.config["pipeline"]["stages"]["output_generation"]["enabled"]:
            logger.info("Output generation stage disabled")
            return {}
        
        # Load filtered data
        try:
            filtered_data_path = self.session_dir / "filtered_data.csv"
            if filtered_data_path.exists():
                filtered_df = pd.read_csv(filtered_data_path)
                logger.info(f"Loaded filtered data: {filtered_df.shape}")
            else:
                logger.error("Filtered data file not found")
                return {"error": "Filtered data not available"}
        except Exception as e:
            logger.error(f"Error loading filtered data: {e}")
            return {"error": str(e)}
        
        # Load enhanced guidance prompt
        prompt_path = self.project_root / "prompts" / "enhanced_guidance" / "output_generation.md"
        
        try:
            with open(prompt_path, 'r') as f:
                output_prompt = f.read()
        except FileNotFoundError:
            logger.warning("Output generation prompt not found, using basic prompt")
            output_prompt = "Generate actionable business insights and recommendations."
        
        # Create comprehensive context for final output
        pipeline_context = {
            "schema_discovery": schema_result,
            "question_analysis": question_result,
            "data_filtering": filter_result
        }
        
        context_json = json.dumps(pipeline_context, indent=2, default=str)
        
        full_prompt = f"""
{output_prompt}

Original Question: {question}

Pipeline Context:
{context_json}

Filtered Data for Analysis:
{filtered_df.to_string()}

Please provide comprehensive business analysis with actionable recommendations using the specified format.
"""
        
        # Call LLM for final output generation
        try:
            response = self.api_client.messages.create(
                model=self.config["api"]["model"],
                max_tokens=self.config["pipeline"]["stages"]["output_generation"]["max_tokens"],
                temperature=0.2,  # Slightly higher for more creative recommendations
                messages=[{"role": "user", "content": full_prompt}]
            )
            
            output_result = {
                "timestamp": datetime.now().isoformat(),
                "stage": "output_generation",
                "original_question": question,
                "final_response": response.content[0].text,
                "pipeline_context": pipeline_context,
                "token_usage": {
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                    "total": response.usage.input_tokens + response.usage.output_tokens
                }
            }
            
            # Save stage results
            stage_file = self.session_dir / "stage_4_output_generation.json"
            with open(stage_file, 'w') as f:
                json.dump(output_result, f, indent=2, default=str)
            
            # Save human-readable output
            output_file = self.session_dir / "final_output.txt"
            with open(output_file, 'w') as f:
                f.write(response.content[0].text)
            
            logger.info("Stage 4 complete: Output generation")
            return output_result
            
        except Exception as e:
            logger.error(f"Error in output generation stage: {e}")
            return {"error": str(e)}
    
    def _load_existing_config_knowledge(self) -> Dict[str, Any]:
        """Load existing configuration knowledge for schema enrichment"""
        config_file = self.project_root / "llm_columns_canonical.yaml"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.warning(f"Could not load existing config: {e}")
        
        return {}
    
    def run_complete_pipeline(self, question: str) -> Dict[str, Any]:
        """
        Execute the complete 4-stage multi-prompt pipeline
        
        Args:
            question: User's question to analyze
            
        Returns:
            Complete pipeline results
        """
        logger.info(f"Starting complete multi-prompt pipeline for session: {self.session_id}")
        logger.info(f"Question: {question}")
        
        pipeline_start = datetime.now()
        
        try:
            # Stage 1: Data Discovery and Schema Analysis
            data_files = self.discover_data_sources()
            schema_result = self.stage_1_schema_discovery(data_files)
            
            # Stage 2: Question Analysis
            question_result = self.stage_2_question_analysis(question, schema_result)
            
            # Stage 3: Data Filtering
            filter_result = self.stage_3_data_filtering(data_files, question_result)
            
            # Stage 4: Output Generation
            output_result = self.stage_4_output_generation(question, schema_result, 
                                                         question_result, filter_result)
            
            # Calculate pipeline metrics
            pipeline_end = datetime.now()
            total_duration = (pipeline_end - pipeline_start).total_seconds()
            
            # Aggregate token usage
            total_tokens = 0
            for result in [schema_result, question_result, filter_result, output_result]:
                if "token_usage" in result:
                    total_tokens += result["token_usage"].get("total", 0)
            
            # Complete pipeline results
            complete_results = {
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "question": question,
                "pipeline_duration_seconds": total_duration,
                "total_token_usage": total_tokens,
                "stages": {
                    "data_discovery": data_files,
                    "schema_discovery": schema_result,
                    "question_analysis": question_result,
                    "data_filtering": filter_result,
                    "output_generation": output_result
                },
                "success": True
            }
            
            # Save complete results
            complete_file = self.session_dir / "complete_pipeline_results.json"
            with open(complete_file, 'w') as f:
                json.dump(complete_results, f, indent=2, default=str)
            
            logger.info(f"Pipeline complete! Duration: {total_duration:.1f}s, Tokens: {total_tokens}")
            logger.info(f"Results saved to: {self.session_dir}")
            
            return complete_results
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return {
                "session_id": self.session_id,
                "error": str(e),
                "success": False
            }


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-Prompt Agent Pipeline")
    parser.add_argument("--question", "-q", 
                       default="Which of my locations need immediate attention and what specific actions should I take?",
                       help="Question to analyze")
    parser.add_argument("--config", "-c", 
                       help="Path to agent configuration file")
    
    args = parser.parse_args()
    
    # Initialize and run pipeline
    agent = MultiPromptAgent(args.config)
    results = agent.run_complete_pipeline(args.question)
    
    # Print summary
    if results.get("success"):
        print("\n" + "="*60)
        print("MULTI-PROMPT AGENT PIPELINE RESULTS")
        print("="*60)
        print(f"Session ID: {results['session_id']}")
        print(f"Duration: {results['pipeline_duration_seconds']:.1f} seconds")
        print(f"Total Tokens: {results['total_token_usage']}")
        print(f"Question: {results['question']}")
        print("\nFinal output saved to:")
        print(f"  {Path(results['session_id']).parent / f'session_{results['session_id']}' / 'final_output.txt'}")
    else:
        print(f"Pipeline failed: {results.get('error')}")


if __name__ == "__main__":
    main()
