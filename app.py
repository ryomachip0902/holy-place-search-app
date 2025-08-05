from flask import Flask, render_template, request, jsonify
import os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

app = Flask(__name__)

# 環境変数からAPIキーを取得
API_KEY = os.environ.get('YOUTUBE_API_KEY')

def get_youtube_service():
    """YouTube Data APIのサービスオブジェクトを構築して返す"""
    return build('youtube', 'v3', developerKey=API_KEY)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    try:
        youtube = get_youtube_service()
        
        query = request.args.get('query', '')
        if not query:
            return jsonify({'error': 'Query parameter is required'}), 400

        search_response = youtube.search().list(
            q=query,
            part='snippet',
            type='video',
            maxResults=10
        ).execute()

        videos = []
        for item in search_response.get('items', []):
            video_id = item['id']['videoId']
            video_info = youtube.videos().list(
                id=video_id,
                part='snippet,statistics,liveStreamingDetails'
            ).execute()
            
            # ライブ配信の詳細を取得しようと試みる
            live_details = video_info['items'][0].get('liveStreamingDetails', {})
            actual_start_time = live_details.get('actualStartTime')

            # ライブ配信だった場合のみリストに追加
            if actual_start_time:
                videos.append({
                    'title': item['snippet']['title'],
                    'thumbnail': item['snippet']['thumbnails']['high']['url'],
                    'channelTitle': item['snippet']['channelTitle'],
                    'videoId': video_id,
                    'actualStartTime': actual_start_time
                })

        return jsonify(videos)

    except Exception as e:
        # エラーログをRenderのコンソールに出力
        print(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500

# Gunicornがこの'app'オブジェクトを見つけるため、
# `if __name__ == '__main__':`ブロックは不要です。
