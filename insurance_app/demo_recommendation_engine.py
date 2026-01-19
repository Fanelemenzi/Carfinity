#!/usr/bin/env python
"""
Demo script for QuoteRecommendationEngine

This script demonstrates the recommendation engine functionality
with sample data to show how it works in practice.
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carfinity.settings')
django.setup()

from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.models import User

from insurance_app.recommendation_engine import QuoteRecommendationEngine
from insurance_app.models import DamagedPart, PartQuote, PartQuoteRequest
from assessments.models import VehicleAssessment
from vehicles.models import Vehicle


def create_demo_data():
    """Create demo data for testing the recommendation engine"""
    print("Creating demo data...")
    
    # Create or get test user
    user, created = User.objects.get_or_create(
        username='demo_user',
        defaults={
            'email': 'demo@example.com',
            'first_name': 'Demo',
            'last_name': 'User'
        }
    )
    
    # Create or get test vehicle
    vehicle, created = Vehicle.objects.get_or_create(
        vin='DEMO123456789',
        defaults={
            'make': 'Toyota',
            'model': 'Camry',
            'manufacture_year': 2020
        }
    )
    
    # Create or get test assessment
    assessment, created = VehicleAssessment.objects.get_or_create(
        assessment_id='DEMO-ASSESS-001',
        defaults={
            'vehicle': vehicle,
            'user': user,
            'assessment_type': 'insurance_claim',
            'status': 'in_progress',
            'assessor_name': 'Demo Assessor',
            'overall_severity': 'moderate'
        }
    )
    
    # Create damaged part
    damaged_part, created = DamagedPart.objects.get_or_create(
        assessment=assessment,
        part_name='Front Bumper',
        defaults={
            'section_type': 'exterior',
            'part_category': 'body',
            'damage_severity': 'moderate',
            'damage_description': 'Scratches and dent on front bumper',
            'estimated_labor_hours': Decimal('2.5')
        }
    )
    
    # Create quote request
    quote_request, created = PartQuoteRequest.objects.get_or_create(
        damaged_part=damaged_part,
        assessment=assessment,
        defaults={
            'expiry_date': timezone.now() + timedelta(days=7),
            'vehicle_make': 'Toyota',
            'vehicle_model': 'Camry',
            'vehicle_year': 2020,
            'dispatched_by': user
        }
    )
    
    # Clear existing quotes for clean demo
    PartQuote.objects.filter(quote_request=quote_request).delete()
    
    # Create sample quotes with different characteristics
    quotes_data = [
        {
            'provider_name': 'Premium Toyota Dealer',
            'provider_type': 'dealer',
            'total_cost': 1400,
            'part_type': 'oem',
            'delivery_days': 3,
            'completion_days': 5,
            'part_warranty': 24,
            'labor_warranty': 12,
            'confidence': 95,
            'part_manufacturer': 'Toyota',
            'part_number': 'TOY-52119-06903',
            'notes': 'Genuine OEM part with full Toyota warranty'
        },
        {
            'provider_name': 'Budget Auto Parts',
            'provider_type': 'independent',
            'total_cost': 650,
            'part_type': 'aftermarket_standard',
            'delivery_days': 10,
            'completion_days': 14,
            'part_warranty': 12,
            'labor_warranty': 6,
            'confidence': 65,
            'part_manufacturer': 'Generic',
            'notes': 'Aftermarket part, good value option'
        },
        {
            'provider_name': 'Network Auto Solutions',
            'provider_type': 'network',
            'total_cost': 950,
            'part_type': 'oem_equivalent',
            'delivery_days': 5,
            'completion_days': 7,
            'part_warranty': 18,
            'labor_warranty': 12,
            'confidence': 85,
            'part_manufacturer': 'OEM Equivalent',
            'part_number': 'NET-52119-EQ',
            'notes': 'OEM equivalent part with good warranty'
        },
        {
            'provider_name': 'Express Repair Shop',
            'provider_type': 'independent',
            'total_cost': 1100,
            'part_type': 'oem',
            'delivery_days': 2,
            'completion_days': 3,
            'part_warranty': 12,
            'labor_warranty': 12,
            'confidence': 80,
            'part_manufacturer': 'Toyota',
            'notes': 'Fast service with OEM parts'
        },
        {
            'provider_name': 'Cheap & Quick',
            'provider_type': 'independent',
            'total_cost': 480,
            'part_type': 'generic',
            'delivery_days': 7,
            'completion_days': 10,
            'part_warranty': 6,
            'labor_warranty': 3,
            'confidence': 50,
            'notes': 'Basic quality, lowest price option'
        }
    ]
    
    quotes = []
    for quote_data in quotes_data:
        total_cost = quote_data['total_cost']
        quote = PartQuote.objects.create(
            quote_request=quote_request,
            damaged_part=damaged_part,
            provider_name=quote_data['provider_name'],
            provider_type=quote_data['provider_type'],
            part_cost=Decimal(str(total_cost * 0.7)),
            labor_cost=Decimal(str(total_cost * 0.25)),
            paint_cost=Decimal(str(total_cost * 0.05)),
            additional_costs=Decimal('0'),
            total_cost=Decimal(str(total_cost)),
            part_type=quote_data['part_type'],
            estimated_delivery_days=quote_data['delivery_days'],
            estimated_completion_days=quote_data['completion_days'],
            part_warranty_months=quote_data['part_warranty'],
            labor_warranty_months=quote_data['labor_warranty'],
            confidence_score=quote_data['confidence'],
            valid_until=timezone.now() + timedelta(days=30),
            status='validated',
            part_manufacturer=quote_data.get('part_manufacturer', ''),
            part_number_quoted=quote_data.get('part_number', ''),
            notes=quote_data.get('notes', '')
        )
        quotes.append(quote)
    
    print(f"Created {len(quotes)} demo quotes")
    return damaged_part, quotes


def demo_recommendation_engine():
    """Demonstrate the recommendation engine functionality"""
    print("\n" + "="*60)
    print("QUOTE RECOMMENDATION ENGINE DEMO")
    print("="*60)
    
    # Create demo data
    damaged_part, quotes = create_demo_data()
    
    # Initialize recommendation engine
    engine = QuoteRecommendationEngine()
    
    print(f"\nAnalyzing {len(quotes)} quotes for: {damaged_part.part_name}")
    print("-" * 50)
    
    # Display all quotes
    print("\nAVAILABLE QUOTES:")
    for i, quote in enumerate(quotes, 1):
        print(f"{i}. {quote.provider_name} ({quote.provider_type})")
        print(f"   Cost: £{quote.total_cost}")
        print(f"   Part: {quote.part_type}")
        print(f"   Timeline: {quote.estimated_delivery_days}d delivery, {quote.estimated_completion_days}d completion")
        print(f"   Warranty: {quote.part_warranty_months}m part, {quote.labor_warranty_months}m labor")
        print(f"   Confidence: {quote.confidence_score}%")
        print()
    
    # Calculate scores
    scores = engine.calculate_provider_scores(quotes)
    
    print("DETAILED SCORING:")
    print("-" * 50)
    for quote in quotes:
        score = scores[quote.id]
        print(f"\n{quote.provider_name}:")
        print(f"  Total Score: {score.total_score:.1f}/100")
        print(f"  Price Score: {score.price_score:.1f}/100")
        print(f"  Quality Score: {score.quality_score:.1f}/100")
        print(f"  Timeline Score: {score.timeline_score:.1f}/100")
        print(f"  Warranty Score: {score.warranty_score:.1f}/100")
        print(f"  Reliability Score: {score.reliability_score:.1f}/100")
        print(f"  Reasoning: {score.reasoning}")
    
    # Generate recommendation
    recommendation = engine.generate_recommendation(damaged_part)
    
    print("\n" + "="*60)
    print("RECOMMENDATION RESULTS")
    print("="*60)
    
    if recommendation.recommended_quotes:
        recommended = recommendation.recommended_quotes[0]
        print(f"\nRECOMMENDED PROVIDER: {recommended.provider_name}")
        print(f"Cost: £{recommendation.total_cost}")
        print(f"Potential Savings: £{recommendation.potential_savings}")
        print(f"Confidence Level: {recommendation.confidence_level}%")
        print(f"\nReasoning: {recommendation.reasoning}")
        
        print(f"\nALTERNATIVE STRATEGIES:")
        for strategy, quotes_list in recommendation.alternative_strategies.items():
            if quotes_list:
                alt_quote = quotes_list[0]
                strategy_name = strategy.replace('_', ' ').title()
                print(f"  {strategy_name}: {alt_quote.provider_name} - £{alt_quote.total_cost}")
    
    # Calculate potential savings
    savings = engine.potential_savings_calculator(quotes)
    
    print(f"\nPOTENTIAL SAVINGS ANALYSIS:")
    print(f"  Highest Quote: £{savings['highest_quote']}")
    print(f"  Lowest Quote: £{savings['lowest_quote']}")
    print(f"  Average Quote: £{savings['average_quote']:.2f}")
    print(f"  Maximum Savings: £{savings['max_savings']}")
    print(f"  Savings Percentage: {savings['savings_percentage']:.1f}%")
    
    # Test custom weights
    print(f"\n" + "="*60)
    print("CUSTOM WEIGHTS DEMONSTRATION")
    print("="*60)
    
    # Price-focused recommendation
    price_focused_engine = QuoteRecommendationEngine({
        'price': 0.70, 'quality': 0.10, 'timeline': 0.10, 'warranty': 0.05, 'reliability': 0.05
    })
    price_recommendation = price_focused_engine.generate_recommendation(damaged_part)
    
    print(f"\nPRICE-FOCUSED RECOMMENDATION (70% price weight):")
    if price_recommendation.recommended_quotes:
        rec = price_recommendation.recommended_quotes[0]
        print(f"  Provider: {rec.provider_name}")
        print(f"  Cost: £{rec.total_cost}")
    
    # Quality-focused recommendation
    quality_focused_engine = QuoteRecommendationEngine({
        'price': 0.10, 'quality': 0.70, 'timeline': 0.10, 'warranty': 0.05, 'reliability': 0.05
    })
    quality_recommendation = quality_focused_engine.generate_recommendation(damaged_part)
    
    print(f"\nQUALITY-FOCUSED RECOMMENDATION (70% quality weight):")
    if quality_recommendation.recommended_quotes:
        rec = quality_recommendation.recommended_quotes[0]
        print(f"  Provider: {rec.provider_name}")
        print(f"  Cost: £{rec.total_cost}")
    
    print(f"\n" + "="*60)
    print("DEMO COMPLETED SUCCESSFULLY!")
    print("="*60)


if __name__ == '__main__':
    demo_recommendation_engine()