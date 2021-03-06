import base64
import config
import json
import telstra_auth
import urllib
import xbmcaddon

from aussieaddonscommon.exceptions import AussieAddonsException
from aussieaddonscommon import session as custom_session
from aussieaddonscommon import utils

session = custom_session.Session()
addon = xbmcaddon.Addon()


def get_embed_token(video_id):
    """send our user token to get our embed token, including api key"""
    token = telstra_auth.get_user_token(session)
    user_id = token.get('uuid')
    url = config.EMBED_TOKEN_URL.format(user_id, video_id)
    req = session.get(url)
    embed_token = json.loads(req.text).get('embedToken')
    return urllib.quote(embed_token)


def get_secure_token(secure_url, videoId):
    """send our embed token back with a few other url encoded parameters"""
    res = session.get(secure_url)
    data = res.text
    try:
        parsed_json = json.loads(data)
        for stream in parsed_json['authorization_data'][videoId]['streams']:
            if stream.get('delivery_type') == 'dash':
                dash_url = stream['url'].get('data')
                wv_lic = stream.get('widevine_server_path')
    except KeyError:
        utils.log('Parsed json data: {0}'.format(parsed_json))
        try:
            auth_msg = parsed_json['authorization_data'][videoId]['message']
            if auth_msg == 'unauthorizedlocation':
                country = parsed_json['user_info']['country']
                raise AussieAddonsException('Unauthorised location for '
                                            'streaming. '
                                            'Detected location is: {0}. '
                                            'Please check VPN/smart DNS '
                                            'settings and try again'
                                            ''.format(country))
        except Exception as e:
            raise e
    return {'dash_url': base64.b64decode(dash_url), 'wv_lic': wv_lic}


def get_dash_playlist(video_id):
    """ Main function to call other functions that will return us our m3u8 HLS
        playlist as a string, which we can then write to a file for Kodi
        to use"""
    embed_token = get_embed_token(video_id)
    authorize_url = config.AUTH_URL.format(config.PCODE, video_id, embed_token)
    return get_secure_token(authorize_url, video_id)
