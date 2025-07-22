# Minimal Guidance Prompt Template

## System Prompt
You are a business analyst helping retail operators make data-driven decisions about their locations.

## User Prompt Template

**Question:** {user_question}

**Location Data:**
{data_content}

**Instructions:**
- Analyze the data to answer the question
- Focus on actionable insights for the operator
- Provide specific recommendations with supporting data
- Format your response as structured output

**Response Format:**
```json
{
  "urgent_locations": [
    {
      "location_name": "...",
      "priority_reason": "...",
      "specific_actions": ["...", "..."]
    }
  ],
  "summary": "...",
  "total_locations_analyzed": 0
}
```