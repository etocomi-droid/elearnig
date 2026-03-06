from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from apps.accounts.decorators import project_permission_required
from apps.products.forms import ProductForm
from apps.products.models import Product, Order


@method_decorator(project_permission_required('can_manage_products'), name='dispatch')
class ProductListView(LoginRequiredMixin, ListView):
    """商品一覧"""
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 50

    def get_queryset(self):
        project = self.request.current_project
        return Product.objects.filter(project=project)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.request.current_project
        context['total_count'] = Product.objects.filter(project=project).count()
        return context


@login_required
@project_permission_required('can_manage_products')
def product_create_view(request):
    """商品作成"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    if request.method == 'POST':
        form = ProductForm(request.POST, current_project=project)
        if form.is_valid():
            product = form.save(commit=False)
            product.project = project
            product.save()
            messages.success(request, f'商品「{product.name}」を作成しました。')
            return redirect('products:product_list')
    else:
        form = ProductForm(current_project=project)

    return render(request, 'products/product_edit.html', {
        'form': form,
        'is_new': True,
    })


@login_required
@project_permission_required('can_manage_products')
def product_edit_view(request, pk):
    """商品編集"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    product = get_object_or_404(Product, pk=pk, project=project)

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product, current_project=project)
        if form.is_valid():
            form.save()
            messages.success(request, f'商品「{product.name}」を更新しました。')
            return redirect('products:product_list')
    else:
        form = ProductForm(instance=product, current_project=project)

    return render(request, 'products/product_edit.html', {
        'form': form,
        'product': product,
        'is_new': False,
    })


@login_required
@project_permission_required('can_manage_products')
def product_delete_view(request, pk):
    """商品削除"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    product = get_object_or_404(Product, pk=pk, project=project)

    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'商品「{name}」を削除しました。')
        return redirect('products:product_list')

    return render(request, 'products/product_confirm_delete.html', {
        'product': product,
    })


@method_decorator(project_permission_required('can_manage_products'), name='dispatch')
class OrderListView(LoginRequiredMixin, ListView):
    """注文一覧"""
    model = Order
    template_name = 'products/order_list.html'
    context_object_name = 'orders'
    paginate_by = 50

    def get_queryset(self):
        project = self.request.current_project
        return Order.objects.filter(project=project).select_related('contact')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.request.current_project
        context['total_count'] = Order.objects.filter(project=project).count()
        return context


@login_required
@project_permission_required('can_manage_products')
def order_detail_view(request, pk):
    """注文詳細"""
    project = getattr(request, 'current_project', None)
    if not project:
        return redirect('accounts:project_list')

    order = get_object_or_404(
        Order.objects.select_related('contact').prefetch_related('items__product'),
        pk=pk,
        project=project,
    )

    return render(request, 'products/order_detail.html', {
        'order': order,
    })
