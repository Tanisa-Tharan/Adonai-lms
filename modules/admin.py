from django.contrib import admin

from .models import Module, ModuleRun, ModuleSession, ModuleVideo


admin.site.register(Module)
admin.site.register(ModuleRun)
admin.site.register(ModuleSession)
admin.site.register(ModuleVideo)

