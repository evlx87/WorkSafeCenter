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

    def get_queryset(self):
        queryset = super().get_queryset().select_related('employee')
        search_query = self.request.GET.get('search_query', '')
        doc_type = self.request.GET.get('doc_type', '')

        if search_query:
            queryset = queryset.filter(title__icontains=search_query)

        if doc_type:
            queryset = queryset.filter(document_type=doc_type)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Передаем типы документов и текущие значения фильтров в шаблон
        context['doc_types'] = Document.DOCUMENT_TYPES
        context['search_query'] = self.request.GET.get('search_query', '')
        context['selected_doc_type'] = self.request.GET.get('doc_type', '')
        return context


class DocumentCreateView(CreateView):
    model = Document
    form_class = DocumentForm
    template_name = 'documents/document_form.html'
    success_url = reverse_lazy('documents:documents_list')


class DocumentDeleteView(DeleteView):
    model = Document
    template_name = 'documents/document_confirm_delete.html'
    success_url = reverse_lazy('documents:documents_list')
