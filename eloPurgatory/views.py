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

from django.http import HttpResponse
import eloPurgatory.logic
from eloPurgatory.logic import handleSummoner, handleMatchRank, handleMatchDetails, convertModelToDict

def basicCall(request, region, queue, summonerName):
    summonerInfo = getSummonerInfo(region, summonerName)
    summoner = handleSummoner(summonerName, summonerInfo)
    summonerRank = handleMatchRank(summoner, queue, getRankInfo(region, summoner.summonerId), None)
    matchlistInfo = getMatchListInfo(region, summoner.summonerId, queue)
    matches = matchlistInfo['matches']
    index = 0
    matchlimit = 5
    matchlist = {}
    for match in matches:
        if index >= matchlimit:
            break
        matchInfo = getMatchInfo(match['region'], match['matchId'])
        if matchInfo == None:
            continue
        data = handleMatchDetails(matchInfo, summoner.summonerId)
        matchlist.update(data)
        index += 1

    for matchId, matchData in matchlist.items():
        players = matchData['players']
        matchPlayerIds = ','.join(str(x) for x in players.keys())
        matchPlayerInfo = getSummonerInfoById(region, matchPlayerIds)
        matchRanks = getRankInfo(region, matchPlayerIds)
        for playerId, data in players.items():
            player = handleSummoner(playerId, matchPlayerInfo)
            rank = handleMatchRank(player, queue, matchRanks, data['prevSeasonTier'])
            data.update({ 'rank': convertModelToDict(rank) })
     
    jsonData = json.dumps({ 'summoner': convertModelToDict(summoner), 'region': region, 'rank': convertModelToDict(summonerRank), 'matchlist': matchlist })
    return render(request, 'elo.html', { "data": jsonData,  'matchlist': matchlist })


def executeRequest(url, payload):
    response = requests.get(url, params=payload)
    while response.status_code == requests.codes.too_many_requests:
        time.sleep(int(response.headers.get('Retry-After')))
        response = requests.get(url, params=payload)    
    return response

def getSummonerInfo(region, summonerName):
    url = (base_url+URLS['summoner_by_name']).format(region=region, summonerName=summonerName)
    payload = {'api_key': api_key}
    response = executeRequest(url, payload)
    while response.status_code != requests.codes.ok:
        time.sleep(1)
        response = executeRequest(url, payload)
    return response.json()

def getSummonerInfoById(region, summonerId):
    url = (base_url+URLS['summoner_by_id']).format(region=region, summonerId=summonerId)
    payload = {'api_key': api_key}
    response = executeRequest(url, payload)
    while response.status_code != requests.codes.ok:
        time.sleep(1)
        response = executeRequest(url, payload)
    return response.json()

def getRankInfo(region, summonerId):
    url = (base_url+URLS['rank_data']).format(region=region, summonerId=summonerId)
    payload = {'api_key': api_key}
    response = executeRequest(url, payload)
    while response.status_code != requests.codes.ok:
        time.sleep(1)
        response = executeRequest(url, payload)
    return response.json()

def getMatchListInfo(region, summonerId, queue):
    url = (base_url+URLS['match_list']).format(region=region, summonerId=summonerId)
    payload = {'api_key': api_key, 'rankedQueues': queue}
    response = executeRequest(url, payload)
    while response.status_code != requests.codes.ok:
        time.sleep(1)
        response = executeRequest(url, payload)
    return response.json()

def getMatchInfo(region, matchId):
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
    
