from django.contrib import admin
from booking.models import Treatment, Package, Membership, TreatmentImage


class PackageInline(admin.TabularInline):
    model = Package


class MembershipInline(admin.TabularInline):
    model = Membership


class TreatmentImageInline(admin.StackedInline):
    model = TreatmentImage


class TreatmentAdmin(admin.ModelAdmin):
    model = Treatment
    inlines = [
        TreatmentImageInline,
        PackageInline,
        MembershipInline
    ]


admin.site.register(Treatment, TreatmentAdmin)
