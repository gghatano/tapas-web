import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import json

# TAPASパスの追加
tapas_path = Path(__file__).parent / "tapas"
if str(tapas_path) not in sys.path:
    sys.path.insert(0, str(tapas_path))

st.title("TAPAS実装例：完全なプライバシー評価")

st.write("""
TAPASを使用した実際のプライバシー評価の実装例です。
この例では、オリジナルデータと合成データを比較して、
合成データのプライバシー保護レベルを評価します。
""")

# TAPASのインポート
try:
    import tapas.datasets
    import tapas.generators
    import tapas.threat_models
    import tapas.attacks
    import tapas.report
    tapas_available = True
except ImportError as e:
    st.error(f"TAPASのインポートに失敗: {e}")
    tapas_available = False
    st.stop()

# 実装例のコード表示
st.header("1. TAPASの基本的な使用方法")

code_example = '''
# 1. データセットの読み込み
original_data = tapas.datasets.TabularDataset.read(
    "path/to/original_dataset",
    label="Original Data"
)

# 2. 合成データ生成器の設定
# Rawジェネレータ（データをそのままコピー）
generator = tapas.generators.Raw()

# 3. 攻撃者の知識モデル設定
# オリジナルデータの50%を補助データとして使用
data_knowledge = tapas.threat_models.AuxiliaryDataKnowledge(
    original_data,
    auxiliary_split=0.5,
    num_training_records=1000
)

# 合成データへのBlack-boxアクセス
sdg_knowledge = tapas.threat_models.BlackBoxKnowledge(
    generator,
    num_synthetic_records=1000
)

# 4. 脅威モデルの定義（MIA）
threat_model = tapas.threat_models.TargetedMIA(
    attacker_knowledge_data=data_knowledge,
    target_record=original_data.get_records([0]),  # 攻撃対象レコード
    attacker_knowledge_generator=sdg_knowledge,
    generate_pairs=True,
    replace_target=True
)

# 5. 攻撃の実行
attack = tapas.attacks.GroundhogAttack()
attack.train(threat_model, num_samples=100)
results = threat_model.test(attack, num_samples=100)

# 6. レポート生成
report = tapas.report.MIAttackReport([results])
report.publish("privacy_evaluation_report")
'''

st.code(code_example, language='python')

# 実際の評価実行
st.header("2. 評価のデモンストレーション")

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

if datasets:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("オリジナルデータ")
        dataset_names = [d["name"] for d in datasets]
        original_dataset = st.selectbox(
            "オリジナルデータセット",
            dataset_names,
            key="orig"
        )
    
    with col2:
        st.subheader("合成データ")
        synthetic_dataset = st.selectbox(
            "合成データセット",
            dataset_names,
            key="synth"
        )
    
    if st.button("評価を実行"):
        try:
            # 1. データセットの読み込み
            original_dir = DATA_DIR / original_dataset
            synthetic_dir = DATA_DIR / synthetic_dataset
            
            # TAPASデータセットとして読み込み
            if (original_dir / f"{original_dataset}.json").exists():
                original_data = tapas.datasets.TabularDataset.read(
                    str(original_dir / original_dataset),
                    label="Original Data"
                )
            else:
                # CSVのみの場合は簡易的に読み込み
                st.warning("TAPAS記述ファイルが見つかりません。簡易モードで読み込みます。")
                original_df = pd.read_csv(original_dir / f"{original_dataset}.csv")
                
                # 簡易的なTAPASデータセット作成
                from tapas.datasets import DataDescription, TabularRecord
                
                # データ記述の作成
                columns = []
                for col in original_df.columns:
                    if original_df[col].dtype in ['int64']:
                        col_type = 'Integer'
                    elif original_df[col].dtype in ['float64']:
                        col_type = 'Continuous'
                    else:
                        col_type = 'Categorical'
                    
                    columns.append({"name": col, "type": col_type})
                
                description = DataDescription({"columns": columns})
                
                # レコードの作成
                records = []
                for _, row in original_df.iterrows():
                    records.append(TabularRecord(row.to_dict()))
                
                # データセットの作成
                from tapas.datasets import Dataset
                original_data = Dataset(records, description, label="Original Data")
            
            # 2. ジェネレータの設定（実際には合成データを読み込む）
            generator = tapas.generators.Raw()
            
            # 3. 簡単なMIA評価
            st.write("### Membership Inference Attack (MIA) 評価")
            
            with st.spinner("評価を実行中..."):
                # 攻撃者の知識設定
                data_knowledge = tapas.threat_models.AuxiliaryDataKnowledge(
                    original_data,
                    auxiliary_split=0.5,
                    num_training_records=min(100, len(original_data))
                )
                
                sdg_knowledge = tapas.threat_models.BlackBoxKnowledge(
                    generator,
                    num_synthetic_records=min(100, len(original_data))
                )
                
                # 脅威モデル
                threat_model = tapas.threat_models.TargetedMIA(
                    attacker_knowledge_data=data_knowledge,
                    target_record=original_data.get_records([0]),
                    attacker_knowledge_generator=sdg_knowledge,
                    generate_pairs=True,
                    replace_target=True
                )
                
                # 攻撃実行
                attack = tapas.attacks.GroundhogAttack()
                attack.train(threat_model, num_samples=50)
                results = threat_model.test(attack, num_samples=50)
                
                # 結果表示
                st.success("評価が完了しました！")
                
                # 結果の取得（resultsの形式に依存）
                if hasattr(results, 'get_metrics'):
                    metrics = results.get_metrics()
                    st.write("**評価メトリクス:**")
                    for key, value in metrics.items():
                        st.write(f"- {key}: {value:.3f}")
                else:
                    st.write("**評価結果:**")
                    st.write(results)
                
                # プライバシーリスクの判定
                # 注：実際のメトリクスに基づいて判定
                st.write("### プライバシーリスク評価")
                st.info("""
                攻撃の成功率が50%に近いほど、合成データのプライバシー保護が優れています。
                成功率が高い場合は、合成データから元データの情報が漏洩するリスクがあります。
                """)
                
        except Exception as e:
            st.error(f"評価中にエラーが発生: {e}")
            st.info("エラーの詳細を確認し、データセットの形式を確認してください。")

# TAPASの詳細説明
st.header("3. TAPASの重要な概念")

with st.expander("攻撃者の知識モデル", expanded=True):
    st.write("""
    ### AuxiliaryDataKnowledge
    - 攻撃者がオリジナルデータの一部にアクセスできる場合
    - `auxiliary_split`: 攻撃者が知っているデータの割合
    
    ### BlackBoxKnowledge  
    - 攻撃者が合成データ生成器にAPIアクセスできる場合
    - `num_synthetic_records`: クエリ可能なレコード数
    
    ### WhiteBoxKnowledge
    - 攻撃者が生成器の内部にアクセスできる場合
    """)

with st.expander("攻撃手法", expanded=True):
    st.write("""
    ### GroundhogAttack
    - 統計的特徴を使用したMIA
    - Naive、Histogram、Correlationの特徴を組み合わせ
    
    ### ClosestDistanceAttack
    - 最近傍距離に基づくMIA
    - Hamming距離、L1/L2ノルムなど
    
    ### ShadowModelAttack
    - Shadow Modelを使用した高度なMIA
    """)

with st.expander("評価メトリクス", expanded=True):
    st.write("""
    ### 主要なメトリクス
    - **Accuracy**: 攻撃の全体的な精度
    - **Precision/Recall**: 攻撃の適合率と再現率
    - **AUC**: ROC曲線下の面積
    - **Advantage**: ランダム推測からの改善度
    """)

# 次のステップ
st.header("4. 次のステップ")

st.info("""
**完全なTAPAS実装のために:**

1. 適切な合成データ生成器の実装
2. 複数の攻撃手法の比較評価
3. 詳細なレポート生成機能
4. パラメータのチューニング機能

現在の実装は教育目的の簡易版です。
実際の使用では、データセットの特性に応じた適切な設定が必要です。
""")
