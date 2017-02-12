from django.utils import timezone
from django.forms.models import model_to_dict
from eloPurgatory.models import *
import pdb
def handleSummoner(region, summonerId, json):
    info = json[str(summonerId)]
    summoner = Summoner(summonerId=info['id'],name=info['name'], region=region)
    #summoner.save()
    return summoner

def handleRank(summoner, queue, json):
    ranks = json[str(summoner.summonerId)]
    for rank in ranks:
        if rank['queue'] == queue:
            result = RankInfo(summoner=summoner, queue=rank['queue'], division=rank['entries'][0]['division'], tier=rank['tier'])   
            #result.save()
            return result

def handleMatchRank(summoner, queue, json):
    if str(summoner.summonerId) not in json.keys():
        unranked = RankInfo(summoner=summoner, queue=queue, division='UNRANKED', tier='UNRANKED')
        #unranked.save()
        return unranked
    ranks = json[str(summoner.summonerId)]
    for rank in ranks:
        if rank['queue'] == queue:
            if rank['tier'] == "CHALLENGER" or rank['tier'] == "MASTER":
                rankInfo = RankInfo(summoner=summoner, queue=rank['queue'], division=rank['entries'][0]['leaguePoints'], tier=rank['tier'])
            else:
                rankInfo = RankInfo(summoner=summoner, queue=rank['queue'], division=rank['entries'][0]['division'], tier=rank['tier'])
            #rankInfo.save()
            return rankInfo
    unranked = RankInfo(summoner=summoner, queue=queue, division='UNRANKED', tier='UNRANKED')
    #unranked.save()
    return unranked

def handleMatchDetails(json):
    participants = json['participants']
    participantIds = json['participantIdentities']
    players = {}
    matchData = {}

    for participantId in participantIds:
        for participant in participants:
            if participant['participantId'] == participantId['participantId']:
                players.update({ participantId['player']['summonerId']: participant })
                continue

    for playerId, playerInfo in players.items():
        data = { 'prevSeasonTier': playerInfo['highestAchievedSeasonTier'], 'teamId': playerInfo['teamId'] }
        players.update({ playerId: data })

    for team in json['teams']:
        if team['winner']:
            matchData.update({ 'winner': team['teamId'] })
        else:
            matchData.update({ 'loser': team['teamId'] })
    matchData.update({ 'players': players})
    return { json['matchId']: matchData }

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
        
