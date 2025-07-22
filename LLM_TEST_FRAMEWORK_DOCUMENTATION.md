# LLM Testing Framework Documentation

**[Last updated: 2025-07-21]**

This documentation describes the 2x2 LLM test matrix (curated vs. source, minimal vs. enhanced guidance), using version-controlled `mart_llm_curated_*` and `mart_llm_source_*` tables. All tables are filtered to a single hardcoded org and optimized for LLM interpretability and context window size.

---

## Retail Location Intelligence: Source vs. Curated Data Analysis

### Executive Summary

This framework tests whether Large Language Models (LLMs) perform better analyzing **granular source data** versus **pre-computed executive insights** for the core business question: *"Which locations need immediate attention and what specific actions should be taken?"*

---

## Test Design Overview

**Core Question:** *"Which locations need immediate attention and what specific actions should be taken?"*

**2x2 Test Matrix:**
- **Data Type:** Source (transactional) vs Curated (executive summaries)  
- **Guidance:** Minimal vs Enhanced (business context + schema)

**Implementation Phases:**
1. **Phase 1:** Curated + Minimal (baseline performance)
2. **Phase 2:** Source + Minimal (analytical capability test)
3. **Phase 3:** Enhanced Guidance (context impact comparison)

---

## Dataset Specifications

### Source Data Scenario (4 Tables)
*"Raw ingredients requiring LLM analysis and aggregation"*

#### 1. `mart_llm_source_transactions_compact`
**Purpose:** Transaction-level data with customer and location context  
**Base Model:** `int_salesheader_unified`  
**Key Features:**
- Transaction dates and financial metrics (total, subtotal, tax)
- Location context (name, city, state, org)
- Customer classification (Registered vs Guest)
- Payment context (type, status)
- Temporal patterns (day of week, hour)

**Constraints:** Single org, most recent completed week, 10K transaction limit

#### 2. `mart_llm_source_line_items_compact`
**Purpose:** Product-level purchase details  
**Base Model:** `int_salesitem`  
**Key Features:**
- Product names and quantities
- Pricing details (unit price, line total, tax)
- Location context
- Temporal patterns

**Constraints:** Single org, most recent completed week, 25K line item limit

#### 3. `mart_llm_source_locations_compact`
**Purpose:** Location master data with geographic context  
**Base Model:** `int_location_enriched`  
**Key Features:**
- Location names and geographic data (city, state, coordinates)
- Organizational hierarchy
- Data quality indicators (Google Maps enhanced vs original)
- Timezone information

**Constraints:** Single org only

#### 4. `mart_llm_source_weekly_sales_compact`
**Purpose:** Weekly aggregated sales by product/location  
**Base Model:** `int_weekly_sales_by_product_by_location`  
**Key Features:**
- Sales metrics (before/after tax, volume)
- Transaction counts
- Calculated averages (price per unit, sales per transaction)

**Constraints:** Single org, most recent completed week, 15K product-location combinations

---

### Curated Data Scenario (3 Tables)
*"Executive-ready insights with pre-computed analytics"*

#### 1. `mart_llm_curated_location_compact`
**Purpose:** Location-level executive insights and recommendations  
**Base Model:** `mart_ai_weekly_demo_extended_with_recs_5`  
**Key Features:**

**Sales Performance:**
- Current week sales, daily averages, transaction counts
- Trend metrics: WoW, short-term (3w), long-term (48w) percentage changes
- Health status classification and confidence scores

**Customer Intelligence:**
- Behavioral segmentation: New/Onetime, Less-than-Weekly, Weekly-or-More
- Customer counts, spend patterns, and retention metrics
- App usage percentages

**Product Intelligence:**
- Top 5 category performance with trend indicators
- Product recommendations (top adds with scores)
- Drop candidates for optimization

**Executive Context:**
- Priority scoring (lower = higher priority)
- Urgency flags (urgent, growing, declining locations)
- Action classifications and trend directions
- Executive narratives for recommendations

#### 2. `mart_llm_curated_org_compact`
**Purpose:** Organization-level aggregated metrics  
**Base Model:** `mart_ai_weekly_demo_org_enhanced_5`  
**Key Features:**
- Aggregated customer segment metrics (averages and totals)
- Customer mix percentages and engagement rates
- Retention trends and segment concentration
- Organization-wide performance indicators

#### 3. `mart_llm_curated_global_compact`
**Purpose:** Global-level summary metrics  
**Base Model:** `mart_ai_weekly_demo_global_enhanced_5`  
**Key Features:**
- Global customer segment performance
- System-wide retention and engagement trends
- Benchmark metrics for comparison

---

## Business Logic Deep Dive

### Location Health Classification System
**Source:** `int_location_health_metrics.sql`

**Trend Analysis Framework:**
- **Week-over-Week (WoW):** Current vs previous week daily sales
- **Short-term:** Current vs recent 3-week average daily sales  
- **Long-term:** Recent 3-week average vs 48-week baseline daily sales

**Health Status Categories:**
- `GROWING`: Short-term > long-term by 10%+
- `DECLINING`: Short-term < long-term by 10%+
- `RECOVERING`: Declining long-term but improving short-term
- `STABLE`: Within 10% variance

**Action Classifications:**
- `CRISIS_INTERVENTION`: Weak across all timeframes
- `PERFORMANCE_RECOVERY`: Short-term decline, stable long-term
- `GROWTH_ACCELERATION`: Strong performance across timeframes
- `GROWTH_OPTIMIZATION`: Growing short-term, stable long-term
- `OPPORTUNITY_DEVELOPMENT`: Stable short-term, growing long-term
- `INVESTIGATE_ANOMALY`: Conflicting trend signals

**Confidence Scoring (0-100):**
- 90: All trends aligned (strong signal)
- 75: Short and long-term aligned
- 60: Only short-term signal
- 30: Conflicting signals
- 45: Default/unclear

### Customer Segmentation Logic
**Source:** `int_customer_segment_metrics_weekly_v4.sql`

**Behavioral Segments (based on prior 52-week purchase frequency):**
- **NEW_OR_ONETIME:** New customers or single purchase in prior year
- **LESS_THAN_WEEKLY:** Occasional purchasers (< 1x/week average)
- **WEEKLY_OR_MORE:** Frequent customers (≥ 1x/week average)

**Key Metrics per Segment:**
- **Active vs Known Customers:** Distinguishes current week purchasers from total database
- **Spend Patterns:** Average spend per active customer (not diluted by inactive)
- **Retention Analysis:** 12-week cohort retention with 3-week trend averaging
- **App Usage:** Percentage using mobile app by segment

**Retention Methodology:**
- **12-week Cohort:** Customers from 12 weeks ago tracked for return behavior
- **3-week Baseline:** Average of weeks 2-4 prior for trend comparison
- **Trend Calculation:** Percent change from baseline to current retention rate

### Product Recommendation Engine
**Source:** `int_location_product_replacements_wide_clean.sql`

**Recommendation Logic:**
- **Seed Products:** Top-performing existing products (best composite rank)
- **Add Recommendations:** NEW_OPPORTUNITY products with highest scores
- **Drop Candidates:** Worst-performing existing products (lowest composite rank)
- **Narrative Generation:** Executive summary of top 3 adds and drops

**Scoring Framework:**
- **Composite Rank:** Multi-factor scoring including sales performance, trend, and opportunity
- **Recommendation Score:** Predicted uplift potential for new products
- **Executive Format:** Concise add/drop lists for operational decision-making

---

## Data Lineage and Quality

### Shared Foundation
Both source and curated scenarios use identical intermediate models:
- `int_salesheader_unified` → Transaction enrichment
- `int_salesitem` → Product-level details  
- `int_location_enriched` → Geographic and organizational context
- `int_weekly_sales_by_product_by_location` → Aggregated performance

### Data Constraints
**Temporal:** Most recent completed week (Sunday-Saturday)  
**Organizational:** Single org (`'c01703f255da85493396548af84ff43b'`)  
**Volume Management:** Row limits for 200K token context window  
**Quality:** Google Maps enhanced location data where available

### Token Optimization
- **ID Removal:** All hash/UUID columns removed for human-readable identifiers
- **Decimal Precision:** Rounded to 1-2 decimal places
- **Essential Fields:** Only actionable metrics included
- **Narrative Focus:** Concise executive summaries

---

## Test Implementation Guide

### Condition 1: Source + Minimal Guidance
**Data:** 4 source tables with transactional detail  
**Prompt:** Basic question with minimal business context  
**Tests:** LLM's ability to aggregate, analyze, and prioritize from raw data

### Condition 2: Source + Enhanced Guidance  
**Data:** Same 4 source tables  
**Prompt:** Detailed business context, metric definitions, and analysis framework  
**Tests:** Impact of guidance on source data analysis quality

### Condition 3: Curated + Minimal Guidance
**Data:** 3 curated tables with pre-computed insights  
**Prompt:** Basic question with minimal business context  
**Tests:** Baseline performance with executive-ready data

### Condition 4: Curated + Enhanced Guidance
**Data:** Same 3 curated tables  
**Prompt:** Detailed business context and metric explanations  
**Tests:** Maximum performance potential with both curated data and guidance

### Success Metrics
- **Accuracy:** Correct identification of priority locations
- **Actionability:** Specific, implementable recommendations
- **Business Alignment:** Understanding of retail operations context
- **Efficiency:** Speed and token usage for analysis
- **Consistency:** Reproducible results across test runs

---

## Expected Outcomes

### Hypothesis Testing
1. **Curated data** will produce more accurate business insights
2. **Enhanced guidance** will improve performance across both data types
3. **Source data** may reveal novel patterns missed by pre-processing
4. **Token efficiency** will favor curated data significantly

### Business Value
- **Optimal LLM deployment strategy** for retail analytics
- **Data preparation guidelines** for AI-driven insights
- **Context window optimization** for complex business analysis
- **Executive decision support** framework validation

This framework provides a rigorous foundation for comparing LLM performance across data preparation strategies while maintaining real-world business relevance and operational applicability.
