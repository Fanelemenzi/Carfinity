from django.views.generic import CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import MaintenanceRecord
from .forms import MaintenanceRecordForm

class TechnicianDashboardView(LoginRequiredMixin, ListView):
    model = MaintenanceRecord
    template_name = 'maintenance/technician_dashboard.html'
    context_object_name = 'records'
    
    def get_queryset(self):
        return MaintenanceRecord.objects.filter(
            technician=self.request.user
        ).order_by('-date_performed')[:10]

class CreateMaintenanceRecordView(LoginRequiredMixin, CreateView):
    model = MaintenanceRecord
    form_class = MaintenanceRecordForm
    template_name = 'maintenance/create_record.html'
    success_url = '/technician-dashboard/'
    
    def form_valid(self, form):
        form.instance.technician = self.request.user
        return super().form_valid(form)