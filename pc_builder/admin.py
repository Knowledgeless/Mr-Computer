from django.contrib import admin

from pc_builder.models import Build, BuildItem, BuildRequest


admin.site.register([Build, BuildItem, BuildRequest])
