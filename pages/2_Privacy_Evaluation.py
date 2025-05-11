import streamlit as st
import pandas as pd
import json
import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

# TAPASパスの追加
tapas_path = Path(__file__).parent.parent / "tapas"
if str(tapas_path) not in sys.path:
    sys.path.insert(0, str(tapas_path))

st.set_page_config(
    page_title="プライバシー評価 - TAPAS",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 プライバシー評価")
st.write("""
TAPASを使用して、合成データのプライバシー保護レベルを評価します。
オリジナルデータと合成データを比較し、合成データからオリジナルデータの情報がどの程度漏洩するかを測定します。
""")

# データ保存用ディレクトリ
DATA_DIR = Path("data/uploaded")
RESULTS_DIR = Path("data/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# TAPASのインポート
try:
    import tapas.datasets
    import tapas.generators
    import tapas.threat_models
    import tapas.attacks
    import tapas.report
    tapas_available = True
except ImportError:
    tapas_available = False
    st.error("TAPASライブラリが正しくインポートできません。")

if not tapas_available:
    st.stop()

# 保存済みデータセットの取得
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
    st.warning("評価可能なデータセットがありません。まずデータセットをアップロードしてください。")
    st.stop()

# TAPASによるプライバシー評価の説明
with st.expander("📚 TAPASプライバシー評価の仕組み", expanded=True):
    st.write("""
    ### プライバシー評価の流れ
    
    1. **オリジナルデータ**: 保護したい個人情報を含む実際のデータセット
    2. **合成データ生成**: オリジナルデータから合成データを生成（または既存の合成データを使用）
    3. **攻撃シミュレーション**: 合成データからオリジナルデータの情報を推測する攻撃を実行
    4. **リスク評価**: 攻撃の成功率に基づいてプライバシーリスクを評価
    
    ### 重要な概念
    
    - **Membership Inference Attack (MIA)**: 特定のレコードがオリジナルデータに含まれているかを推測
    - **Attribute Inference Attack (AIA)**: レコードの特定の属性値を推測
    - **補助データ**: 攻撃者が持っている部分的な知識（オリジナルデータの一部）
    """)

# データセット選択
st.header("1. データセット選択")

# オリジナルデータの選択
col1, col2 = st.columns(2)

with col1:
    st.subheader("オリジナルデータ")
    dataset_names = [d["name"] for d in datasets]
    original_dataset = st.selectbox(
        "オリジナルデータセットを選択",
        dataset_names,
        help="保護したい個人情報を含む元のデータセット"
    )

with col2:
    st.subheader("合成データ")
    synthetic_option = st.radio(
        "合成データの選択",
        ["既存の合成データを使用", "新しく合成データを生成", "簡易テスト（同じデータを使用）"]
    )
    
    if synthetic_option == "既存の合成データを使用":
        synthetic_dataset = st.selectbox(
            "合成データセットを選択",
            dataset_names,
            help="既に生成済みの合成データセット"
        )
    elif synthetic_option == "新しく合成データを生成":
        st.info("合成データ生成機能は現在開発中です。")
        generator_type = st.selectbox(
            "生成器の種類",
            ["Raw (コピー)", "ノイズ付加", "差分プライバシー"]
        )
        
        if generator_type == "ノイズ付加":
            noise_level = st.slider("ノイズレベル", 0.0, 1.0, 0.1)
        elif generator_type == "差分プライバシー":
            epsilon = st.slider("プライバシーパラメータ (ε)", 0.1, 10.0, 1.0)
    else:
        st.warning("テストモード: オリジナルデータを合成データとして使用します（プライバシー保護なし）")
        synthetic_dataset = original_dataset

# 攻撃設定
st.header("2. プライバシー攻撃の設定")

col1, col2 = st.columns(2)

with col1:
    st.subheader("攻撃種別")
    attack_type = st.selectbox(
        "実行する攻撃を選択",
        [
            "Membership Inference Attack (MIA)",
            "Attribute Inference Attack (AIA)",
            "Groundhog Attack",
            "Closest Distance Attack"
        ]
    )
    
    # 攻撃の説明
    attack_descriptions = {
        "Membership Inference Attack (MIA)": "特定のレコードがオリジナルデータに含まれているかどうかを推定する攻撃です。",
        "Attribute Inference Attack (AIA)": "データセット内のレコードの特定の属性値を推定する攻撃です。",
        "Groundhog Attack": "統計的特徴を使用してメンバーシップを推定する攻撃です。",
        "Closest Distance Attack": "最近傍距離を使用してメンバーシップを推定する攻撃です。"
    }
    st.info(attack_descriptions[attack_type])

with col2:
    st.subheader("攻撃パラメータ")
    
    # 共通パラメータ
    num_samples = st.number_input(
        "評価サンプル数",
        min_value=10,
        max_value=1000,
        value=100,
        help="攻撃評価に使用するサンプル数"
    )
    
    if attack_type == "Membership Inference Attack (MIA)":
        mia_target = st.radio(
            "攻撃対象",
            ["ランダムなレコード", "特定のレコード"]
        )
        if mia_target == "特定のレコード":
            target_record_idx = st.number_input("ターゲットレコードのインデックス", min_value=0, value=0)
    
    elif attack_type == "Attribute Inference Attack (AIA)":
        target_attribute = st.text_input("推定対象の属性名")
    
    elif attack_type == "Groundhog Attack":
        use_naive = st.checkbox("Naive features", value=True)
        use_hist = st.checkbox("Histogram features", value=True)
        use_corr = st.checkbox("Correlation features", value=True)

# 攻撃者の知識設定
st.header("3. 攻撃者の知識設定")

col1, col2 = st.columns(2)

with col1:
    auxiliary_split = st.slider(
        "補助データの割合",
        min_value=0.0,
        max_value=0.9,
        value=0.5,
        help="攻撃者が知っているオリジナルデータの割合"
    )
    
    st.write(f"攻撃者は、オリジナルデータの{auxiliary_split:.0%}にアクセスできると仮定します。")

with col2:
    synthetic_access = st.selectbox(
        "合成データへのアクセス",
        ["Black-box (APIのみ)", "White-box (完全アクセス)"],
        help="攻撃者の合成データへのアクセスレベル"
    )
    
    num_queries = st.number_input(
        "合成データクエリ数",
        min_value=100,
        max_value=10000,
        value=1000,
        help="攻撃者が合成データに対して行えるクエリ数"
    )

# 評価実行
st.header("4. 評価実行")

# 実行前の確認
st.write("### 評価設定の確認")
col1, col2, col3 = st.columns(3)

with col1:
    st.write("**データセット**")
    st.write(f"- オリジナル: {original_dataset}")
    if synthetic_option == "既存の合成データを使用":
        st.write(f"- 合成データ: {synthetic_dataset}")
    else:
        st.write(f"- 合成データ: {synthetic_option}")

with col2:
    st.write("**攻撃設定**")
    st.write(f"- 攻撃種別: {attack_type}")
    st.write(f"- サンプル数: {num_samples}")

with col3:
    st.write("**攻撃者の知識**")
    st.write(f"- 補助データ: {auxiliary_split:.0%}")
    st.write(f"- アクセス: {synthetic_access}")

if st.button("プライバシー評価を実行", type="primary"):
    with st.spinner("評価を実行中..."):
        try:
            # 簡易実装：実際のTAPAS評価の代わりにダミー結果を生成
            st.warning("現在は簡易実装です。実際のTAPAS攻撃は実装中です。")
            
            # ダミーの評価結果
            results = []
            for i in range(5):
                accuracy = np.random.uniform(0.5, 0.9)
                results.append({
                    "run": i + 1,
                    "accuracy": accuracy,
                    "precision": accuracy + np.random.uniform(-0.1, 0.1),
                    "recall": accuracy + np.random.uniform(-0.1, 0.1),
                    "f1_score": accuracy + np.random.uniform(-0.05, 0.05),
                    "auc": accuracy + np.random.uniform(-0.05, 0.05)
                })
            
            results_df = pd.DataFrame(results)
            avg_accuracy = results_df['accuracy'].mean()
            
            # 結果の表示
            st.success("評価が完了しました！")
            
            # メトリクスの表示
            st.write("### 評価結果")
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("平均精度", f"{results_df['accuracy'].mean():.3f}")
            with col2:
                st.metric("平均適合率", f"{results_df['precision'].mean():.3f}")
            with col3:
                st.metric("平均再現率", f"{results_df['recall'].mean():.3f}")
            with col4:
                st.metric("平均F1スコア", f"{results_df['f1_score'].mean():.3f}")
            with col5:
                st.metric("平均AUC", f"{results_df['auc'].mean():.3f}")
            
            # プライバシーリスクの評価
            st.write("### プライバシーリスク評価")
            
            if avg_accuracy > 0.8:
                risk_level = "高"
                risk_color = "#ff4444"
                risk_message = "合成データから元データの情報が漏洩するリスクが高いです。"
            elif avg_accuracy > 0.65:
                risk_level = "中"
                risk_color = "#ffaa00"
                risk_message = "中程度のプライバシーリスクがあります。"
            else:
                risk_level = "低"
                risk_color = "#44ff44"
                risk_message = "プライバシーリスクは比較的低いです。"
            
            st.markdown(f"""
            <div style="background-color: {risk_color}20; padding: 20px; border-radius: 10px; border: 2px solid {risk_color};">
                <h3 style="color: {risk_color};">プライバシーリスクレベル: {risk_level}</h3>
                <p>{risk_message}</p>
                <p>攻撃の成功率（精度）が {avg_accuracy:.1%} であることは、合成データから元データの情報を
                {avg_accuracy:.1%} の確率で推測できることを意味します。</p>
            </div>
            """, unsafe_allow_html=True)
            
            # 詳細結果のプロット
            fig, ax = plt.subplots(figsize=(10, 6))
            metrics = ['accuracy', 'precision', 'recall', 'f1_score', 'auc']
            x = range(len(results))
            
            for metric in metrics:
                values = [r[metric] for r in results]
                ax.plot(x, values, marker='o', label=metric)
            
            ax.set_xlabel('実行回')
            ax.set_ylabel('スコア')
            ax.set_title('評価メトリクスの推移')
            ax.legend()
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)
            
        except Exception as e:
            st.error(f"評価中にエラーが発生しました: {e}")

# サイドバー
st.sidebar.header("📌 評価のヒント")
st.sidebar.info("""
**プライバシー評価のポイント**

1. **オリジナルデータと合成データ**の両方が必要です
2. **補助データの割合**が高いほど、攻撃が成功しやすくなります
3. **攻撃の成功率が50%に近い**ほど、プライバシー保護が優れています
4. **複数の攻撃手法**で評価することが推奨されます
""")

st.sidebar.divider()

st.sidebar.header("🔍 用語説明")
st.sidebar.write("""
- **MIA**: メンバーシップ推論攻撃
- **AIA**: 属性推論攻撃
- **補助データ**: 攻撃者が持つ部分的な知識
- **Black-box**: APIアクセスのみ
- **White-box**: 完全アクセス
""")
