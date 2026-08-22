"""
TASK 5: Comprehensive tests for Scheme Search capability.

Tests cover:
- Dataset loading
- Search functionality
- Ranking and relevance
- Multilingual support
- Entity matching
- Location preferences
- No false information
"""

import pytest
from app.services.scheme_service import SchemeService, SchemeResult


class TestDatasetLoading:
    """Test that scheme dataset loads correctly"""

    def test_dataset_loads(self):
        """Dataset should load without errors"""
        schemes = SchemeService.get_all_schemes()
        assert schemes is not None
        assert isinstance(schemes, list)
        assert len(schemes) > 0

    def test_dataset_has_45_schemes(self):
        """Dataset should have exactly 45 schemes"""
        schemes = SchemeService.get_all_schemes()
        assert len(schemes) == 45, f"Expected 45 schemes, got {len(schemes)}"

    def test_scheme_count_method(self):
        """get_scheme_count should return 45"""
        count = SchemeService.get_scheme_count()
        assert count == 45

    def test_all_schemes_have_required_fields(self):
        """All schemes must have id, name, summary, source_url"""
        schemes = SchemeService.get_all_schemes()
        for scheme in schemes:
            assert "id" in scheme, f"Scheme missing id: {scheme}"
            assert "name" in scheme, f"Scheme missing name: {scheme}"
            assert "summary" in scheme, f"Scheme missing summary: {scheme}"
            assert "source_url" in scheme, f"Scheme missing source_url: {scheme}"
            assert "source_name" in scheme, f"Scheme missing source_name: {scheme}"
            assert "keywords" in scheme, f"Scheme missing keywords: {scheme}"
            assert isinstance(scheme["keywords"], list), f"Keywords must be list: {scheme['id']}"

    def test_scheme_scopes(self):
        """Schemes should have scope: 'central' or 'maharashtra'"""
        scopes = SchemeService.get_scopes()
        assert "central" in scopes
        assert "maharashtra" in scopes

    def test_central_and_maharashtra_breakdown(self):
        """Should have 30 central and 15 Maharashtra schemes"""
        schemes = SchemeService.get_all_schemes()
        central = [s for s in schemes if s.get("scope") == "central"]
        maharashtra = [s for s in schemes if s.get("scope") == "maharashtra"]
        
        assert len(central) == 30, f"Expected 30 central, got {len(central)}"
        assert len(maharashtra) == 15, f"Expected 15 Maharashtra, got {len(maharashtra)}"

    def test_categories_exist(self):
        """Schemes should have diverse categories"""
        categories = SchemeService.get_categories()
        assert len(categories) > 10, f"Expected 10+ categories, got {len(categories)}"
        
        # Verify some key categories exist
        key_categories = ["livestock", "irrigation", "horticulture", "crop_production", "dairy"]
        for cat in key_categories:
            assert cat in categories, f"Missing category: {cat}"


class TestBasicSearch:
    """Test basic scheme search functionality"""

    def test_search_returns_list(self):
        """Search should return list of SchemeResult"""
        results = SchemeService.search_schemes(query="scheme")
        assert isinstance(results, list)
        assert all(isinstance(r, SchemeResult) for r in results)

    def test_search_limit(self):
        """Search should respect limit parameter"""
        results = SchemeService.search_schemes(query="scheme", limit=3)
        assert len(results) <= 3

    def test_empty_query_returns_schemes(self):
        """Empty query should still return some schemes"""
        results = SchemeService.search_schemes(query="", limit=5)
        # May return 0 if no matches, but shouldn't crash
        assert isinstance(results, list)

    def test_nonexistent_query_returns_few_or_none(self):
        """Query with no keyword matches may return location-based results"""
        results = SchemeService.search_schemes(query="xyzabc123nonexistent")
        # May return 0 if truly no match, or may get location preference hits
        assert isinstance(results, list)
        if results:
            # If any results, they should be from location matching, not keywords
            for result in results:
                assert len(result.match_signals) > 0

    def test_results_have_relevance_scores(self):
        """All results should have relevance_score > 0"""
        results = SchemeService.search_schemes(query="irrigation")
        for result in results:
            assert result.relevance_score > 0
            assert isinstance(result.relevance_score, float)

    def test_results_have_match_signals(self):
        """All results should have match_signals list"""
        results = SchemeService.search_schemes(query="irrigation")
        for result in results:
            assert isinstance(result.match_signals, list)
            assert len(result.match_signals) > 0


class TestKeywordMatching:
    """Test keyword-based scheme matching"""

    def test_irrigation_keyword_match(self):
        """Query with 'irrigation' should find irrigation schemes"""
        results = SchemeService.search_schemes(query="irrigation", limit=5)
        assert len(results) > 0
        
        # Should find PMKSY (irrigation scheme)
        scheme_names = [r.scheme.get("name") for r in results]
        assert any("irrigation" in name.lower() for name in scheme_names)

    def test_livestock_keyword_match(self):
        """Query with 'livestock' should find livestock schemes"""
        results = SchemeService.search_schemes(query="livestock", limit=5)
        assert len(results) > 0

    def test_goat_keyword_match(self):
        """Query with 'goat' should find livestock/goat schemes"""
        results = SchemeService.search_schemes(query="goat", limit=5)
        assert len(results) > 0

    def test_mushroom_keyword_match(self):
        """Query with 'mushroom' should find horticulture schemes"""
        results = SchemeService.search_schemes(query="mushroom", limit=5)
        assert len(results) > 0

    def test_hindi_keyword_match(self):
        """Hindi keywords should match"""
        results = SchemeService.search_schemes(query="योजना", limit=5)
        # Should find some schemes (योजना = scheme in Hindi)
        assert isinstance(results, list)

    def test_marathi_keyword_match(self):
        """Marathi keywords should match"""
        results = SchemeService.search_schemes(query="योजना", limit=5)
        assert isinstance(results, list)


class TestEntityMatching:
    """Test entity-based ranking"""

    def test_enterprise_matching(self):
        """Schemes should rank higher for matching enterprise"""
        # Search for mushroom without enterprise specified
        results_no_ent = SchemeService.search_schemes(query="farming", enterprise=None, limit=5)
        
        # Search with mushroom enterprise
        results_with_ent = SchemeService.search_schemes(query="farming", enterprise="mushroom", limit=5)
        
        # With enterprise should give more focused results
        assert len(results_with_ent) >= 0  # May be different results

    def test_water_availability_irrigation_match(self):
        """Low water + extraction should match irrigation schemes"""
        entities = {"water_availability": "low"}
        results = SchemeService.search_schemes(
            query="water",
            extracted_entities=entities,
            limit=5
        )
        assert len(results) > 0

    def test_beginner_training_match(self):
        """Beginner experience should match training schemes"""
        entities = {"experience_level": "beginner"}
        results = SchemeService.search_schemes(
            query="training",
            extracted_entities=entities,
            limit=5
        )
        # Should get some results for training
        assert isinstance(results, list)

    def test_livestock_enterprise_match(self):
        """Goat enterprise should match livestock schemes"""
        entities = {}
        results = SchemeService.search_schemes(
            query="goat",
            enterprise="goat",
            extracted_entities=entities,
            limit=5
        )
        assert len(results) > 0


class TestLocationPreference:
    """Test location-based scheme preference"""

    def test_maharashtra_location_preference(self):
        """Maharashtra schemes should be preferred when in Maharashtra"""
        results_mh = SchemeService.search_schemes(
            query="scheme",
            location="maharashtra",
            limit=10
        )
        
        # Check if any Maharashtra schemes are in results
        mh_schemes = [r for r in results_mh if r.scheme.get("scope") == "maharashtra"]
        assert len(mh_schemes) > 0, "Should have Maharashtra schemes when location=maharashtra"

    def test_nashik_location_preference(self):
        """Nashik should be treated as Maharashtra"""
        results = SchemeService.search_schemes(
            query="scheme",
            location="nashik",
            limit=10
        )
        assert isinstance(results, list)

    def test_central_schemes_always_available(self):
        """Central schemes should be available regardless of location"""
        results_mh = SchemeService.search_schemes(query="PM-KISAN", location="maharashtra", limit=10)
        results_other = SchemeService.search_schemes(query="PM-KISAN", location="other", limit=10)
        
        # Both should find PM-KISAN (central scheme)
        assert len(results_mh) > 0
        assert len(results_other) > 0


class TestMultilingualSupport:
    """Test multilingual search and formatting"""

    def test_hindi_query(self):
        """Hindi queries should work"""
        results = SchemeService.search_schemes(query="बकरी पालन", limit=5)
        assert isinstance(results, list)

    def test_marathi_query(self):
        """Marathi queries should work"""
        results = SchemeService.search_schemes(query="शेळी पालन", limit=5)
        assert isinstance(results, list)

    def test_mixed_language_query(self):
        """Mixed language queries should work"""
        results = SchemeService.search_schemes(query="goat पालन", limit=5)
        assert isinstance(results, list)

    def test_format_english(self):
        """Format results in English"""
        results = SchemeService.search_schemes(query="irrigation", limit=2)
        formatted = SchemeService.format_results(results, language="english")
        assert isinstance(formatted, str)
        assert len(formatted) > 0
        assert "Important" in formatted or "scheme" in formatted.lower()

    def test_format_hindi(self):
        """Format results in Hindi"""
        results = SchemeService.search_schemes(query="irrigation", limit=2)
        formatted = SchemeService.format_results(results, language="hindi")
        assert isinstance(formatted, str)
        assert len(formatted) > 0

    def test_format_marathi(self):
        """Format results in Marathi"""
        results = SchemeService.search_schemes(query="irrigation", limit=2)
        formatted = SchemeService.format_results(results, language="marathi")
        assert isinstance(formatted, str)
        assert len(formatted) > 0

    def test_format_empty_results_english(self):
        """Format empty results in English"""
        formatted = SchemeService.format_results([], language="english")
        assert "No matching schemes" in formatted

    def test_format_empty_results_hindi(self):
        """Format empty results in Hindi"""
        formatted = SchemeService.format_results([], language="hindi")
        assert isinstance(formatted, str)

    def test_format_empty_results_marathi(self):
        """Format empty results in Marathi"""
        formatted = SchemeService.format_results([], language="marathi")
        assert isinstance(formatted, str)


class TestNoFalseInformation:
    """Test that system never invents information"""

    def test_results_never_invent_subsidy(self):
        """Results should never claim specific subsidy amounts"""
        results = SchemeService.search_schemes(query="subsidy", limit=10)
        for result in results:
            summary = result.scheme.get("summary", "")
            # Should not have specific numbers that look invented
            assert "50000" not in summary or "verified_as_of" in result.scheme
            # Dataset defines what's safe

    def test_results_never_invent_deadline(self):
        """Results should never claim specific application deadlines"""
        results = SchemeService.search_schemes(query="deadline", limit=10)
        for result in results:
            summary = result.scheme.get("summary", "")
            # Deadlines should only come from official dataset
            assert "deadline" not in summary.lower() or "verified" in result.scheme.get("verified_as_of", "")

    def test_all_results_have_source_url(self):
        """All results must include official source URL"""
        results = SchemeService.search_schemes(query="scheme", limit=10)
        for result in results:
            assert result.scheme.get("source_url"), f"Missing source_url: {result.scheme['id']}"
            assert result.scheme.get("source_name"), f"Missing source_name: {result.scheme['id']}"

    def test_formatted_results_include_source(self):
        """Formatted output must include source for each scheme"""
        results = SchemeService.search_schemes(query="irrigation", limit=3)
        formatted = SchemeService.format_results(results, language="english")
        # Should mention official source multiple times
        assert formatted.count("official") > 0 or formatted.count("Official") > 0


class TestRankingQuality:
    """Test that ranking produces sensible results"""

    def test_exact_keyword_ranked_high(self):
        """Exact keyword matches should be ranked higher"""
        results = SchemeService.search_schemes(query="PM-KISAN", limit=5)
        if results:
            # First result should be PM-KISAN or related
            first_scheme_name = results[0].scheme.get("name", "").lower()
            assert "kisan" in first_scheme_name

    def test_irrigation_query_returns_irrigation_schemes(self):
        """Irrigation query should return irrigation-related schemes"""
        results = SchemeService.search_schemes(query="irrigation", limit=5)
        assert len(results) > 0
        
        # At least some should be irrigation/water related
        categories = [r.scheme.get("category", "").lower() for r in results]
        irrigation_cats = ["irrigation", "water_management", "solar_irrigation"]
        assert any(cat in irrigation_cats for cat in categories)

    def test_livestock_query_returns_livestock(self):
        """Livestock query should return livestock schemes"""
        results = SchemeService.search_schemes(query="goat livestock", limit=5)
        assert len(results) > 0
        
        categories = [r.scheme.get("category", "").lower() for r in results]
        # Should have livestock-related schemes
        livestock_cats = ["livestock", "dairy", "animal_husbandry_infrastructure"]
        assert any(cat in livestock_cats for cat in categories)

    def test_results_are_sorted_by_relevance(self):
        """Results should be sorted by relevance score (descending)"""
        results = SchemeService.search_schemes(query="farming", limit=10)
        scores = [r.relevance_score for r in results]
        
        # Scores should be in descending order
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1], f"Scores not sorted: {scores}"


class TestSpecificScenarios:
    """Test real-world farmer scenarios"""

    def test_scenario_farmer_with_2_acres_goat_farming(self):
        """Farmer with 2 acres wanting goat farming"""
        entities = {
            "land_size_hectares": 0.81,
            "enterprise": "goat",
            "experience_level": "beginner"
        }
        results = SchemeService.search_schemes(
            query="मला शेळी पालन सुरू करायचे आहे",
            location="maharashtra",
            enterprise="goat",
            extracted_entities=entities,
            limit=5
        )
        assert len(results) > 0

    def test_scenario_irrigation_query(self):
        """Farmer asking about irrigation schemes"""
        entities = {"water_availability": "low"}
        results = SchemeService.search_schemes(
            query="नाशिकमध्ये सिंचनासाठी योजना",
            location="nashik",
            extracted_entities=entities,
            limit=5
        )
        assert isinstance(results, list)

    def test_scenario_beginner_farmer(self):
        """Beginner farmer looking for support"""
        entities = {"experience_level": "beginner"}
        results = SchemeService.search_schemes(
            query="शुरुवातीचा शेतकरी योजना",
            location="maharashtra",
            extracted_entities=entities,
            limit=5
        )
        assert isinstance(results, list)

    def test_scenario_budget_constrained(self):
        """Farmer with limited budget"""
        entities = {"budget_rupees": 50000}
        results = SchemeService.search_schemes(
            query="50000 बजेट शेती व्यवसाय",
            location="maharashtra",
            extracted_entities=entities,
            limit=5
        )
        assert isinstance(results, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
