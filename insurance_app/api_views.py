# api_views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import (
    DamagedPart, PartQuoteRequest, PartQuote, 
    PartMarketAverage, AssessmentQuoteSummary
)
from .serializers import (
    DamagedPartSerializer, PartQuoteRequestSerializer, PartQuoteSerializer,
    PartMarketAverageSerializer, AssessmentQuoteSummarySerializer
)
from .quote_managers import PartQuoteRequestManager
from .market_analysis import MarketAverageCalculator
from .recommendation_engine import QuoteRecommendationEngine


class DamagedPartViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing damaged parts identified from vehicle assessments.
    Provides CRUD operations and additional actions for parts management.
    """
    serializer_class = DamagedPartSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter damaged parts by user's assessments"""
        return DamagedPart.objects.filter(
            assessment__user=self.request.user
        ).select_related(
            'assessment', 'assessment__vehicle'
        ).prefetch_related('damage_images', 'quotes')
    
    def perform_create(self, serializer):
        """Ensure user can only create parts for their assessments"""
        assessment = serializer.validated_data['assessment']
        if assessment.user != self.request.user:
            raise permissions.PermissionDenied("Cannot create parts for other users' assessments")
        serializer.save()
    
    @action(detail=False, methods=['get'])
    def by_assessment(self, request):
        """Get damaged parts for a specific assessment"""
        assessment_id = request.query_params.get('assessment_id')
        if not assessment_id:
            return Response(
                {'error': 'assessment_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        parts = self.get_queryset().filter(assessment__assessment_id=assessment_id)
        serializer = self.get_serializer(parts, many=True)
        
        # Add summary statistics
        summary = {
            'total_parts': parts.count(),
            'parts_by_category': dict(parts.values_list('part_category').annotate(Count('id'))),
            'parts_by_severity': dict(parts.values_list('damage_severity').annotate(Count('id'))),
            'total_estimated_labor': sum(float(p.estimated_labor_hours) for p in parts)
        }
        
        return Response({
            'parts': serializer.data,
            'summary': summary
        })
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get damaged parts grouped by category"""
        category = request.query_params.get('category')
        if not category:
            return Response(
                {'error': 'category parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        parts = self.get_queryset().filter(part_category=category)
        serializer = self.get_serializer(parts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_damage_image(self, request, pk=None):
        """Add damage image to a part"""
        part = self.get_object()
        image_id = request.data.get('image_id')
        
        if not image_id:
            return Response(
                {'error': 'image_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from assessments.models import AssessmentPhoto
            photo = AssessmentPhoto.objects.get(
                id=image_id, 
                assessment=part.assessment
            )
            part.damage_images.add(photo)
            return Response({'status': 'Image added successfully'})
        except AssessmentPhoto.DoesNotExist:
            return Response(
                {'error': 'Image not found or not associated with this assessment'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def update_labor_estimate(self, request, pk=None):
        """Update estimated labor hours for a part"""
        part = self.get_object()
        labor_hours = request.data.get('labor_hours')
        
        if labor_hours is None:
            return Response(
                {'error': 'labor_hours is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            part.estimated_labor_hours = float(labor_hours)
            part.save()
            return Response({
                'status': 'Labor estimate updated',
                'new_labor_hours': part.estimated_labor_hours
            })
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid labor_hours value'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class PartQuoteRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing quote requests sent to providers.
    Handles creation, dispatch, and tracking of quote requests.
    """
    serializer_class = PartQuoteRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter quote requests by user's assessments"""
        return PartQuoteRequest.objects.filter(
            assessment__user=self.request.user
        ).select_related(
            'damaged_part', 'assessment', 'dispatched_by'
        ).prefetch_related('quotes')
    
    def perform_create(self, serializer):
        """Set dispatched_by to current user and validate assessment ownership"""
        assessment = serializer.validated_data['assessment']
        if assessment.user != self.request.user:
            raise permissions.PermissionDenied("Cannot create requests for other users' assessments")
        
        serializer.save(dispatched_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def create_batch_requests(self, request):
        """Create quote requests for multiple parts at once"""
        assessment_id = request.data.get('assessment_id')
        part_ids = request.data.get('part_ids', [])
        provider_selection = request.data.get('providers', {})
        
        if not assessment_id or not part_ids:
            return Response(
                {'error': 'assessment_id and part_ids are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Validate assessment ownership
            from assessments.models import VehicleAssessment
            assessment = VehicleAssessment.objects.get(
                assessment_id=assessment_id,
                user=request.user
            )
            
            # Create requests using manager
            manager = PartQuoteRequestManager()
            requests = manager.batch_create_requests_for_parts(
                assessment=assessment,
                part_ids=part_ids,
                provider_selection=provider_selection,
                user=request.user
            )
            
            serializer = self.get_serializer(requests, many=True)
            return Response({
                'status': 'Batch requests created successfully',
                'requests': serializer.data,
                'count': len(requests)
            })
            
        except VehicleAssessment.DoesNotExist:
            return Response(
                {'error': 'Assessment not found or access denied'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to create batch requests: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def dispatch_request(self, request, pk=None):
        """Dispatch quote request to selected providers"""
        quote_request = self.get_object()
        
        if quote_request.status != 'draft':
            return Response(
                {'error': 'Only draft requests can be dispatched'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            manager = PartQuoteRequestManager()
            success = manager.dispatch_quote_request(quote_request)
            
            if success:
                quote_request.status = 'sent'
                quote_request.dispatched_at = timezone.now()
                quote_request.save()
                
                return Response({
                    'status': 'Request dispatched successfully',
                    'request_id': quote_request.request_id
                })
            else:
                return Response(
                    {'error': 'Failed to dispatch request'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            return Response(
                {'error': f'Dispatch failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def pending_requests(self, request):
        """Get all pending quote requests"""
        pending = self.get_queryset().filter(
            status__in=['draft', 'pending', 'sent'],
            expiry_date__gt=timezone.now()
        )
        serializer = self.get_serializer(pending, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expired_requests(self, request):
        """Get all expired quote requests"""
        expired = self.get_queryset().filter(
            Q(expiry_date__lte=timezone.now()) | Q(status='expired')
        )
        serializer = self.get_serializer(expired, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def extend_expiry(self, request, pk=None):
        """Extend expiry date for a quote request"""
        quote_request = self.get_object()
        days_to_extend = request.data.get('days', 7)
        
        try:
            quote_request.expiry_date = quote_request.expiry_date + timedelta(days=int(days_to_extend))
            quote_request.save()
            
            return Response({
                'status': 'Expiry date extended',
                'new_expiry_date': quote_request.expiry_date
            })
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid days value'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class PartQuoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing quotes received from providers.
    Handles quote submission, validation, and retrieval.
    """
    serializer_class = PartQuoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter quotes by user's quote requests"""
        return PartQuote.objects.filter(
            quote_request__assessment__user=self.request.user
        ).select_related(
            'quote_request', 'damaged_part', 'quote_request__assessment'
        )
    
    def perform_create(self, serializer):
        """Validate quote request ownership before creating quote"""
        quote_request = serializer.validated_data['quote_request']
        if quote_request.assessment.user != self.request.user:
            raise permissions.PermissionDenied("Cannot create quotes for other users' requests")
        serializer.save()
    
    @action(detail=False, methods=['get'])
    def by_request(self, request):
        """Get quotes for a specific quote request"""
        request_id = request.query_params.get('request_id')
        if not request_id:
            return Response(
                {'error': 'request_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        quotes = self.get_queryset().filter(quote_request__request_id=request_id)
        serializer = self.get_serializer(quotes, many=True)
        
        # Add comparison data
        if quotes.exists():
            costs = [float(q.total_cost) for q in quotes]
            comparison = {
                'lowest_cost': min(costs),
                'highest_cost': max(costs),
                'average_cost': sum(costs) / len(costs),
                'cost_variance': max(costs) - min(costs)
            }
        else:
            comparison = {}
        
        return Response({
            'quotes': serializer.data,
            'comparison': comparison
        })
    
    @action(detail=False, methods=['get'])
    def by_provider_type(self, request):
        """Get quotes filtered by provider type"""
        provider_type = request.query_params.get('provider_type')
        if not provider_type:
            return Response(
                {'error': 'provider_type parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        quotes = self.get_queryset().filter(provider_type=provider_type)
        serializer = self.get_serializer(quotes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def validate_quote(self, request, pk=None):
        """Validate a submitted quote"""
        quote = self.get_object()
        
        if quote.status != 'submitted':
            return Response(
                {'error': 'Only submitted quotes can be validated'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Perform validation checks
        validation_errors = []
        
        # Check required fields
        if not quote.part_cost or quote.part_cost <= 0:
            validation_errors.append('Invalid part cost')
        if not quote.labor_cost or quote.labor_cost < 0:
            validation_errors.append('Invalid labor cost')
        if not quote.estimated_delivery_days or quote.estimated_delivery_days <= 0:
            validation_errors.append('Invalid delivery timeline')
        
        # Check if quote is still valid
        if not quote.is_valid():
            validation_errors.append('Quote has expired')
        
        if validation_errors:
            return Response(
                {'error': 'Validation failed', 'details': validation_errors}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        quote.status = 'validated'
        quote.save()
        
        return Response({
            'status': 'Quote validated successfully',
            'quote_id': quote.id
        })
    
    @action(detail=True, methods=['post'])
    def accept_quote(self, request, pk=None):
        """Accept a validated quote"""
        quote = self.get_object()
        
        if quote.status != 'validated':
            return Response(
                {'error': 'Only validated quotes can be accepted'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        quote.status = 'accepted'
        quote.save()
        
        # Update quote request status
        quote.quote_request.status = 'received'
        quote.quote_request.save()
        
        return Response({
            'status': 'Quote accepted successfully',
            'quote_id': quote.id
        })
    
    @action(detail=False, methods=['get'])
    def comparison_report(self, request):
        """Generate comparison report for quotes"""
        assessment_id = request.query_params.get('assessment_id')
        if not assessment_id:
            return Response(
                {'error': 'assessment_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        quotes = self.get_queryset().filter(
            quote_request__assessment__assessment_id=assessment_id,
            status='validated'
        )
        
        # Group quotes by provider type
        provider_comparison = {}
        for provider_type, _ in PartQuote.PROVIDER_TYPES:
            provider_quotes = quotes.filter(provider_type=provider_type)
            if provider_quotes.exists():
                costs = [float(q.total_cost) for q in provider_quotes]
                provider_comparison[provider_type] = {
                    'quote_count': provider_quotes.count(),
                    'total_cost': sum(costs),
                    'average_cost': sum(costs) / len(costs),
                    'lowest_cost': min(costs),
                    'highest_cost': max(costs)
                }
        
        return Response({
            'assessment_id': assessment_id,
            'provider_comparison': provider_comparison,
            'total_quotes': quotes.count()
        })


class MarketAverageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for accessing market average calculations and statistics.
    Provides read-only access to market data with calculation triggers.
    """
    serializer_class = PartMarketAverageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter market averages by user's damaged parts"""
        return PartMarketAverage.objects.filter(
            damaged_part__assessment__user=self.request.user
        ).select_related('damaged_part', 'damaged_part__assessment')
    
    @action(detail=False, methods=['post'])
    def calculate_for_part(self, request):
        """Calculate market average for a specific damaged part"""
        part_id = request.data.get('part_id')
        if not part_id:
            return Response(
                {'error': 'part_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            damaged_part = DamagedPart.objects.get(
                id=part_id,
                assessment__user=request.user
            )
            
            calculator = MarketAverageCalculator()
            market_average = calculator.calculate_market_average(damaged_part)
            
            serializer = self.get_serializer(market_average)
            return Response({
                'status': 'Market average calculated successfully',
                'market_average': serializer.data
            })
            
        except DamagedPart.DoesNotExist:
            return Response(
                {'error': 'Damaged part not found or access denied'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Calculation failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def calculate_for_assessment(self, request):
        """Calculate market averages for all parts in an assessment"""
        assessment_id = request.data.get('assessment_id')
        if not assessment_id:
            return Response(
                {'error': 'assessment_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from assessments.models import VehicleAssessment
            assessment = VehicleAssessment.objects.get(
                assessment_id=assessment_id,
                user=request.user
            )
            
            calculator = MarketAverageCalculator()
            results = calculator.calculate_assessment_market_average(assessment)
            
            return Response({
                'status': 'Market averages calculated successfully',
                'assessment_id': assessment_id,
                'results': results
            })
            
        except VehicleAssessment.DoesNotExist:
            return Response(
                {'error': 'Assessment not found or access denied'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Calculation failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def high_confidence_averages(self, request):
        """Get market averages with high confidence levels"""
        high_confidence = self.get_queryset().filter(confidence_level__gte=70)
        serializer = self.get_serializer(high_confidence, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_part_category(self, request):
        """Get market averages grouped by part category"""
        category = request.query_params.get('category')
        if not category:
            return Response(
                {'error': 'category parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        averages = self.get_queryset().filter(damaged_part__part_category=category)
        serializer = self.get_serializer(averages, many=True)
        
        # Calculate category statistics
        if averages.exists():
            costs = [float(avg.average_total_cost) for avg in averages]
            category_stats = {
                'count': len(costs),
                'average_cost': sum(costs) / len(costs),
                'min_cost': min(costs),
                'max_cost': max(costs),
                'high_confidence_count': averages.filter(confidence_level__gte=70).count()
            }
        else:
            category_stats = {}
        
        return Response({
            'market_averages': serializer.data,
            'category_statistics': category_stats
        })


class QuoteRecommendationViewSet(viewsets.ViewSet):
    """
    ViewSet for generating and managing quote recommendations.
    Provides intelligent recommendations based on multiple criteria.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def generate_for_assessment(self, request):
        """Generate recommendations for all parts in an assessment"""
        assessment_id = request.data.get('assessment_id')
        strategy = request.data.get('strategy', 'best_value')
        
        if not assessment_id:
            return Response(
                {'error': 'assessment_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from assessments.models import VehicleAssessment
            assessment = VehicleAssessment.objects.get(
                assessment_id=assessment_id,
                user=request.user
            )
            
            engine = QuoteRecommendationEngine()
            recommendations = engine.generate_assessment_recommendations(
                assessment, strategy
            )
            
            return Response({
                'status': 'Recommendations generated successfully',
                'assessment_id': assessment_id,
                'strategy': strategy,
                'recommendations': recommendations
            })
            
        except VehicleAssessment.DoesNotExist:
            return Response(
                {'error': 'Assessment not found or access denied'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Recommendation generation failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def generate_for_part(self, request):
        """Generate recommendation for a specific damaged part"""
        part_id = request.data.get('part_id')
        strategy = request.data.get('strategy', 'best_value')
        
        if not part_id:
            return Response(
                {'error': 'part_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            damaged_part = DamagedPart.objects.get(
                id=part_id,
                assessment__user=request.user
            )
            
            engine = QuoteRecommendationEngine()
            recommendation = engine.generate_recommendation(damaged_part, strategy)
            
            return Response({
                'status': 'Recommendation generated successfully',
                'part_id': part_id,
                'strategy': strategy,
                'recommendation': recommendation
            })
            
        except DamagedPart.DoesNotExist:
            return Response(
                {'error': 'Damaged part not found or access denied'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Recommendation generation failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def available_strategies(self, request):
        """Get list of available recommendation strategies"""
        strategies = [
            {
                'key': 'best_value',
                'name': 'Best Value',
                'description': 'Balanced recommendation considering price, quality, timeline, and reliability'
            },
            {
                'key': 'lowest_price',
                'name': 'Lowest Price',
                'description': 'Focus on minimizing cost'
            },
            {
                'key': 'fastest_completion',
                'name': 'Fastest Completion',
                'description': 'Prioritize shortest completion time'
            },
            {
                'key': 'highest_quality',
                'name': 'Highest Quality',
                'description': 'Focus on OEM parts and premium providers'
            }
        ]
        
        return Response({'strategies': strategies})
    
    @action(detail=False, methods=['post'])
    def calculate_savings(self, request):
        """Calculate potential savings for different recommendation strategies"""
        assessment_id = request.data.get('assessment_id')
        
        if not assessment_id:
            return Response(
                {'error': 'assessment_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from assessments.models import VehicleAssessment
            assessment = VehicleAssessment.objects.get(
                assessment_id=assessment_id,
                user=request.user
            )
            
            engine = QuoteRecommendationEngine()
            savings_analysis = engine.calculate_potential_savings(assessment)
            
            return Response({
                'status': 'Savings analysis completed',
                'assessment_id': assessment_id,
                'savings_analysis': savings_analysis
            })
            
        except VehicleAssessment.DoesNotExist:
            return Response(
                {'error': 'Assessment not found or access denied'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Savings calculation failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# Additional API endpoints for parts review interface

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def identify_parts_for_assessment(request, assessment_id):
    """
    API endpoint to identify damaged parts from assessment data
    """
    try:
        from assessments.models import VehicleAssessment
        assessment = get_object_or_404(
            VehicleAssessment, 
            id=assessment_id, 
            user=request.user
        )
        
        # Import parts identification service
        from .parts_identification import PartsIdentificationService
        
        service = PartsIdentificationService()
        identified_parts = service.identify_damaged_parts(assessment)
        
        # Mark parts identification as complete
        assessment.parts_identification_complete = True
        assessment.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully identified {len(identified_parts)} damaged parts',
            'parts_count': len(identified_parts),
            'parts': [
                {
                    'id': part.id,
                    'part_name': part.part_name,
                    'category': part.part_category,
                    'severity': part.damage_severity,
                    'section': part.section_type
                } for part in identified_parts
            ]
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error identifying parts: {str(e)}'
        }, status=500)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_damaged_part(request, assessment_id):
    """
    API endpoint to create a new damaged part for an assessment
    """
    try:
        from assessments.models import VehicleAssessment
        assessment = get_object_or_404(
            VehicleAssessment, 
            id=assessment_id, 
            user=request.user
        )
        
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['part_name', 'part_category', 'damage_severity', 'damage_description']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }, status=400)
        
        # Create the damaged part
        damaged_part = DamagedPart.objects.create(
            assessment=assessment,
            section_type=data.get('section_type', 'exterior'),
            part_name=data['part_name'],
            part_number=data.get('part_number', ''),
            part_category=data['part_category'],
            damage_severity=data['damage_severity'],
            damage_description=data['damage_description'],
            requires_replacement=data['damage_severity'] == 'replace',
            estimated_labor_hours=float(data.get('estimated_labor_hours', 0))
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Damaged part created successfully',
            'part': {
                'id': damaged_part.id,
                'part_name': damaged_part.part_name,
                'category': damaged_part.part_category,
                'severity': damaged_part.damage_severity,
                'labor_hours': float(damaged_part.estimated_labor_hours)
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating part: {str(e)}'
        }, status=500)


@api_view(['PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def manage_damaged_part(request, part_id):
    """
    API endpoint to update or delete a damaged part
    """
    try:
        damaged_part = get_object_or_404(
            DamagedPart,
            id=part_id,
            assessment__user=request.user
        )
        
        if request.method == 'PATCH':
            data = json.loads(request.body)
            
            # Update allowed fields
            allowed_fields = [
                'part_name', 'part_number', 'part_category', 'damage_severity',
                'damage_description', 'estimated_labor_hours', 'section_type'
            ]
            
            for field, value in data.items():
                if field in allowed_fields:
                    if field == 'estimated_labor_hours':
                        value = float(value)
                    elif field == 'requires_replacement':
                        value = bool(value)
                    setattr(damaged_part, field, value)
            
            # Auto-set requires_replacement based on severity
            if 'damage_severity' in data:
                damaged_part.requires_replacement = data['damage_severity'] == 'replace'
            
            damaged_part.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Part updated successfully',
                'part': {
                    'id': damaged_part.id,
                    'part_name': damaged_part.part_name,
                    'category': damaged_part.part_category,
                    'severity': damaged_part.damage_severity,
                    'labor_hours': float(damaged_part.estimated_labor_hours)
                }
            })
            
        elif request.method == 'DELETE':
            part_name = damaged_part.part_name
            damaged_part.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Part "{part_name}" deleted successfully'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error managing part: {str(e)}'
        }, status=500)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_quote_requests(request, assessment_id):
    """
    API endpoint to create quote requests for selected parts
    """
    try:
        from assessments.models import VehicleAssessment
        assessment = get_object_or_404(
            VehicleAssessment, 
            id=assessment_id, 
            user=request.user
        )
        
        data = json.loads(request.body)
        part_ids = data.get('part_ids', [])
        providers = data.get('providers', [])
        
        if not part_ids:
            return JsonResponse({
                'success': False,
                'message': 'No parts selected for quote request'
            }, status=400)
        
        if not providers:
            return JsonResponse({
                'success': False,
                'message': 'No providers selected for quote request'
            }, status=400)
        
        # Validate parts belong to this assessment
        damaged_parts = DamagedPart.objects.filter(
            id__in=part_ids,
            assessment=assessment
        )
        
        if damaged_parts.count() != len(part_ids):
            return JsonResponse({
                'success': False,
                'message': 'Some parts do not belong to this assessment'
            }, status=400)
        
        # Create quote requests using the manager
        from .quote_managers import PartQuoteRequestManager
        manager = PartQuoteRequestManager()
        
        provider_selection = {
            'include_assessor': 'assessor' in providers,
            'include_dealer': 'dealer' in providers,
            'include_independent': 'independent' in providers,
            'include_network': 'network' in providers,
        }
        
        requests = manager.batch_create_requests_for_parts(
            assessment=assessment,
            part_ids=part_ids,
            provider_selection=provider_selection,
            user=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Quote requests created successfully',
            'requests_created': len(requests),
            'requests': [
                {
                    'id': req.id,
                    'request_id': req.request_id,
                    'part_name': req.damaged_part.part_name,
                    'status': req.status,
                    'expiry_date': req.expiry_date.isoformat()
                } for req in requests
            ]
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating quote requests: {str(e)}'
        }, status=500)