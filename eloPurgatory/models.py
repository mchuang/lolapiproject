from django.db import models

class Summoner(models.Model):
    summonerId = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=200)
    region = models.CharField(max_length=10)
    def __str__(self):
        return str(self.summonerId) + ':' + self.name

class RankInfo(models.Model):
    summoner = models.ForeignKey(Summoner, on_delete=models.CASCADE)
    queue = models.CharField(max_length=100)
    tier = models.CharField(max_length=20)
    division = models.CharField(max_length=10)
    prevSeasonTier = models.CharField(max_length=20)
    tierNum = { 'BRONZE'     : 0,
                'SILVER'     : 1,
                'GOLD'       : 2,
                'PLATINUM'   : 3,
                'DIAMOND'    : 4,
                'MASTER'     : 5,
                'CHALLENGER' : 6, }
    divNum = { 'I'   : 4,
               'II'  : 3,
               'III' : 2,
               'IV'  : 1,
               'V'   : 0, }

    def __str__(self):
        return ('{summoner}:{queue}:{tier} {division}').format(summoner=self.summoner, queue=self.queue, tier=self.tier, division=self.division)
    def __cmp__(self, other):
        if RankInfo.tierNum[self.tier] == RankInfo.tierNum[other.tier]:
            if RankInfo.divNum[self.division] == RankInfo.divNum[other.division]:
                return 0
            elif RankInfo.divNum[self.division] > RankInfo.divNum[other.division]:
                return 1
            else:
                return -1
        else:
            if RankInfo.tierNum[self.tier] > RankInfo.tierNum[other.tier]:
                return 1
            else:
                return -1

class Match(models.Model):
    matchId = models.BigIntegerField(primary_key=True)
    queueType = models.CharField(max_length=100)
    region = models.CharField(max_length=10)
    season = models.CharField(max_length=20)
    def __str__(self):
        return self.region + ':' + self.queueType + ':' + str(self.matchId) 
