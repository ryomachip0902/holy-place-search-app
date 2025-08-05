from flask import Flask, render_template, request, jsonify
import os
from googleapiclient.discovery import build
import traceback

app = Flask(__name__)

# 環境変数からAPIキーを取得
API_KEY = os.environ.get('YOUTUBE_API_KEY')

# スプレッドシートID
SPREADSHEET_ID = '13_ULI6vv8fcM5JKlObL3Su58pDAu7iJu4r7CILhxIWk'

def get_sheets_service():
    """Google Sheets APIのサービスオブジェクトを構築して返す"""
    if not API_KEY:
        raise ValueError("API_KEY environment variable not set.")
    return build('sheets', 'v4', developerKey=API_KEY)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    try:
        sheets_service = get_sheets_service()
        
        # スプレッドシートからデータを読み込む
        range_name = '聖地リスト!A:Z' 
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name
        ).execute()
        
        values = result.get('values', [])

        if not values:
            return jsonify({'error': 'No data found in spreadsheet.'}), 404

        # ヘッダー行を抽出（最初の行がヘッダーと仮定）
        headers = values[0]
        data_rows = values[1:]

        # データを辞書のリストに変換
        all_locations = []
        for row in data_rows:
            location = {}
            for i, header in enumerate(headers):
                if i < len(row):
                    location[header] = row[i]
                else:
                    location[header] = "" # データがない場合は空文字列
            all_locations.append(location)

        # クエリパラメータの取得
        prefecture_query = request.args.get('prefecture', '').lower()
        title_query = request.args.get('title', '').lower()

        filtered_locations = []

        if prefecture_query:
            # 都道府県でフィルタリング
            for loc in all_locations:
                if loc.get('prefecture', '').lower() == prefecture_query:
                    filtered_locations.append(loc)
        elif title_query:
            # 作品名でフィルタリング
            for loc in all_locations:
                if loc.get('title', '').lower() == title_query:
                    filtered_locations.append(loc)
        else:
            # クエリがない場合は全データを返す
            filtered_locations = all_locations

        return jsonify(filtered_locations)

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500