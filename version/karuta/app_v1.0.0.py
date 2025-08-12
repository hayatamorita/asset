# app.py  (UTF-8)
import io
import streamlit as st
from gtts import gTTS

st.set_page_config(page_title="テキスト読み上げ", page_icon="🗣️", layout="centered")

# --- サイドバー（パラメータは全部ここ） ---
st.sidebar.header("設定")
lang_label = st.sidebar.selectbox("言語", ["日本語", "英語", "中国語（簡体）", "韓国語"])
lang_map = {
    "日本語": "ja",
    "英語": "en",
    "中国語（簡体）": "zh-CN",
    "韓国語": "ko",
}
lang = lang_map[lang_label]

slow = st.sidebar.checkbox("ゆっくり読み上げ（slow）", value=False)
filename = st.sidebar.text_input("ファイル名（拡張子不要）", value="tts_output")
auto_play = st.sidebar.checkbox("生成後に自動再生", value=True)

st.title("🗣️ テキスト読み上げ（Streamlit + gTTS）")
st.caption("テキストをMP3に変換して再生＆ダウンロードできます。")

text = st.text_area("読み上げるテキストを入力", height=200, placeholder="ここにテキストを貼り付け…")

col1, col2 = st.columns([1,1])
with col1:
    gen = st.button("🎧 読み上げ音声を作成", use_container_width=True)
with col2:
    st.download_button(
        "📥（生成後に表示）", data=b"", file_name="",
        disabled=True, use_container_width=True
    )

# --- 生成処理 ---
if gen:
    if not text.strip():
        st.warning("テキストを入力してください。")
        st.stop()
    try:
        tts = gTTS(text=text, lang=lang, slow=slow)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        mp3_bytes = buf.read()

        st.success("音声を生成しました。")
        if auto_play:
            st.audio(mp3_bytes, format="audio/mp3")

        st.download_button(
            "📥 MP3をダウンロード",
            data=mp3_bytes,
            file_name=f"{filename or 'tts_output'}.mp3",
            mime="audio/mpeg",
        )

    except Exception as e:
        st.error(f"音声生成でエラーが発生しました：{e}")
        st.info("長文で失敗する場合は、段落ごとなどに分けて実行してみてください。")
