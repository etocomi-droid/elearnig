from django.urls import path

from apps.emails.views import (
    ScenarioListView,
    scenario_create_view,
    scenario_edit_view,
    scenario_delete_view,
    step_create_view,
    step_edit_view,
    step_delete_view,
    CampaignListView,
    campaign_create_view,
    campaign_edit_view,
    campaign_delete_view,
    campaign_send_view,
)

app_name = 'emails'

urlpatterns = [
    # シナリオ
    path('scenarios/', ScenarioListView.as_view(), name='scenario_list'),
    path('scenarios/create/', scenario_create_view, name='scenario_create'),
    path('scenarios/<int:pk>/edit/', scenario_edit_view, name='scenario_edit'),
    path('scenarios/<int:pk>/delete/', scenario_delete_view, name='scenario_delete'),

    # シナリオステップ
    path('scenarios/<int:scenario_id>/steps/create/', step_create_view, name='step_create'),
    path('scenarios/<int:scenario_id>/steps/<int:pk>/edit/', step_edit_view, name='step_edit'),
    path('scenarios/<int:scenario_id>/steps/<int:pk>/delete/', step_delete_view, name='step_delete'),

    # 一斉配信（キャンペーン）
    path('campaigns/', CampaignListView.as_view(), name='campaign_list'),
    path('campaigns/create/', campaign_create_view, name='campaign_create'),
    path('campaigns/<int:pk>/edit/', campaign_edit_view, name='campaign_edit'),
    path('campaigns/<int:pk>/delete/', campaign_delete_view, name='campaign_delete'),
    path('campaigns/<int:pk>/send/', campaign_send_view, name='campaign_send'),
]
