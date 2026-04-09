from django.urls import path
from . import views

urlpatterns = [
    path('',                  views.search,            name='search'),
    path('docs/',             views.document_list,     name='document_list'),
    path('upload/',           views.upload,            name='upload'),
    path('doc/<int:doc_id>/', views.retrieve_document, name='retrieve_document'),
 
]