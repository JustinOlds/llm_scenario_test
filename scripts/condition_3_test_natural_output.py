#!/usr/bin/env python3
"""
Condition 3 Test: Curated Data + Minimal Guidance
Tests Claude API with processed weekly location summaries and basic prompting.
Now handles natural language responses instead of JSON.
"""

from dotenv import load_dotenv
load_dotenv()
import json
import time
import csv
import os
from datetime import datetime
from typing import Dict, List, Any
import anthropic

class Condition3Tester:
    def __init__(self, api_key: str):
        """Initialize the tester with Claude API client."""
        self.client = anthropic.Anthropic(api_key=api_key)
        self.results = []
        self.test_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create results directory
        self.results_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results", "condition_3")
        os.makedirs(self.results_dir, exist_ok=True)
        
    def discover_curated_files(self, data_dir: str) -> List[str]:
        """Discover all CSV files in the curated data directory."""
        import glob
        csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
        return csv_files
    
    def load_curated_data(self, filepath: str) -> str:
        """Load and format curated weekly data for prompt."""
        data_rows = []
        
        with open(filepath, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data_rows.append(row)
        
        # Format as readable table for Claude
        if not data_rows:
            raise ValueError("No data loaded from file")
            
        # Create formatted table
        headers = list(data_rows[0].keys())
        formatted_data = f"Location Data ({len(data_rows)} locations):\n\n"
        
        # Add header row
        formatted_data += " | ".join(headers) + "\n"
        formatted_data += " | ".join(["-" * len(h) for h in headers]) + "\n"
        
        # Add data rows
        for row in data_rows:
            formatted_data += " | ".join([str(row.get(h, "")) for h in headers]) + "\n"
            
        return formatted_data
        
    def create_minimal_prompt(self, user_question: str, data_content: str) -> str:
        """Create minimal guidance prompt."""
        return f"""You are a business analyst helping retail operators make data-driven decisions about their locations.

Question: {user_question}

Location Data:
{data_content}

Instructions:
- Analyze the data to answer the question
- Focus on high priority locations for the operator  
- Provide specific recommendations with supporting data (e.g., product recommendations to add or drop, category trends, etc.)
"""

    def call_claude_api(self, prompt: str, user_question: str = None) -> Dict[str, Any]:
        """Make API call to Claude and return structured response."""
        start_time = time.time()
        
        try:
            # Estimate tokens in prompt (rough approximation)
            est_input_tokens = len(prompt) // 3  # Rough estimate: ~3 chars per token on average
            
            # Log token estimation
            print(f"Estimated input tokens: {est_input_tokens} (Claude limit: 200,000)")
            
            if est_input_tokens > 190000:  # Buffer for safety
                raise ValueError(f"Estimated input tokens ({est_input_tokens}) likely exceeds Claude's limit")
            
            # Save final prompt for transparency (same as Condition 4)
            final_prompt_file = os.path.join(self.results_dir, f"final_prompt_{self.test_timestamp}.txt")
            with open(final_prompt_file, 'w', encoding='utf-8') as f:
                f.write("FINAL PROMPT SENT TO LLM (CONDITION 3 - NATURAL OUTPUT)\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Model: claude-3-5-sonnet-20241022\n")
                f.write(f"Max Tokens: 8192\n")
                f.write(f"Temperature: 0.1\n")
                f.write(f"Estimated Tokens: {est_input_tokens}\n")
                f.write(f"Prompt Length: {len(prompt)} characters\n")
                f.write("\n" + "=" * 60 + "\n\n")
                f.write(prompt)
            
            print(f"Final prompt saved to {final_prompt_file}")
            print(f"Prompt length: {len(prompt)} characters, estimated tokens: {est_input_tokens}")
                
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=8192,  # Increased from 4000 to allow more detailed responses
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_time = time.time() - start_time
            
            # Extract response content as natural language
            response_text = message.content[0].text
            
            # Save structured response (comparable to Condition 4)
            result = {
                "timestamp": datetime.now().isoformat(),
                "condition": "3_natural_output",
                "question": user_question,
                "response": response_text,
                "response_time": response_time,
                "token_usage": {
                    "input_tokens": message.usage.input_tokens,
                    "output_tokens": message.usage.output_tokens,
                    "total_tokens": message.usage.input_tokens + message.usage.output_tokens
                },
                "prompt_length": len(prompt),
                "estimated_input_tokens": est_input_tokens,
                "guidance_type": "minimal"
            }
            
            # Save results in comparable format to Condition 4
            results_file = os.path.join(self.results_dir, f"condition_3_result_{self.test_timestamp}.json")
            with open(results_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            
            # Save human-readable response
            response_file = os.path.join(self.results_dir, f"condition_3_response_{self.test_timestamp}.txt")
            with open(response_file, 'w') as f:
                f.write(f"Question: {user_question}\n")
                f.write(f"Timestamp: {result['timestamp']}\n")
                f.write(f"Condition: 3 - Natural Output (Minimal Guidance)\n")
                f.write("=" * 80 + "\n\n")
                f.write(response_text)
            
            print(f"Results saved to {results_file}")
            
            return result
            
        except Exception as e:
            return {
                "error": str(e),
                "response_time": time.time() - start_time
            }
    
    def run_test(self, data_dir: str, user_question: str, output_dir: str = None) -> Dict[str, Any]:
        """Run the complete Condition 3 test."""
        print(f"Starting Condition 3 Test: Curated Data + Minimal Guidance")
        print(f"Question: {user_question}")
        print(f"Data directory: {data_dir}")
        
        # Discover available CSV files
        try:
            csv_files = self.discover_curated_files(data_dir)
            if not csv_files:
                return {"error": f"No CSV files found in {data_dir}"}
            
            print(f"Found {len(csv_files)} CSV files:")
            for file in csv_files:
                print(f"  - {os.path.basename(file)}")
            
            # Load and combine all CSV data
            all_data_content = ""
            for csv_file in csv_files:
                try:
                    file_content = self.load_curated_data(csv_file)
                    all_data_content += f"\n{file_content}\n"
                except Exception as e:
                    print(f"Warning: Failed to load {csv_file}: {e}")
            
            if not all_data_content.strip():
                return {"error": "No data could be loaded from CSV files"}
                
            print(f"Loaded combined data: {len(all_data_content)} characters")
            
        except Exception as e:
            return {"error": f"Data discovery/loading failed: {e}"}
        
        # Create prompt
        prompt = self.create_minimal_prompt(user_question, all_data_content)
        print(f"Created prompt: {len(prompt)} characters")
        
        # Call Claude API
        print("Calling Claude API...")
        result = self.call_claude_api(prompt, user_question)
        
        if "error" in result:
            print(f"API call failed: {result['error']}")
            return result
        
        print("Condition 3 test complete!")
        
        # Print comparable summary to Condition 4
        print("\n" + "=" * 80)
        print("CONDITION 3: NATURAL OUTPUT TEST RESULTS")
        print("=" * 80)
        print(f"Guidance Type: Minimal")
        print(f"Data Files: {len(csv_files)}")
        print(f"Token Usage: {result.get('token_usage', {}).get('total_tokens', 'Unknown')}")
        print(f"Prompt Length: {len(prompt)} characters")
        print(f"Response Time: {result.get('response_time', 0):.2f} seconds")
        print("")
        print(f"Results saved to: {os.path.join(self.results_dir, f'condition_3_result_{self.test_timestamp}.json')}")
        
        return result
        
        # Save results as JSON (but containing natural language response)
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"condition_3_result_{timestamp}.json")
        
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            
        # Also save just the response text as a separate readable file
        text_output_file = os.path.join(output_dir, f"condition_3_response_{timestamp}.txt")
        with open(text_output_file, 'w', encoding='utf-8') as f:
            f.write(f"Question: {user_question}\n")
            f.write(f"Timestamp: {result['test_metadata']['timestamp']}\n")
            f.write(f"Data files: {', '.join(result['test_metadata']['data_files'])}\n")
            f.write("=" * 50 + "\n\n")
            f.write(result["response_text"])
            
        print(f"Results saved to: {output_file}")
        print(f"Response text saved to: {text_output_file}")
        print(f"Response time: {result['response_time']:.2f}s")
        print(f"Token usage: {result['token_usage']['total_tokens']}")
        
        return result

def main():
    """Main execution function."""
    # Configuration
    API_KEY = os.getenv('ANTHROPIC_API_KEY')
    if not API_KEY:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        return
    
    # Configuration - will auto-discover CSV files in curated directory
    CURATED_DATA_DIR = "data/curated"
    OUTPUT_DIR = "results/condition_3"
    USER_QUESTION = "Which of my locations need immediate attention and what specific actions should I take?"
    
    # Run test
    tester = Condition3Tester(API_KEY)
    result = tester.run_test(CURATED_DATA_DIR, USER_QUESTION, OUTPUT_DIR)
    
    # Print summary
    if "error" not in result:
        print("\n=== Test Summary ===")
        print(f"Response length: {len(result['response'])} characters")
        print(f"Total tokens used: {result['token_usage']['total_tokens']}")
        print(f"Cost estimate: ${result['token_usage']['total_tokens'] * 0.000015:.4f}")  # Rough estimate
        
        # Show first few lines of response
        print("\n=== Response Preview ===")
        response_lines = result['response_text'].split('\n')
        for i, line in enumerate(response_lines[:5]):
            print(line)
        if len(response_lines) > 5:
            print("...")
    else:
        print(f"Test failed: {result['error']}")

if __name__ == "__main__":
    main()