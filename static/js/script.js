/* static/js/script.js */
// APIベースURL
const API_BASE = '/api';

// DOM要素
let prefectureInput, titleInput, loadingSection, resultSection, errorSection, seichiGrid, statsSection, titleList;
let tabPrefecture, tabTitle, searchByPrefecture, searchByTitle;

// 現在の検索タイプ
let currentSearchType = 'prefecture';

// 初期化
document.addEventListener('DOMContentLoaded', function() {
    // DOM要素の取得
    prefectureInput = document.getElementById('prefectureInput');
    titleInput = document.getElementById('titleInput');
    loadingSection = document.getElementById('loadingSection');
    resultSection = document.getElementById('resultSection');
    errorSection = document.getElementById('errorSection');
    seichiGrid = document.getElementById('seichiGrid');
    statsSection = document.getElementById('statsSection');
    titleList = document.getElementById('titleList');
    tabPrefecture = document.getElementById('tabPrefecture');
    tabTitle = document.getElementById('tabTitle');
    searchByPrefecture = document.getElementById('searchByPrefecture');
    searchByTitle = document.getElementById('searchByTitle');

    // Enterキーでの検索対応
    prefectureInput?.addEventListener('keypress', handleKeyPress);
    titleInput?.addEventListener('keypress', handleKeyPress);

    // タイトルリストを読み込む
    loadTitles();
});

// タイトルリストをサーバーから読み込んでdatalistに設定
async function loadTitles() {
    try {
        const response = await fetch(`${API_BASE}/get_titles`);
        const data = await response.json();
        if (!data.error && titleList) {
            titleList.innerHTML = data.titles.map(title => `<option value="${title}">`).join('');
        }
    } catch (error) {
        console.error('タイトルリストの読み込みエラー:', error);
    }
}

function handleKeyPress(e) {
    if (e.key === 'Enter') {
        searchSeichi();
    }
}

// 検索タブ切り替え
function switchTab(tabName) {
    currentSearchType = tabName;
    
    // タブのアクティブ状態を更新
    tabPrefecture.classList.toggle('active', tabName === 'prefecture');
    tabTitle.classList.toggle('active', tabName === 'title');
    
    // フォームの表示状態を更新
    searchByPrefecture.classList.toggle('active', tabName === 'prefecture');
    searchByTitle.classList.toggle('active', tabName === 'title');
    
    // 結果をクリア
    hideResults();
    hideError();
}

// 聖地検索メイン関数
async function searchSeichi() {
    let query = '';
    let value = '';

    if (currentSearchType === 'prefecture') {
        value = prefectureInput?.value?.trim();
        if (!value) {
            showError('都道府県名を入力してください');
            return;
        }
        query = `prefecture=${encodeURIComponent(value)}`;
    } else {
        value = titleInput?.value?.trim();
        if (!value) {
            showError('作品名を入力してください');
            return;
        }
        query = `title=${encodeURIComponent(value)}`;
    }

    showLoading();
    hideError();
    hideResults();

    try {
        const response = await fetch(`${API_BASE}/search_seichi?${query}`);
        const data = await response.json();

        hideLoading();

        if (data.error) {
            showError(data.message);
            return;
        }

        displayResults(data);

    } catch (error) {
        hideLoading();
        console.error('検索エラー:', error);
        showError('通信エラーが発生しました。しばらくしてから再度お試しください。');
    }
}

// 都道府県タグクリック時の検索
function searchPrefecture(prefectureName) {
    if (prefectureInput) {
        prefectureInput.value = prefectureName;
    }
    switchTab('prefecture');
    searchSeichi();
}

// タイトルタグクリック時の検索
function searchTitle(titleName) {
    if (titleInput) {
        titleInput.value = titleName;
    }
    switchTab('title');
    searchSeichi();
}

// 結果表示
function displayResults(data) {
    // 統計情報の表示
    if (statsSection) {
        const animeCount = data.seichi_list.filter(s => s.category.includes('アニメ')).length;
        const movieCount = data.seichi_list.filter(s => s.category.includes('映画')).length;
        const dramaCount = data.seichi_list.filter(s => s.category.includes('ドラマ')).length;

        statsSection.innerHTML = `
            <div class="stat-item">
                <div class="stat-number">${data.total_count || data.seichi_list.length}</div>
                <div>発見された聖地</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">${animeCount}</div>
                <div>アニメ作品</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">${movieCount + dramaCount}</div>
                <div>映画・ドラマ</div>
            </div>
        `;
    }

    // 聖地カードの表示
    if (seichiGrid) {
        seichiGrid.innerHTML = data.seichi_list.map(seichi => createSeichiCard(seichi)).join('');
    }

    showResults();
}

// 聖地カード作成
function createSeichiCard(seichi) {
    const categoryClass = getCategoryClass(seichi.category);
    const emoji = getCategoryEmoji(seichi.category);
    
    const famousSceneHtml = seichi.famous_scene ? 
        `<div class="famous-scene">💡 ${seichi.famous_scene}</div>` : '';

    return `
        <div class="seichi-card">
            <h3>
                <span class="emoji">${emoji}</span>
                ${seichi.title}
                <span class="category-tag ${categoryClass}">${seichi.category}</span>
            </h3>
            <div class="location-name">${seichi.location}</div>
            <div class="description">${seichi.description}</div>
            <div class="access-info">🚃 ${seichi.access}</div>
            ${famousSceneHtml}
        </div>
    `;
}

// カテゴリークラス取得
function getCategoryClass(category) {
    if (category.includes('アニメ映画')) return 'anime-movie-tag';
    if (category.includes('アニメ')) return 'anime-tag';
    if (category.includes('映画')) return 'movie-tag';
    if (category.includes('ドラマ')) return 'drama-tag';
    return 'anime-tag';
}

// カテゴリー絵文字取得
function getCategoryEmoji(category) {
    if (category.includes('アニメ映画')) return '🎬';
    if (category.includes('アニメ')) return '📺';
    if (category.includes('映画')) return '🎬';
    if (category.includes('ドラマ')) return '📺';
    return '🌟';
}

// UI状態管理
function showLoading() {
    if (loadingSection) loadingSection.style.display = 'block';
}

function hideLoading() {
    if (loadingSection) loadingSection.style.display = 'none';
}

function showResults() {
    if (resultSection) resultSection.style.display = 'block';
}

function hideResults() {
    if (resultSection) resultSection.style.display = 'none';
}

function showError(message) {
    if (errorSection) {
        document.getElementById('errorText').textContent = message;
        errorSection.style.display = 'block';
    }
}

function hideError() {
    if (errorSection) errorSection.style.display = 'none';
}
