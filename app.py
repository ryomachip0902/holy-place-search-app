from flask import Flask, render_template, request, jsonify
import os
from googleapiclient.discovery import build
import traceback

app = Flask(__name__)

# 環境変数からAPIキーを取得
API_KEY = os.environ.get('YOUTUBE_API_KEY')

def get_youtube_service():
    """YouTube Data APIのサービスオブジェクトを構築して返す"""
    # APIキーが設定されていない場合はエラーを発生させる
    if not API_KEY:
        raise ValueError("YOUTUBE_API_KEY environment variable not set.")
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

        # 1. 最初のAPI呼び出し: 動画を検索してIDのリストを取得
        search_response = youtube.search().list(
            q=query,
            part='snippet',
            type='video',
            maxResults=25  # 少し多めに取得してライブ配信が見つかる確率を上げる
        ).execute()

        search_items = search_response.get('items', [])
        if not search_items:
            return jsonify([])  # 結果がなければ空のリストを返す

        # 後で使うために、動画IDとスニペット（タイトルなど）を保持
        video_snippets = {item['id']['videoId']: item.get('snippet', {}) for item in search_items}
        video_ids = list(video_snippets.keys())

        # 2. ２回目のAPI呼び出し: 見つかった全動画の詳細を一度に取得
        video_details_response = youtube.videos().list(
            id=','.join(video_ids),
            part='liveStreamingDetails'  # ライブ配信情報だけ取得すればOK
        ).execute()

        # 処理とフィルタリング
        videos = []
        for item in video_details_response.get('items', []):
            video_id = item.get('id')
            details = item.get('liveStreamingDetails')
            
            # ライブ配信の詳細があり、実際に開始された動画のみを対象
            if details and details.get('actualStartTime'):
                snippet = video_snippets.get(video_id, {})
                thumbnails = snippet.get('thumbnails', {})
                # 'high'がなくてもエラーにならないように、中解像度も試す
                thumbnail_url = thumbnails.get('high', {}).get('url') or thumbnails.get('medium', {}).get('url')

                videos.append({
                    'title': snippet.get('title', 'No Title'),
                    'thumbnail': thumbnail_url,
                    'channelTitle': snippet.get('channelTitle', 'No Channel'),
                    'videoId': video_id,
                    'actualStartTime': details.get('actualStartTime')
                })
        
        # ライブ配信の開始時間が新しい順に並び替え
        videos.sort(key=lambda v: v['actualStartTime'], reverse=True)

        return jsonify(videos)

    except Exception as e:
        # Renderのログに詳細なエラーを出力
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500