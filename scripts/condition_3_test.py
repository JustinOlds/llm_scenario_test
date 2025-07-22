#!/usr/bin/env python3
"""
Condition 3 Test: Curated Data + Minimal Guidance
Tests Claude API with processed weekly location summaries and basic prompting.
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
- Focus on actionable insights for the operator  
- Provide specific recommendations with supporting data
- Format your response as structured JSON

Response Format:
{{
  "urgent_locations": [
    {{
      "location_name": "...",
      "priority_reason": "...", 
      "specific_actions": ["...", "..."]
    }}
  ],
  "summary": "...",
  "total_locations_analyzed": 0
}}"""

    def call_claude_api(self, prompt: str) -> Dict[str, Any]:
        """Make API call to Claude and return structured response."""
        start_time = time.time()
        
        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_time = time.time() - start_time
            
            # Extract response content
            response_text = message.content[0].text
            
            # Try to parse JSON from response
            try:
                # Look for JSON block in response
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    json_text = response_text[json_start:json_end].strip()
                elif "{" in response_text and "}" in response_text:
                    json_start = response_text.find("{")
                    json_end = response_text.rfind("}") + 1
                    json_text = response_text[json_start:json_end]
                else:
                    json_text = response_text
                    
                parsed_response = json.loads(json_text)
            except json.JSONDecodeError:
                # If JSON parsing fails, create structured response
                parsed_response = {
                    "raw_response": response_text,
                    "parsing_error": "Could not parse JSON response"
                }
            
            return {
                "response": parsed_response,
                "response_time": response_time,
                "token_usage": {
                    "input_tokens": message.usage.input_tokens,
                    "output_tokens": message.usage.output_tokens,
                    "total_tokens": message.usage.input_tokens + message.usage.output_tokens
                },
                "raw_text": response_text
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "response_time": time.time() - start_time
            }
    
    def run_test(self, data_dir: str, user_question: str, output_dir: str) -> Dict[str, Any]:
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
        result = self.call_claude_api(prompt)
        
        if "error" in result:
            print(f"API call failed: {result['error']}")
            return result
            
        # Add metadata
        result["test_metadata"] = {
            "condition": "3_curated_minimal",
            "timestamp": datetime.now().isoformat(),
            "question": user_question,
            "data_files": [os.path.basename(f) for f in csv_files],
            "data_directory": data_dir,
            "prompt_length": len(prompt)
        }
        
        # Save results
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"condition_3_result_{timestamp}.json")
        
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
            
        print(f"Results saved to: {output_file}")
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
        if "urgent_locations" in result["response"]:
            urgent_count = len(result["response"]["urgent_locations"])
            print(f"Urgent locations identified: {urgent_count}")
            for loc in result["response"]["urgent_locations"][:3]:  # Show first 3
                print(f"  - {loc.get('location_name', 'Unknown')}: {loc.get('priority_reason', 'No reason')}")
        print(f"Total tokens used: {result['token_usage']['total_tokens']}")
        print(f"Cost estimate: ${result['token_usage']['total_tokens'] * 0.000015:.4f}")  # Rough estimate
    else:
        print(f"Test failed: {result['error']}")

if __name__ == "__main__":
    main()