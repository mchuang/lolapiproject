from django.utils import timezone
from django.forms.models import model_to_dict
from eloPurgatory.models import *

def handleSummoner(name, json):
    info = json[str(name).lower()]
    summoner = Summoner(summonerId=info['id'],name=info['name'])
    return summoner

def handleRank(summoner, queue, json):
    ranks = json[str(summoner.summonerId)]
    for rank in ranks:
        if rank['queue'] == queue:
            return Rank(summoner=summoner, queue=rank['queue'], division=rank['entries'][0]['division'], tier=rank['tier'])   

def handleMatchRank(summoner, queue, json, prevRank):
    if str(summoner.summonerId) not in json.keys():
        return RankInfo(summoner=summoner, queue=queue, division='UNRANKED', tier='UNRANKED', prevSeasonTier=prevRank)
    ranks = json[str(summoner.summonerId)]
    for rank in ranks:
        if rank['queue'] == queue:
            if rank['tier'] == "CHALLENGER" or rank['tier'] == "MASTER":
                return RankInfo(summoner=summoner, queue=rank['queue'], division=rank['entries'][0]['leaguePoints'], tier=rank['tier'], prevSeasonTier=prevRank)
            else:
                return RankInfo(summoner=summoner, queue=rank['queue'], division=rank['entries'][0]['division'], tier=rank['tier'], prevSeasonTier=prevRank)
    return RankInfo(summoner=summoner, queue=queue, division='UNRANKED', tier='UNRANKED', prevSeasonTier=prevRank)

def handleMatchDetails(json, summonerId):
    participants = json['participants']
    participantIds = json['participantIdentities']
    summonerTeamId = 0
    players = {}
    matchData = {}

    for participantId in participantIds:
        for participant in participants:
            if participant['participantId'] == participantId['participantId']:
                if participantId['player']['summonerId'] == summonerId:
                    summonerTeamId = participant['teamId']
                else:
                    players.update({ participantId['player']['summonerId']: participant })
                continue
                
    for playerId, playerInfo in players.items():
        if playerId == summonerId: 
            continue #should never reach here
        #Change data to pass on more individual particpant data regarding playerInfo
        data = { 'prevSeasonTier': playerInfo['highestAchievedSeasonTier'] } 
        if playerInfo['teamId'] == summonerTeamId:
            data.update({ 'isAlly': True })
        else:
            data.update({ 'isAlly': False})
        players.update({ playerId: data })
    matchData.update({ 'players': players })

    teams = json['teams']
    for team in teams:
        if team['teamId'] == summonerTeamId:
            matchData.update({ 'winner': team['winner'] })
    
    return { json['matchId'] : matchData }

def convertModelToDict(model):
    data = model_to_dict(model)
    if type(model) is RankInfo:
        data.update({ 'summoner': model_to_dict(model.summoner) })
    return data
        
