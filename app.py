"""
OnePaperSlide - A3資料自動生成アプリケーション
公務員向け業務改善提案・施策説明資料を自動生成
"""

import streamlit as st
from pathlib import Path
import sys
import os
from datetime import datetime
from io import BytesIO
import time
from streamlit_modal import Modal

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_service import generate_structured_content, AIServiceError, get_available_models, get_provider_type
from layout_engine import process_layout
from pptx_builder import build_pptx
from logging_config import setup_logging, get_logger
from config import config


# ロガーの設定
setup_logging(level="INFO")
logger = get_logger("app")

# ページ設定（最初に呼び出す）
st.set_page_config(
    page_title="OnePaperSlide - A3資料自動生成",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Loading
def load_css():
    css_file = Path(__file__).parent / "assets" / "custom.css"
    if css_file.exists():
        with open(css_file, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()


def check_rate_limit(limit_count: int = 5, time_window: int = 60) -> bool:
    """
    レート制限チェック
    
    Args:
        limit_count: 時間枠内の最大リクエスト数
        time_window: 制限判定の時間枠（秒）
    
    Returns:
        bool: 制限超過ならTrue、そうでなければFalse
    """
    if "request_timestamps" not in st.session_state:
        st.session_state["request_timestamps"] = []
    
    now = time.time()
    # 期限切れのタイムスタンプを削除
    timestamps = [t for t in st.session_state["request_timestamps"] if now - t < time_window]
    
    if len(timestamps) >= limit_count:
        return True
    
    # 新しいタイムスタンプを追加
    timestamps.append(now)
    st.session_state["request_timestamps"] = timestamps
    return False


def get_api_key() -> str | None:
    """
    APIキーの取得（UI入力優先、secrets、環境変数フォールバック）
    """
    # 1. UI入力 (Session State)
    if st.session_state.get("user_api_key"):
        return st.session_state["user_api_key"]

    # 2. Streamlit Secrets
    try:
        key = st.secrets.get("GEMINI_API_KEY")
        if key:
            return key
    except (KeyError, FileNotFoundError):
        pass
    except Exception as e:
        logger.warning(f"Streamlit secrets読み込みエラー: {e}")

    # 3. 環境変数
    return os.environ.get("GEMINI_API_KEY")


def render_sidebar():
    """サイドバーの描画"""
    st.header("⚙️ 設定")

    with st.container():
        st.markdown("### 🔑 APIキー")
        # APIキー入力
        api_key_input = st.text_input(
            "APIキー",
            type="password",
            placeholder="Gemini / OpenAI / Anthropic...",
            label_visibility="collapsed",
            help="各社のAPIキーを自動認識します（Gemini: AIza..., OpenAI: sk-..., Anthropic: sk-ant-...）",
            key="user_api_key_input"  # 一時的なキー
        )
        
        # 入力値をsession_stateのメインキーに保存
        if api_key_input:
            st.session_state["user_api_key"] = api_key_input

        # APIキー状態確認
        current_key = get_api_key()
        available_models = []
        
        if current_key:
            provider_type = get_provider_type(current_key)
            provider_label = {
                "gemini": "Google Gemini",
                "openai": "OpenAI",
                "anthropic": "Anthropic Claude"
            }.get(provider_type, provider_type)

            # 動的にモデルリストを取得
            with st.spinner(f"{provider_label} のモデル一覧を取得中..."):
                available_models = get_available_models(current_key)
                
            if available_models:
                st.success(f"✅ {provider_label}: 接続済み")
                is_disabled = False
            else:
                st.warning("⚠️ モデルが見つかりません")
                # 取得失敗時はデフォルトモデル表示（プロバイダーに合わせて）
                if provider_type == "openai":
                    available_models = ["gpt-4o", "gpt-4-turbo"]
                elif provider_type == "anthropic":
                    available_models = ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229"]
                elif provider_type == "gemini":
                    available_models = ["gemini-2.0-flash", "gemini-1.5-pro"]
                is_disabled = False # フォールバックとして選択可能にする
        else:
            st.error("⚠️ APIキーが必要です")
            is_disabled = True
            
    st.markdown("---")

    with st.container():
        st.markdown("### 🤖 AIモデル")
        # AIモデル選択
        default_options = ["gemini-2.0-flash", "gemini-2.0-pro"]
        options = available_models if available_models else default_options
        
        current_selection = st.session_state.get("model", options[0])
        try:
            index = options.index(current_selection)
        except ValueError:
            index = 0

        model = st.selectbox(
            "AIモデル",
            options=options,
            index=index,
            label_visibility="collapsed",
            disabled=is_disabled
        )
        st.session_state["model"] = model

    st.markdown("---")

    with st.container():
        st.markdown("### 📄 テンプレート")
        template_mode = st.radio(
            "選択モード",
            options=["自動選択", "手動選択"],
            index=0,
            horizontal=True,
            disabled=is_disabled,
            label_visibility="collapsed"
        )

        if template_mode == "手動選択":
            template_options = [
                ("T1", "問題解決型 - 課題解決の提案"),
                ("T2", "比較検討型 - 選択肢の比較"),
                ("T3", "施策提案型 - 新規施策の説明"),
                ("T4", "業務フロー型 - プロセス改善")
            ]
            template = st.selectbox(
                "テンプレート種別",
                options=template_options,
                format_func=lambda x: x[1],
                disabled=is_disabled,
                label_visibility="collapsed"
            )
            st.session_state["template_id"] = template[0]
        else:
            st.session_state["template_id"] = None
            st.caption("AIが内容に応じて最適なレイアウトを自動選択します。")

    # デザイン設定（UX改善）
    st.markdown("---")
    with st.expander("🎨 デザイン設定"):
        current_colors = config.colors
        
        primary_color = st.color_picker("アクセントカラー", value=current_colors.primary)
        bg_color = st.color_picker("背景色", value=current_colors.background)
        
        # 設定を適用
        config.override_colors(primary=primary_color, background=bg_color)
    
    st.markdown("---")
    
    # 使い方ボタン（モーダルトリガー）
    if st.button("📖 使い方ガイドを開く", use_container_width=True):
        st.session_state["show_guide_modal"] = True


def render_download_section(pptx_data: BytesIO | bytes, title: str):
    """ダウンロードセクションの表示"""
    st.balloons()
    st.success("✨ 資料が生成されました！")

    # BytesIOの場合はバイト列を取得
    if isinstance(pptx_data, BytesIO):
        pptx_bytes = pptx_data.getvalue()
        download_data = pptx_data
    else:
        pptx_bytes = pptx_data
        download_data = pptx_bytes

    # ファイル名生成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c for c in title if c.isalnum() or c in "_ ").strip()[:30]
    if not safe_title:
        safe_title = "OnePaperSlide"
    filename = f"{safe_title}_{timestamp}.pptx"

    # ダウンロードボタン
    st.download_button(
        label="📥 ダウンロード (.pptx)",
        data=download_data,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        type="primary",
        use_container_width=True
    )

    # ファイルサイズ表示
    size_kb = len(pptx_bytes) / 1024
    st.caption(f"💾 ファイルサイズ: {size_kb:.1f} KB")


def handle_error(error: Exception):
    """エラーハンドリング（日本語メッセージ）"""
    error_msg = str(error)

    # APIキー関連
    if "API_KEY" in error_msg or "authentication" in error_msg.lower():
        st.error("APIキーエラー")
        st.info("APIキーが無効または期限切れです。設定を確認してください。")
        return

    # クォータ超過
    if "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
        st.error("API利用制限")
        st.info("APIの利用制限に達しました。しばらく待ってから再試行してください。")
        return

    # JSON解析エラー
    if "json" in error_msg.lower() or "parse" in error_msg.lower():
        st.error("AI応答の解析に失敗しました")
        st.info("入力内容を変更して再試行してください。")
        return

    # その他のエラー
    st.error("エラーが発生しました")
    st.exception(error)


def process_generation(memo_text: str):
    """資料生成処理（プログレス表示付き）"""
    
    # レート制限チェック
    if check_rate_limit(limit_count=5, time_window=60):
        st.error("リクエスト制限超過")
        st.warning("短時間にリクエストが集中しています。しばらく（1分程度）待ってから再試行してください。")
        return

    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # Step 1: AI構造化
        status_text.markdown("### 🧠 テキストを分析・構造化しています...")
        progress_bar.progress(20)

        api_key = get_api_key()
        structured_data = generate_structured_content(
            memo_text,
            model=st.session_state.get("model", "gemini-2.0-flash"),
            template_id=st.session_state.get("template_id"),
            api_key=api_key
        )

        # Step 2: レイアウト処理
        status_text.markdown("### 📐 最適なレイアウトを計算しています...")
        progress_bar.progress(50)

        layout_data = process_layout(structured_data)
        
        # 簡易プレビュー表示（UX改善）
        st.markdown('<div class="preview-card">', unsafe_allow_html=True)
        st.markdown(f"### {structured_data.get('title')}")
        st.markdown(f"**Template**: {structured_data.get('recommended_template')}")
        st.markdown("---")
        
        cols = st.columns(2)
        sections = structured_data.get("sections", [])
        for i, section in enumerate(sections):
            col_idx = section.get("column", 0)
            if col_idx < 0 or col_idx >= len(cols):
                col_idx = 0
            with cols[col_idx]:
                st.info(f"{section.get('header')} ({section.get('type')})")
        st.markdown('</div>', unsafe_allow_html=True)

        # Step 3: PPTX生成
        status_text.markdown("### 💾 PowerPointファイルを生成しています...")
        progress_bar.progress(80)

        pptx_stream = build_pptx(layout_data)

        # 完了
        progress_bar.progress(100)
        status_text.empty() # テキストを消す

        # ダウンロードボタン表示
        render_download_section(pptx_stream, structured_data.get("title", "資料"))

    except AIServiceError as e:
        progress_bar.empty()
        status_text.empty()
        handle_error(e)
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        handle_error(e)


def render_guide_modal():
    """使い方ガイドモーダルの表示"""
    # 閉じるボタンの処理（モーダル表示前にチェック）
    if st.session_state.get("close_modal_clicked", False):
        st.session_state["show_guide_modal"] = False
        st.session_state["close_modal_clicked"] = False
        st.rerun()

    modal = Modal(title="OnePaperSlide ユーザーガイド", key="guide_modal", max_width=700)
    
    # セッション状態でモーダル表示制御
    if st.session_state.get("show_guide_modal", False):
        with modal.container():
            # スクロール可能なコンテナでラップ
            with st.container():
                st.markdown("""
                ### 🚀 3ステップで資料作成
                
                <div class="usage-step">
                    <h4><b>Step 1: メモを入力</b></h4>
                    <p>提案内容、課題、解決策などを箇条書きや文章で自由に貼り付けてください。</p>
                </div>
                
                <div class="usage-step">
                    <h4><b>Step 2: 設定を確認</b></h4>
                    <p>サイドバーでAIモデルを選択します。テンプレートは「自動選択」がおすすめです。</p>
                </div>
                
                <div class="usage-step">
                    <h4><b>Step 3: 生成 & ダウンロード</b></h4>
                    <p>「OnePaperSlideを作成する」ボタンをクリックし、完成したPPTXを保存します。</p>
                </div>
                
                <hr>
                
                ### 💡 Tips
                - **情報量**: 箇条書きだけでなく、詳細な数値や背景を含めると精度が上がります。
                - **プレビュー**: 生成前に右側のプレビューで構成を確認できます。
                - **エラー**: 生成に失敗する場合は、モデルを変更するか時間を置いて再試行してください。
                """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # 閉じるボタン（コールバックを使用）
                st.button("閉じる", key="close_modal_btn", type="primary", use_container_width=True, on_click=lambda: st.session_state.update({"close_modal_clicked": True}))


def render_main_area():
    """メインエリアの描画"""
    st.markdown("# OnePaperSlide <span style='font-size: 1.2rem; color: #718096; font-weight:normal'>AI A3資料生成</span>", unsafe_allow_html=True)
    st.markdown("公務員向け業務改善提案・施策説明資料を、AIが最適なレイアウトで自動生成します。")

    # 入力内容の保持（Session State）
    if "memo_text" not in st.session_state:
        st.session_state["memo_text"] = ""
        
    # 入力テキストエリア
    memo_text = st.text_area(
        "原稿入力",
        height=300,
        placeholder="ここに提案内容のメモを貼り付けてください...\n\n例:\n・現状: 紙ベースの申請処理で時間がかかっている\n・課題: 1件あたり平均30分の処理時間\n・解決策: オンライン申請システムの導入",
        help="現状・課題・解決策などを自由形式で入力（最大10,000文字）",
        key="memo_text"
    )

    # 文字数カウント表示 & 生成ボタン配置
    col1, col2 = st.columns([3, 1])
    with col1:
        char_count = len(memo_text)
        if char_count > 10000:
            st.warning(f"⚠️ 文字数: {char_count}/10,000（超過分は切り捨てられます）")
        else:
            st.caption(f"📝 文字数: {char_count}/10,000")
            
    with col2:
        generate_button = st.button(
            "⚡ OnePaperSlideを作成",
            type="primary",
            use_container_width=True,
            disabled=not memo_text.strip()
        )

    # 生成処理
    if generate_button:
        if not get_api_key():
            st.error("🚫 APIキーが設定されていません")
            st.info("サイドバーでAPIキーを入力するか、`.streamlit/secrets.toml`を確認してください。")
            return

        process_generation(memo_text[:10000])


def main():
    """メインアプリケーション"""
    # モーダルレンダリング
    render_guide_modal()
    
    # サイドバー
    with st.sidebar:
        render_sidebar()

    # メインエリア
    render_main_area()


if __name__ == "__main__":
    main()
