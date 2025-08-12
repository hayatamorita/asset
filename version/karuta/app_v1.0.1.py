# app.py (UTF-8)
import io
import os
import time
import base64
import random
import streamlit as st
from gtts import gTTS
from streamlit.components.v1 import html

st.set_page_config(page_title="カルタ読み上げ", page_icon="🗣️", layout="centered")

# ===== ちょいCSS（ボタン強調 & スマホで押しやすく） =====
st.markdown("""
<style>
/* 全ボタンを大きめに＆指で押しやすく */
.stButton > button {
  font-size: 1.15rem;
  font-weight: 700;
  padding: 1rem 1.25rem;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.10);
}
/* 次のカードを強め色に */
.next-btn > button {
  background: #2563eb !important;  /* blue-600 */
  color: #fff !important;
}
/* リピートをセカンダリ色に */
.repeat-btn > button {
  background: #f59e0b !important; /* amber-500 */
  color: #111 !important;
}
/* モバイルの横幅でボタンを幅広に */
@media (max-width: 640px){
  .stButton > button { width: 100% !important; }
}
</style>
""", unsafe_allow_html=True)

# ===== ユーティリティ =====
def load_lines(path: str):
    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f.readlines()]
    return [ln for ln in lines if ln]

def ensure_state():
    ss = st.session_state
    ss.setdefault("file_name", "karuta.txt")
    ss.setdefault("lines", [])
    ss.setdefault("order", [])             # 読み上げ順（indexのシャッフル）
    ss.setdefault("pos", 0)                # 現在の順序位置（0ベース）
    ss.setdefault("started", False)        # 1枚目は押されるまで再生しない
    ss.setdefault("audio_bytes", None)     # 直近の音声
    ss.setdefault("audio_token", 0)        # プレイヤー差し替え用トークン
    ss.setdefault("last_play_ts", 0.0)     # 最後に読み上げた時刻
    ss.setdefault("await_next", False)     # 次ボタン待ち中（リピート対象）
    ss.setdefault("lang", "ja")            # gTTS言語
    ss.setdefault("slow", False)           # gTTSスロー
    ss.setdefault("repeat_sec", 1.0)       # リピートまでの待ち秒（要件：1秒）
    ss.setdefault("read_set", set())       # 既読 index
    ss.setdefault("read_history", [])      # 既読テキストの順序リスト

def shuffle_order():
    st.session_state.order = list(range(len(st.session_state.lines)))
    random.shuffle(st.session_state.order)
    st.session_state.pos = 0
    st.session_state.started = False
    st.session_state.read_set = set()
    st.session_state.read_history = []

def current_index() -> int:
    ss = st.session_state
    if not ss.lines:
        return -1
    return ss.order[ss.pos]

def current_text() -> str:
    idx = current_index()
    if idx < 0:
        return ""
    return st.session_state.lines[idx]

def mark_read(idx: int, text: str):
    ss = st.session_state
    if idx not in ss.read_set:
        ss.read_set.add(idx)
        ss.read_history.append(text)

def synth_say(text: str):
    """gTTSで合成して session_state.audio_bytes に保存し、既読登録も行う"""
    tts = gTTS(text=text, lang=st.session_state.lang, slow=st.session_state.slow)
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    st.session_state.audio_bytes = buf.read()
    st.session_state.audio_token += 1
    st.session_state.last_play_ts = time.time()
    st.session_state.await_next = True
    # 既読登録
    idx = current_index()
    if idx >= 0:
        mark_read(idx, text)

def go_next():
    """次の札に進める。全消化したら自動で再シャッフル"""
    ss = st.session_state
    if not ss.lines:
        return
    ss.pos += 1
    if ss.pos >= len(ss.order):
        shuffle_order()

def js_autorefresh(ms: int = 1200):
    """一定時間後にクエリ更新してリロード（リピート用）"""
    html(f"""
    <script>
      setTimeout(function(){{
        const u = new URL(window.location);
        u.searchParams.set('_t', Date.now().toString());
        window.location.href = u.toString();
      }}, {ms});
    </script>
    """, height=0)

def render_audio(mp3_bytes: bytes, token: int):
    """HTML5 audioで自動再生＆前の再生を停止"""
    b64 = base64.b64encode(mp3_bytes).decode("ascii")
    html(f"""
    <audio id="player-{token}" controls autoplay>
      <source src="data:audio/mpeg;base64,{b64}" type="audio/mpeg">
      Your browser does not support the audio element.
    </audio>
    <script>
      // 以前のプレイヤーを停止
      const others = document.querySelectorAll('audio[id^="player-"]');
      others.forEach(a => {{
        if (a.id !== "player-{token}") {{
          try {{ a.pause(); a.currentTime = 0; }} catch(e) {{ }}
        }}
      }});
      // 自動再生（ブラウザによる制限時は黙って失敗）
      const p = document.getElementById("player-{token}");
      if (p) {{
        const pr = p.play();
        if (pr !== undefined) pr.catch(_=>{{}});
      }}
    </script>
    """, height=80)

# ===== 初期化 & 起動時自動読込 =====
ensure_state()
if not st.session_state.lines and os.path.exists(st.session_state.file_name):
    try:
        st.session_state.lines = load_lines(st.session_state.file_name)
        if st.session_state.lines:
            shuffle_order()
    except Exception as e:
        st.error(f"起動時の読み込みに失敗しました: {e}")

# ===== サイドバー =====
st.sidebar.header("設定")
st.session_state.slow = st.sidebar.checkbox("ゆっくり読み上げ（slow）", value=st.session_state.slow)

# ===== 本体UI =====
st.title("🗣️ カルタ読み上げ（ランダム・重複なし）")

# ファイルが無い／空なら案内
if not st.session_state.lines:
    st.info("同じフォルダに `karuta.txt`（UTF-8／1行=1札）を置いてください。アプリは起動時に自動で読み込みます。")
    st.stop()

# 現在の札（テキスト表示）
cur_text = current_text()
st.subheader("現在の札")
st.write(f"**{cur_text if cur_text else '（読み込めませんでした）'}**")

# 進捗（既読枚数 / 合計）
read_count = len(st.session_state.read_set)
total = len(st.session_state.lines)
st.caption(f"進捗: {read_count} / {total}")

# ===== ボタン行：左=リピート、右=次のカード =====
left, right = st.columns([1, 1])

with left:
    st.markdown('<div class="repeat-btn">', unsafe_allow_html=True)
    repeat_clicked = st.button("🔁 リピート", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="next-btn">', unsafe_allow_html=True)
    next_clicked = st.button("⏭ 次のカード", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ===== クリック時の挙動 =====
if repeat_clicked:
    # 同じ札をもう一度読み上げ（位置は進めない）
    if st.session_state.started:
        synth_say(current_text())
    else:
        # まだ開始していない場合は、開始して現在札を再生
        st.session_state.started = True
        synth_say(current_text())

if next_clicked:
    if not st.session_state.started:
        # 初回クリック：現在の札を再生開始（posは進めない）
        st.session_state.started = True
        synth_say(current_text())
    else:
        # 次の札へ進めて再生
        go_next()
        synth_say(current_text())

# ===== 自動リピート（次ボタン未クリックが1秒超なら同じ札を再読） =====
now = time.time()
if st.session_state.started and st.session_state.await_next and st.session_state.audio_bytes:
    elapsed = now - st.session_state.last_play_ts
    if elapsed >= st.session_state.repeat_sec:
        st.session_state.audio_token += 1
        st.session_state.last_play_ts = now
    else:
        ms = int((st.session_state.repeat_sec - elapsed) * 1000) + 100
        js_autorefresh(max(ms, 400))

# ===== 音声の描画（HTML5 audio） =====
if st.session_state.audio_bytes:
    render_audio(st.session_state.audio_bytes, st.session_state.audio_token)

# ===== 既読の一覧（ボタンの下） =====
st.markdown("### すでに読んだ札")
if st.session_state.read_history:
    for t in reversed(st.session_state.read_history):
        st.markdown(f"- {t}")
else:
    st.write("（まだありません）")
