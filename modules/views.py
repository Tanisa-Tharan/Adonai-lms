from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from accounts.decorators import admin_required

from .models import Module, CourseMaterial


@login_required
@admin_required
def delete_module(request, module_id):
    module = get_object_or_404(Module, id=module_id)

    if request.method == "POST":
        module.delete()

    return redirect("/home/?tab=modules")


@login_required
@admin_required
@require_POST
def upload_course_material(request):
    """Handle course material uploads (files and links)"""
    try:
        title = request.POST.get('title')
        material_type = request.POST.get('material_type')
        resource_type = request.POST.get('resource_type', 'REQUIRED')
        module_id = request.POST.get('module_id')
        
        print(f"[UPLOAD] Received: title={title}, type={material_type}, resource_type={resource_type}, module_id={module_id}")
        
        if not all([title, material_type, module_id]):
            error_msg = f'Missing required fields: title={bool(title)}, type={bool(material_type)}, module_id={bool(module_id)}'
            print(f"[UPLOAD ERROR] {error_msg}")
            return JsonResponse({'success': False, 'error': error_msg}, status=400)
        
        # Get the module
        module = get_object_or_404(Module, id=module_id)
        print(f"[UPLOAD] Found module: {module.title}")
        
        # Create the course material
        course_material = CourseMaterial(
            module=module,
            title=title,
            material_type=material_type,
            resource_type=resource_type,
            uploaded_by=request.user
        )
        
        # Handle file upload or link
        if material_type == 'LINK':
            # For links, store the URL in file_url field
            link_url = request.POST.get('link_url') or request.POST.get('file_url')
            if not link_url:
                print("[UPLOAD ERROR] Link URL is missing")
                return JsonResponse({'success': False, 'error': 'Link URL is required'}, status=400)
            course_material.file_url = link_url
            print(f"[UPLOAD] Link URL: {link_url}")
        else:
            # For files (PDF, PPT, VIDEO), handle file upload
            uploaded_file = request.FILES.get('file') or request.FILES.get('file_url')
            if not uploaded_file:
                print("[UPLOAD ERROR] File is missing from request.FILES")
                return JsonResponse({'success': False, 'error': 'File is required'}, status=400)
            course_material.file_url = uploaded_file
            print(f"[UPLOAD] File: {uploaded_file.name}, Size: {uploaded_file.size} bytes")
        
        course_material.save()
        print(f"[UPLOAD SUCCESS] Material saved with ID: {course_material.id}")
        
        return JsonResponse({
            'success': True,
            'message': 'Course material uploaded successfully',
            'material_id': str(course_material.id),
            'module_title': module.title
        })
        
    except Exception as e:
        print(f"[UPLOAD EXCEPTION] {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@admin_required
@require_POST
def delete_course_material(request, material_id):
    """Delete a course material"""
    try:
        material = get_object_or_404(CourseMaterial, id=material_id)
        material.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Course material deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

