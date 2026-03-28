"""
Views for soil data management.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import SoilData
from .forms import SoilDataForm, SoilDataFetchForm
from .services import SoilDataService
from apps.farms.models import Field


@login_required
def soil_data_list(request):
    """List all soil data for user's fields."""
    fields = Field.objects.filter(farm__user=request.user)
    soil_data_list = SoilData.objects.filter(field__in=fields).select_related('field', 'field__farm').order_by('-timestamp')
    
    context = {
        'soil_data_list': soil_data_list,
        'fields': fields,
    }
    return render(request, 'soil/soil_data_list.html', context)


@login_required
def soil_data_options(request):
    """Show options for adding soil data (manual or fetch from API)."""
    from apps.farms.models import Farm, Field
    user_fields = Field.objects.filter(farm__user=request.user)
    user_farms = Farm.objects.filter(user=request.user)
    
    has_fields = user_fields.exists()
    has_farms = user_farms.exists()
    
    context = {
        'has_fields': has_fields,
        'has_farms': has_farms,
        'fields_count': user_fields.count(),
        'farms_count': user_farms.count(),
    }
    return render(request, 'soil/soil_data_options.html', context)


@login_required
def soil_data_add(request):
    """Add soil data manually."""
    # Check if user has fields
    from apps.farms.models import Farm, Field
    user_fields = Field.objects.filter(farm__user=request.user)
    user_farms = Farm.objects.filter(user=request.user)
    
    if not user_fields.exists():
        if not user_farms.exists():
            messages.warning(request, 'You need to create a farm first before adding soil data.')
            return render(request, 'soil/soil_data_add.html', {
                'form': None,
                'no_farms': True,
                'no_fields': True
            })
        else:
            messages.warning(request, 'You need to create a field first before adding soil data.')
            return render(request, 'soil/soil_data_add.html', {
                'form': None,
                'no_farms': False,
                'no_fields': True,
                'farms': user_farms
            })
    
    if request.method == 'POST':
        form = SoilDataForm(request.POST, user=request.user)
        if form.is_valid():
            soil_data = form.save()
            # Update field's soil properties
            field = soil_data.field
            field.soil_ph = soil_data.ph
            field.soil_moisture = soil_data.moisture
            field.n_content = soil_data.n
            field.p_content = soil_data.p
            field.k_content = soil_data.k
            field.save()
            
            messages.success(request, f'Soil data added successfully for {field.name}!')
            return redirect('soil:soil_data_list')
    else:
        form = SoilDataForm(user=request.user)
    
    return render(request, 'soil/soil_data_add.html', {
        'form': form,
        'no_fields': False,
        'no_farms': False
    })


@login_required
def soil_data_fetch(request):
    """Fetch soil data from API."""
    # Check if user has fields
    from apps.farms.models import Farm, Field
    user_fields = Field.objects.filter(farm__user=request.user)
    user_farms = Farm.objects.filter(user=request.user)
    
    if not user_fields.exists():
        if not user_farms.exists():
            messages.warning(request, 'You need to create a farm and field first before fetching soil data.')
            return render(request, 'soil/soil_data_fetch.html', {
                'form': None,
                'no_farms': True,
                'no_fields': True
            })
        else:
            messages.warning(request, 'You need to create a field first before fetching soil data.')
            return render(request, 'soil/soil_data_fetch.html', {
                'form': None,
                'no_farms': False,
                'no_fields': True,
                'farms': user_farms
            })
    
    if request.method == 'POST':
        form = SoilDataFetchForm(request.POST, user=request.user)
        if form.is_valid():
            field = form.cleaned_data['field']
            source = form.cleaned_data['source']
            
            # Get field coordinates
            if field.latitude and field.longitude:
                lat = float(field.latitude)
                lon = float(field.longitude)
            elif field.farm.latitude and field.farm.longitude:
                lat = float(field.farm.latitude)
                lon = float(field.farm.longitude)
            else:
                messages.error(request, 'Field or farm location is required to fetch soil data.')
                form = SoilDataFetchForm(user=request.user)
                return render(request, 'soil/soil_data_fetch.html', {'form': form, 'no_fields': False})
            
            # Fetch soil data
            soil_data = SoilDataService.get_soil_data(lat, lon, source)
            
            if soil_data:
                # Validate data
                is_valid, error_msg = SoilDataService.validate_soil_data(soil_data)
                if not is_valid:
                    messages.error(request, f'Invalid soil data: {error_msg}')
                    form = SoilDataFetchForm(user=request.user)
                    return render(request, 'soil/soil_data_fetch.html', {'form': form})
                
                # Check if this is an estimated value
                is_estimated = soil_data.get('_estimated', False)
                region_name = soil_data.get('_region', '')
                note = soil_data.get('_note', '')
                
                # Remove internal keys before saving
                for key in ['_estimated', '_region', '_note', '_depth_used']:
                    soil_data.pop(key, None)
                
                # Create SoilData record
                data_source = soil_data.pop('source', 'satellite')
                
                # Remove extra keys not in model
                save_data = {
                    'ph': soil_data.get('ph'),
                    'moisture': soil_data.get('moisture'),
                    'n': soil_data.get('n'),
                    'p': soil_data.get('p'),
                    'k': soil_data.get('k'),
                }
                
                soil_record = SoilData.objects.create(
                    field=field,
                    source=data_source,
                    **save_data
                )
                
                # Update field's soil properties
                if save_data.get('ph'):
                    field.soil_ph = save_data['ph']
                if save_data.get('moisture'):
                    field.soil_moisture = save_data['moisture']
                if save_data.get('n'):
                    field.n_content = save_data['n']
                if save_data.get('p'):
                    field.p_content = save_data['p']
                if save_data.get('k'):
                    field.k_content = save_data['k']
                field.save()
                
                # Build appropriate success message
                if is_estimated:
                    messages.success(
                        request,
                        f'Soil data populated for {field.name} using regional estimates '
                        f'for {region_name}. These are approximate values — '
                        f'consider updating with actual soil test results.'
                    )
                elif note:
                    messages.success(request, f'Soil data fetched for {field.name}! Note: {note}')
                else:
                    messages.success(request, f'Soil data fetched successfully from {data_source} for {field.name}!')
                
                return redirect('soil:soil_data_list')
            else:
                messages.error(
                    request,
                    'Could not fetch soil data for this location. '
                    'The satellite database may not have coverage for this area (e.g. urban zones). '
                    'Please try manual input instead.'
                )
                form = SoilDataFetchForm(user=request.user)
                return render(request, 'soil/soil_data_fetch.html', {'form': form, 'no_fields': False})
    else:
        form = SoilDataFetchForm(user=request.user)
    
    return render(request, 'soil/soil_data_fetch.html', {'form': form, 'no_fields': False})


@login_required
def soil_data_detail(request, pk):
    """View soil data details."""
    soil_data = get_object_or_404(SoilData, pk=pk, field__farm__user=request.user)
    return render(request, 'soil/soil_data_detail.html', {'soil_data': soil_data})


@login_required
@require_http_methods(["POST"])
def soil_data_fetch_ajax(request):
    """AJAX endpoint for fetching soil data."""
    field_id = request.POST.get('field_id')
    source = request.POST.get('source', 'auto')
    
    try:
        field = Field.objects.get(pk=field_id, farm__user=request.user)
    except Field.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Field not found'}, status=404)
    
    # Get coordinates
    if field.latitude and field.longitude:
        lat = float(field.latitude)
        lon = float(field.longitude)
    elif field.farm.latitude and field.farm.longitude:
        lat = float(field.farm.latitude)
        lon = float(field.farm.longitude)
    else:
        return JsonResponse({'success': False, 'error': 'Field location required'}, status=400)
    
    # Fetch soil data
    soil_data = SoilDataService.get_soil_data(lat, lon, source)
    
    if soil_data:
        # Validate
        is_valid, error_msg = SoilDataService.validate_soil_data(soil_data)
        if not is_valid:
            return JsonResponse({'success': False, 'error': error_msg}, status=400)
        
        return JsonResponse({
            'success': True,
            'data': {
                'ph': soil_data.get('ph'),
                'moisture': soil_data.get('moisture'),
                'n': soil_data.get('n'),
                'p': soil_data.get('p'),
                'k': soil_data.get('k'),
                'source': soil_data.get('source', 'satellite'),
                'estimated': soil_data.get('_estimated', False),
                'region': soil_data.get('_region', ''),
            }
        })
    else:
        return JsonResponse({
            'success': False,
            'error': 'No soil data available for this location. The area may not have satellite coverage.'
        }, status=500)
