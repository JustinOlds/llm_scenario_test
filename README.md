# Enhanced Guidance Multi-Prompt Agent System

## Overview

This system has evolved from basic condition testing to a sophisticated multi-prompt agent approach focused on curated data analysis with enhanced guidance. Based on condition 3 results (49 locations), we've pivoted away from source data tests to focus on intelligent data curation and multi-stage analysis.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up API key:**
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```

3. **Run enhanced guidance conditions:**
   ```bash
   # Minimal vs Enhanced Guidance Benchmark
   python scripts/enhanced_guidance_benchmark.py
   
   # Multi-prompt agent pipeline
   python scripts/multi_prompt_agent.py
   ```

## System Architecture

### Multi-Prompt Agent Pipeline
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Schema Discovery│ -> │Question Analysis│ -> │ Data Filtering  │ -> │Human Output Gen │
│                 │    │                 │    │                 │    │                 │
│ • Field metadata│    │ • Question types│    │ • Representative│    │ • Final insights│
│ • Business rules│    │ • Approach ID   │    │ • Priority score│    │ • Actionable    │
│ • Data quality  │    │ • Machine output│    │ • Volume filter │    │ • recommendations│
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Project Structure

```
llm_scenario_test/
├── data/
│   ├── curated/                    # Location data (49 rows)
│   ├── org/                        # Organization benchmarks (1 row)
│   └── global/                     # Global benchmarks (1 row)
├── agents/
│   ├── schema_discovery.py         # Stage 1: Schema & metadata
│   ├── question_analyzer.py        # Stage 2: Question type identification
│   ├── data_filter.py             # Stage 3: Efficient data selection
│   └── output_generator.py         # Stage 4: Human-readable results
├── prompts/
│   ├── enhanced_guidance/          # Business context prompts
│   │   ├── schema_discovery.md
│   │   ├── question_analysis.md
│   │   ├── data_filtering.md
│   │   └── output_generation.md
│   └── minimal_guidance.md         # Basic prompt for benchmarking
├── scripts/
│   ├── enhanced_guidance_benchmark.py  # Minimal vs Enhanced comparison
│   └── multi_prompt_agent.py           # Full pipeline execution
├── results/
│   ├── condition_3/                # Previous test results
│   ├── enhanced_guidance/          # Benchmark results
│   └── multi_prompt/               # Agent pipeline outputs
└── config/
    ├── agent_config.yaml           # Multi-prompt agent settings
    └── claude_api_config.py        # API configuration
```

## Development Phases

### Phase 1: Enhanced Guidance Benchmarking ✅
- **Condition 3 Complete**: 49 locations with minimal guidance
- **Next**: Enhanced guidance with org/global table benchmarks
- **Goal**: Establish baseline performance improvements

### Phase 2: Multi-Prompt Agent Development 🔄
- **Stage 1**: Schema discovery with business context
- **Stage 2**: Question type identification and approach selection
- **Stage 3**: Intelligent data filtering (representative + priority + volume)
- **Stage 4**: Human-readable output generation

### Phase 3: Production Optimization 📋
- Performance tuning and cost optimization
- Advanced filtering algorithms
- Extended question type support

## Key Features

### Enhanced Guidance System
- **Business Context**: Rich metadata and field descriptions
- **Question Types**: Automated identification of supported analysis types
- **Data Quality**: Intelligent handling of missing/incomplete data

### Intelligent Data Filtering
- **Representative Selection**: Choose rows that best represent question characteristics
- **Priority Scoring**: Use business-defined priority metrics
- **Volume Balancing**: Include high-sales locations for comprehensive analysis
- **Efficiency**: Minimize token usage while maximizing insight quality

### Machine-Readable Intermediate Output
- Structured data exchange between pipeline stages
- Consistent format for downstream processing
- Audit trail for decision-making logic

## Current Status

✅ **Condition 3**: Curated data + minimal guidance (49 locations)
🔄 **Enhanced Guidance Benchmark**: Org/global table integration
📋 **Multi-Prompt Agent**: Pipeline architecture defined, implementation pending

## Configuration

See `config/agent_config.yaml` for:
- Pipeline stage settings
- Token limits per stage
- Data filtering parameters
- Output format specifications