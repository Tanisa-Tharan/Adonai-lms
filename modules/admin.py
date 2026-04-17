from django.contrib import admin

from .models import Module, ModuleRun, ModuleSession


admin.site.register(Module)
admin.site.register(ModuleRun)
admin.site.register(ModuleSession)

