from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from accounts.decorators import admin_required

from .models import Module


@login_required
@admin_required
def delete_module(request, module_id):
    module = get_object_or_404(Module, id=module_id)

    if request.method == "POST":
        module.delete()

    return redirect("/home/?tab=modules")

