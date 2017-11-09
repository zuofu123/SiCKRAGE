# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import datetime
import time
import traceback

from CodernityDB.database import RecordNotFound

import sickrage
from sickrage.core.helpers import findCertainShow, try_int
from sickrage.indexers import IndexerApi


def get_scene_numbering(indexer_id, indexer, season, episode, fallback_to_xem=True):
    """
    Returns a tuple, (season, episode), with the scene numbering (if there is one),
    otherwise returns the xem numbering (if fallback_to_xem is set), otherwise
    returns the TVDB numbering.
    (so the return values will always be set)

    :param indexer_id: int
    :param season: int
    :param episode: int
    :param fallback_to_xem: bool If set (the default), check xem for matches if there is no local scene numbering
    :return: (int, int) a tuple with (season, episode)
    """
    if indexer_id is None or season is None or episode is None:
        return season, episode

    showObj = findCertainShow(sickrage.app.showlist, int(indexer_id))
    if showObj and not showObj.is_scene:
        return season, episode

    result = find_scene_numbering(int(indexer_id), int(indexer), season, episode)
    if result:
        return result
    else:
        if fallback_to_xem:
            xem_result = find_xem_numbering(int(indexer_id), int(indexer), season, episode)
            if xem_result:
                return xem_result
        return season, episode


def find_scene_numbering(indexer_id, indexer, season, episode):
    """
    Same as get_scene_numbering(), but returns None if scene numbering is not set
    """
    if indexer_id is None or season is None or episode is None:
        return season, episode

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    dbData = [x['doc'] for x in sickrage.app.main_db.db.get_many('scene_numbering', indexer_id, with_doc=True)
              if x['doc']['indexer'] == indexer
              and x['doc']['season'] == season
              and x['doc']['episode'] == episode
              and x['doc']['scene_season'] != 0
              and x['doc']['scene_episode'] != 0]

    if dbData:
        return try_int(dbData[0].get("scene_season")), try_int(dbData[0].get("scene_episode"))


def get_scene_absolute_numbering(indexer_id, indexer, absolute_number, fallback_to_xem=True):
    """
    Returns a tuple, (season, episode), with the scene numbering (if there is one),
    otherwise returns the xem numbering (if fallback_to_xem is set), otherwise
    returns the TVDB numbering.
    (so the return values will always be set)

    :param indexer_id: int
    ;param absolute_number: int
    :param fallback_to_xem: bool If set (the default), check xem for matches if there is no local scene numbering
    :return: (int, int) a tuple with (season, episode)
    """
    if indexer_id is None or absolute_number is None:
        return absolute_number

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    showObj = findCertainShow(sickrage.app.showlist, indexer_id)
    if showObj and not showObj.is_scene:
        return absolute_number

    result = find_scene_absolute_numbering(indexer_id, indexer, absolute_number)
    if result:
        return result
    else:
        if fallback_to_xem:
            xem_result = find_xem_absolute_numbering(indexer_id, indexer, absolute_number)
            if xem_result:
                return xem_result
        return absolute_number


def find_scene_absolute_numbering(indexer_id, indexer, absolute_number):
    """
    Same as get_scene_numbering(), but returns None if scene numbering is not set
    """
    if indexer_id is None or absolute_number is None:
        return absolute_number

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    dbData = [x['doc'] for x in sickrage.app.main_db.db.get_many('scene_numbering', indexer_id, with_doc=True)
              if x['doc']['indexer'] == indexer
              and x['doc']['absolute_number'] == absolute_number
              and x['doc']['scene_absolute_number'] != 0]

    if dbData:
        return try_int(dbData[0].get('scene_absolute_number'))


def get_indexer_numbering(indexer_id, indexer, sceneSeason, sceneEpisode, fallback_to_xem=True):
    """
    Returns a tuple, (season, episode) with the TVDB numbering for (sceneSeason, sceneEpisode)
    (this works like the reverse of get_scene_numbering)
    """
    if indexer_id is None or sceneSeason is None or sceneEpisode is None:
        return sceneSeason, sceneEpisode

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    dbData = [x['doc'] for x in sickrage.app.main_db.db.get_many('scene_numbering', indexer_id, with_doc=True)
              if x['doc']['indexer'] == indexer
              and x['doc']['scene_season'] == sceneSeason
              and x['doc']['scene_episode'] == sceneEpisode]

    if dbData:
        return try_int(dbData[0].get("season")), try_int(dbData[0].get("episode"))
    else:
        if fallback_to_xem:
            return get_indexer_numbering_for_xem(indexer_id, indexer, sceneSeason, sceneEpisode)
        return sceneSeason, sceneEpisode


def get_indexer_absolute_numbering(indexer_id, indexer, sceneAbsoluteNumber, fallback_to_xem=True, scene_season=None):
    """
    Returns a tuple, (season, episode, absolute_number) with the TVDB absolute numbering for (sceneAbsoluteNumber)
    (this works like the reverse of get_absolute_numbering)
    """
    if indexer_id is None or sceneAbsoluteNumber is None:
        return sceneAbsoluteNumber

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    if scene_season is None:
        dbData = [x['doc'] for x in sickrage.app.main_db.db.get_many('scene_numbering', indexer_id, with_doc=True)
                  if x['doc']['indexer'] == indexer
                  and x['doc']['scene_absolute_number'] == sceneAbsoluteNumber]
    else:
        dbData = [x['doc'] for x in sickrage.app.main_db.db.get_many('scene_numbering', indexer_id, with_doc=True)
                  if x['doc']['indexer'] == indexer
                  and x['doc']['scene_absolute_number'] == sceneAbsoluteNumber
                  and x['doc']['scene_season'] == scene_season]

    if dbData:
        return try_int(dbData[0].get("absolute_number"))
    else:
        if fallback_to_xem:
            return get_indexer_absolute_numbering_for_xem(indexer_id, indexer, sceneAbsoluteNumber, scene_season)
        return sceneAbsoluteNumber


def set_scene_numbering(indexer_id, indexer, season=0, episode=0, absolute_number=0, sceneSeason=0,
                        sceneEpisode=0, sceneAbsolute=0):
    """
    Set scene numbering for a season/episode.
    To clear the scene numbering, leave both sceneSeason and sceneEpisode as None.
    """
    if indexer_id is None:
        return

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    if season and episode:
        dbData = [x['doc'] for x in sickrage.app.main_db.db.get_many('scene_numbering', indexer_id, with_doc=True)
                  if x['doc']['index'] == indexer
                  and x['doc']['season'] == season
                  and x['doc']['episode'] == episode]

        if len(dbData):
            dbData[0]['scene_season'] = sceneSeason
            dbData[0]['scene_episode'] = sceneEpisode
            sickrage.app.main_db.db.update(dbData[0])
        else:
            sickrage.app.main_db.db.insert({
                '_t': 'scene_numbering',
                'indexer': indexer,
                'indexer_id': indexer_id,
                'season': season,
                'episode': episode,
                'scene_season': sceneSeason,
                'scene_episode': sceneEpisode,
                'absolute_number': absolute_number,
                'scene_absolute_number': sceneAbsolute
            })

    elif absolute_number:
        dbData = [x['doc'] for x in sickrage.app.main_db.db.get_many('scene_numbering', indexer_id, with_doc=True)
                  if x['doc']['index'] == indexer
                  and x['doc']['absolute_number'] == absolute_number]

        if len(dbData):
            dbData[0]['scene_absolute_number'] = sceneAbsolute
            sickrage.app.main_db.db.update(dbData[0])
        else:
            sickrage.app.main_db.db.insert({
                '_t': 'scene_numbering',
                'indexer': indexer,
                'indexer_id': indexer_id,
                'season': season,
                'episode': episode,
                'scene_season': sceneSeason,
                'scene_episode': sceneEpisode,
                'absolute_number': absolute_number,
                'scene_absolute_number': sceneAbsolute
            })

    # Reload data from DB so that cache and db are in sync
    show = findCertainShow(sickrage.app.showlist, indexer_id)
    show.flushEpisodes()


def find_xem_numbering(indexer_id, indexer, season, episode):
    """
    Returns the scene numbering, as retrieved from xem.
    Refreshes/Loads as needed.

    :param indexer_id: int
    :param season: int
    :param episode: int
    :return: (int, int) a tuple of scene_season, scene_episode, or None if there is no special mapping.
    """
    if indexer_id is None or season is None or episode is None:
        return season, episode

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    xem_refresh(indexer_id, indexer)

    dbData = [x['doc'] for x in sickrage.app.main_db.db.get_many('tv_episodes', indexer_id, with_doc=True)
              if x['doc']['indexer'] == indexer
              and x['doc']['season'] == season
              and x['doc']['episode'] == episode
              and x['doc']['scene_season'] != 0
              and x['doc']['scene_episode'] != 0]

    if dbData:
        return try_int(dbData[0].get("scene_season")), try_int(dbData[0].get("scene_episode"))


def find_xem_absolute_numbering(indexer_id, indexer, absolute_number):
    """
    Returns the scene numbering, as retrieved from xem.
    Refreshes/Loads as needed.

    :param indexer_id: int
    :param absolute_number: int
    :return: int
    """
    if indexer_id is None or absolute_number is None:
        return absolute_number

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    xem_refresh(indexer_id, indexer)

    dbData = [x['doc'] for x in sickrage.app.main_db.db.get_many('tv_episodes', indexer_id, with_doc=True)
              if x['doc']['indexer'] == indexer
              and x['doc']['absolute_number'] == absolute_number
              and x['doc']['scene_absolute_number'] != 0]

    if dbData:
        return try_int(dbData[0].get('scene_absolute_number'))


def get_indexer_numbering_for_xem(indexer_id, indexer, sceneSeason, sceneEpisode):
    """
    Reverse of find_xem_numbering: lookup a tvdb season and episode using scene numbering

    :param indexer_id: int
    :param sceneSeason: int
    :param sceneEpisode: int
    :return: (int, int) a tuple of (season, episode)
    """
    if indexer_id is None or sceneSeason is None or sceneEpisode is None:
        return sceneSeason, sceneEpisode

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    xem_refresh(indexer_id, indexer)

    dbData = [x['doc'] for x in sickrage.app.main_db.db.get_many('tv_episodes', indexer_id, with_doc=True)
              if x['doc']['indexer'] == indexer
              and x['doc']['scene_season'] == sceneSeason
              and x['doc']['scene_episode'] == sceneEpisode]

    if dbData:
        return try_int(dbData[0].get("season")), try_int(dbData[0].get("episode"))

    return sceneSeason, sceneEpisode


def get_indexer_absolute_numbering_for_xem(indexer_id, indexer, sceneAbsoluteNumber, scene_season=None):
    """
    Reverse of find_xem_numbering: lookup a tvdb season and episode using scene numbering

    :param indexer_id: int
    :param sceneAbsoluteNumber: int
    :return: int
    """
    if indexer_id is None or sceneAbsoluteNumber is None:
        return sceneAbsoluteNumber

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    xem_refresh(indexer_id, indexer)

    if scene_season is None:
        dbData = [x['doc'] for x in sickrage.app.main_db.db.get_many('tv_episodes', indexer_id, with_doc=True)
                  if x['doc']['indexer'] == indexer
                  and x['doc']['scene_absolute_number'] == sceneAbsoluteNumber]
    else:
        dbData = [x['doc'] for x in sickrage.app.main_db.db.get_many('tv_episodes', indexer_id, with_doc=True)
                  if x['doc']['indexer'] == indexer
                  and x['doc']['scene_absolute_number'] == sceneAbsoluteNumber
                  and x['doc']['scene_season'] == scene_season]

    if dbData:
        return try_int(dbData[0].get('absolute_number'))

    return sceneAbsoluteNumber


def get_scene_numbering_for_show(indexer_id, indexer):
    """
    Returns a dict of (season, episode) : (sceneSeason, sceneEpisode) mappings
    for an entire show.  Both the keys and values of the dict are tuples.
    Will be empty if there are no scene numbers set
    """
    if indexer_id is None:
        return {}

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    result = {}
    for dbData in [x['doc'] for x in sickrage.app.main_db.db.get_many('scene_numbering', indexer_id, with_doc=True)]:
        season = try_int(dbData['season'])
        episode = try_int(dbData['episode'])
        scene_season = try_int(dbData['scene_season'])
        scene_episode = try_int(dbData['scene_episode'])
        if try_int(dbData['indexer']) != indexer or (scene_season or scene_episode) == 0: continue

        result[(season, episode)] = (scene_season, scene_episode)

    return result


def get_xem_numbering_for_show(indexer_id, indexer):
    """
    Returns a dict of (season, episode) : (sceneSeason, sceneEpisode) mappings
    for an entire show.  Both the keys and values of the dict are tuples.
    Will be empty if there are no scene numbers set in xem
    """
    if indexer_id is None:
        return {}

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    xem_refresh(indexer_id, indexer)

    result = {}
    for dbData in [x['doc'] for x in sickrage.app.main_db.db.get_many('tv_episodes', indexer_id, with_doc=True)]:
        season = try_int(dbData.get('season'))
        episode = try_int(dbData.get('episode'))
        scene_season = try_int(dbData.get('scene_season'))
        scene_episode = try_int(dbData.get('scene_episode'))
        if try_int(dbData['indexer']) != indexer or (scene_season or scene_episode) == 0: continue

        result[(season, episode)] = (scene_season, scene_episode)

    return result


def get_scene_absolute_numbering_for_show(indexer_id, indexer):
    """
    Returns a dict of (season, episode) : (sceneSeason, sceneEpisode) mappings
    for an entire show.  Both the keys and values of the dict are tuples.
    Will be empty if there are no scene numbers set
    """
    if indexer_id is None:
        return {}

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    result = {}
    for dbData in [x['doc'] for x in sickrage.app.main_db.db.get_many('scene_numbering', indexer_id, with_doc=True)]:
        absolute_number = try_int(dbData.get('absolute_number'))
        scene_absolute_number = try_int(dbData.get('scene_absolute_number'))
        if try_int(dbData.get('indexer')) != indexer or scene_absolute_number == 0: continue

        result[absolute_number] = scene_absolute_number

    return result


def get_xem_absolute_numbering_for_show(indexer_id, indexer):
    """
    Returns a dict of (season, episode) : (sceneSeason, sceneEpisode) mappings
    for an entire show.  Both the keys and values of the dict are tuples.
    Will be empty if there are no scene numbers set in xem
    """
    if indexer_id is None:
        return {}

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    xem_refresh(indexer_id, indexer)

    result = {}
    for dbData in [x['doc'] for x in sickrage.app.main_db.db.get_many('tv_episodes', indexer_id, with_doc=True)]:
        absolute_number = try_int(dbData.get('absolute_number'))
        scene_absolute_number = try_int(dbData.get('scene_absolute_number'))
        if try_int(dbData['indexer']) != indexer or scene_absolute_number == 0: continue

        result[absolute_number] = scene_absolute_number

    return result


def xem_refresh(indexer_id, indexer, force=False):
    """
    Refresh data from xem for a tv show

    :param indexer_id: int
    """
    if not indexer_id or indexer_id < 1:
        return

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    MAX_REFRESH_AGE_SECS = 86400  # 1 day

    try:
        dbData = sickrage.app.main_db.db.get('xem_refresh', indexer_id, with_doc=True)['doc']
        lastRefresh = try_int(dbData['last_refreshed'])
        refresh = int(time.mktime(datetime.datetime.today().timetuple())) > lastRefresh + MAX_REFRESH_AGE_SECS
    except RecordNotFound:
        refresh = True

    if refresh or force:
        sickrage.app.log.debug(
            'Looking up XEM scene mapping for show %s on %s' % (indexer_id, IndexerApi(indexer).name))

        # mark refreshed
        try:
            dbData = sickrage.app.main_db.db.get('xem_refresh', indexer_id, with_doc=True)['doc']
            dbData['last_refreshed'] = int(time.mktime(datetime.datetime.today().timetuple()))
            sickrage.app.main_db.db.update(dbData)
        except RecordNotFound:
            sickrage.app.main_db.db.insert({
                '_t': 'xem_refresh',
                'indexer': indexer,
                'last_refreshed': int(time.mktime(datetime.datetime.today().timetuple())),
                'indexer_id': indexer_id
            })

        try:
            # XEM MAP URL
            url = "http://thexem.de/map/havemap?origin=%s" % IndexerApi(indexer).config['xem_origin']

            try:
                parsedJSON = sickrage.app.wsession.get(url).json()
                if indexer_id not in map(int, parsedJSON['data']):
                    raise
            except:
                for x in sickrage.app.main_db.db.get_many('tv_episodes', indexer_id, with_doc=True):
                    x['doc']['scene_season'], x['doc']['scene_episode'], x['doc']['scene_absolute_number'] = 0, 0, 0
                    sickrage.app.main_db.db.update(x['doc'])
                return

            # XEM API URL
            url = "http://thexem.de/map/all?id={}&origin={}&destination=scene".format(
                indexer_id, IndexerApi(indexer).config['xem_origin'])

            try:
                parsedJSON = sickrage.app.wsession.get(url).json()
                if 'success' not in parsedJSON['result']:
                    raise
            except:
                sickrage.app.log.info(
                    'No XEM data for show "%s on %s"' % (indexer_id, IndexerApi(indexer).name,))
                return

            for entry in parsedJSON['data']:
                try:
                    dbData = \
                        [x['doc'] for x in sickrage.app.main_db.db.get_many('tv_episodes', indexer_id, with_doc=True)
                         if x['doc']['season'] == entry[IndexerApi(indexer).config['xem_origin']]['season']
                         and x['doc']['episode'] == entry[IndexerApi(indexer).config['xem_origin']]['episode']][
                            0]
                except:
                    continue

                if 'scene' in entry:
                    dbData['scene_season'] = entry['scene']['season']
                    dbData['scene_episode'] = entry['scene']['episode']
                    dbData['scene_absolute_number'] = entry['scene']['absolute']
                if 'scene_2' in entry:  # for doubles
                    dbData['scene_season'] = entry['scene_2']['season']
                    dbData['scene_episode'] = entry['scene_2']['episode']
                    dbData['scene_absolute_number'] = entry['scene_2']['absolute']

                sickrage.app.main_db.db.update(dbData)

        except Exception as e:
            sickrage.app.log.warning(
                "Exception while refreshing XEM data for show {} on {}: {}".format(indexer_id,
                                                                                   IndexerApi(indexer).name,
                                                                                   e.message))
            sickrage.app.log.debug(traceback.format_exc())


def get_absolute_number_from_season_and_episode(show, season, episode):
    """
    Find the absolute number for a show episode

    :param show: Show object
    :param season: Season number
    :param episode: Episode number
    :return: The absolute number
    """

    absolute_number = None

    if season and episode:
        dbData = [x['doc'] for x in sickrage.app.main_db.db.get_many('tv_episodes', show.indexerid, with_doc=True)
                  if x['doc']['season'] == season
                  and x['doc']['episode'] == episode]

        if len(dbData) == 1:
            absolute_number = try_int(dbData[0].get("absolute_number"))
            sickrage.app.log.debug(
                "Found absolute number %s for show %s S%02dE%02d" % (absolute_number, show.name, season, episode))
        else:
            sickrage.app.log.debug(
                "No entries for absolute number for show %s S%02dE%02d" % (show.name, season, episode))

    return absolute_number
