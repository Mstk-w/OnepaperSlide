# UI-Agent: Streamlit UI開発ガイド

## 担当ファイル

- `app.py` - メインアプリケーション
- `requirements.txt` - 依存パッケージ
- `.gitignore` - セキュリティ設定
- `.streamlit/secrets.toml` - APIキー管理

## 目次

1. [プロジェクトセットアップ](#1-プロジェクトセットアップ)
2. [app.py基本構造](#2-apppy基本構造)
3. [サイドバー実装](#3-サイドバー実装)
4. [メインエリア実装](#4-メインエリア実装)
5. [プログレス表示](#5-プログレス表示)
6. [ダウンロード機能](#6-ダウンロード機能)
7. [エラーハンドリング](#7-エラーハンドリング)

---

## 1. プロジェクトセットアップ

### requirements.txt

```
streamlit>=1.28.0
python-pptx>=0.6.21
google-generativeai>=0.3.0
python-dotenv>=1.0.0
```

### .gitignore

```gitignore
# APIキー・シークレット
.env
.streamlit/secrets.toml

# Python
__pycache__/
*.pyc
.pytest_cache/
venv/
.venv/

# IDE
.vscode/
.idea/

# 生成ファイル
*.pptx
output/
```

### .streamlit/secrets.toml（テンプレート）

```toml
# 本番環境用 - このファイルはgitignore対象
GEMINI_API_KEY = "your-api-key-here"
```

---

## 2. app.py基本構造

```python
import streamlit as st
from pathlib import Path
import sys

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_service import generate_structured_content
from layout_engine import process_layout
from pptx_builder import build_pptx

# ページ設定（最初に呼び出す）
st.set_page_config(
    page_title="OnePaperSlide - A3資料自動生成",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("OnePaperSlide - A3資料自動生成")
    st.markdown("公務員向け業務改善提案・施策説明資料を自動生成します")

    # サイドバー
    with st.sidebar:
        render_sidebar()

    # メインエリア
    render_main_area()

if __name__ == "__main__":
    main()
```

---

## 3. サイドバー実装

```python
def render_sidebar():
    """サイドバーの描画"""
    st.header("設定")

    # AIモデル選択
    model = st.selectbox(
        "AIモデル",
        options=["gemini-2.0-flash", "gemini-2.0-pro"],
        index=0,
        help="Flashは高速、Proは高精度"
    )
    st.session_state["model"] = model

    # テンプレート選択
    template_mode = st.radio(
        "テンプレート選択",
        options=["自動選択", "手動選択"],
        index=0
    )

    if template_mode == "手動選択":
        template = st.selectbox(
            "テンプレート種別",
            options=[
                ("T1", "問題解決型 - 課題解決の提案"),
                ("T2", "比較検討型 - 選択肢の比較"),
                ("T3", "施策提案型 - 新規施策の説明"),
                ("T4", "業務フロー型 - プロセス改善")
            ],
            format_func=lambda x: x[1]
        )
        st.session_state["template_id"] = template[0]
    else:
        st.session_state["template_id"] = None  # AI自動選択

    # APIキー状態表示
    st.divider()
    if get_api_key():
        st.success("APIキー: 設定済み")
    else:
        st.error("APIキー: 未設定")
        st.info("`.streamlit/secrets.toml`にGEMINI_API_KEYを設定してください")
```

---

## 4. メインエリア実装

```python
def render_main_area():
    """メインエリアの描画"""

    # 入力テキストエリア
    memo_text = st.text_area(
        "原稿入力",
        height=300,
        placeholder="""ここに提案内容のメモを貼り付けてください。

例:
・現状: 紙ベースの申請処理で時間がかかっている
・課題: 1件あたり平均30分の処理時間
・原因: 手作業による転記ミス、承認フローの非効率
・解決策: オンライン申請システムの導入
・期待効果: 処理時間50%削減、ミス率80%減少""",
        help="現状・課題・解決策などを自由形式で入力"
    )

    # 文字数カウント表示
    char_count = len(memo_text)
    if char_count > 10000:
        st.warning(f"文字数: {char_count}/10,000（超過分は切り捨てられます）")
    else:
        st.caption(f"文字数: {char_count}/10,000")

    # 生成ボタン
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        generate_button = st.button(
            "A3資料を生成する",
            type="primary",
            use_container_width=True,
            disabled=not memo_text.strip()
        )

    # 生成処理
    if generate_button:
        if not get_api_key():
            st.error("APIキーが設定されていません")
            return

        process_generation(memo_text[:10000])  # 10000文字制限
```

---

## 5. プログレス表示

```python
def process_generation(memo_text: str):
    """資料生成処理（プログレス表示付き）"""

    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # Step 1: AI構造化
        status_text.text("📝 テキストを構造化中...")
        progress_bar.progress(20)

        structured_data = generate_structured_content(
            memo_text,
            model=st.session_state.get("model", "gemini-2.0-flash"),
            template_id=st.session_state.get("template_id")
        )

        # Step 2: レイアウト処理
        status_text.text("📐 レイアウトを計算中...")
        progress_bar.progress(50)

        layout_data = process_layout(structured_data)

        # Step 3: PPTX生成
        status_text.text("📊 PowerPointを生成中...")
        progress_bar.progress(80)

        pptx_bytes = build_pptx(layout_data)

        # 完了
        progress_bar.progress(100)
        status_text.text("✅ 生成完了！")

        # ダウンロードボタン表示
        render_download_section(pptx_bytes, structured_data.get("title", "資料"))

    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        handle_error(e)
```

---

## 6. ダウンロード機能

```python
def render_download_section(pptx_bytes: bytes, title: str):
    """ダウンロードセクションの表示"""

    st.success("資料が生成されました！")

    # ファイル名生成（日本語対応）
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c for c in title if c.isalnum() or c in "_ ").strip()[:30]
    filename = f"{safe_title}_{timestamp}.pptx"

    # ダウンロードボタン
    st.download_button(
        label="📥 ダウンロード（.pptx）",
        data=pptx_bytes,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        type="primary"
    )

    # ファイルサイズ表示
    size_kb = len(pptx_bytes) / 1024
    st.caption(f"ファイルサイズ: {size_kb:.1f} KB")
```

---

## 7. エラーハンドリング

```python
def get_api_key() -> str | None:
    """APIキーの取得（secrets優先、環境変数フォールバック）"""
    import os

    # Streamlit Secrets
    try:
        return st.secrets.get("GEMINI_API_KEY")
    except:
        pass

    # 環境変数
    return os.environ.get("GEMINI_API_KEY")

def handle_error(error: Exception):
    """エラーハンドリング（日本語メッセージ）"""

    error_msg = str(error)

    # APIキー関連
    if "API_KEY" in error_msg or "authentication" in error_msg.lower():
        st.error("❌ APIキーエラー")
        st.info("APIキーが無効または期限切れです。設定を確認してください。")
        return

    # クォータ超過
    if "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
        st.error("❌ API利用制限")
        st.info("APIの利用制限に達しました。しばらく待ってから再試行してください。")
        return

    # JSON解析エラー
    if "json" in error_msg.lower() or "parse" in error_msg.lower():
        st.error("❌ AI応答の解析に失敗しました")
        st.info("入力内容を変更して再試行してください。")
        return

    # その他のエラー
    st.error("❌ エラーが発生しました")
    st.exception(error)  # 開発時のみ詳細表示
```

---

## ベストプラクティス

### セッション状態の活用

```python
# 初期化
if "generation_count" not in st.session_state:
    st.session_state["generation_count"] = 0

# 更新
st.session_state["generation_count"] += 1
```

### キャッシュの活用

```python
@st.cache_data(ttl=3600)  # 1時間キャッシュ
def load_template(template_id: str) -> dict:
    """テンプレートJSONの読み込み（キャッシュ付き）"""
    import json
    path = Path(__file__).parent / "templates" / f"{template_id}.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)
```

### レスポンシブ対応

```python
# カラムレイアウトで画面幅に応じた配置
col1, col2 = st.columns([2, 1])

with col1:
    st.text_area("入力", height=400)

with col2:
    st.info("ヒント: 箇条書きで整理すると精度が上がります")
```
