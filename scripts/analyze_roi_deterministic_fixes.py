#!/usr/bin/env python3
"""
TASK 4.3 PART 4: ROI Analysis for Deterministic Fixes
Identify which fixes will have highest return on investment
"""

import json
import sys
sys.path.insert(0, '.')

# Based on baseline analysis:
# - Enterprise: 90.5% (19/21 correct) - very good, low ROI for fixes
# - Risk tolerance: 100% (8/8) - perfect, zero ROI
# - Water availability: 66.7% (2/3) - good enough
# - Budget/rupees: 52.9% (9/17 correct) - 8 failures, medium frequency
# - Experience level: 33.3% (1/3) - small dataset, but high failure rate
# - Land size: 12.5% (1/8) - 7 failures, HIGH frequency, critical
# - Location: 0% (0 or all failed) - if in dataset, critical
# - Time availability: 0% (not in dataset)
# - Willingness_to_learn: 0% (not in dataset)

ROI_ANALYSIS = {
    "analysis_date": "2026-08-22",
    "baseline_entity_accuracy": 0.468,
    "total_failures_detected": 32,  # Roughly estimated from metrics
    
    "fixes_by_roi_priority": [
        {
            "rank": 1,
            "entity_type": "land_size_hectares",
            "current_accuracy": 0.125,
            "current_failures": 7,  # Out of 8 test cases
            "failure_rate": 87.5,
            "estimated_fix_complexity": 2,  # Low - just unit conversion logic
            "estimated_impact": 0.50,  # 12.5% → 62.5% (+50 points, very high)
            "root_cause": "Unit conversion (acres↔hectares) broken or missing edge cases",
            "estimated_roi_score": (7 * 50) / 2,  # (Frequency × Impact) / Complexity = 175
            "fix_strategy": [
                "1. Verify acre-to-hectare conversion constant (1 acre = 0.404686 hectares)",
                "2. Handle decimal hectares (e.g., 1.5 acres → 0.607 hectares)",
                "3. Add tests for common values: 0.5, 1, 1.5, 2, 2.5, 3, 5 hectares",
                "4. Test both 'hectare' and 'हेक्टेयर' variants"
            ],
            "estimated_time_minutes": 15,
            "implementation_notes": "High confidence fix - purely mathematical conversion"
        },
        {
            "rank": 2,
            "entity_type": "location",
            "current_accuracy": 0.0,
            "current_failures": "unknown (0% means either not in dataset or all failed)",
            "failure_rate": "100% (if in dataset)",
            "estimated_fix_complexity": 3,  # Medium - requires district mapping
            "estimated_impact": 0.40,  # Could improve significantly if many queries
            "root_cause": "District mapping incomplete; may return state instead of district",
            "estimated_roi_score": "high_but_uncertain",  # Depends on frequency
            "fix_strategy": [
                "1. Check if location entity is even in farmer_queries.jsonl",
                "2. If present: Create comprehensive Marathi↔English district mapping",
                "3. Handle Marathi variations (नाशिक vs नाशीक)",
                "4. Verify mapper returns district, not state"
            ],
            "estimated_time_minutes": 30,
            "implementation_notes": "HIGH UNCERTAINTY: Need to verify location is in dataset first"
        },
        {
            "rank": 3,
            "entity_type": "budget_rupees",
            "current_accuracy": 0.529,
            "current_failures": 8,  # Out of 17
            "failure_rate": 47.1,
            "estimated_fix_complexity": 2,  # Low - pattern matching
            "estimated_impact": 0.25,  # 52.9% → 77.9% (+25 points)
            "root_cause": "Range/approximation patterns missing (e.g., '50-100k', 'around 50k')",
            "estimated_roi_score": (8 * 25) / 2,  # = 100
            "fix_strategy": [
                "1. Add patterns for ranges: '50-100k', '50 to 100k'",
                "2. Handle approximations: 'around', 'लगभग', 'करीब'",
                "3. Extract boundaries and compute midpoint or range",
                "4. Test with Marathi number words (पन्नास हजार)"
            ],
            "estimated_time_minutes": 20,
            "implementation_notes": "Good ROI; relatively straightforward pattern extension"
        },
        {
            "rank": 4,
            "entity_type": "experience_level",
            "current_accuracy": 0.333,
            "current_failures": 2,  # Out of 3 (small dataset)
            "failure_rate": 66.7,
            "estimated_fix_complexity": 2,  # Low - keyword + years
            "estimated_impact": 0.40,  # 33.3% → 73.3% (+40 points)
            "root_cause": "Year-based detection unreliable; thresholds unclear",
            "estimated_roi_score": (2 * 40) / 2,  # = 40 (but small frequency)
            "fix_strategy": [
                "1. Clarify thresholds: Beginner (<2yr), Intermediate (2-10yr), Expert (>10yr)",
                "2. Handle Hindi variations: 'अनुभव', 'अनुभवी', 'नया', 'नई'",
                "3. Look for year indicators: '1 year', '5 साल', '10 वर्ष'",
                "4. Fallback: If no years mentioned, use keywords only"
            ],
            "estimated_time_minutes": 15,
            "implementation_notes": "Small dataset (3 samples) means lower confidence in gain estimates"
        },
        {
            "rank": 5,
            "entity_type": "enterprise",
            "current_accuracy": 0.905,
            "current_failures": 2,  # Out of 21
            "failure_rate": 9.5,
            "estimated_fix_complexity": 3,  # Medium - requires new keyword/spelling variants
            "estimated_impact": 0.08,  # 90.5% → 98.5% (+8 points, diminishing returns)
            "root_cause": "Rare business types or spelling variants not covered",
            "estimated_roi_score": (2 * 8) / 3,  # = 5.3 (low ROI)
            "fix_strategy": [
                "1. Analyze the 2 failures - likely rare business types",
                "2. Add missing keywords or Marathi/Hindi variants",
                "3. Do NOT add complex rules; keep keyword matching simple"
            ],
            "estimated_time_minutes": 10,
            "implementation_notes": "LOW ROI - already high accuracy; diminishing returns; risk of regex explosion"
        }
    ],
    
    "critical_questions_before_implementation": [
        "Q1: Is 'location' entity actually in the farmer_queries.jsonl evaluation set?",
        "    → If NO: Skip location fixes entirely (zero impact)",
        "    → If YES: Location becomes rank 2 priority",
        "",
        "Q2: Are the current test failures representative of real-world queries?",
        "    → If test set is skewed toward edge cases: Impact estimates may be pessimistic",
        "    → If test set is skewed toward easy cases: Impact estimates may be optimistic",
        "",
        "Q3: What is the cost of false positives?",
        "    → If false positives are harmful: Be conservative in normalization",
        "    → If false positives are benign: Can be more aggressive"
    ],
    
    "stopping_criteria": {
        "stop_if_improvement_less_than": "2-3 percentage points per fix",
        "stop_if_special_cases_exceed": "5-10 per entity type (regex explosion risk)",
        "stop_if_false_positives_increase": "More than 5% of non-failures become false positives",
        "stop_if_complexity_becomes_high": "Normalizer code becomes hard to understand/maintain"
    },
    
    "summary": {
        "recommended_fix_order": [
            "1. land_size_hectares (ROI=175, HIGH CONFIDENCE)",
            "2. Check location dataset presence (HIGH IMPACT IF PRESENT)",
            "3. budget_rupees (ROI=100, MEDIUM CONFIDENCE)",
            "4. experience_level (ROI=40, but small sample size)",
            "5. Skip enterprise (ROI=5.3, DIMINISHING RETURNS)"
        ],
        "estimated_total_effort": "45-60 minutes",
        "estimated_accuracy_improvement": "5-15% total (cumulative across fixes)",
        "confidence_level": "MEDIUM (small test dataset, need real-world validation)"
    }
}

# Save analysis
with open('data/evaluation/task_4_3_roi_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(ROI_ANALYSIS, f, ensure_ascii=False, indent=2)

print("="*80)
print("TASK 4.3 PART 4: ROI ANALYSIS FOR DETERMINISTIC FIXES")
print("="*80)
print()
print(f"Baseline Entity Accuracy: {ROI_ANALYSIS['baseline_entity_accuracy']*100:.1f}%")
print(f"Total Estimated Failures: {ROI_ANALYSIS['total_failures_detected']}")
print()

for fix in ROI_ANALYSIS['fixes_by_roi_priority']:
    print(f"\n#{fix['rank']}: {fix['entity_type'].upper()}")
    print(f"   Current: {fix['current_accuracy']*100:.1f}% | Failures: {fix['current_failures']}")
    print(f"   ROI Score: {fix['estimated_roi_score']} | Complexity: {fix['estimated_fix_complexity']}/5")
    print(f"   Root Cause: {fix['root_cause']}")
    print(f"   Est. Impact: +{fix['estimated_impact']*100:.0f} percentage points")
    print(f"   Est. Time: {fix['estimated_time_minutes']} min")

print("\n" + "="*80)
print("CRITICAL QUESTIONS TO ANSWER FIRST:")
print("="*80)
for q in ROI_ANALYSIS['critical_questions_before_implementation']:
    print(q)

print("\n" + "="*80)
print("RECOMMENDED FIX ORDER:")
print("="*80)
for line in ROI_ANALYSIS['summary']['recommended_fix_order']:
    print(line)

print("\n" + "="*80)
print("STOPPING CRITERIA (DO NOT CONTINUE IF):")
print("="*80)
for criterion, value in ROI_ANALYSIS['stopping_criteria'].items():
    print(f"- {criterion}: {value}")

print("\n" + "="*80)
print(f"Analysis saved to: data/evaluation/task_4_3_roi_analysis.json")
print("="*80)
