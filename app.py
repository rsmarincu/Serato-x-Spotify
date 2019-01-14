import json
from flask import Flask, request, redirect, g, render_template
import requests
import base64
import urllib
from urllib.parse import quote
from collections import OrderedDict
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

spotify_auth_url = "https://accounts.spotify.com/authorize"
spotify_token_url = "https://accounts.spotify.com/api/token"
spotify_api_url = "https://api.spotify.com/v1"
playlist_tracks_url = "https://api.spotify.com/v1/playlists/{}/tracks"
spotify_artist_url = "https://api.spotify.com/v1/artists/"

client_side_url = 'http://127.0.0.1:5000'
redirect_uri = "{}/callback/q".format(client_side_url)
scope = "user-read-private"

auth_query_parameters = {
    "client_id": client_id,
    "response_type": "code",
    "scope": scope,
    "redirect_uri": redirect_uri
}


@app.route('/')
def index():
    url_args = "&".join(["{}={}".format(key, quote(val))
                         for key, val in auth_query_parameters.items()])
    auth_url = "{}/?{}".format(spotify_auth_url, url_args)
    return redirect(auth_url)


@app.route('/callback/q')
def callback():

    tokenCode = request.args['code']
    auth_ids = "{}:{}".format(client_id, client_secret)
    encodedIds = base64.b64encode(auth_ids.encode('ascii'))
    encodedIds = encodedIds.decode()
    HEADERS = {
        'Authorization': 'Basic {}'.format(encodedIds)
    }

    DATA = {
        'grant_type': 'authorization_code',
        'code': str(tokenCode),
        'redirect_uri': redirect_uri
    }

    # DATA=json.dumps(DATA,sort_keys=True)
    r = requests.post(spotify_token_url, data=DATA, headers=HEADERS)
    response = json.loads(r.text)
    access_token = response['access_token']
    refresh_token = response['refresh_token']
    token_type = response['token_type']
    expires_in = response['expires_in']

    authorization_header = {"Authorization": "Bearer {}".format(access_token)}
    user_profile_api = "{}/me".format(spotify_api_url)

    profile_response = requests.get(
        user_profile_api, headers=authorization_header)

    profile_data = json.loads(profile_response.text)

    playlist_api = "{}/playlists".format(profile_data['href'])

    playlist_response = requests.get(
        playlist_api, headers=authorization_header)

    playlist_data = json.loads(playlist_response.text)

    playlist_name = []
    tracks = []
    artists = []

    for playlist in playlist_data['items']:
        playlist_name.append(playlist['name'])
        tracks.append(getTracks(playlist['id'],access_token))
    # for track in tracks:
    #     for artist in track:
    #         print(getGenre(artist[0],access_token))


    return render_template("main.html", tracks=tracks, playlists = playlist_name)

def getTracks(playlist_id,token):
    tracklist = []
    artists = []
    HEADERS = {
        "Authorization": "Bearer {}".format(token)
    }
    query_url = playlist_tracks_url.format(playlist_id)
    r = requests.get(query_url,headers = HEADERS)
    response = json.loads(r.text)
    for item in response['items']:
        genre = getGenre(item['track']['artists'][0]['id'],token)
        tracklist.append((item['track']['artists'][0]['name'],item['track']['name'],genre))

    return tracklist

def getGenre(arist_id,token):
    genres = []
    HEADERS = {
        "Authorization": "Bearer {}".format(token)
    }

    query_url = spotify_artist_url + arist_id
    r = requests.get(query_url,headers = HEADERS)
    response = json.loads(r.text)
    genres = response['genres']
    return genres





if __name__ == "__main__":
    app.run(debug=True)
