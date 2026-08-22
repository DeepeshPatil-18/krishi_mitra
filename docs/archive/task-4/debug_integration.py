"""Debug integration issues"""

from app.services.ai_orchestrator import AIOrchestrator
from app.services.entity_extractor import EntityExtractor
from app.services.entity_normalizer import EntityNormalizer

# Test 1: English land
print("=" * 80)
print("TEST: English land")
print("=" * 80)
message = "I have 2 acres of land"
print(f"Message: {message}")

# Check raw extraction
raw = EntityExtractor.extract_all(message, "english")
print(f"\nRaw extraction: {raw}")

# Check normalization
for key, val in raw.items():
    norm = EntityNormalizer.normalize_entity(key, val)
    print(f"\nEntity: {key}")
    print(f"  Raw: {val}")
    print(f"  Normalized: {norm.get('normalized_value')}")
    print(f"  Confidence: {norm.get('normalization_confidence')}")
    print(f"  Format: {norm.get('format_detected')}")

# Check orchestrator
ctx = AIOrchestrator.orchestrate(message, language="english")
print(f"\nOrchestrator extracted_entities: {ctx.extracted_entities}")
print(f"Farmer context: {ctx.farmer_context}")

print("\n" + "=" * 80)
print("TEST: Marathi land")
print("=" * 80)
message = "माझ्याकडे 2 एकर जमीन आहे"
print(f"Message: {message}")

# Check raw extraction
raw = EntityExtractor.extract_all(message, "marathi")
print(f"\nRaw extraction: {raw}")

# Check normalization
for key, val in raw.items():
    norm = EntityNormalizer.normalize_entity(key, val)
    print(f"\nEntity: {key}")
    print(f"  Raw: {val}")
    print(f"  Normalized: {norm.get('normalized_value')}")

# Check orchestrator
ctx = AIOrchestrator.orchestrate(message, language="marathi")
print(f"\nOrchestrator extracted_entities: {ctx.extracted_entities}")

print("\n" + "=" * 80)
print("TEST: Budget range")
print("=" * 80)
message = "I have 50-100k budget"
print(f"Message: {message}")

# Check raw extraction
raw = EntityExtractor.extract_all(message, "english")
print(f"\nRaw extraction: {raw}")

# Check normalization
for key, val in raw.items():
    norm = EntityNormalizer.normalize_entity(key, val)
    print(f"\nEntity: {key}")
    print(f"  Raw: {val}")
    print(f"  Normalized: {norm.get('normalized_value')}")

# Check orchestrator
ctx = AIOrchestrator.orchestrate(message, language="english")
print(f"\nOrchestrator extracted_entities: {ctx.extracted_entities}")
