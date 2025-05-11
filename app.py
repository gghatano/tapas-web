import streamlit as st
import sys
from pathlib import Path
import pandas as pd

# TAPASパスの追加
tapas_path = Path(__file__).parent / "tapas"
if str(tapas_path) not in sys.path:
    sys.path.insert(0, str(tapas_path))

st.set_page_config(
    page_title="TAPAS Privacy Evaluation",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🔒 TAPAS Privacy Evaluation Tool")
st.write("""
TAPAS (Toolbox for Adversarial Privacy Auditing of Synthetic Data) は、
合成データのプライバシー保護レベルを評価するためのツールです。
""")

# システム情報を折りたたみセクションに
with st.expander("システム情報", expanded=False):
    st.write(f"Python version: {sys.version}")
    st.write(f"Streamlit version: {st.__version__}")
    
    # TAPASのインポート確認
    try:
        import tapas
        st.success("✅ TAPASが正常にインポートされました！")
        st.write(f"TAPASバージョン: {tapas.__version__}")
        
        # 利用可能なモジュールの確認
        modules = []
        for module in ['datasets', 'generators', 'threat_models', 'attacks', 'report']:
            try:
                __import__(f'tapas.{module}')
                modules.append(module)
            except ImportError:
                pass
        
        if modules:
            st.write("利用可能なTAPASモジュール：")
            st.write(modules)
    except ImportError as e:
        st.warning(f"TAPASのインポートができませんでした: {e}")

# メインコンテンツ
st.header("🚀 はじめに")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 主な機能")
    st.write("""
    - **データセットのアップロード**: CSV形式のデータに対応
    - **プライバシー攻撃のテスト**: 各種攻撃手法でプライバシーリスクを評価
    - **レポート生成**: 評価結果の可視化とレポート出力
    """)

with col2:
    st.subheader("🔍 対応する攻撃手法")
    st.write("""
    - Membership Inference Attack (MIA)
    - Attribute Inference Attack (AIA)
    - Groundhog Attack
    - Closest Distance Attack
    - その他のプライバシー攻撃
    """)

st.divider()

# サンプルデータセクション
st.header("🧪 サンプルデータ実験")

# データセット選択
dataset_option = st.selectbox(
    "サンプルデータセットを選択",
    ["なし", "UCI Adult Dataset", "カスタムデータ生成"]
)

if dataset_option == "UCI Adult Dataset":
    st.subheader("UCI Adult Dataset")
    st.write("""
    UCI Machine Learning RepositoryのAdult datasetを使用した実験が可能です。
    このデータセットは、人口統計データに基づいて年収が50K以上かどうかを予測するためのものです。
    """)
    
    if st.button("Adult Datasetをロード", key="load_adult"):
        try:
            from ucimlrepo import fetch_ucirepo
            
            with st.spinner("データをロード中..."):
                # データセットの取得
                adult = fetch_ucirepo(id=2)
                X = adult.data.features
                y = adult.data.targets
                
                # データの結合
                data = pd.concat([X, y], axis=1)
                
                # データを保存
                DATA_DIR = Path("data/uploaded/adult_dataset")
                DATA_DIR.mkdir(parents=True, exist_ok=True)
                
                csv_path = DATA_DIR / "adult_dataset.csv"
                data.to_csv(csv_path, index=False)
                
                # メタデータの保存
                metadata = {
                    "name": "adult_dataset",
                    "description": "UCI Adult Dataset - Income prediction dataset",
                    "original_filename": "adult_uci.csv",
                    "rows": len(data),
                    "columns": len(data.columns),
                    "column_names": data.columns.tolist(),
                    "dtypes": data.dtypes.astype(str).to_dict(),
                    "upload_date": pd.Timestamp.now().isoformat()
                }
                
                metadata_path = DATA_DIR / "metadata.json"
                import json
                with open(metadata_path, "w") as f:
                    json.dump(metadata, f, indent=2)
                
                st.success("✅ Adult Datasetが正常にロードされました！")
                
                # データの概要表示
                st.write("### データセット概要")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("レコード数", len(data))
                with col2:
                    st.metric("特徴量数", len(X.columns))
                with col3:
                    st.metric("ターゲット変数", y.columns[0])
                
                # データプレビュー
                st.write("### データプレビュー")
                st.dataframe(data.head(10))
                
                # 統計情報
                st.write("### 基本統計量")
                st.dataframe(data.describe())
                
                st.info("データセット管理ページで、このデータセットを確認できます。")
                
        except ImportError:
            st.error("ucimlrepoがインストールされていません。以下のコマンドでインストールしてください：")
            st.code("poetry add ucimlrepo")
        except Exception as e:
            st.error(f"データのロード中にエラーが発生しました: {e}")

elif dataset_option == "カスタムデータ生成":
    st.subheader("カスタムデータ生成")
    st.write("簡単な合成データを生成して実験できます。")
    
    col1, col2 = st.columns(2)
    with col1:
        num_records = st.number_input("レコード数", min_value=100, max_value=10000, value=1000)
        num_features = st.number_input("特徴量数", min_value=2, max_value=20, value=5)
    
    with col2:
        noise_level = st.slider("ノイズレベル", min_value=0.0, max_value=1.0, value=0.1)
        random_seed = st.number_input("ランダムシード", min_value=0, value=42)
    
    if st.button("データ生成", key="generate_custom"):
        import numpy as np
        
        np.random.seed(random_seed)
        
        # データ生成
        X = np.random.randn(num_records, num_features)
        
        # ノイズの追加
        noise = np.random.randn(num_records, num_features) * noise_level
        X += noise
        
        # ターゲット変数の生成（線形結合 + ノイズ）
        weights = np.random.randn(num_features)
        y = X @ weights + np.random.randn(num_records) * noise_level
        y_binary = (y > np.median(y)).astype(int)
        
        # DataFrameに変換
        feature_names = [f"feature_{i+1}" for i in range(num_features)]
        data = pd.DataFrame(X, columns=feature_names)
        data['target'] = y_binary
        
        # データを保存
        DATA_DIR = Path("data/uploaded/custom_dataset")
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        csv_path = DATA_DIR / "custom_dataset.csv"
        data.to_csv(csv_path, index=False)
        
        # メタデータの保存
        metadata = {
            "name": "custom_dataset",
            "description": f"Custom generated dataset with {num_records} records and {num_features} features",
            "original_filename": "custom_generated.csv",
            "rows": len(data),
            "columns": len(data.columns),
            "column_names": data.columns.tolist(),
            "dtypes": data.dtypes.astype(str).to_dict(),
            "upload_date": pd.Timestamp.now().isoformat(),
            "generation_params": {
                "num_records": num_records,
                "num_features": num_features,
                "noise_level": noise_level,
                "random_seed": random_seed
            }
        }
        
        metadata_path = DATA_DIR / "metadata.json"
        import json
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        st.success("✅ カスタムデータセットが生成されました！")
        
        # データプレビュー
        st.write("### データプレビュー")
        st.dataframe(data.head(10))
        
        st.info("データセット管理ページで、このデータセットを確認できます。")

st.divider()

# ナビゲーション
st.header("📁 ページ一覧")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 1. データセット管理
    
    CSVファイルのアップロード、データの確認、
    前処理を行います。
    
    **→ 左側のメニューから選択**
    """)

with col2:
    st.markdown("""
    ### 2. プライバシー評価
    
    各種攻撃手法を選択し、データセットの
    プライバシーリスクを評価します。
    
    **→ 左側のメニューから選択**
    """)

with col3:
    st.markdown("""
    ### 3. レポート
    
    実行した評価の結果を確認し、
    レポートを生成・ダウンロードします。
    
    **→ 左側のメニューから選択**
    """)

# サイドバー
st.sidebar.header("📌 ページ一覧")
st.sidebar.info("""
次のページが利用可能です：

- **📊 データセット管理**: CSVファイルのアップロードと管理
- **🔍 プライバシー評価**: 各種攻撃の実行
- **📄 レポート**: 評価結果の確認とレポート生成

左側のメニューからページを選択してください。
""")

st.sidebar.divider()

st.sidebar.header("ℹ️ About")
st.sidebar.info("""
このツールは、Alan Turing Instituteの
TAPASライブラリをWebアプリケーション化
したものです。
""")
