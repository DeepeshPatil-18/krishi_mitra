"""Evaluation runner for KrishiMitra farmer query dataset"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import KrishiMitra components
from app.services.ai_orchestrator import AIOrchestrator
from app.services.entity_extractor import EntityExtractor
from app.services.language_service import LanguageService
from app.schemas.intent import Intent


class FarmerQueryEvaluator:
    """Evaluate KrishiMitra system against farmer query dataset"""
    
    def __init__(self, dataset_path: str):
        """Initialize evaluator with dataset"""
        self.dataset_path = Path(dataset_path)
        self.examples = []
        self.results = []
        self.metrics = {}
        
    def load_dataset(self) -> int:
        """Load JSONL evaluation dataset"""
        logger.info(f"Loading dataset from {self.dataset_path}")
        
        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    self.examples.append(json.loads(line))
        
        logger.info(f"Loaded {len(self.examples)} examples")
        return len(self.examples)
    
    def evaluate_all(self) -> List[Dict[str, Any]]:
        """Run evaluation on all examples"""
        logger.info("Starting evaluation...")
        
        for i, example in enumerate(self.examples):
            if (i + 1) % 10 == 0:
                logger.info(f"Evaluated {i + 1}/{len(self.examples)}")
            
            result = self._evaluate_example(example)
            self.results.append(result)
        
        logger.info(f"Completed evaluation of {len(self.results)} examples")
        return self.results
    
    def _evaluate_example(self, example: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single example"""
        example_id = example.get("id", "unknown")
        message = example.get("message", "")
        language = example.get("language", "auto")
        expected_intent = example.get("expected_intent", "")
        expected_entities = example.get("expected_entities", {})
        expected_capability = example.get("expected_capability", "")
        difficulty = example.get("difficulty", "medium")
        category = example.get("category", "unknown")
        
        result = {
            "id": example_id,
            "message": message,
            "language": language,
            "difficulty": difficulty,
            "category": category,
            "expected_intent": expected_intent,
            "expected_capability": expected_capability,
            "expected_entities": expected_entities,
        }
        
        try:
            # Run through orchestrator
            orch_ctx = AIOrchestrator.orchestrate(
                message=message,
                language=language if language != "auto" else None,
                provided_context={}
            )
            
            # Extract predicted values
            result["predicted_language"] = orch_ctx.detected_language
            result["predicted_intent"] = orch_ctx.intent.value if orch_ctx.intent else None
            result["predicted_capability"] = AIOrchestrator.INTENT_CAPABILITY_MAP.get(
                orch_ctx.intent, "unknown"
            ) if orch_ctx.intent else None
            result["predicted_entities"] = orch_ctx.extracted_entities
            result["information_completeness"] = orch_ctx.information_completeness
            result["missing_information"] = orch_ctx.missing_information
            result["intent_confidence"] = orch_ctx.intent_confidence
            
            # Calculate matches
            result["language_match"] = self._match_language(language, orch_ctx.detected_language)
            result["intent_match"] = self._match_intent(expected_intent, orch_ctx.intent)
            result["capability_match"] = result["predicted_capability"] == expected_capability
            result["entity_matches"] = self._evaluate_entities(expected_entities, orch_ctx.extracted_entities)
            
            result["error"] = None
            
        except Exception as e:
            logger.error(f"Error evaluating {example_id}: {e}")
            result["error"] = str(e)
            result["predicted_intent"] = None
            result["predicted_capability"] = None
            result["predicted_entities"] = {}
            result["language_match"] = False
            result["intent_match"] = False
            result["capability_match"] = False
            result["entity_matches"] = {}
        
        return result
    
    def _match_language(self, expected: str, predicted: str) -> bool:
        """Check if language matches"""
        if expected == "auto":
            return True
        return expected.lower() == predicted.lower()
    
    def _match_intent(self, expected: str, predicted_intent) -> bool:
        """Check if intent matches"""
        if not predicted_intent:
            return False
        return expected == predicted_intent.value
    
    def _evaluate_entities(self, expected: Dict[str, Any], predicted: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate entity extraction"""
        results = {}
        
        for entity_type, expected_value in expected.items():
            predicted_value = predicted.get(entity_type)
            
            if entity_type == "budget_rupees":
                # Exact match or None
                results[entity_type] = {
                    "expected": expected_value,
                    "predicted": predicted_value,
                    "match": expected_value == predicted_value,
                    "partial": False
                }
            
            elif entity_type == "land_size_hectares":
                # Allow small tolerance for conversions (acres to hectares)
                if expected_value is None or predicted_value is None:
                    match = expected_value == predicted_value
                else:
                    # Allow 5% tolerance
                    tolerance = abs(expected_value) * 0.05
                    match = abs(expected_value - predicted_value) <= tolerance
                
                results[entity_type] = {
                    "expected": expected_value,
                    "predicted": predicted_value,
                    "match": match,
                    "partial": False
                }
            
            elif entity_type in ["location", "enterprise", "experience_level", "water_availability", "time_availability", "risk_tolerance"]:
                # String matching (case-insensitive)
                if expected_value is None or predicted_value is None:
                    match = expected_value == predicted_value
                else:
                    match = str(expected_value).lower() == str(predicted_value).lower()
                
                results[entity_type] = {
                    "expected": expected_value,
                    "predicted": predicted_value,
                    "match": match,
                    "partial": False
                }
            
            elif entity_type == "income_goal_monthly":
                # Numeric match
                results[entity_type] = {
                    "expected": expected_value,
                    "predicted": predicted_value,
                    "match": expected_value == predicted_value,
                    "partial": False
                }
            
            else:
                results[entity_type] = {
                    "expected": expected_value,
                    "predicted": predicted_value,
                    "match": expected_value == predicted_value,
                    "partial": False
                }
        
        return results
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive metrics"""
        logger.info("Calculating metrics...")
        
        if not self.results:
            logger.error("No results to calculate metrics from")
            return {}
        
        metrics = {
            "dataset_size": len(self.results),
            "error_count": sum(1 for r in self.results if r.get("error")),
            "successful_evaluations": sum(1 for r in self.results if not r.get("error")),
        }
        
        # Overall accuracy
        metrics["overall_intent_accuracy"] = self._calculate_intent_accuracy()
        metrics["overall_capability_accuracy"] = self._calculate_capability_accuracy()
        metrics["overall_language_accuracy"] = self._calculate_language_accuracy()
        metrics["overall_entity_accuracy"] = self._calculate_entity_accuracy()
        
        # By language
        metrics["by_language"] = self._calculate_by_language()
        
        # By intent
        metrics["by_intent"] = self._calculate_by_intent()
        
        # By difficulty
        metrics["by_difficulty"] = self._calculate_by_difficulty()
        
        # Entity-specific metrics
        metrics["entity_metrics"] = self._calculate_entity_metrics()
        
        # Failure analysis
        metrics["failure_analysis"] = self._analyze_failures()
        
        self.metrics = metrics
        return metrics
    
    def _calculate_intent_accuracy(self) -> float:
        """Calculate intent detection accuracy"""
        valid_results = [r for r in self.results if not r.get("error")]
        if not valid_results:
            return 0.0
        
        correct = sum(1 for r in valid_results if r.get("intent_match", False))
        return correct / len(valid_results)
    
    def _calculate_capability_accuracy(self) -> float:
        """Calculate capability routing accuracy"""
        valid_results = [r for r in self.results if not r.get("error")]
        if not valid_results:
            return 0.0
        
        correct = sum(1 for r in valid_results if r.get("capability_match", False))
        return correct / len(valid_results)
    
    def _calculate_language_accuracy(self) -> float:
        """Calculate language detection accuracy"""
        valid_results = [r for r in self.results if not r.get("error")]
        if not valid_results:
            return 0.0
        
        correct = sum(1 for r in valid_results if r.get("language_match", False))
        return correct / len(valid_results)
    
    def _calculate_entity_accuracy(self) -> float:
        """Calculate entity extraction accuracy (all entities must match)"""
        valid_results = [r for r in self.results if not r.get("error") and r.get("expected_entities")]
        if not valid_results:
            return 0.0
        
        def all_entities_match(entity_matches: Dict) -> bool:
            if not entity_matches:
                return True
            return all(em.get("match", False) for em in entity_matches.values())
        
        correct = sum(1 for r in valid_results if all_entities_match(r.get("entity_matches", {})))
        return correct / len(valid_results)
    
    def _calculate_by_language(self) -> Dict[str, Dict[str, float]]:
        """Calculate metrics by language"""
        by_lang = defaultdict(lambda: {
            "count": 0,
            "errors": 0,
            "intent_correct": 0,
            "capability_correct": 0,
            "language_correct": 0,
            "entity_correct": 0,
        })
        
        for result in self.results:
            lang = result.get("language", "unknown")
            by_lang[lang]["count"] += 1
            
            if result.get("error"):
                by_lang[lang]["errors"] += 1
            else:
                if result.get("intent_match"):
                    by_lang[lang]["intent_correct"] += 1
                if result.get("capability_match"):
                    by_lang[lang]["capability_correct"] += 1
                if result.get("language_match"):
                    by_lang[lang]["language_correct"] += 1
                
                # Check all entities
                entity_matches = result.get("entity_matches", {})
                if entity_matches and all(em.get("match", False) for em in entity_matches.values()):
                    by_lang[lang]["entity_correct"] += 1
        
        # Calculate percentages
        result_dict = {}
        for lang, stats in by_lang.items():
            valid = stats["count"] - stats["errors"]
            result_dict[lang] = {
                "total": stats["count"],
                "errors": stats["errors"],
                "intent_accuracy": stats["intent_correct"] / valid if valid > 0 else 0,
                "capability_accuracy": stats["capability_correct"] / valid if valid > 0 else 0,
                "language_accuracy": stats["language_correct"] / valid if valid > 0 else 0,
                "entity_accuracy": stats["entity_correct"] / valid if valid > 0 else 0,
            }
        
        return result_dict
    
    def _calculate_by_intent(self) -> Dict[str, Dict[str, float]]:
        """Calculate metrics by intent"""
        by_intent = defaultdict(lambda: {
            "count": 0,
            "errors": 0,
            "correct": 0,
        })
        
        for result in self.results:
            intent = result.get("expected_intent", "unknown")
            by_intent[intent]["count"] += 1
            
            if result.get("error"):
                by_intent[intent]["errors"] += 1
            elif result.get("intent_match"):
                by_intent[intent]["correct"] += 1
        
        # Calculate percentages
        result_dict = {}
        for intent, stats in by_intent.items():
            valid = stats["count"] - stats["errors"]
            result_dict[intent] = {
                "total": stats["count"],
                "errors": stats["errors"],
                "accuracy": stats["correct"] / valid if valid > 0 else 0,
            }
        
        return result_dict
    
    def _calculate_by_difficulty(self) -> Dict[str, Dict[str, float]]:
        """Calculate metrics by difficulty"""
        by_diff = defaultdict(lambda: {
            "count": 0,
            "errors": 0,
            "intent_correct": 0,
            "capability_correct": 0,
        })
        
        for result in self.results:
            diff = result.get("difficulty", "unknown")
            by_diff[diff]["count"] += 1
            
            if result.get("error"):
                by_diff[diff]["errors"] += 1
            else:
                if result.get("intent_match"):
                    by_diff[diff]["intent_correct"] += 1
                if result.get("capability_match"):
                    by_diff[diff]["capability_correct"] += 1
        
        # Calculate percentages
        result_dict = {}
        for diff, stats in by_diff.items():
            valid = stats["count"] - stats["errors"]
            result_dict[diff] = {
                "total": stats["count"],
                "errors": stats["errors"],
                "intent_accuracy": stats["intent_correct"] / valid if valid > 0 else 0,
                "capability_accuracy": stats["capability_correct"] / valid if valid > 0 else 0,
            }
        
        return result_dict
    
    def _calculate_entity_metrics(self) -> Dict[str, Dict[str, float]]:
        """Calculate per-entity extraction metrics"""
        entity_stats = defaultdict(lambda: {
            "count": 0,
            "correct": 0,
            "missing_in_output": 0,
        })
        
        for result in self.results:
            if result.get("error"):
                continue
            
            expected_entities = result.get("expected_entities", {})
            entity_matches = result.get("entity_matches", {})
            
            for entity_type, expected_value in expected_entities.items():
                entity_stats[entity_type]["count"] += 1
                
                if entity_type in entity_matches:
                    if entity_matches[entity_type].get("match"):
                        entity_stats[entity_type]["correct"] += 1
                else:
                    entity_stats[entity_type]["missing_in_output"] += 1
        
        # Calculate percentages
        result_dict = {}
        for entity_type, stats in entity_stats.items():
            result_dict[entity_type] = {
                "total_expected": stats["count"],
                "extraction_rate": (stats["count"] - stats["missing_in_output"]) / stats["count"] if stats["count"] > 0 else 0,
                "accuracy_when_extracted": stats["correct"] / (stats["count"] - stats["missing_in_output"]) if (stats["count"] - stats["missing_in_output"]) > 0 else 0,
            }
        
        return result_dict
    
    def _analyze_failures(self) -> Dict[str, Any]:
        """Analyze failure patterns"""
        failures = [r for r in self.results if r.get("error") or not r.get("intent_match")]
        
        failure_by_lang = defaultdict(int)
        failure_by_intent = defaultdict(int)
        failure_by_difficulty = defaultdict(int)
        
        for failure in failures:
            if not failure.get("intent_match") and not failure.get("error"):
                failure_by_lang[failure.get("language", "unknown")] += 1
                failure_by_intent[failure.get("expected_intent", "unknown")] += 1
                failure_by_difficulty[failure.get("difficulty", "unknown")] += 1
        
        return {
            "total_failures": len(failures),
            "by_language": dict(failure_by_lang),
            "by_intent": dict(failure_by_intent),
            "by_difficulty": dict(failure_by_difficulty),
        }
    
    def get_failed_examples(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get failed examples for analysis"""
        failed = [r for r in self.results if r.get("error") or not r.get("intent_match")]
        return failed[:limit]
    
    def print_summary(self):
        """Print metrics summary"""
        if not self.metrics:
            logger.warning("No metrics calculated yet")
            return
        
        print("\n" + "="*80)
        print("EVALUATION SUMMARY")
        print("="*80)
        
        m = self.metrics
        print(f"\nDataset: {m['dataset_size']} examples")
        print(f"Successful evaluations: {m['successful_evaluations']} ({100*m['successful_evaluations']/m['dataset_size']:.1f}%)")
        print(f"Errors: {m['error_count']} ({100*m['error_count']/m['dataset_size']:.1f}%)")
        
        print(f"\nOVERALL METRICS:")
        print(f"  Intent Detection Accuracy: {100*m['overall_intent_accuracy']:.1f}%")
        print(f"  Capability Routing Accuracy: {100*m['overall_capability_accuracy']:.1f}%")
        print(f"  Language Detection Accuracy: {100*m['overall_language_accuracy']:.1f}%")
        print(f"  Entity Extraction Accuracy: {100*m['overall_entity_accuracy']:.1f}%")
        
        print(f"\nBY LANGUAGE:")
        for lang, stats in m['by_language'].items():
            print(f"  {lang.upper()}: {stats['total']} examples")
            print(f"    Intent Accuracy: {100*stats['intent_accuracy']:.1f}%")
            print(f"    Capability Accuracy: {100*stats['capability_accuracy']:.1f}%")
            print(f"    Entity Accuracy: {100*stats['entity_accuracy']:.1f}%")
        
        print(f"\nBY INTENT:")
        for intent, stats in m['by_intent'].items():
            print(f"  {intent}: {stats['total']} examples, Accuracy: {100*stats['accuracy']:.1f}%")
        
        print(f"\nBY DIFFICULTY:")
        for diff, stats in m['by_difficulty'].items():
            print(f"  {diff.upper()}: {stats['total']} examples")
            print(f"    Intent Accuracy: {100*stats['intent_accuracy']:.1f}%")
        
        print(f"\nENTITY EXTRACTION:")
        for entity, stats in m['entity_metrics'].items():
            print(f"  {entity}: Extraction Rate: {100*stats['extraction_rate']:.1f}%, Accuracy: {100*stats['accuracy_when_extracted']:.1f}%")
        
        print(f"\nFAILURE ANALYSIS:")
        fa = m['failure_analysis']
        print(f"  Total Failures: {fa['total_failures']}")
        if fa['by_intent']:
            print(f"  Failures by Intent: {fa['by_intent']}")
        
        print("\n" + "="*80)


def main():
    """Main evaluation function"""
    import sys
    import os
    
    # Add workspace root to path for imports
    workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if workspace_root not in sys.path:
        sys.path.insert(0, workspace_root)
    
    # Initialize evaluator
    dataset_path = "data/evaluation/farmer_queries.jsonl"
    evaluator = FarmerQueryEvaluator(dataset_path)
    
    # Load dataset
    evaluator.load_dataset()
    
    # Run evaluation
    evaluator.evaluate_all()
    
    # Calculate metrics
    evaluator.calculate_metrics()
    
    # Print summary
    evaluator.print_summary()
    
    # Save detailed results
    output_path = "data/evaluation/results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "metrics": evaluator.metrics,
            "results": evaluator.results[:10]  # Save first 10 for inspection
        }, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Detailed results saved to {output_path}")
    
    # Print some failed examples
    print("\nFAILED EXAMPLES (first 5):")
    print("-"*80)
    for failed in evaluator.get_failed_examples(5):
        print(f"\nID: {failed['id']}")
        print(f"Message: {failed['message']}")
        print(f"Expected Intent: {failed['expected_intent']}")
        print(f"Predicted Intent: {failed.get('predicted_intent', 'ERROR')}")
        if failed.get('error'):
            print(f"Error: {failed['error']}")


if __name__ == "__main__":
    main()
