from django.urls import path
from . import views

app_name = 'homeorg'
urlpatterns = [
    # Room URLs
    path('rooms/', views.RoomListView.as_view(), name='index'),
    path('rooms/<int:pk>/', views.RoomDetailView.as_view(), name='room-detail'),
    path('rooms/create/', views.RoomCreateView.as_view(), name='room-create'),
    path('rooms/<int:pk>/update/', views.RoomUpdateView.as_view(), name='room-update'),
    path('rooms/<int:pk>/delete/', views.RoomDeleteView.as_view(), name='room-delete'),

    # Container URLs
    path('containers/', views.ContainerListView.as_view(), name='container-list'),
    path('containers/<int:pk>/', views.ContainerDetailView.as_view(), name='container-detail'),
    path('containers/create/', views.ContainerCreateView.as_view(), name='container-create'),
    path('containers/<int:pk>/update/', views.ContainerUpdateView.as_view(), name='container-update'),
    path('containers/<int:pk>/delete/', views.ContainerDeleteView.as_view(), name='container-delete'),

    # Item URLs
    path('items/', views.ItemListView.as_view(), name='item-list'),
    path('items/<int:pk>/', views.ItemDetailView.as_view(), name='item-detail'),
    path('items/create/', views.ItemCreateView.as_view(), name='item-create'),
    path('items/<int:pk>/update/', views.ItemUpdateView.as_view(), name='item-update'),
    path('items/<int:pk>/delete/', views.ItemDeleteView.as_view(), name='item-delete'),
]

