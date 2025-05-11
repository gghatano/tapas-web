import streamlit as st
import pandas as pd
import numpy as np
import sys
from pathlib import Path
import json

# TAPASパスの追加
tapas_path = Path(__file__).parent / "tapas"
if str(tapas_path) not in sys.path:
    sys.path.insert(0, str(tapas_path))

st.title("合成データ生成ツール")

st.write("""
オリジナルデータから合成データを生成します。
TAPASでプライバシー評価を行うためには、オリジナルデータと合成データの両方が必要です。
""")

# 合成データ生成手法の説明
with st.expander("合成データ生成手法について", expanded=True):
    st.write("""
    ### 利用可能な生成手法
    
    1. **Raw (コピー)**: オリジナルデータをそのままコピー（プライバシー保護なし）
    2. **ノイズ付加**: 各値にランダムノイズを追加
    3. **データ置換**: カテゴリカル値をランダムに置換
    4. **k-匿名化**: k-匿名性を満たすようにデータを一般化
    5. **差分プライバシー**: ε-差分プライバシーを適用
    
    ### 注意事項
    - Raw以外の手法は簡易実装です
    - 実際の使用では、より高度な合成データ生成ライブラリの使用を推奨
    """)

# データセット選択
DATA_DIR = Path("data/uploaded")
datasets = []
if DATA_DIR.exists():
    for dataset_dir in DATA_DIR.iterdir():
        if dataset_dir.is_dir():
            metadata_path = dataset_dir / "metadata.json"
            if metadata_path.exists():
                with open(metadata_path) as f:
                    metadata = json.load(f)
                    datasets.append(metadata)

if not datasets:
    st.warning("利用可能なデータセットがありません。")
    st.stop()

st.header("1. オリジナルデータの選択")
dataset_names = [d["name"] for d in datasets]
selected_dataset = st.selectbox("オリジナルデータセット", dataset_names)

# データの読み込み
dataset_dir = DATA_DIR / selected_dataset
csv_path = dataset_dir / f"{selected_dataset}.csv"
df = pd.read_csv(csv_path)

st.write(f"データセットサイズ: {len(df)} レコード、{len(df.columns)} 列")
st.dataframe(df.head())

# 生成手法の選択
st.header("2. 生成手法の選択")
generation_method = st.selectbox(
    "合成データ生成手法",
    ["Raw (コピー)", "ノイズ付加", "データ置換", "k-匿名化（簡易版）", "差分プライバシー（簡易版）"]
)

# パラメータ設定
st.header("3. パラメータ設定")

if generation_method == "ノイズ付加":
    noise_level = st.slider("ノイズレベル", 0.01, 1.0, 0.1)
    noise_type = st.selectbox("ノイズタイプ", ["ガウシアン", "ラプラス", "一様分布"])
    
elif generation_method == "データ置換":
    replacement_rate = st.slider("置換率", 0.01, 0.5, 0.1)
    
elif generation_method == "k-匿名化（簡易版）":
    k_value = st.slider("k値", 2, 10, 5)
    quasi_identifiers = st.multiselect(
        "準識別子（一般化する列）",
        df.columns.tolist(),
        help="年齢、郵便番号など、組み合わせで個人を特定可能な属性"
    )
    
elif generation_method == "差分プライバシー（簡易版）":
    epsilon = st.slider("プライバシーパラメータ (ε)", 0.1, 10.0, 1.0)
    st.info("εが小さいほどプライバシー保護が強くなりますが、データの有用性は低下します。")

# 生成実行
st.header("4. 合成データ生成")

output_name = st.text_input(
    "出力データセット名",
    value=f"{selected_dataset}_synthetic",
    help="生成される合成データセットの名前"
)

if st.button("合成データを生成", type="primary"):
    with st.spinner("合成データを生成中..."):
        try:
            # 合成データの生成
            if generation_method == "Raw (コピー)":
                synthetic_df = df.copy()
                
            elif generation_method == "ノイズ付加":
                synthetic_df = df.copy()
                
                # 数値列にノイズを追加
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                for col in numeric_cols:
                    if noise_type == "ガウシアン":
                        noise = np.random.normal(0, noise_level * df[col].std(), size=len(df))
                    elif noise_type == "ラプラス":
                        noise = np.random.laplace(0, noise_level * df[col].std(), size=len(df))
                    else:  # 一様分布
                        noise = np.random.uniform(-noise_level * df[col].std(), 
                                                noise_level * df[col].std(), 
                                                size=len(df))
                    synthetic_df[col] = df[col] + noise
            
            elif generation_method == "データ置換":
                synthetic_df = df.copy()
                
                # カテゴリカル列の値をランダムに置換
                categorical_cols = df.select_dtypes(include=['object']).columns
                for col in categorical_cols:
                    mask = np.random.random(len(df)) < replacement_rate
                    unique_values = df[col].unique()
                    synthetic_df.loc[mask, col] = np.random.choice(unique_values, sum(mask))
            
            elif generation_method == "k-匿名化（簡易版）":
                synthetic_df = df.copy()
                st.warning("簡易実装：実際のk-匿名化アルゴリズムではありません")
                
                # 準識別子の一般化（簡易版）
                for col in quasi_identifiers:
                    if df[col].dtype in ['int64', 'float64']:
                        # 数値の場合：範囲に一般化
                        bins = pd.qcut(df[col], q=len(df)//k_value, duplicates='drop')
                        synthetic_df[col] = bins
                    else:
                        # カテゴリカルの場合：頻度の低い値を「その他」に
                        value_counts = df[col].value_counts()
                        rare_values = value_counts[value_counts < k_value].index
                        synthetic_df.loc[synthetic_df[col].isin(rare_values), col] = "その他"
            
            elif generation_method == "差分プライバシー（簡易版）":
                synthetic_df = df.copy()
                st.warning("簡易実装：実際の差分プライバシーアルゴリズムではありません")
                
                # 数値列にラプラスノイズを追加
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                for col in numeric_cols:
                    sensitivity = df[col].max() - df[col].min()
                    scale = sensitivity / epsilon
                    noise = np.random.laplace(0, scale, size=len(df))
                    synthetic_df[col] = df[col] + noise
            
            else:
                synthetic_df = df.copy()
            
            # 合成データの保存
            output_dir = DATA_DIR / output_name
            output_dir.mkdir(exist_ok=True)
            
            # CSVファイルの保存
            csv_path = output_dir / f"{output_name}.csv"
            synthetic_df.to_csv(csv_path, index=False)
            
            # メタデータの保存
            metadata = {
                "name": output_name,
                "description": f"Synthetic data generated from {selected_dataset} using {generation_method}",
                "original_dataset": selected_dataset,
                "generation_method": generation_method,
                "generation_params": {
                    "method": generation_method,
                    "noise_level": noise_level if generation_method == "ノイズ付加" else None,
                    "replacement_rate": replacement_rate if generation_method == "データ置換" else None,
                    "k_value": k_value if generation_method == "k-匿名化（簡易版）" else None,
                    "epsilon": epsilon if generation_method == "差分プライバシー（簡易版）" else None,
                },
                "rows": len(synthetic_df),
                "columns": len(synthetic_df.columns),
                "column_names": synthetic_df.columns.tolist(),
                "dtypes": synthetic_df.dtypes.astype(str).to_dict(),
                "generation_date": pd.Timestamp.now().isoformat()
            }
            
            metadata_path = output_dir / "metadata.json"
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
            
            # TAPAS記述ファイルもコピー（存在する場合）
            original_json_path = dataset_dir / f"{selected_dataset}.json"
            if original_json_path.exists():
                import shutil
                shutil.copy(original_json_path, output_dir / f"{output_name}.json")
            
            st.success(f"✅ 合成データが生成されました: {output_name}")
            
            # 結果の表示
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("### オリジナルデータ（最初の5行）")
                st.dataframe(df.head())
            
            with col2:
                st.write("### 合成データ（最初の5行）")
                st.dataframe(synthetic_df.head())
            
            # 基本統計量の比較
            st.write("### 基本統計量の比較")
            
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                stats_comparison = pd.DataFrame({
                    'Original_mean': df[numeric_cols].mean(),
                    'Synthetic_mean': synthetic_df[numeric_cols].mean(),
                    'Original_std': df[numeric_cols].std(),
                    'Synthetic_std': synthetic_df[numeric_cols].std()
                })
                st.dataframe(stats_comparison)
            
            st.info("""
            合成データが生成されました。
            データセット管理ページで確認し、プライバシー評価ページで評価を実行できます。
            """)
            
        except Exception as e:
            st.error(f"合成データ生成中にエラーが発生しました: {e}")

# 注意事項
st.divider()
st.warning("""
**注意事項**
- この実装は教育目的の簡易版です
- 実際の使用では、専門的な合成データ生成ライブラリ（SDV、DataSynthesizer等）の使用を推奨します
- 生成された合成データのプライバシー保護レベルは、TAPASで評価する必要があります
""")
