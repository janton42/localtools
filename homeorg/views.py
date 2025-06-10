from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Room, Container, Item
from .forms import ItemForm

# Room Views
class RoomListView(ListView):
    model = Room
    template_name = 'homeorg/index.html'

class RoomDetailView(DetailView):
    model = Room
    template_name = 'homeorg/room_detail.html'

class RoomCreateView(CreateView):
    model = Room
    fields = ['name', 'description']
    template_name = 'homeorg/room_form.html'
    success_url = reverse_lazy('homeorg:index')

class RoomUpdateView(UpdateView):
    model = Room
    fields = ['name', 'description']
    template_name = 'homeorg/room_form.html'
    success_url = reverse_lazy('homeorg:index')

class RoomDeleteView(DeleteView):
    model = Room
    template_name = 'homeorg/room_confirm_delete.html'
    success_url = reverse_lazy('homeorg:index')

# Container Views
class ContainerListView(ListView):
    model = Container
    template_name = 'homeorg/container_list.html'

class ContainerDetailView(DetailView):
    model = Container
    template_name = 'homeorg/container_detail.html'

class ContainerCreateView(CreateView):
    model = Container
    fields = ['name', 'description', 'room', 'parent_container']
    template_name = 'homeorg/container_form.html'
    success_url = reverse_lazy('homeorg:container-list')

class ContainerUpdateView(UpdateView):
    model = Container
    fields = ['name', 'description', 'room', 'parent_container']
    template_name = 'homeorg/container_form.html'
    success_url = reverse_lazy('homeorg:container-list')

class ContainerDeleteView(DeleteView):
    model = Container
    template_name = 'homeorg/container_confirm_delete.html'
    success_url = reverse_lazy('homeorg:container-list')

# Item Views
class ItemListView(ListView):
    model = Item
    template_name = 'homeorg/item_list.html'

class ItemDetailView(DetailView):
    model = Item
    template_name = 'homeorg/item_detail.html'

class ItemCreateView(CreateView):
    model = Item
    form_class = ItemForm
    template_name = 'homeorg/item_form.html'
    success_url = reverse_lazy('homeorg:item-list')

    def get_initial(self):
        initial = super().get_initial()
        room_id = self.request.GET.get('room')
        if room_id:
            initial['room'] = room_id
        return initial

class ItemUpdateView(UpdateView):
    model = Item
    fields = ['name', 'description', 'container']
    template_name = 'homeorg/item_form.html'
    success_url = reverse_lazy('homeorg:item-list')

class ItemDeleteView(DeleteView):
    model = Item
    template_name = 'homeorg/item_confirm_delete.html'
    success_url = reverse_lazy('homeorg:item-list')
