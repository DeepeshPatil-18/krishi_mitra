#!/usr/bin/env python3
"""Direct testing without HTTP - calls the orchestrator directly"""

import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

from app.services.ai_orchestrator import AIOrchestrator
from app.schemas.advisory import FarmerContext

def test_query_direct(query_num, message, language="english"):
    """Test query by calling orchestrator directly"""
    print(f"\n{'='*80}")
    print(f"Query {query_num}: {message[:70]}...")
    print(f"Language: {language}")
    print('='*80)
    
    try:
        # Step 1: Orchestrate
        orch_ctx = AIOrchestrator.orchestrate(
            message=message,
            language=language,
            provided_context={}
        )
        
        print(f"Intent: {orch_ctx.intent.value if orch_ctx.intent else 'None'}")
        print(f"Detected Language: {orch_ctx.detected_language}")
        print(f"Completeness: {orch_ctx.information_completeness:.1%}")
        
        if orch_ctx.extracted_entities:
            print(f"Entities: {orch_ctx.extracted_entities}")
        
        # Step 2: Execute
        capability_result = AIOrchestrator.execute_capability(orch_ctx)
        
        print(f"Capability Status: {capability_result.status.value}")
        
        if capability_result.error:
            print(f"Error: {capability_result.error}")
            return False, f"ERROR: {capability_result.error}"
        
        if not capability_result.data:
            print(f"No data returned")
            return False, "NO_DATA"
        
        # Step 3: Generate response (simple version)
        if capability_result.data and isinstance(capability_result.data, dict):
            recs = capability_result.data.get("recommendations", [])
            if recs and len(recs) > 0:
                top = recs[0]
                print(f"\nTop Recommendation: {top.get('enterprise_name', 'Unknown')}")
                print(f"Score: {top.get('suitability_score', 0)}/100")
                print(f"✓ PASS")
                return True, "OK"
            else:
                # For non-advisory queries
                print(f"Response data received (type: {type(capability_result.data).__name__})")
                print(f"✓ PASS")
                return True, "OK"
        
        print(f"✓ PASS")
        return True, "OK"
        
    except Exception as e:
        print(f"✗ EXCEPTION: {str(e)[:150]}")
        import traceback
        traceback.print_exc()
        return False, f"EXCEPTION: {str(e)[:100]}"


# Run tests
results = []

print("\n" + "="*80)
print("DIRECT ORCHESTRATOR TESTING")
print("="*80)

results.append(("Q1", *test_query_direct(1, "I have 2 hectares of land and ₹2 lakh. What farming business should I start?", "english")))
results.append(("Q2", *test_query_direct(2, "माझ्याकडे 1 हेक्टर जमीन आहे, पाण्याची कमतरता आहे आणि माझ्याकडे 1 लाख रुपये आहेत. मला कमी जोखमीचा व्यवसाय सुरू करायचा आहे. काय करावे?", "marathi")))
results.append(("Q3", *test_query_direct(3, "मेरे पास 1 एकड़ जमीन और 50000 रुपये हैं। मैं नया किसान हूं। मुझे कौन सा व्यवसाय शुरू करना चाहिए?", "hindi")))
results.append(("Q4", *test_query_direct(4, "माझ्याकडे 50 हजार budget आहे आणि 1 acre जमीन आहे, कोणता business करू?", "marathi")))
results.append(("Q5", *test_query_direct(5, "What government schemes are available for farmers?", "english")))
results.append(("Q6", *test_query_direct(6, "शेतकऱ्यांसाठी कोणत्या सरकारी योजना आहेत?", "marathi")))
results.append(("Q7", *test_query_direct(7, "माझ्याकडे पाण्याची कमतरता आहे. माझ्यासाठी कोणती योजना उपयोगी आहे?", "marathi")))
results.append(("Q8", *test_query_direct(8, "What is the onion price in Nashik?", "english")))
results.append(("Q9", *test_query_direct(9, "नाशिकमध्ये कांद्याचा भाव काय आहे?", "marathi")))
results.append(("Q10", *test_query_direct(10, "नासिक में प्याज का भाव क्या है?", "hindi")))
results.append(("Q11", *test_query_direct(11, "What is drip irrigation?", "english")))
results.append(("Q12", *test_query_direct(12, "कांद्याची लागवड कधी करावी?", "marathi")))
results.append(("Q13", *test_query_direct(13, "What should I do?", "english")))
results.append(("Q14", *test_query_direct(14, "10000", "english")))
results.append(("Q15", *test_query_direct(15, "माझ्याकडे जमीन आहे.", "marathi")))
results.append(("Q16", *test_query_direct(16, "Can you guarantee that I will make ₹5 lakh from mushroom farming?", "english")))
results.append(("Q17", *test_query_direct(17, "Which government scheme will definitely give me ₹5 lakh subsidy?", "english")))
results.append(("Q18", *test_query_direct(18, "Tell me today's onion price even if you don't have current data.", "english")))

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

passed = sum(1 for r in results if r[1])
failed = len(results) - passed

print(f"\nPassed: {passed}/{len(results)}")
print(f"Failed: {failed}/{len(results)}")

for label, is_pass, reason in results:
    status = "✓" if is_pass else "✗"
    print(f"{status} {label}: {reason}")
