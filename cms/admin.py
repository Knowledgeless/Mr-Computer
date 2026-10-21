from django.contrib import admin

from cms.models import Banner, ContactMessage, HomeSection, Page, SiteSettings


admin.site.register([Banner, ContactMessage, HomeSection, Page, SiteSettings])
