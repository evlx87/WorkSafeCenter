from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DeleteView

from .forms import DocumentForm
from .models import Document


# Create your views here.
class DocumentListView(ListView):
    model = Document
    template_name = 'documents/documents_list.html'
    context_object_name = 'documents'
    ordering = ['-upload_date']


class DocumentCreateView(CreateView):
    model = Document
    form_class = DocumentForm
    template_name = 'documents/document_form.html'
    success_url = reverse_lazy('documents:documents_list')


class DocumentDeleteView(DeleteView):
    model = Document
    template_name = 'documents/document_confirm_delete.html'
    success_url = reverse_lazy('documents:documents_list')
