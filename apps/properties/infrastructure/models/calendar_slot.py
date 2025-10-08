from django.db import models
from .property import Property
from .unit import Unit


class CalendarSlot(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_slots')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='unit_slots', null=True, default=None)
    date = models.DateField()
    status = models.CharField(
        max_length=50,
        choices=[('available', 'Available'), ('unavailable', 'Unavailable')]
    )
    reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.date} - {self.status}"