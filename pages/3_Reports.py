import streamlit as st
import pandas as pd
import json
import sys
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import base64
from io import BytesIO
import numpy as np

# TAPASパスの追加
tapas_path = Path(__file__).parent.parent / "tapas"
if str(tapas_path) not in sys.path:
    sys.path.insert(0, str(tapas_path))

st.set_page_config(
    page_title="レポート - TAPAS",
    page_icon="📄",
    layout="wide"
)

st.title("📄 プライバシー評価レポート")
st.write("実行した評価の結果を確認し、レポートを生成します。")

# データディレクトリ
RESULTS_DIR = Path("data/results")

# 結果ファイルの取得
result_files = []
if RESULTS_DIR.exists():
    result_files = list(RESULTS_DIR.glob("*.json"))

if not result_files:
    st.warning("評価結果がありません。プライバシー評価を実行してください。")
    st.stop()

# タブ作成
tab1, tab2, tab3 = st.tabs(["📊 個別レポート", "📈 比較分析", "📥 レポートダウンロード"])

with tab1:
    st.header("個別評価レポート")
    
    # 評価結果の選択
    result_options = {}
    for file in result_files:
        with open(file) as f:
            data = json.load(f)
            label = f"{data['dataset']} - {data['attack_type']} ({data['timestamp'][:19]})"
            result_options[label] = file
    
    selected_result = st.selectbox("評価結果を選択", list(result_options.keys()))
    
    if selected_result:
        # 選択された結果の読み込み
        with open(result_options[selected_result]) as f:
            result_data = json.load(f)
        
        # 基本情報の表示
        st.subheader("評価概要")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**データセット:**", result_data['dataset'])
            st.write("**攻撃タイプ:**", result_data['attack_type'])
        
        with col2:
            st.write("**データ種別:**", result_data['parameters']['data_type'])
            st.write("**補助データ分割:**", f"{result_data['parameters']['auxiliary_split']:.1%}")
        
        with col3:
            st.write("**評価実行回数:**", result_data['parameters']['evaluation_runs'])
            st.write("**評価日時:**", result_data['timestamp'][:19])
        
        # メトリクスの表示
        st.subheader("評価メトリクス")
        
        results_df = pd.DataFrame(result_data['results'])
        avg_metrics = results_df.mean(numeric_only=True)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("平均精度", f"{avg_metrics['accuracy']:.3f}")
        with col2:
            st.metric("平均適合率", f"{avg_metrics['precision']:.3f}")
        with col3:
            st.metric("平均再現率", f"{avg_metrics['recall']:.3f}")
        with col4:
            st.metric("平均F1スコア", f"{avg_metrics['f1_score']:.3f}")
        with col5:
            st.metric("平均AUC", f"{avg_metrics['auc']:.3f}")
        
        # 詳細テーブル
        st.subheader("実行ごとの詳細結果")
        st.dataframe(results_df, use_container_width=True)
        
        # メトリクスのプロット
        st.subheader("メトリクスの推移")
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()
        
        metrics = ['accuracy', 'precision', 'recall', 'f1_score', 'auc']
        for idx, metric in enumerate(metrics):
            ax = axes[idx]
            ax.plot(results_df['run'], results_df[metric], marker='o', linewidth=2, markersize=8)
            ax.set_xlabel('実行回')
            ax.set_ylabel(metric.replace('_', ' ').title())
            ax.set_title(f'{metric.replace("_", " ").title()} の推移')
            ax.grid(True, alpha=0.3)
        
        # 最後のサブプロットは使わないので非表示に
        axes[-1].set_visible(False)
        
        plt.tight_layout()
        st.pyplot(fig)
        
        # リスク評価
        st.subheader("プライバシーリスク評価")
        
        avg_accuracy = avg_metrics['accuracy']
        if avg_accuracy > 0.9:
            risk_level = "高"
            risk_color = "#ff4444"
            risk_icon = "⚠️"
        elif avg_accuracy > 0.7:
            risk_level = "中"
            risk_color = "#ffaa00"
            risk_icon = "⚠️"
        else:
            risk_level = "低"
            risk_color = "#44ff44"
            risk_icon = "✅"
        
        st.markdown(f"""
        <div style="background-color: {risk_color}20; padding: 20px; border-radius: 10px; border: 2px solid {risk_color};">
            <h3 style="color: {risk_color};">{risk_icon} プライバシーリスクレベル: {risk_level}</h3>
            <p>攻撃の成功率（精度）が {avg_accuracy:.1%} であることから、プライバシーリスクは「{risk_level}」と評価されます。</p>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.header("比較分析")
    
    # 複数の結果を選択
    selected_results = st.multiselect(
        "比較する評価結果を選択（最大5つ）",
        list(result_options.keys()),
        max_selections=5
    )
    
    if len(selected_results) >= 2:
        # 選択された結果のデータを読み込み
        comparison_data = []
        for result_label in selected_results:
            with open(result_options[result_label]) as f:
                data = json.load(f)
                avg_metrics = pd.DataFrame(data['results']).mean(numeric_only=True)
                comparison_data.append({
                    'label': f"{data['dataset']} - {data['attack_type']}",
                    'accuracy': avg_metrics['accuracy'],
                    'precision': avg_metrics['precision'],
                    'recall': avg_metrics['recall'],
                    'f1_score': avg_metrics['f1_score'],
                    'auc': avg_metrics['auc']
                })
        
        comparison_df = pd.DataFrame(comparison_data)
        
        # 比較プロット
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # 各メトリクスのバープロット
        metrics = ['accuracy', 'precision', 'recall', 'f1_score', 'auc']
        x = np.arange(len(comparison_df))
        width = 0.15
        
        for i, metric in enumerate(metrics):
            offset = (i - 2) * width
            ax.bar(x + offset, comparison_df[metric], width, label=metric.replace('_', ' ').title())
        
        ax.set_xlabel('評価結果')
        ax.set_ylabel('スコア')
        ax.set_title('評価メトリクスの比較')
        ax.set_xticks(x)
        ax.set_xticklabels(comparison_df['label'], rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        st.pyplot(fig)
        
        # レーダーチャート
        st.subheader("レーダーチャート比較")
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        # 角度の設定
        angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
        angles += angles[:1]  # 閉じた形にする
        
        # 各評価結果のプロット
        for idx, row in comparison_df.iterrows():
            values = row[metrics].tolist()
            values += values[:1]  # 閉じた形にする
            ax.plot(angles, values, 'o-', linewidth=2, label=row['label'])
            ax.fill(angles, values, alpha=0.25)
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([m.replace('_', ' ').title() for m in metrics])
        ax.set_ylim(0, 1)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        ax.grid(True)
        
        plt.tight_layout()
        st.pyplot(fig)
        
        # 比較テーブル
        st.subheader("比較テーブル")
        display_df = comparison_df.set_index('label')
        
        # カラーマップで視覚化
        cm = sns.light_palette("green", as_cmap=True)
        styled_df = display_df.style.background_gradient(cmap=cm)
        
        st.dataframe(styled_df)
        
    else:
        st.info("比較分析を行うには、2つ以上の評価結果を選択してください。")

with tab3:
    st.header("レポートダウンロード")
    
    # レポート対象の選択
    selected_report = st.selectbox(
        "レポートを生成する評価結果を選択",
        list(result_options.keys()),
        key="report_select"
    )
    
    if selected_report:
        with open(result_options[selected_report]) as f:
            result_data = json.load(f)
        
        # レポートフォーマットの選択
        report_format = st.radio(
            "レポート形式",
            ["PDF", "HTML", "JSON", "CSV"]
        )
        
        # レポートの内容オプション
        st.subheader("レポート内容の設定")
        col1, col2 = st.columns(2)
        
        with col1:
            include_summary = st.checkbox("概要情報を含める", value=True)
            include_metrics = st.checkbox("評価メトリクスを含める", value=True)
            include_charts = st.checkbox("グラフを含める", value=True)
        
        with col2:
            include_recommendations = st.checkbox("推奨事項を含める", value=True)
            include_raw_data = st.checkbox("生データを含める", value=False)
        
        # レポート生成ボタン
        if st.button("レポートを生成", type="primary"):
            try:
                if report_format == "JSON":
                    # JSONフォーマット
                    report_content = json.dumps(result_data, indent=2, ensure_ascii=False)
                    file_name = f"privacy_report_{result_data['id']}.json"
                    mime_type = "application/json"
                    
                elif report_format == "CSV":
                    # CSVフォーマット
                    results_df = pd.DataFrame(result_data['results'])
                    csv_buffer = BytesIO()
                    results_df.to_csv(csv_buffer, index=False, encoding='utf-8')
                    report_content = csv_buffer.getvalue()
                    file_name = f"privacy_report_{result_data['id']}.csv"
                    mime_type = "text/csv"
                    
                elif report_format == "HTML":
                    # HTMLフォーマット
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>プライバシー評価レポート - {result_data['id']}</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 40px; }}
                            .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 10px; }}
                            .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #e8f5e9; border-radius: 5px; }}
                            table {{ border-collapse: collapse; width: 100%; }}
                            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                            th {{ background-color: #f2f2f2; }}
                        </style>
                    </head>
                    <body>
                        <div class="header">
                            <h1>プライバシー評価レポート</h1>
                            <p>評価ID: {result_data['id']}</p>
                            <p>評価日時: {result_data['timestamp']}</p>
                        </div>
                        
                        <h2>概要</h2>
                        <p>データセット: {result_data['dataset']}</p>
                        <p>攻撃タイプ: {result_data['attack_type']}</p>
                        
                        <h2>評価メトリクス</h2>
                        <div>
                    """
                    
                    # メトリクスの追加
                    avg_metrics = pd.DataFrame(result_data['results']).mean(numeric_only=True)
                    for metric, value in avg_metrics.items():
                        html_content += f'<div class="metric">{metric}: {value:.3f}</div>'
                    
                    html_content += """
                        </div>
                    </body>
                    </html>
                    """
                    
                    report_content = html_content
                    file_name = f"privacy_report_{result_data['id']}.html"
                    mime_type = "text/html"
                    
                else:
                    # PDF（仮実装 - 実際にはPDFライブラリが必要）
                    st.warning("PDF形式のレポート生成は現在開発中です。代わりにHTMLレポートを生成します。")
                    
                    # HTMLフォーマットで代用
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>プライバシー評価レポート - {result_data['id']}</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 40px; }}
                            .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 10px; }}
                            .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #e8f5e9; border-radius: 5px; }}
                            table {{ border-collapse: collapse; width: 100%; }}
                            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                            th {{ background-color: #f2f2f2; }}
                        </style>
                    </head>
                    <body>
                        <div class="header">
                            <h1>プライバシー評価レポート</h1>
                            <p>評価ID: {result_data['id']}</p>
                            <p>評価日時: {result_data['timestamp']}</p>
                        </div>
                    </body>
                    </html>
                    """
                    
                    report_content = html_content
                    file_name = f"privacy_report_{result_data['id']}.html"
                    mime_type = "text/html"
                
                # ダウンロードボタンの表示
                if isinstance(report_content, str):
                    report_bytes = report_content.encode('utf-8')
                else:
                    report_bytes = report_content
                
                b64 = base64.b64encode(report_bytes).decode()
                href = f'<a href="data:{mime_type};base64,{b64}" download="{file_name}">レポートをダウンロード</a>'
                st.markdown(href, unsafe_allow_html=True)
                
                st.success("レポートが正常に生成されました！")
                
            except Exception as e:
                st.error(f"レポート生成中にエラーが発生しました: {e}")

# サイドバー
st.sidebar.header("📊 レポート統計")

if result_files:
    # 評価の統計情報
    total_evaluations = len(result_files)
    
    # データセット別の評価数
    dataset_counts = {}
    attack_counts = {}
    
    for file in result_files:
        with open(file) as f:
            data = json.load(f)
            dataset = data['dataset']
            attack = data['attack_type']
            
            dataset_counts[dataset] = dataset_counts.get(dataset, 0) + 1
            attack_counts[attack] = attack_counts.get(attack, 0) + 1
    
    st.sidebar.metric("総評価数", total_evaluations)
    
    st.sidebar.subheader("データセット別評価数")
    for dataset, count in dataset_counts.items():
        st.sidebar.write(f"• {dataset}: {count}回")
    
    st.sidebar.subheader("攻撃タイプ別評価数")
    for attack, count in attack_counts.items():
        st.sidebar.write(f"• {attack}: {count}回")
    
    # 最新の評価
    latest_file = max(result_files, key=lambda f: f.stat().st_mtime)
    with open(latest_file) as f:
        latest_data = json.load(f)
    
    st.sidebar.subheader("最新の評価")
    st.sidebar.write(f"**データセット:** {latest_data['dataset']}")
    st.sidebar.write(f"**攻撃:** {latest_data['attack_type']}")
    st.sidebar.write(f"**日時:** {latest_data['timestamp'][:19]}")
    
    # 平均リスクレベル
    risk_levels = []
    for file in result_files:
        with open(file) as f:
            data = json.load(f)
            avg_accuracy = pd.DataFrame(data['results']).mean(numeric_only=True)['accuracy']
            if avg_accuracy > 0.9:
                risk_levels.append(3)  # 高
            elif avg_accuracy > 0.7:
                risk_levels.append(2)  # 中
            else:
                risk_levels.append(1)  # 低
    
    avg_risk = sum(risk_levels) / len(risk_levels) if risk_levels else 0
    
    if avg_risk > 2.5:
        risk_text = "高"
        risk_color = "🔴"
    elif avg_risk > 1.5:
        risk_text = "中"
        risk_color = "🟡"
    else:
        risk_text = "低"
        risk_color = "🟢"
    
    st.sidebar.subheader("平均リスクレベル")
    st.sidebar.write(f"{risk_color} {risk_text}")
    
else:
    st.sidebar.info("まだ評価結果がありません。")
