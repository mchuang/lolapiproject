from django.shortcuts import render

import json
import requests
import time
import pdb

RATE_LIMIT_EXCEEDED_SLEEP_DURATION = 10

api_key='RGAPI-fb6382dc-b504-49fb-8361-54dec10d386b'

base_url = 'https://{region}.api.pvp.net/api/lol/{region}/'
URLS = dict(
    summoner_by_name='v1.4/summoner/by-name/{summonerName}',
    summoner_by_id='v1.4/summoner/{summonerId}',
    match_list='v2.2/matchlist/by-summoner/{summonerId}',
    match='v2.2/match/{matchId}',
    recent_games='v1.3/game/by-summoner/{summonerId}/recent',
    ranked_stats='v1.3/stats/by-summoner/{summonerId}/ranked',
    summary_stats='v1.3/stats/by-summoner/{summonerId}/summary',
    rank_data='v2.5/league/by-summoner/{summonerId}/entry'
)
platforms = dict(
    br='BR1',
    eune='EUN1',
    euw='EUW1',
    jp='JP1',
    kr='KR',
    lan='LA1',
    las='LA2',
    na='NA1',
    oce='OC1',
    tr='TR1',
    ru='RU',
    pbe='PBE1',
)
tiers = ["UNRANKED", "BRONZE", "SILVER", "GOLD", "PLATINUM", "DIAMOND", "MASTER", "CHALLENGER"]
tier_icons = dict(
    UNRANKED='base_icons/provisional.png',
    BRONZE='base_icons/bronze.png',
    SILVER='base_icons/silver.png',
    GOLD='base_icons/gold.png',
    PLATINUM='base_icons/platinum.png',
    DIAMOND='base_icons/diamond.png',
    MASTER='base_icons/master.png',
    CHALLENGER='base_icons/challenger.png',
)

from django.http import HttpResponse
from eloPurgatory.models import *
from eloPurgatory.logic import handleSummoner, handleMatchRank, handleMatchDetails, convertModelToDict

def home(request):
    return render(request, 'search.html')

def basicCall(request, region, queue, summonerName, update=False):
    summoner = getSummonerInfo(region, summonerName, update)
    summonerRank = handleMatchRank(summoner, queue, getRankInfo(region, summoner.summonerId))
    
    matches = getMatchListInfo(region, summoner.summonerId, queue)['matches']
    #matches = matchlistInfo['matches']
    index = 0
    matchlimit = 20
    matchlist = {}
    for match in matches:
        if index >= matchlimit:
            break
        if matchInfo == None:
            continue
        data = handleMatchDetails(matchInfo, summoner.summonerId)
        matchlist.update(data)
        index += 1

    for matchId, matchData in matchlist.items():
        players = matchData['players']
        playerList = getSummonerInfoByIdList(region, players.keys(), update)
        rankList = getRankInfoByList(region, summonerList, update)
        for rank in rankList:
            playerId = rank.summoner.summonerId
            players[playerId].update({ 'rank': convertModelToDict(rank) })
     
    jsonData = json.dumps(matchlist)
    return render(request, 'elo.html', 
        { 'data': jsonData, 'region': region, 'summoner': summoner, 'rank':summonerRank, 
        'platform': platforms[region], 'matchlist': matchlist, 'tier_icons': tier_icons, 'tiers': tiers })

def handler(request):
    pdb.set_trace()
    region = request.POST['region']
    summonerName = request.POST['summoner']
    queue = request.POST['queue'] 
    
    return basicCall(request, region, queue, summonerName)

def update(request):
    region = request.POST['region']
    summonerName = request.POST['summoner']
    queue = request.POST['queue']
    return basicCall(request, region, queue, summonerName, True)

def executeRequest(url, payload):
    response = requests.get(url, params=payload)
    while response.status_code == requests.codes.too_many_requests:
        time.sleep(int(response.headers.get('Retry-After')))
        response = requests.get(url, params=payload)    
    return response

def getSummonerInfo(region, summonerName, update=False):
    url = (base_url+URLS['summoner_by_name']).format(region=region, summonerName=summonerName)
    payload = {'api_key': api_key}
    response = executeRequest(url, payload)
    while response.status_code != requests.codes.ok:
        time.sleep(1)
        response = executeRequest(url, payload)
    summonerId = response.json()[summonerName.lower()]['id']
    summoner = getSummonerInfoById(region, summonerId, update)
    return summoner

def getSummonerInfoById(region, summonerId, update=False):
    if Summoner.filter(summonerId=summonerId, region=region).exists() and not update:
        return Summoner.get(summonerId=summonerId, region=region)
    else:
        url = (base_url+URLS['summoner_by_id']).format(region=region, summonerId=summonerId)
        payload = {'api_key': api_key}
        response = executeRequest(url, payload)
        while response.status_code != requests.codes.ok:
            time.sleep(1)
            response = executeRequest(url, payload)
        summonerName = response.json()[summonerId]["name"]
        return handleSummoner(region, summonerName, response.json())

def getSummonerInfoByIdList(region, summonerIds, update=False):
    summonerList = []
    new = []
    for summonerId in summonerIds:
        if Summoner.filter(summonerId=summonerId, region=region).exists() and not update:
            summonerList.append(Summoner.get(summonerId=summonerId, region))
        else:
            new.append(summonerId)
    if len(new) > 0:
        url = (base_url+URLS['summoner_by_id']).format(region=region, summonerId=','.join(str(x) for x in new))
        payload = {'api_key': api_key}
        response = executeRequest(url, payload)
        while response.status_code != requests.codes.ok:
            time.sleep(1)
        response = executeRequest(url, payload)
        for summonerId in new:
            summonerName = response.json()[summonerId]['name']
            newSummoner = handleSummoner(region, summonerName, response.json())
            summonerList.append(newSummoner)
    return summonerList

def getRankInfo(region, summonerId, queue, update=False):
    if RankInfo.filter(summoner.summonerId=summonerId, queue=queue).exists() and not update:
        return RankInfo.get(summoner.summonerId=summonerId, queue=queue)
    else:
        url = (base_url+URLS['rank_data']).format(region=region, summonerId=summonerId)
        payload = {'api_key': api_key}
        response = executeRequest(url, payload)
        while response.status_code != requests.codes.ok:
            time.sleep(1)
            response = executeRequest(url, payload)
        summoner = getSummonerInfoById(summonerId)
        if update and RankInfo.objects.filter(summoner=summoner, queue=queue).exists():
            RankInfo.objects.get(summoner=summoner, queue=queue).delete()
        return handleMatchRank(summoner, queue, response.json())

def getRankInfoByList(region, summoners, queue, update=False):
    rankList = []
    new = []
    for summoner in summoners:
        if RankInfo.filter(summoner=summoner, region=region, queue=queue).exists() and not update:
            rankList.append(RankInfo.get(summoner=summoner, region=region, queue=queue))
        else:
            new.append(summoner)
    
    if len(new) > 0:
        url = (base_url+URLS['rank_data']).format(region=region, summonerId=','.join(str(x) for x in new))
        payload = {'api_key': api_key}
        response = executeRequest(url, payload)
        while response.status_code != requests.codes.ok:
            time.sleep(1)
        response = executeRequest(url, payload)
        for summoner in new:
            if update and RankInfo.objects.filter(summoner=summoner, queue=queue).exists():
                RankInfo.objects.get(summoner=summoner, queue=queue).delete()
            newRank = handleMatchRank(summoner, queue, response.json())
            rankList.append(rankList)
    return rankList

def getMatchListInfo(region, summonerId, queue):
    url = (base_url+URLS['match_list']).format(region=region, summonerId=summonerId)
    payload = {'api_key': api_key, 'rankedQueues': queue}
    response = executeRequest(url, payload)
    while response.status_code != requests.codes.ok:
        time.sleep(1)
        response = executeRequest(url, payload)
    return response.json()

def getMatchInfo(region, matchId):
    if Match.filter(matchId=matchId, region=region).exists():
        return Match.get(matchId=matchId, region=region)
    else:
        url = (base_url+URLS['match']).format(region=region, matchId=matchId)
        payload = {'api_key': api_key}
        response = executeRequest(url, payload)
        if response.status_code != requests.codes.ok:
            return None
        else:
            return response.json()

def handle_status(r):
    if r.status_code == requests.codes.ok:
        return True
    elif r.status_code == requests.codes.too_many_requests:
        time.sleep(int(r.headers.get('Retry-After', RATE_LIMIT_EXCEEDED_SLEEP_DURATION))) 
    else:
        r.raise_for_status()
    
