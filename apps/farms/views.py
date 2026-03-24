"""
Views for farm and field management.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum
from .models import Farm, Field
from .forms import FarmForm, FieldForm


@login_required
def farm_list(request):
    """List all farms for the current user."""
    farms = Farm.objects.filter(user=request.user).annotate(
        field_count=Count('fields')
    ).order_by('-created_at')
    
    context = {
        'farms': farms,
    }
    return render(request, 'farms/farm_list.html', context)


@login_required
def farm_create(request):
    """Create a new farm."""
    if request.method == 'POST':
        form = FarmForm(request.POST, user=request.user)
        if form.is_valid():
            farm = form.save(commit=False)
            farm.user = request.user
            farm.save()
            messages.success(request, f'Farm "{farm.name}" created successfully!')
            return redirect('farms:farm_detail', pk=farm.pk)
    else:
        form = FarmForm(user=request.user)
    
    return render(request, 'farms/farm_form.html', {
        'form': form,
        'title': 'Create Farm',
        'action': 'Create'
    })


@login_required
def farm_detail(request, pk):
    """View farm details."""
    farm = get_object_or_404(Farm, pk=pk, user=request.user)
    fields = farm.fields.all().order_by('name')
    
    # Calculate total area of all fields
    total_field_area = fields.aggregate(total=Sum('area'))['total'] or 0
    
    context = {
        'farm': farm,
        'fields': fields,
        'total_field_area': total_field_area,
    }
    return render(request, 'farms/farm_detail.html', context)


@login_required
def farm_update(request, pk):
    """Update an existing farm."""
    farm = get_object_or_404(Farm, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = FarmForm(request.POST, instance=farm, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Farm "{farm.name}" updated successfully!')
            return redirect('farms:farm_detail', pk=farm.pk)
    else:
        form = FarmForm(instance=farm, user=request.user)
    
    return render(request, 'farms/farm_form.html', {
        'form': form,
        'farm': farm,
        'title': 'Update Farm',
        'action': 'Update'
    })


@login_required
def farm_delete(request, pk):
    """Delete a farm."""
    farm = get_object_or_404(Farm, pk=pk, user=request.user)
    
    if request.method == 'POST':
        farm_name = farm.name
        farm.delete()
        messages.success(request, f'Farm "{farm_name}" deleted successfully!')
        return redirect('farms:farm_list')
    
    return render(request, 'farms/farm_confirm_delete.html', {
        'farm': farm
    })


@login_required
def field_list(request):
    """List all fields for the current user."""
    fields = Field.objects.filter(farm__user=request.user).select_related('farm').order_by('farm', 'name')
    
    # Group by farm
    farms_with_fields = {}
    for field in fields:
        farm = field.farm
        if farm not in farms_with_fields:
            farms_with_fields[farm] = []
        farms_with_fields[farm].append(field)
    
    context = {
        'farms_with_fields': farms_with_fields,
        'fields': fields,
    }
    return render(request, 'farms/field_list.html', context)


@login_required
def field_create(request):
    """Create a new field."""
    # Check if user has farms
    user_farms = Farm.objects.filter(user=request.user)
    if not user_farms.exists():
        messages.warning(request, 'You need to create a farm first before adding fields.')
        return redirect('farms:farm_create')
    
    if request.method == 'POST':
        form = FieldForm(request.POST, user=request.user)
        if form.is_valid():
            field = form.save()
            messages.success(request, f'Field "{field.name}" created successfully!')
            return redirect('farms:field_detail', pk=field.pk)
    else:
        form = FieldForm(user=request.user)
        # Pre-select farm if provided in query parameter
        farm_id = request.GET.get('farm')
        if farm_id:
            try:
                farm = Farm.objects.get(pk=farm_id, user=request.user)
                form.fields['farm'].initial = farm
            except Farm.DoesNotExist:
                pass
    
    return render(request, 'farms/field_form.html', {
        'form': form,
        'title': 'Create Field',
        'action': 'Create'
    })


@login_required
def field_detail(request, pk):
    """View field details."""
    field = get_object_or_404(Field, pk=pk, farm__user=request.user)
    crop_history = field.crop_history.all().order_by('-year', '-season')[:10]
    soil_data = field.soil_data.all().order_by('-timestamp')[:5]
    
    context = {
        'field': field,
        'crop_history': crop_history,
        'soil_data': soil_data,
    }
    return render(request, 'farms/field_detail.html', context)


@login_required
def field_update(request, pk):
    """Update an existing field."""
    field = get_object_or_404(Field, pk=pk, farm__user=request.user)
    
    if request.method == 'POST':
        form = FieldForm(request.POST, instance=field, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Field "{field.name}" updated successfully!')
            return redirect('farms:field_detail', pk=field.pk)
    else:
        form = FieldForm(instance=field, user=request.user)
    
    return render(request, 'farms/field_form.html', {
        'form': form,
        'field': field,
        'title': 'Update Field',
        'action': 'Update'
    })


@login_required
def field_delete(request, pk):
    """Delete a field."""
    field = get_object_or_404(Field, pk=pk, farm__user=request.user)
    
    if request.method == 'POST':
        field_name = field.name
        farm_pk = field.farm.pk
        field.delete()
        messages.success(request, f'Field "{field_name}" deleted successfully!')
        return redirect('farms:farm_detail', pk=farm_pk)
    
    return render(request, 'farms/field_confirm_delete.html', {
        'field': field
    })
