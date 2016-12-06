from django.db import models

class Summoner(models.Model):
    summonerId = models.BigIntegerField(primary_key=True)
    name = models.CharField()
    profileIcon = models.IntegerField()

class RankInfo(models.Model):
    summonerId = models.ForeignKey(Summoner, on_delete=models.CASCAFE, verbose_name="Summoner ranks",)
    queue = models.CharField()
    lp = models.IntegerField()
    tier = models.CharField()
    division = models.CharField()

