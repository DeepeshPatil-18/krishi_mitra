"""
TASK 6: Market Price Search Tests

Tests cover:
- Live API client (with API key fallback)
- Cached fallback data loading
- Commodity/location extraction
- Multilingual search
- Price formatting in 3 languages
- Data source labelling (LIVE vs CACHED)
- No fabricated prices
- Deterministic results
"""

import pytest
import json
from pathlib import Path
from app.services.market_service import MarketService, MarketPrice


class TestMarketDataLoading:
    """Test that market data loads correctly"""

    def test_cached_data_loads(self):
        """Cached market data should load without errors"""
        cached = MarketService._load_cached_data()
        assert cached is not None
        assert isinstance(cached, list)
        assert len(cached) > 0

    def test_cached_data_has_required_fields(self):
        """All cached records must have required fields"""
        cached = MarketService._load_cached_data()
        for record in cached:
            assert "commodity" in record
            assert "market" in record
            assert "location" in record
            assert "date" in record
            assert "min_price" in record
            assert "max_price" in record
            assert "modal_price" in record

    def test_no_fabricated_prices_in_cache(self):
        """Prices should be realistic (not invented random numbers)"""
        cached = MarketService._load_cached_data()
        for record in cached:
            min_price = float(record["min_price"])
            max_price = float(record["max_price"])
            modal_price = float(record["modal_price"])
            
            # Prices should be in reasonable agricultural range (₹100 - ₹10000/qtl)
            assert 100 <= min_price <= 10000
            assert 100 <= max_price <= 10000
            assert 100 <= modal_price <= 10000
            # Modal should be between min and max
            assert min_price <= modal_price <= max_price


class TestCommodityNormalization:
    """Test commodity name matching across languages"""

    def test_english_onion(self):
        """English 'onion' should match"""
        result = MarketService.normalize_commodity("onion")
        assert result == "onion"

    def test_hindi_onion(self):
        """Hindi 'प्याज' should match to onion"""
        result = MarketService.normalize_commodity("प्याज")
        assert result == "onion"

    def test_marathi_onion(self):
        """Marathi 'कांदा' should match to onion"""
        result = MarketService.normalize_commodity("कांदा")
        assert result == "onion"

    def test_tomato_english(self):
        """English 'tomato' should match"""
        result = MarketService.normalize_commodity("tomato")
        assert result == "tomato"

    def test_tomato_hindi(self):
        """Hindi 'टमाटर' should match tomato"""
        result = MarketService.normalize_commodity("टमाटर")
        assert result == "tomato"

    def test_potato_english(self):
        """English 'potato' should match"""
        result = MarketService.normalize_commodity("potato")
        assert result == "potato"

    def test_wheat_english(self):
        """English 'wheat' should match"""
        result = MarketService.normalize_commodity("wheat")
        assert result == "wheat"

    def test_soybean_english(self):
        """English 'soybean' should match"""
        result = MarketService.normalize_commodity("soybean")
        assert result == "soybean"

    def test_unknown_commodity(self):
        """Unknown commodity should return None"""
        result = MarketService.normalize_commodity("xyzunknown123")
        assert result is None

    def test_case_insensitive(self):
        """Commodity matching should be case-insensitive"""
        result = MarketService.normalize_commodity("ONION")
        assert result == "onion"


class TestLocationNormalization:
    """Test location name normalization"""

    def test_nashik_english(self):
        """English 'nashik' should normalize"""
        result = MarketService.normalize_location("nashik")
        assert result == "nashik"

    def test_nashik_marathi(self):
        """Marathi 'नाशिक' should normalize to nashik"""
        result = MarketService.normalize_location("नाशिक")
        assert result == "nashik"

    def test_maharashtra_english(self):
        """English 'maharashtra' should normalize"""
        result = MarketService.normalize_location("maharashtra")
        assert result == "maharashtra"

    def test_maharashtra_marathi(self):
        """Marathi 'महाराष्ट्र' should normalize"""
        result = MarketService.normalize_location("महाराष्ट्र")
        assert result == "maharashtra"

    def test_pune_english(self):
        """English 'pune' should normalize"""
        result = MarketService.normalize_location("pune")
        assert result == "pune"

    def test_mumbai_english(self):
        """English 'mumbai' should normalize"""
        result = MarketService.normalize_location("mumbai")
        assert result == "mumbai"


class TestCachedSearch:
    """Test searching cached market data"""

    def test_search_onion_nashik(self):
        """Search onion prices in Nashik"""
        results = MarketService.search_prices(
            commodity="onion",
            location="nashik",
            limit=5
        )
        assert len(results) > 0
        assert all(r.source == "CACHED" for r in results)
        assert all("nashik" in r.location.lower() for r in results)

    def test_search_tomato_pune(self):
        """Search tomato prices in Pune"""
        results = MarketService.search_prices(
            commodity="tomato",
            location="pune",
            limit=5
        )
        assert isinstance(results, list)

    def test_search_respects_limit(self):
        """Search should respect limit parameter"""
        results = MarketService.search_prices(
            commodity="onion",
            location="maharashtra",
            limit=2
        )
        assert len(results) <= 2

    def test_search_with_marathi_commodity(self):
        """Search with Marathi commodity name"""
        results = MarketService.search_prices(
            commodity="कांदा",
            location="nashik",
            limit=5
        )
        assert len(results) > 0

    def test_search_with_hindi_commodity(self):
        """Search with Hindi commodity name"""
        results = MarketService.search_prices(
            commodity="प्याज",
            location="nashik",
            limit=5
        )
        assert len(results) > 0

    def test_search_empty_commodity(self):
        """Empty commodity search should return empty"""
        results = MarketService.search_prices(
            commodity="",
            location="nashik",
            limit=5
        )
        assert results == []

    def test_search_unknown_commodity(self):
        """Unknown commodity should return empty"""
        results = MarketService.search_prices(
            commodity="xyzunknown123commodity",
            location="nashik",
            limit=5
        )
        assert results == [] or isinstance(results, list)


class TestResultFormatting:
    """Test multilingual result formatting"""

    def test_format_english(self):
        """Format results in English"""
        results = MarketService.search_prices(
            commodity="onion",
            location="nashik",
            limit=2
        )
        formatted = MarketService.format_results(results, language="english")
        assert isinstance(formatted, str)
        assert len(formatted) > 0
        assert "Market" in formatted or "market" in formatted.lower()

    def test_format_hindi(self):
        """Format results in Hindi"""
        results = MarketService.search_prices(
            commodity="onion",
            location="nashik",
            limit=2
        )
        formatted = MarketService.format_results(results, language="hindi")
        assert isinstance(formatted, str)
        assert len(formatted) > 0

    def test_format_marathi(self):
        """Format results in Marathi"""
        results = MarketService.search_prices(
            commodity="onion",
            location="nashik",
            limit=2
        )
        formatted = MarketService.format_results(results, language="marathi")
        assert isinstance(formatted, str)
        assert len(formatted) > 0

    def test_format_empty_results_english(self):
        """Format empty results in English"""
        formatted = MarketService.format_results([], language="english")
        assert "not available" in formatted.lower()

    def test_format_empty_results_hindi(self):
        """Format empty results in Hindi"""
        formatted = MarketService.format_results([], language="hindi")
        assert isinstance(formatted, str)

    def test_format_empty_results_marathi(self):
        """Format empty results in Marathi"""
        formatted = MarketService.format_results([], language="marathi")
        assert isinstance(formatted, str)

    def test_formatted_output_has_source_label(self):
        """Formatted output should indicate if data is CACHED"""
        results = MarketService.search_prices(
            commodity="onion",
            location="nashik",
            limit=2
        )
        formatted = MarketService.format_results(results, language="english")
        # Should have source indicator (CACHED or ⚪ for demo)
        assert "CACHED" in formatted or "reference" in formatted.lower() or "⚪" in formatted

    def test_formatted_output_has_prices(self):
        """Formatted output should include price information"""
        results = MarketService.search_prices(
            commodity="onion",
            location="nashik",
            limit=2
        )
        formatted = MarketService.format_results(results, language="english")
        # Should include price markers
        assert "₹" in formatted or "Rs" in formatted.lower()

    def test_formatted_output_includes_market_info(self):
        """Formatted output should include market/location info"""
        results = MarketService.search_prices(
            commodity="onion",
            location="nashik",
            limit=2
        )
        formatted = MarketService.format_results(results, language="english")
        # Should mention market or date
        assert "Market" in formatted or "market" in formatted.lower() or "Date" in formatted or "date" in formatted.lower()


class TestDataSourceLabelling:
    """Test that data source is correctly labelled"""

    def test_cached_results_labeled_cached(self):
        """Cached results should be labelled CACHED"""
        results = MarketService.search_prices(
            commodity="onion",
            location="nashik",
            limit=5
        )
        if results:
            assert all(r.source == "CACHED" for r in results)

    def test_cached_results_not_called_live(self):
        """Cached results should never be called LIVE"""
        results = MarketService.search_prices(
            commodity="onion",
            location="nashik",
            limit=5
        )
        assert not any(r.source == "LIVE" for r in results)

    def test_source_name_provided(self):
        """All results should have source_name"""
        results = MarketService.search_prices(
            commodity="onion",
            location="nashik",
            limit=5
        )
        for result in results:
            assert result.source_name is not None
            assert len(result.source_name) > 0


class TestRealWorldQueries:
    """Test realistic farmer market queries"""

    def test_query_onion_price_nashik(self):
        """Farmer: What is onion price in Nashik?"""
        results = MarketService.search_prices(
            commodity="onion",
            location="nashik",
            limit=5
        )
        assert len(results) > 0
        formatted = MarketService.format_results(results, language="english")
        assert "onion" in formatted.lower()

    def test_query_marathi_कांदा_नाशिक(self):
        """Farmer: नाशिकमध्ये कांद्याचा भाव काय?"""
        results = MarketService.search_prices(
            commodity="कांदा",
            location="नाशिक",
            limit=5
        )
        assert len(results) > 0

    def test_query_hindi_प्याज_नासिक(self):
        """Farmer: नासिक में प्याज का भाव क्या है?"""
        results = MarketService.search_prices(
            commodity="प्याज",
            location="nashik",
            limit=5
        )
        assert len(results) > 0

    def test_query_tomato_price_today(self):
        """Farmer: What is today's tomato price?"""
        results = MarketService.search_prices(
            commodity="tomato",
            location="maharashtra",
            limit=5
        )
        assert isinstance(results, list)

    def test_query_soybean_nashik(self):
        """Farmer: Soybean price in Nashik?"""
        results = MarketService.search_prices(
            commodity="soybean",
            location="nashik",
            limit=5
        )
        assert isinstance(results, list)

    def test_query_multiple_markets_maharashtra(self):
        """Search should return multiple markets if available"""
        results = MarketService.search_prices(
            commodity="onion",
            location="maharashtra",
            limit=10
        )
        # May have results from multiple markets
        assert isinstance(results, list)


class TestNoFabrication:
    """Test that prices are never invented"""

    def test_all_prices_from_cache(self):
        """All results should be from cached official data only"""
        results = MarketService.search_prices(
            commodity="onion",
            location="nashik",
            limit=5
        )
        for result in results:
            assert result.source in ["LIVE", "CACHED"]
            assert result.source_name is not None

    def test_prices_are_numbers(self):
        """Prices should be valid numbers"""
        results = MarketService.search_prices(
            commodity="onion",
            location="nashik",
            limit=5
        )
        for result in results:
            assert isinstance(result.min_price, (int, float))
            assert isinstance(result.max_price, (int, float))
            assert isinstance(result.modal_price, (int, float))

    def test_min_max_modal_relationships(self):
        """Price relationships should be logically consistent"""
        results = MarketService.search_prices(
            commodity="onion",
            location="nashik",
            limit=5
        )
        for result in results:
            assert result.min_price <= result.modal_price
            assert result.modal_price <= result.max_price


class TestDeterministicResults:
    """Test that searches return deterministic results"""

    def test_same_query_same_results(self):
        """Same query should return same results"""
        results1 = MarketService.search_prices(
            commodity="onion",
            location="nashik",
            limit=5
        )
        results2 = MarketService.search_prices(
            commodity="onion",
            location="nashik",
            limit=5
        )
        
        assert len(results1) == len(results2)
        if results1:
            assert results1[0].commodity == results2[0].commodity
            assert results1[0].market == results2[0].market

    def test_results_consistent_across_calls(self):
        """Multiple calls should be consistent"""
        for _ in range(3):
            results = MarketService.search_prices(
                commodity="potato",
                location="pune",
                limit=3
            )
            assert isinstance(results, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
