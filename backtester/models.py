from django.db import models
from django.contrib.auth.models import User

class BacktestStrategy(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    k_period = models.IntegerField(default=9)
    buy_threshold = models.IntegerField(default=20)
    sell_threshold = models.IntegerField(default=80)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.name}"