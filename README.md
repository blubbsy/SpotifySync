# SpotifySync

## Description
SpotifySync is a Python script that synchronizes playlists from Apple Music to Spotify. It fetches tracks from an Apple Music playlist, searches for them on Spotify, and adds them to a specified Spotify playlist. If the Spotify playlist does not exist, it will be created automatically.

## How it works
1. **Authorization**: The script first checks if a refresh token is available. If not, it prompts the user to authorize the application via a URL and obtain an authorization code. This code is then exchanged for access and refresh tokens.
2. **Fetching Apple Music Tracks**: The script scrapes the Apple Music playlist page to get track names and artists.
3. **Fetching Spotify Playlist Tracks**: The script fetches the existing tracks from the specified Spotify playlist.
4. **Searching for Tracks on Spotify**: The script searches for each Apple Music track on Spotify.
5. **Adding Tracks to Spotify Playlist**: The script adds the tracks that are not already in the Spotify playlist. If the playlist does not exist, it creates a new one.

## Usage
1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/SpotifySync.git
    cd SpotifySync
    ```

2. Install the required packages:
    ```sh
    pip install requests beautifulsoup4
    ```

3. Run the script:
    ```sh
    python SpotifySync.py
    ```

4. Follow the instructions to authorize the application and enter the authorization code.

## Used packages and used Python version
- **requests**: Used for making HTTP requests to the Spotify and Apple Music APIs.
- **base64**: Used for encoding client credentials for Spotify API authentication.
- **json**: Used for parsing JSON responses from APIs.
- **beautifulsoup4**: Used for parsing HTML content from Apple Music pages.
- **os**: Used for interacting with the operating system (e.g., checking if a file exists).
- **urllib.parse**: Used for URL-encoding query parameters.
- **re**: Used for regular expressions to find specific HTML tags.

**Python version**: 3.8 or higher
