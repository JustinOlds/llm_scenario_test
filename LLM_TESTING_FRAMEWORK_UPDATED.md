# LLM Testing Framework: Data vs Guidance Optimization

**[Last updated: 2025-07-21 - Final Version with Schema Discovery Integration]**

## Key Insights & Design Decisions

**From Data Engineering Analysis:**
- **Production Data Foundation:** All test tables use the same intermediate models and business logic as executive dashboards and weekly reviews
- **Consistent Naming Convention:** Double underscore separation (e.g., `weekly_or_more__avg_purchase_value`) for LLM interpretability
- **Token Optimization:** Human-readable columns, no IDs/hashes, rounded decimals, essential fields only
- **Business Alignment:** Hardcoded org filter ensures consistent scope; metrics directly used by retail operators.

**From Schema Discovery Engine:**
- **Intelligent Data Reduction:** Progressive strategies (temporal → location → column importance) with business logic
- **Scenario-Aware Context:** Schema discovery provided only in enhanced guidance scenarios, not minimal
- **Column Profiling:** Business categorization (identifier, metric, date, categorical, text) with importance scoring
- **Token Budget Management:** Configurable limits with overflow handling and reduction transparency

## Project Overview

This framework evaluates Claude API performance across different data preparation and guidance strategies to optimize operator insights for retail location management using our production dbt-snowflake data models.

## Test Design

**Core Question:** *"Which locations need immediate attention and what specific actions should be taken?"*

**2x2 Test Matrix:**
- **Data Type:** Source (transactional) vs Curated (executive summaries)  
- **Guidance:** Minimal vs Enhanced (business context + schema)

## Implementation Phases with Schema Discovery Integration

### Phase 1: Condition 3 (Curated + Minimal)
- **Data:** Processed location-level executive insights (~45K tokens)
- **Guidance:** Minimal prompt only
- **Schema Context:** None provided
- **Objective:** Establish baseline LLM performance with executive-ready data

### Phase 2: Condition 1 (Source + Minimal) 
- **Data:** Raw transactional data with intelligent reduction (~180K tokens)
- **Guidance:** Minimal prompt only
- **Schema Context:** None provided (data reduction applied silently)
- **Objective:** Test Claude's analytical capabilities on raw data

### Phase 3: Condition 2 (Source + Enhanced Guidance)
- **Data:** Same reduced source data as Condition 1
- **Guidance:** Enhanced prompts with business context
- **Schema Context:** Full schema discovery object provided
- **Objective:** Measure impact of business context on source data analysis

### Phase 4: Condition 4 (Curated + Enhanced Guidance)
- **Data:** Same curated data as Condition 3
- **Guidance:** Enhanced prompts with business context
- **Schema Context:** Curated data schema discovery object
- **Objective:** Maximum performance potential with both curated data and guidance

## Project Structure

```
llm_testing_framework/
├── README.md                          # This file
├── data/
│   ├── source/                        # Raw transactional data
│   │   ├── transactions_compact.csv   # 10K transactions (most recent week)
│   │   ├── line_items_compact.csv     # 25K line items (most recent week)
│   │   ├── locations_compact.csv      # Location master data
│   │   └── weekly_sales_compact.csv   # 15K product-location combinations
│   ├── curated/                       # Executive-ready insights  
│   │   ├── location_insights.csv      # ~2K location-weeks (last 4 weeks)
│   │   ├── org_summary.csv           # Organization-level aggregates
│   │   └── global_metrics.csv        # Global benchmarks
│   └── sample_responses/              # Expected outputs for validation
├── prompts/
│   ├── minimal_guidance.md            # Basic prompt templates
│   ├── enhanced_guidance.md           # Business context prompts
│   └── question_templates.md          # Test question variations
├── scripts/
│   ├── condition_3_test.py           # Curated + Minimal (Phase 1)
│   ├── condition_1_test.py           # Source + Minimal (Phase 2)
│   ├── run_all_conditions.py         # Full 2x2 test suite
│   └── response_analyzer.py          # Output quality assessment
├── results/
│   ├── condition_3/                  # Phase 1 outputs
│   ├── condition_1/                  # Phase 2 outputs
│   ├── condition_2/                  # Enhanced guidance results
│   ├── condition_4/                  # Full context results
│   └── comparison_analysis.md        # Cross-condition insights
└── config/
    ├── claude_api_config.py          # API settings and limits
    ├── test_parameters.yaml          # Test configuration
    └── evaluation_criteria.md        # Success metrics definition
```

## Data Specifications with Intelligent Reduction

### Source Data Scenario (Condition 1 & 2)
**Powered by Schema Discovery Engine (`schema_discovery_adaptive_reduction.py`)**
**Tables:** 4 source tables from `mart_llm_source_*` models
- **mart_llm_source_transactions_compact:** 10K transactions (most recent completed week)
- **mart_llm_source_line_items_compact:** 25K line items (most recent completed week)  
- **mart_llm_source_locations_compact:** Location master data (single org)
- **mart_llm_source_weekly_sales_compact:** 15K product-location combinations (most recent week)

**Intelligent Token Management:**
- **Target:** 180K tokens (20K buffer for prompts)
- **Schema Discovery Engine:** Automatic profiling and reduction
- **Progressive Reduction Strategy:**
  1. **Temporal Reduction:** Most recent 3 days (43% of weekly data)
  2. **Location Reduction:** Top 50 locations by sales volume
  3. **Column Reduction:** Keep 75% of most important columns (business logic)
- **Business Intelligence:** Column importance scoring (1-5) based on retail KPIs
- **Transparency:** Full logging of reductions applied

**Key Fields:**
- **Transactions:** date, location_name, total_amount, customer_type, payment_type
- **Line Items:** product_name, quantity, unit_price, line_total
- **Locations:** location_name, city, state, org_name, coordinates
- **Weekly Sales:** location_name, product_name, sales_after_tax, quantity_sold

### Curated Data Scenario (Condition 3 & 4)  
**Tables:** 3 curated tables from `mart_llm_curated_*` models
- **mart_llm_curated_location_compact:** ~2K location-weeks (last 4 weeks, limited to 2K rows)
- **mart_llm_curated_org_compact:** Organization-level aggregates (last 4 weeks)
- **mart_llm_curated_global_compact:** Global benchmarks (last 4 weeks)

**Token Management:**
- **Estimated Total:** ~45K tokens (well within limits)
- **Key Optimization:** Pre-computed insights, rounded decimals, human-readable columns

**Key Fields:**
- **Location:** priority_score, health_status, sales trends, customer segments, product recommendations
- **Org:** aggregated performance, location counts by health category
- **Global:** benchmark metrics, retention trends

## Data Quality & Constraints

### Shared Foundation
Both scenarios use identical intermediate models and business logic:
- **Single Organization:** Hardcoded to `'c01703f255da85493396548af84ff43b'` for consistency
- **Temporal Scope:** Most recent completed week (Sunday-Saturday)
- **Data Quality:** Google Maps enhanced locations, validated transactions only
- **Human-Readable:** All ID/hash columns removed, descriptive names used

### Token Optimization Features
- **Decimal Precision:** Rounded to 1-2 decimal places
- **Integer Casting:** Whole number counts cast as integers
- **Essential Fields Only:** High-token JSON and narrative fields excluded from source scenario
- **Consistent Naming:** Double underscore convention for segment/metric clarity

## Complete Implementation Guide

### Condition 3: Curated + Minimal
```python
# condition_3_test.py
import pandas as pd
from schema_discovery_adaptive_reduction import SchemaDiscoveryEngine

# Load curated data (no reduction needed - already optimized)
curated_tables = {
    'location_insights': pd.read_csv('data/curated/location_insights.csv'),
    'org_summary': pd.read_csv('data/curated/org_summary.csv'),
    'global_metrics': pd.read_csv('data/curated/global_metrics.csv')
}

# Estimate tokens (should be ~45K)
engine = SchemaDiscoveryEngine()
total_tokens = sum(engine.estimate_token_count(df) for df in curated_tables.values())

# Apply minimal prompt only (no schema context)
response = claude_api_call(curated_tables, minimal_prompt_template)
```

### Condition 1: Source + Minimal
```python
# condition_1_test.py
from schema_discovery_adaptive_reduction import prepare_source_data_minimal_guidance

# Load source data
source_tables = {
    'transactions': pd.read_csv('data/source/transactions_compact.csv'),
    'line_items': pd.read_csv('data/source/line_items_compact.csv'),
    'locations': pd.read_csv('data/source/locations_compact.csv'),
    'weekly_sales': pd.read_csv('data/source/weekly_sales_compact.csv')
}

# Apply intelligent reduction (no schema context provided)
reduced_tables, total_tokens = prepare_source_data_minimal_guidance(source_tables)

# Apply minimal prompt only
response = claude_api_call(reduced_tables, minimal_prompt_template)
```

### Condition 2: Source + Enhanced
```python
# condition_2_test.py
from schema_discovery_adaptive_reduction import prepare_source_data_enhanced_guidance

# Load source data with business context
table_contexts = {
    'transactions': 'Transaction-level data with customer and payment context for retail analysis',
    'line_items': 'Product-level purchase details with pricing and quantity information',
    'locations': 'Location master data with geographic and organizational context',
    'weekly_sales': 'Weekly aggregated sales performance by product and location'
}

# Apply intelligent reduction WITH schema context
reduced_tables, schema_context, total_tokens = prepare_source_data_enhanced_guidance(
    source_tables, table_contexts
)

# Apply enhanced prompt with schema discovery context
response = claude_api_call(reduced_tables, enhanced_prompt_template, schema_context)
```

### Condition 4: Curated + Enhanced
```python
# condition_4_test.py
from schema_discovery_adaptive_reduction import prepare_curated_data_enhanced_guidance

curated_contexts = {
    'location_insights': 'Executive-ready location performance with recommendations',
    'org_summary': 'Organization-level aggregated metrics and trends',
    'global_metrics': 'Global benchmarks and system-wide performance indicators'
}

# Apply enhanced guidance with schema context
curated_tables, schema_context, total_tokens = prepare_curated_data_enhanced_guidance(
    curated_tables, curated_contexts
)

# Apply enhanced prompt with schema discovery context
response = claude_api_call(curated_tables, enhanced_prompt_template, schema_context)
```

### Success Metrics
- **Accuracy:** Correctly identifies high-priority locations using priority_score
- **Actionability:** Leverages product recommendations and customer segment insights
- **Efficiency:** Response time and token consumption
- **Business Alignment:** Uses health_status, trend_category, and executive context

### Expected Output Structure
```json
{
  "urgent_locations": [
    {
      "location_name": "Downtown Store",
      "priority_score": 15,
      "health_status": "critical_attention", 
      "priority_reason": "Sales down 15% WoW, declining customer retention",
      "specific_actions": ["Review top_add_recommendation: Energy Drinks", "Address weekly_or_more customer segment decline"]
    }
  ],
  "total_locations_analyzed": 150,
  "data_freshness": "4 days since report",
  "response_time": "3.2s",
  "token_usage": 38500
}
```

## Phase 2 Implementation: Condition 1

### Objective
Test Claude's analytical capabilities with raw transactional data requiring aggregation.

### Data Loading Strategy with Token Management
```python
# condition_1_test.py should:
1. Load all 4 source tables
2. Check estimated token count
3. If > 180K tokens:
   a. Limit transactions to last 3 days
   b. If still over, limit to top 50 locations by volume
   c. If still over, sample 50% of line items
4. Apply minimal prompt template
5. Send API call to Claude
6. Save structured response with data reduction notes
```

### Schema Discovery Engine Integration

**Scenario-Specific Data Preparation Functions:**

```python
# Condition 1: Source + Minimal (NO schema context)
from schema_discovery_adaptive_reduction import prepare_source_data_minimal_guidance

reduced_tables, total_tokens = prepare_source_data_minimal_guidance({
    'transactions': transactions_df,
    'line_items': line_items_df,
    'locations': locations_df,
    'weekly_sales': weekly_sales_df
})
# Returns: Reduced data only, no schema discovery context

# Condition 2: Source + Enhanced (WITH schema context)
from schema_discovery_adaptive_reduction import prepare_source_data_enhanced_guidance

table_contexts = {
    'transactions': 'Transaction-level data with customer and payment context',
    'line_items': 'Product-level purchase details with pricing',
    'locations': 'Location master data with geographic context',
    'weekly_sales': 'Weekly aggregated sales by product/location'
}

reduced_tables, schema_context, total_tokens = prepare_source_data_enhanced_guidance(
    tables, table_contexts
)
# Returns: Reduced data + rich schema discovery object
```

**Schema Discovery Context Structure:**
```json
{
  "data_overview": {
    "total_tables": 4,
    "total_estimated_tokens": 165000,
    "reductions_applied": ["temporal_3_days", "top50_locations"]
  },
  "tables": {
    "transactions": {
      "business_purpose": "Transaction-level data with customer context",
      "dimensions": {"rows": 4200, "columns": 12, "estimated_tokens": 85000},
      "reduction_applied": "temporal_3_days_and_top50_locations",
      "column_guide": {
        "identifier": [{"name": "location_name", "sample_values": ["Downtown Store"], "importance": 5}],
        "metric": [{"name": "total_amount", "sample_values": [15.99, 23.45], "importance": 5}]
      }
    }
  }
}
```

## Implementation Guidelines for LLM System Designer

### Critical Design Principles
1. **Schema Discovery Integration:** Use provided engine for all data preparation
2. **Scenario Separation:** Never provide schema context in minimal guidance scenarios
3. **Token Budget Management:** Always check estimated tokens before API calls
4. **Business Logic Preservation:** Reduction strategies maintain analytical integrity
5. **Transparency:** Log all reductions applied for result interpretation
6. **Reproducibility:** Use fixed random seeds for consistent test results

### Data Pipeline Architecture
```
CSV Data → Schema Discovery Engine → Scenario-Specific Preparation → Claude API
                    ↓
            [Column Profiling]
            [Token Estimation]
            [Business Categorization]
            [Intelligent Reduction]
                    ↓
        [Minimal: Data Only] vs [Enhanced: Data + Schema Context]
```

### Key Files for Implementation
- **`schema_discovery_adaptive_reduction.py`** - Core engine (provided)
- **Data Sources:** `mart_llm_curated_*` and `mart_llm_source_*` CSV exports
- **Business Context:** Column importance mapping and reduction strategies built-in

### API Configuration
- Use Claude 3.5 Sonnet for cost efficiency
- Set conservative rate limits (respect 200K token context window)
- Implement retry logic for temporary failures
- Log all token usage for cost tracking
- Monitor for context window overflow

## Expected Business Value & Test Outcomes

### Primary Hypotheses
1. **Curated data superiority:** Executive-ready insights will produce more accurate, actionable recommendations
2. **Enhanced guidance impact:** Business context will significantly improve performance across both data types
3. **Novel pattern discovery:** Source data may reveal insights missed by pre-processing pipelines
4. **Token efficiency advantage:** Curated data will deliver superior ROI (45K vs 180K tokens)
5. **Schema discovery value:** Column profiling and business context will enhance LLM understanding

### Strategic ROI Implications
- **Data Pipeline Justification:** Quantify value of continued investment in curated mart development
- **LLM Integration Strategy:** Determine optimal data preparation approach for AI-driven retail insights
- **Executive Decision Support:** Validate AI readiness for operational and strategic decision-making
- **Scalability & Cost Planning:** Understand token economics and context window optimization strategies
- **Competitive Advantage:** Establish framework for AI-enhanced retail analytics capabilities

### Success Metrics Framework
- **Accuracy:** Correct identification of priority locations using business KPIs
- **Actionability:** Specific, implementable recommendations aligned with retail operations
- **Business Alignment:** Understanding of customer segments, product recommendations, and trend analysis
- **Efficiency:** Token usage optimization and response time performance
- **Consistency:** Reproducible results across multiple test iterations
- **Context Utilization:** Effective use of schema discovery information in enhanced scenarios

## Success Criteria

The framework succeeds when it clearly demonstrates:
- Which data preparation strategy delivers superior business insights
- Whether business context significantly improves output quality  
- Optimal token allocation between data volume and guidance
- Clear ROI guidance for data pipeline vs. raw data strategies
- Practical constraints and solutions for 200K token context windows

---

---

## Handoff Summary for LLM System Designer

### What You're Getting
1. **Production Data Foundation:** 7 optimized tables (`mart_llm_*`) with consistent naming and business logic
2. **Schema Discovery Engine:** Complete Python module with intelligent data reduction and column profiling
3. **2x2 Test Framework:** Clear implementation guide for all four conditions
4. **Business Context Integration:** Retail-specific column importance and reduction strategies
5. **Token Management:** Automated overflow handling with transparency and logging

### Key Implementation Notes
- **Hardcoded Org Filter:** All data scoped to single organization for test consistency
- **Human-Readable Design:** No IDs/hashes, descriptive column names, rounded decimals
- **Schema Context Control:** Provided only in enhanced guidance scenarios (Conditions 2 & 4)
- **Progressive Reduction:** Temporal → Location → Column importance with business logic
- **Executive Alignment:** Same data used in dashboards and quarterly reviews

### Next Steps
1. Export CSV data from `mart_llm_*` dbt models
2. Integrate `schema_discovery_adaptive_reduction.py` with your test framework
3. Implement scenario-specific preparation functions
4. Design minimal vs. enhanced prompt templates
5. Execute 2x2 test matrix with consistent evaluation criteria

*This framework provides a comprehensive foundation for data-driven optimization of LLM integration strategies in retail operations, using production-grade dbt data models with intelligent schema discovery and adaptive data reduction capabilities.*
