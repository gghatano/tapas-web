import streamlit as st
import pandas as pd
import json
import os
import sys
from pathlib import Path

# TAPASパスの追加
tapas_path = Path(__file__).parent.parent / "tapas"
if str(tapas_path) not in sys.path:
    sys.path.insert(0, str(tapas_path))

st.set_page_config(
    page_title="データセット管理 - TAPAS",
    page_icon="📊",
    layout="wide"
)

st.title("📊 データセット管理")
st.write("プライバシー評価に使用するデータセットをアップロード・管理します。")

# データ保存用ディレクトリの作成
DATA_DIR = Path("data/uploaded")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# TAPASのインポート
tapas_available = False
try:
    import tapas.datasets
    tapas_available = True
except ImportError as e:
    st.error(f"TAPASライブラリが正しくインポートできません: {e}")
    tapas_available = False

# タブ作成
tab1, tab2, tab3 = st.tabs(["📤 アップロード", "📋 データセット一覧", "🔧 データセット詳細"])

with tab1:
    st.header("データセットのアップロード")
    
    # ファイルアップローダー
    uploaded_file = st.file_uploader(
        "CSVファイルを選択してください",
        type=["csv"],
        help="プライバシー評価を行うデータセットをCSV形式でアップロードします。"
    )
    
    if uploaded_file is not None:
        # ファイル情報表示
        st.write("### アップロードファイル情報")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**ファイル名:** {uploaded_file.name}")
            st.write(f"**ファイルサイズ:** {uploaded_file.size / 1024:.1f} KB")
        
        # データセット名の入力
        with col2:
            dataset_name = st.text_input(
                "データセット名",
                value=uploaded_file.name.replace(".csv", ""),
                help="保存するデータセットの名前を指定してください。"
            )
        
        # データプレビュー
        try:
            df = pd.read_csv(uploaded_file)
            st.write("### データプレビュー")
            st.dataframe(df.head(10))
            
            # データ情報
            st.write("### データセット情報")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("行数", len(df))
            with col2:
                st.metric("列数", len(df.columns))
            with col3:
                st.metric("メモリ使用量", f"{df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
            
            # 列情報
            with st.expander("列の詳細情報", expanded=False):
                col_info = pd.DataFrame({
                    "データ型": df.dtypes,
                    "非NULL数": df.count(),
                    "NULL数": df.isnull().sum(),
                    "ユニーク数": df.nunique()
                })
                st.dataframe(col_info)
            
            # 保存オプション
            st.write("### 保存オプション")
            col1, col2 = st.columns(2)
            
            with col1:
                description = st.text_area(
                    "データセットの説明",
                    help="このデータセットの説明を入力してください。"
                )
            
            with col2:
                st.write("**TAPAS形式への変換オプション**")
                if tapas_available:
                    convert_to_tapas = st.checkbox(
                        "TAPAS形式に変換して保存",
                        value=True,
                        help="TAPASライブラリで使用可能な形式に変換します。"
                    )
                else:
                    st.warning("TAPASライブラリが利用できないため、CSV形式のみで保存されます。")
                    convert_to_tapas = False
            
            # 保存ボタン
            if st.button("データセットを保存", type="primary"):
                try:
                    # CSVファイルの保存
                    dataset_dir = DATA_DIR / dataset_name
                    dataset_dir.mkdir(exist_ok=True)
                    
                    csv_path = dataset_dir / f"{dataset_name}.csv"
                    df.to_csv(csv_path, index=False)
                    
                    # メタデータの保存
                    metadata = {
                        "name": dataset_name,
                        "description": description,
                        "original_filename": uploaded_file.name,
                        "rows": len(df),
                        "columns": len(df.columns),
                        "column_names": df.columns.tolist(),
                        "dtypes": df.dtypes.astype(str).to_dict(),
                        "upload_date": pd.Timestamp.now().isoformat()
                    }
                    
                    metadata_path = dataset_dir / "metadata.json"
                    with open(metadata_path, "w") as f:
                        json.dump(metadata, f, indent=2)
                    
                    # TAPAS形式での保存
                    if convert_to_tapas and tapas_available:
                        try:
                            # TAPASデータセットの説明を作成
                            columns = []
                            for col in df.columns:
                                dtype = str(df[col].dtype)
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
                            
                            description_data = {
                                "columns": columns
                            }
                            
                            # TAPAS用の記述ファイルを保存
                            description_path = dataset_dir / f"{dataset_name}.json"
                            with open(description_path, "w") as f:
                                json.dump(description_data, f, indent=2)
                            
                            st.success(f"✅ データセット '{dataset_name}' が正常に保存されました！")
                            st.info("TAPAS形式での保存も完了しました。")
                        except Exception as e:
                            st.warning(f"TAPAS形式への変換中にエラーが発生しました: {e}")
                            st.info("CSV形式での保存は完了しています。")
                    else:
                        st.success(f"✅ データセット '{dataset_name}' が正常に保存されました！")
                    
                    # アップロードファイルのリセット
                    uploaded_file = None
                    
                except Exception as e:
                    st.error(f"保存中にエラーが発生しました: {e}")
                    
        except Exception as e:
            st.error(f"CSVファイルの読み込みに失敗しました: {e}")

with tab2:
    st.header("保存済みデータセット一覧")
    
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
    
    if datasets:
        # データセット一覧表示
        df_datasets = pd.DataFrame(datasets)
        
        # 選択可能な列のみを表示
        display_columns = ["name", "description", "rows", "columns", "upload_date"]
        available_columns = [col for col in display_columns if col in df_datasets.columns]
        
        if available_columns:
            st.dataframe(
                df_datasets[available_columns],
                hide_index=True,
                use_container_width=True
            )
        else:
            st.write("データセット情報の表示ができません。")
    else:
        st.info("保存済みのデータセットがありません。")

with tab3:
    st.header("データセット詳細")
    
    if datasets:
        # データセット選択
        dataset_names = [d["name"] for d in datasets]
        selected_dataset = st.selectbox("データセットを選択", dataset_names)
        
        if selected_dataset:
            # 選択されたデータセットの情報を取得
            dataset_info = next(d for d in datasets if d["name"] == selected_dataset)
            dataset_dir = DATA_DIR / selected_dataset
            
            # メタデータ表示
            st.write("### メタデータ")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**データセット名:** {dataset_info['name']}")
                st.write(f"**説明:** {dataset_info.get('description', 'なし')}")
                st.write(f"**アップロード日時:** {dataset_info.get('upload_date', '不明')}")
            
            with col2:
                st.write(f"**行数:** {dataset_info.get('rows', '不明')}")
                st.write(f"**列数:** {dataset_info.get('columns', '不明')}")
                st.write(f"**元ファイル名:** {dataset_info.get('original_filename', '不明')}")
            
            # データプレビュー
            csv_path = dataset_dir / f"{selected_dataset}.csv"
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                
                st.write("### データプレビュー")
                st.dataframe(df.head(20))
                
                # 基本統計量
                st.write("### 基本統計量")
                st.dataframe(df.describe())
                
                # データ削除オプション
                st.write("### データセット管理")
                if st.button("このデータセットを削除", type="secondary"):
                    confirm = st.checkbox("本当に削除しますか？この操作は取り消せません。")
                    if confirm:
                        if st.button("削除を実行", type="primary"):
                            try:
                                import shutil
                                shutil.rmtree(dataset_dir)
                                st.success(f"データセット '{selected_dataset}' を削除しました。")
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"削除中にエラーが発生しました: {e}")
            else:
                st.error("データファイルが見つかりません。")
    else:
        st.info("保存済みのデータセットがありません。")
