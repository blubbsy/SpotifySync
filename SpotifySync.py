import requests
import base64
import json
from bs4 import BeautifulSoup
import os
import re
from fuzzywuzzy import fuzz

# Spotify API credentials
CLIENT_ID = '464bf181392546bc9b148a7560727850'
CLIENT_SECRET = '09a0e89876c94108bec7447d08d4bbbd'
REDIRECT_URI = 'https://github.com/blubbsy/SpotifySync'

class SpotifyAPI:
    def __init__(self, client_id, client_secret, redirect_uri, code=None, refresh_token=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.code = code
        self.refresh_token = refresh_token
        self.access_token = None
        if self.code:
            self.get_tokens_from_code()
        elif self.refresh_token:
            self.access_token = self.get_access_token()

    def get_tokens_from_code(self):
        """
        Exchange authorization code for access and refresh tokens.
        """
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'authorization_code',
            'code': self.code,
            'redirect_uri': self.redirect_uri,
        }
        response = requests.post('https://accounts.spotify.com/api/token', data=data)
        response_data = response.json()
        self.access_token = response_data['access_token']
        self.refresh_token = response_data['refresh_token']

    def get_access_token(self):
        """
        Get a new Spotify access token using the refresh token.
        """
        auth_str = f"{self.client_id}:{self.client_secret}"
        b64_auth_str = base64.b64encode(auth_str.encode()).decode()
        headers = {
            'Authorization': f'Basic {b64_auth_str}',
        }
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
        }
        response = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=data)
        response_data = response.json()
        return response_data['access_token']

    def get_playlist_tracks(self, playlist_id):
        """
        Get the list of track names and IDs in a Spotify playlist.
        """
        headers = {
            'Authorization': f'Bearer {self.access_token}',
        }
        response = requests.get(f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks', headers=headers)
        response_data = response.json()
        return [{'name': item['track']['name'], 'artists': [artist['name'] for artist in item['track']['artists']], 'id': item['track']['id']} for item in response_data['items']]

    def search_track(self, track_title, artists):
        """
        Search for a track on Spotify by title and artist.
        """
        headers = {
            'Authorization': f'Bearer {self.access_token}',
        }
        query = f"track:{track_title} artist:{' '.join(artists)}"
        response = requests.get(f'https://api.spotify.com/v1/search?q={query}&type=track', headers=headers)
        response_data = response.json()
        tracks = response_data.get('tracks', {}).get('items', [])
        if tracks:
            return tracks[0]['uri'], tracks[0]['id']
        return None, None

    def add_tracks_to_playlist(self, playlist_id, track_uris):
        """
        Add tracks to a Spotify playlist.
        """
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }
        data = json.dumps({
            'uris': track_uris,
        })
        response = requests.post(f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks', headers=headers, data=data)
        return response.status_code == 201

class AppleMusicScraper:
    @staticmethod
    def get_playlist_tracks(playlist_url):
        """
        Scrape the Apple Music playlist page to get track names.
        """
        response = requests.get(playlist_url)
        
        if response.status_code != 200:
            print(f'\033[32m Error while getting the playlist: {response.text}')
            return []
        
        # Parse the Apple Music page
        soup = BeautifulSoup(response.content, 'html.parser')
        tracks = []
        tracks_metatags = soup.find_all('meta', property=re.compile(r"^music:song$"))
        
        # Scrape song data for each song
        for tag in tracks_metatags:
            track_url = tag['content']
            try:
                r = requests.get(track_url)
                if r.status_code != 200:
                    print(f'\033[93m Could not get song info for: {track_url} ({r.status_code}) \033[90m')
                    continue

                soup = BeautifulSoup(r.content, 'html.parser')

                # Find the server data script tag by its type and id
                script_tag = soup.find('script', {'type': 'application/json', 'id': 'serialized-server-data'})

                # Extract the JSON content from the script tag
                json_data = script_tag.string
                data = json.loads(json_data)

                track_title = data[0]['data']['sections'][0]['items'][0]['title']
                artists_string = data[0]['data']['sections'][0]['items'][0]['artists']
                artists = artists_string.split(', ')

                print(f"Fetched AppleMusic data for {track_title} by {artists}")

                tracks.append({'title': track_title, 'artists': artists})
            except Exception as e:
                print(f'\033[93m Could not get song info for: {track_url} due to {e} \033[90m')
        
        return tracks

class PlaylistSync:
    def __init__(self, spotify_api, playlists):
        self.spotify_api = spotify_api
        self.playlists = playlists

    def is_similar(self, track1, track2):
        """
        Check if two tracks are similar based on title and artists.
        """
        title_similarity = fuzz.ratio(track1['title'], track2['title'])
        artists_similarity = fuzz.ratio(', '.join(track1['artists']), ', '.join(track2['artists']))
        return title_similarity > 80 and artists_similarity > 80

    def sync_playlists(self):
        """
        Sync Apple Music playlists to Spotify.
        """
        for playlist in self.playlists:
            apple_music_tracks = AppleMusicScraper.get_playlist_tracks(playlist['applemusic_playlist_url'])
            spotify_tracks = self.spotify_api.get_playlist_tracks(playlist['spotify_playlist_id'])
            
            # Extract track IDs from Spotify tracks
            spotify_track_ids = {track['id'] for track in spotify_tracks}
            
            new_tracks = []
            added_tracks = []
            for track in apple_music_tracks:
                track_uri, track_id = self.spotify_api.search_track(track['title'], track['artists'])
                if track_id and track_id not in spotify_track_ids:
                    new_tracks.append(track_uri)
                    added_tracks.append(track)
                elif not track_id:
                    print(f"Track not found on Spotify: {track['title']} by {', '.join(track['artists'])}")
            
            if new_tracks:
                success = self.spotify_api.add_tracks_to_playlist(playlist['spotify_playlist_id'], new_tracks)
                if success:
                    print(f"Added {len(new_tracks)} new tracks to Spotify playlist {playlist['spotify_playlist_id']}")
                    print("Tracks added:")
                    for track in added_tracks:
                        print(f"{track['title']} by {', '.join(track['artists'])}")
                else:
                    print(f"Failed to add tracks to Spotify playlist {playlist['spotify_playlist_id']}")
            else:
                print(f"No new tracks to add for Spotify playlist {playlist['spotify_playlist_id']}")

if __name__ == '__main__':
    code = None
    refresh_token = None

    # Check if the script is running for the first time
    if not os.path.exists('refresh_token.txt'):
        # Generate the authorization URL
        scope = 'playlist-modify-public playlist-modify-private'
        auth_url = f"https://accounts.spotify.com/authorize?response_type=code&client_id={CLIENT_ID}&scope={scope}&redirect_uri={REDIRECT_URI}"
        print(f"Please open the following URL in your browser to authorize the application:\n{auth_url}")
        code = input("Enter the authorization code: ")

        # Initialize Spotify API with the authorization code to get tokens
        spotify_api = SpotifyAPI(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, code=code)
        
        # Save the refresh token for future use
        with open('refresh_token.txt', 'w') as f:
            f.write(spotify_api.refresh_token)
    else:
        # Read the refresh token from the file
        with open('refresh_token.txt', 'r') as f:
            refresh_token = f.read().strip()

        # Initialize Spotify API with the refresh token
        spotify_api = SpotifyAPI(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, refresh_token=refresh_token)

    # Spotify playlist details
    playlists = [
        {
            'applemusic_playlist_url': 'https://music.apple.com/de/playlist/2424/pl.u-leyl1q6hMNDZd7X',
            'spotify_playlist_id': '4rz9bzNtfKnRKlUt62ds1F',
        },
        #{
        #    'applemusic_playlist_url': 'https://music.apple.com/us/playlist/xxx/pl.xxx',
        #    'spotify_playlist_id': 'xxx',
        #},
    ]

    playlist_sync = PlaylistSync(spotify_api, playlists)
    playlist_sync.sync_playlists()