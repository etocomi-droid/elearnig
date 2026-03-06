from django.urls import path

from apps.funnels.views import (
    FunnelListView,
    funnel_create_view,
    funnel_edit_view,
    funnel_delete_view,
    page_create_view,
    page_edit_view,
    page_delete_view,
    section_add_view,
    section_edit_view,
    section_delete_view,
    section_reorder_view,
)

app_name = 'funnels'

urlpatterns = [
    path('', FunnelListView.as_view(), name='funnel_list'),
    path('create/', funnel_create_view, name='funnel_create'),
    path('<int:pk>/edit/', funnel_edit_view, name='funnel_edit'),
    path('<int:pk>/delete/', funnel_delete_view, name='funnel_delete'),
    path('<int:funnel_id>/pages/create/', page_create_view, name='page_create'),
    path('pages/<int:pk>/edit/', page_edit_view, name='page_edit'),
    path('pages/<int:pk>/delete/', page_delete_view, name='page_delete'),
    path('pages/<int:page_id>/sections/add/', section_add_view, name='section_add'),
    path('sections/<int:pk>/edit/', section_edit_view, name='section_edit'),
    path('sections/<int:pk>/delete/', section_delete_view, name='section_delete'),
    path('pages/<int:page_id>/sections/reorder/', section_reorder_view, name='section_reorder'),
]
