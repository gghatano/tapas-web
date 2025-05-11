import streamlit as st
import pandas as pd
import json
import sys
from pathlib import Path

# TAPASパスの追加
tapas_path = Path(__file__).parent / "tapas"
if str(tapas_path) not in sys.path:
    sys.path.insert(0, str(tapas_path))

st.title("TAPAS データセット記述ファイル作成ツール")

# TAPASの記述ファイル仕様を説明
st.header("1. TAPAS データセット記述ファイルとは")
st.write("""
TAPASデータセットには、以下の要素を含む記述ファイル（JSON）が必要です：

- **columns**: 各列の名前とデータ型の定義
- **metadata**: データセットに関する追加情報（オプション）

各列のデータ型は以下のいずれかです：
- **Continuous**: 連続値（数値）
- **Integer**: 整数値  
- **Categorical**: カテゴリカル値（文字列や離散値）
""")

# サンプルの記述ファイルを表示
st.header("2. 記述ファイルの例")

example_description = {
    "columns": [
        {"name": "age", "type": "Integer"},
        {"name": "workclass", "type": "Categorical"},
        {"name": "education", "type": "Categorical"},
        {"name": "education-num", "type": "Integer"},
        {"name": "marital-status", "type": "Categorical"},
        {"name": "occupation", "type": "Categorical"},
        {"name": "relationship", "type": "Categorical"},
        {"name": "race", "type": "Categorical"},
        {"name": "sex", "type": "Categorical"},
        {"name": "capital-gain", "type": "Continuous"},
        {"name": "capital-loss", "type": "Continuous"},
        {"name": "hours-per-week", "type": "Continuous"},
        {"name": "native-country", "type": "Categorical"},
        {"name": "income", "type": "Categorical"}
    ],
    "metadata": {
        "description": "UCI Adult Income Dataset",
        "source": "UCI Machine Learning Repository",
        "target": "income"
    }
}

st.json(example_description)

# Adult datasetの正式な記述ファイルを作成
st.header("3. Adult Dataset用の記述ファイル作成")

if st.button("Adult Dataset用の記述ファイルを生成"):
    # データセットディレクトリ
    DATA_DIR = Path("data/uploaded/adult_dataset")
    
    if DATA_DIR.exists():
        # CSVファイルを読み込んで列名を取得
        csv_path = DATA_DIR / "adult_dataset.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            
            # 各列の型を自動判定し、記述を作成
            columns = []
            for col in df.columns:
                dtype = str(df[col].dtype)
                # 型の判定ロジック
                if col in ['age', 'fnlwgt', 'education-num', 'capital-gain', 'capital-loss', 'hours-per-week']:
                    col_type = 'Integer' if 'int' in dtype else 'Continuous'
                elif col in ['income', 'workclass', 'education', 'marital-status', 'occupation', 
                           'relationship', 'race', 'sex', 'native-country']:
                    col_type = 'Categorical'
                else:
                    # デフォルトの型判定
                    if dtype.startswith('int'):
                        col_type = 'Integer'
                    elif dtype.startswith('float'):
                        col_type = 'Continuous'
                    else:
                        col_type = 'Categorical'
                
                columns.append({
                    "name": col,
                    "type": col_type
                })
            
            # 記述ファイルの作成
            description = {
                "columns": columns,
                "metadata": {
                    "description": "UCI Adult Income Dataset",
                    "source": "UCI Machine Learning Repository",
                    "target": "income",
                    "created_date": pd.Timestamp.now().isoformat()
                }
            }
            
            # ファイルに保存
            description_path = DATA_DIR / "adult_dataset.json"
            with open(description_path, "w") as f:
                json.dump(description, f, indent=2)
            
            st.success(f"✅ 記述ファイルが作成されました: {description_path}")
            st.json(description)
            
            # TAPASでのデータセット読み込みテスト
            st.header("4. TAPASデータセットの読み込みテスト")
            
            try:
                import tapas.datasets
                
                # TAPASデータセットとして読み込み
                dataset = tapas.datasets.TabularDataset.read(
                    str(DATA_DIR / "adult_dataset"),
                    label="Adult Dataset"
                )
                
                st.success("✅ TAPASデータセットとして正常に読み込めました！")
                
                # データセット情報の表示
                st.write("### データセット情報")
                st.write(f"- レコード数: {len(dataset)}")
                st.write(f"- ラベル: {dataset.label}")
                
                # サンプルレコードの表示
                st.write("### サンプルレコード")
                sample = dataset.get_records([0, 1, 2])
                st.write(sample)
                
                # 列情報の表示
                if hasattr(dataset, 'description'):
                    st.write("### 列情報")
                    st.json(dataset.description.columns)
                
            except Exception as e:
                st.error(f"TAPASデータセットの読み込みに失敗: {e}")
                st.info("エラーの詳細を確認し、記述ファイルを修正してください。")
        else:
            st.error("Adult datasetのCSVファイルが見つかりません。")
    else:
        st.error("Adult datasetがまだロードされていません。ホームページからロードしてください。")

# カスタムデータセット用の記述ファイル作成
st.header("5. カスタムデータセット用の記述ファイル作成")

uploaded_file = st.file_uploader("CSVファイルをアップロード", type=['csv'])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    st.write("### 列の型指定")
    
    columns = []
    for col in df.columns:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write(f"**{col}**")
            st.write(f"データ型: {df[col].dtype}")
            st.write(f"サンプル値: {df[col].iloc[0]}")
        
        with col2:
            col_type = st.selectbox(
                f"{col}の型",
                ["Categorical", "Integer", "Continuous"],
                key=f"type_{col}"
            )
        
        columns.append({
            "name": col,
            "type": col_type
        })
    
    # メタデータの入力
    st.write("### メタデータ")
    description = st.text_input("データセットの説明")
    target_column = st.selectbox("ターゲット列（予測対象）", ["なし"] + list(df.columns))
    
    if st.button("記述ファイルを作成"):
        metadata = {
            "description": description,
            "created_date": pd.Timestamp.now().isoformat()
        }
        
        if target_column != "なし":
            metadata["target"] = target_column
        
        description_data = {
            "columns": columns,
            "metadata": metadata
        }
        
        # ダウンロード用のJSONを作成
        json_str = json.dumps(description_data, indent=2)
        st.download_button(
            label="記述ファイルをダウンロード",
            data=json_str,
            file_name=f"{uploaded_file.name.replace('.csv', '')}.json",
            mime="application/json"
        )
        
        st.json(description_data)
