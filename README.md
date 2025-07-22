# LLM Testing Framework

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up API key:**
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```

3. **Add your curated CSV data files to:**
   ```
   data/curated/
   ```

4. **Run Condition 3 (Curated Data + Minimal Guidance):**
   ```bash
   python scripts/condition_3_test.py
   ```

## Project Structure

```
llm_scenario_test/
├── data/
│   ├── curated/          # Your CSV files go here
│   └── source/           # Raw data files (future)
├── prompts/
│   ├── minimal_guidance.md     # Basic prompt template
│   └── enhanced_guidance.md    # Business context prompts
├── scripts/
│   └── condition_3_test.py     # Curated + minimal test
├── results/
│   └── condition_3/            # Test outputs
├── config/
│   └── claude_api_config.py    # API settings
└── requirements.txt
```

## Current Status

✅ **Condition 3 (Curated Data + Minimal Guidance)** - Ready to test
- Discovers all CSV files in `data/curated/`
- Uses minimal business guidance
- Outputs structured JSON results

🔄 **Next: Condition 4 (Curated Data + Enhanced Guidance)**
- Will add schema discovery
- Enhanced business context
- More detailed output structure

## Test Results

Results are saved to `results/condition_3/` with:
- API response data
- Token usage metrics
- Performance timing
- Test metadata