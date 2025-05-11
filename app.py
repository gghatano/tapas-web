import streamlit as st
import sys

st.title("TAPAS Web App - 動作確認")
st.write("Streamlitが正常に動作しています！")

# システム情報を表示
st.header("システム情報")
st.write(f"Python version: {sys.version}")
st.write(f"Streamlit version: {st.__version__}")

# TAPASのインポート確認
st.header("TAPAS インポート確認")
try:
    import tapas
    st.success("✅ TAPASが正常にインポートされました！")
    
    # TAPASのモジュールを確認
    st.write("利用可能なTAPASモジュール：")
    tapas_modules = [item for item in dir(tapas) if not item.startswith('_')]
    st.write(tapas_modules)
    
except ImportError as e:
    st.error(f"❌ TAPASのインポートに失敗: {e}")

# サンプル機能
st.header("サンプル機能")
st.write("簡単なデモ機能を試してみましょう")

user_input = st.text_input("何か入力してください：", "Hello TAPAS!")
if st.button("表示"):
    st.write(f"入力された内容: {user_input}")

# サイドバー
st.sidebar.header("設定")
st.sidebar.write("今後、ここに各種設定を配置できます")
