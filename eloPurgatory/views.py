from django.shortcuts import render

import requests
import time

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

def basicCall(request, region, summonerName):
    r = getSummonerInfo(region, summonerName)
    return HttpResponse(r)


def executeRequest(url, payload):
    response = requests.get(url, params=payload)
    while response.status_code == requests.codes.too_many_requests:
        time.sleep(int(r.headers.get('Retry-After')))
        response = requests.get(url, params=payload)    
    return response

def getSummonerInfo(region, summonerName):
    url = (base_url+URLS['summoner_by_name']).format(region=region, summonerName=summonerName)
    payload = {'api_key': api_key}
    response = executeRequest(url, payload)
    return response

def getRankInfo(region, summonerId):
    url = (base_url+URLS['rank_data'].format(region=region, summonerId=summonerId))
    payload = {'api_key': api_key}
    response = executeRequest(url, payload)
    return response

def getMatchInfo(summonderId):
    url = (base_url+URLS['match_list'].format(summonerId=summonerId))
    payload = {'api_key': api_key}
    response = executeRequest(url, payload)
    return response

def handle_status(r):
    if r.status_code == requests.codes.ok:
        return True
    elif r.status_code == requests.codes.too_many_requests:
        time.sleep(int(r.headers.get('Retry-After', RATE_LIMIT_EXCEEDED_SLEEP_DURATION))) 
    else:
        r.raise_for_status()

