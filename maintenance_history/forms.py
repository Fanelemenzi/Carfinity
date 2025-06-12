from django import forms
from .models import MaintenanceRecord

class MaintenanceRecordForm(forms.ModelForm):
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
