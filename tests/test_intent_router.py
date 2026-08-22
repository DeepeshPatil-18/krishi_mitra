"""Tests for intent router"""

import pytest
from app.services.intent_router import IntentRouter
from app.schemas.intent import Intent


def test_detect_market_search_intent():
    """Test market search intent detection"""
    intent, confidence, params = IntentRouter.detect_intent("माझा मध कुठे विकू?")
    assert intent == Intent.MARKET_SEARCH
    assert confidence > 0.8


def test_detect_scheme_search_intent():
    """Test scheme search intent detection"""
    intent, confidence, params = IntentRouter.detect_intent("मला शेळीपालनासाठी सरकारी मदत मिळेल का?")
    assert intent == Intent.SCHEME_SEARCH
    assert confidence > 0.8


def test_detect_training_request_intent():
    """Test training request intent detection"""
    intent, confidence, params = IntentRouter.detect_intent("मशरूम शेती कशी सुरू करू?")
    assert intent == Intent.TRAINING_REQUEST
    assert confidence > 0.8


def test_detect_expert_request_intent():
    """Test expert request intent detection"""
    intent, confidence, params = IntentRouter.detect_intent("मला तज्ञाशी बोलायचं आहे.")
    assert intent == Intent.EXPERT_REQUEST
    assert confidence > 0.8


def test_detect_livelihood_recommendation_intent():
    """Test livelihood recommendation intent detection"""
    intent, confidence, params = IntentRouter.detect_intent("माझ्याकडे ५० हजार आहेत. मी काय सुरू करू?")
    assert intent == Intent.LIVELIHOOD_RECOMMENDATION
    assert confidence > 0.7


def test_english_intent_detection():
    """Test intent detection in English"""
    intent, confidence, params = IntentRouter.detect_intent("Where can I sell my honey?")
    assert intent == Intent.MARKET_SEARCH
    assert confidence > 0.8


def test_extract_budget_parameter():
    """Test parameter extraction - budget"""
    intent, confidence, params = IntentRouter.detect_intent("मुझे 50 हजार का बजट है")
    params = IntentRouter.extract_parameters("मुझे 50 हजार का बजट है", Intent.LIVELIHOOD_RECOMMENDATION)
    # Should extract budget if present


def test_default_to_general_question():
    """Test fallback to general question"""
    intent, confidence, params = IntentRouter.detect_intent("नमस्कार")
    assert intent in [Intent.GENERAL_QUESTION, Intent.COMMUNITY]
