from django import forms
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import MaintenanceRecord, PartUsage, Inspection
from maintenance.models import Part
import json

class MaintenanceRecordForm(forms.ModelForm):
    # Hidden field to store part selection data from JavaScript
    parts_data = forms.CharField(widget=forms.HiddenInput(), required=False)
    
    class Meta:
        model = MaintenanceRecord
        fields = [
            'vehicle', 
            'scheduled_maintenance',
            'work_done',
            'mileage',
            'notes'
        ]
        widgets = {
            'vehicle': forms.Select(attrs={'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500'}),
            'scheduled_maintenance': forms.Select(attrs={'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500'}),
            'work_done': forms.Textarea(attrs={
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Describe work performed...'
            }),
            'mileage': forms.NumberInput(attrs={'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500'}),
            'notes': forms.Textarea(attrs={
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'rows': 2,
                'placeholder': 'Additional notes...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selected_parts = []
        
    def clean_parts_data(self):
        """Validate and parse parts data from JavaScript"""
        parts_data = self.cleaned_data.get('parts_data', '')
        
        if not parts_data:
            return []
            
        try:
            parts_list = json.loads(parts_data)
        except json.JSONDecodeError:
            raise ValidationError("Invalid parts data format.")
            
        if not isinstance(parts_list, list):
            raise ValidationError("Parts data must be a list.")
            
        validated_parts = []
        for part_data in parts_list:
            if not isinstance(part_data, dict):
                raise ValidationError("Each part entry must be an object.")
                
            # Validate required fields
            required_fields = ['id', 'quantity']
            for field in required_fields:
                if field not in part_data:
                    raise ValidationError(f"Missing required field: {field}")
                    
            part_id = part_data.get('id')
            quantity = part_data.get('quantity')
            
            # Validate part exists
            try:
                part = Part.objects.get(id=part_id)
            except Part.DoesNotExist:
                raise ValidationError(f"Part with ID {part_id} does not exist.")
                
            # Validate quantity
            try:
                quantity = int(quantity)
                if quantity <= 0:
                    raise ValidationError(f"Quantity for {part.name} must be greater than 0.")
            except (ValueError, TypeError):
                raise ValidationError(f"Invalid quantity for {part.name}.")
                
            # Validate stock availability
            if part.stock_quantity < quantity:
                raise ValidationError(
                    f"Insufficient stock for {part.name}. "
                    f"Available: {part.stock_quantity}, Requested: {quantity}"
                )
                
            validated_parts.append({
                'part': part,
                'quantity': quantity,
                'unit_cost': part.cost
            })
            
        return validated_parts
        
    def clean(self):
        """Additional form validation"""
        cleaned_data = super().clean()
        
        # Store validated parts for use in save method
        self.selected_parts = self.clean_parts_data()
        
        return cleaned_data
        
    @transaction.atomic
    def save(self, commit=True):
        """Save maintenance record and associated part usage records"""
        # Save the maintenance record
        maintenance_record = super().save(commit=commit)
        
        if commit and self.selected_parts:
            # Create PartUsage records and update inventory
            for part_data in self.selected_parts:
                part = part_data['part']
                quantity = part_data['quantity']
                unit_cost = part_data['unit_cost']
                
                # Create PartUsage record
                PartUsage.objects.create(
                    maintenance_record=maintenance_record,
                    part=part,
                    quantity=quantity,
                    unit_cost=unit_cost
                )
                
                # Update part inventory
                if not part.reduce_stock(quantity):
                    raise ValidationError(
                        f"Failed to update stock for {part.name}. "
                        f"This may be due to concurrent modifications."
                    )
                    
        return maintenance_record
        
    def get_selected_parts_summary(self):
        """Get summary of selected parts for display"""
        if not self.selected_parts:
            return []
            
        summary = []
        total_cost = 0
        
        for part_data in self.selected_parts:
            part = part_data['part']
            quantity = part_data['quantity']
            unit_cost = part_data['unit_cost'] or 0
            line_total = unit_cost * quantity
            total_cost += line_total
            
            summary.append({
                'name': part.name,
                'part_number': part.part_number,
                'quantity': quantity,
                'unit_cost': unit_cost,
                'line_total': line_total
            })
            
        return {
            'parts': summary,
            'total_cost': total_cost
        }

class InspectionForm(forms.ModelForm):
    class Meta:
        model = Inspection
        fields = [
            'vehicle',
            'inspection_number',
            'year',
            'inspection_result',
            'carfinity_rating',
            'inspection_date',
            'link_to_results',
            'inspection_pdf'
        ]
        widgets = {
            'vehicle': forms.Select(attrs={
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500'
            }),
            'inspection_number': forms.TextInput(attrs={
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Enter inspection number'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'min': '1900',
                'max': '2100'
            }),
            'inspection_result': forms.Select(attrs={
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500'
            }),
            'carfinity_rating': forms.TextInput(attrs={
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Enter Carfinity rating'
            }),
            'inspection_date': forms.DateInput(attrs={
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'type': 'date'
            }),
            'link_to_results': forms.URLInput(attrs={
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'https://example.com/inspection-results'
            }),
            'inspection_pdf': forms.FileInput(attrs={
                'class': 'w-full mt-1 block text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100',
                'accept': '.pdf'
            })
        }
    
    def clean_inspection_pdf(self):
        pdf_file = self.cleaned_data.get('inspection_pdf')
        
        if pdf_file:
            # Check file size (limit to 10MB)
            if pdf_file.size > 10 * 1024 * 1024:
                raise ValidationError("PDF file size cannot exceed 10MB.")
            
            # Check file extension
            if not pdf_file.name.lower().endswith('.pdf'):
                raise ValidationError("Only PDF files are allowed.")
        
        return pdf_file
    
    def clean_inspection_number(self):
        inspection_number = self.cleaned_data.get('inspection_number')
        
        # Check for uniqueness (excluding current instance if editing)
        queryset = Inspection.objects.filter(inspection_number=inspection_number)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise ValidationError("An inspection with this number already exists.")
        
        return inspection_number