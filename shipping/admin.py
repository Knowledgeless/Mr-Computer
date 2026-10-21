from django.contrib import admin

from shipping.models import ShippingRate, ShippingZone


admin.site.register([ShippingRate, ShippingZone])
