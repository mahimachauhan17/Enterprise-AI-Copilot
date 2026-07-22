import pandas as pd
import io
import base64
import matplotlib
matplotlib.use('Agg') # required for headless backend
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from backend.rag.intent_parser import parse_analytics_intent
from backend.utils.logger import get_logger

logger = get_logger(__name__)

sns.set_theme(style="whitegrid")

def generate_chart_base64() -> str:
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode('utf-8')
    return f"![Chart](data:image/png;base64,{img_b64})"

def get_executive_summary(df: pd.DataFrame) -> str:
    rows, cols = df.shape
    missing_vals = df.isnull().sum().sum()
    num_cols = df.select_dtypes(include=['number']).columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    md = [
        "### 📊 Executive Summary\n",
        f"- **Total Rows**: {rows}",
        f"- **Total Columns**: {cols}",
        f"- **Missing Values**: {missing_vals}\n",
        "#### 🔢 Numerical Statistics\n"
    ]
    if num_cols:
        stats = df[num_cols].describe().round(2).to_markdown()
        md.append(f"{stats}\n")
    
    chart_md = ""
    if num_cols:
        plt.figure(figsize=(8, 4))
        sns.histplot(df[num_cols[0]].dropna(), kde=True, color='skyblue')
        plt.title(f'Distribution of {num_cols[0]}')
        chart_md += generate_chart_base64() + "\n\n"
    
    if cat_cols and len(df[cat_cols[0]].unique()) <= 10:
        plt.figure(figsize=(8, 4))
        df[cat_cols[0]].value_counts().plot(kind='bar', color='coral')
        plt.title(f'Top categories in {cat_cols[0]}')
        chart_md += generate_chart_base64() + "\n\n"
    
    if len(num_cols) >= 2:
        plt.figure(figsize=(8, 6))
        sns.heatmap(df[num_cols].corr(), annot=True, cmap='coolwarm', fmt='.2f')
        plt.title('Correlation Heatmap')
        chart_md += generate_chart_base64() + "\n\n"

    md.append("#### 📈 Visualizations\n")
    md.append(chart_md if chart_md else "No suitable visualizations generated.")
    
    md.append("\n#### 💡 Recommendations & Business Insights\n")
    md.append("- Regularly monitor missing values to maintain data quality.")
    if num_cols:
         md.append(f"- Analyze outliers in '{num_cols[0]}' to identify anomalies.")
    
    return "\n".join(md)

def generate_trend_chart(df: pd.DataFrame, x_col: str, y_col: str) -> str:
    plt.figure(figsize=(10, 5))
    if x_col in df.columns and y_col in df.columns:
        sns.lineplot(data=df, x=x_col, y=y_col, marker='o')
        plt.title(f'Trend of {y_col} over {x_col}')
        plt.xticks(rotation=45)
    else:
        return f"Could not find columns {x_col} or {y_col} for trend analysis."
    return generate_chart_base64()

def generate_scatter_chart(df: pd.DataFrame, x_col: str, y_col: str) -> str:
    plt.figure(figsize=(8, 6))
    if x_col in df.columns and y_col in df.columns:
        sns.scatterplot(data=df, x=x_col, y=y_col, alpha=0.7)
        plt.title(f'{y_col} vs {x_col}')
    else:
        return f"Could not find columns {x_col} or {y_col}."
    return generate_chart_base64()

def run_analytics_query(file_path: str, query: str) -> str:
    ext = Path(file_path).suffix.lower()
    try:
        if ext == ".csv":
            df = pd.read_csv(file_path)
        elif ext == ".xlsx":
            df = pd.read_excel(file_path)
        else:
            return None # Not a dataset
    except Exception as e:
        logger.error(f"Dataset load error: {e}")
        return f"Error loading dataset: {str(e)}"
        
    intent_data = parse_analytics_intent(query, list(df.columns))
    intent = intent_data.get("intent", "UNKNOWN")
    x_col = intent_data.get("x_col")
    y_col = intent_data.get("y_col")
    
    if intent == "EXECUTIVE_SUMMARY":
        return get_executive_summary(df)
    elif intent == "TREND_ANALYSIS" and x_col and y_col:
        return generate_trend_chart(df, x_col, y_col)
    elif intent == "CORRELATION" and x_col and y_col:
        return generate_scatter_chart(df, x_col, y_col)
    
    # Fallback to executive summary if query matches analytics but lacks details
    fallback_keywords = ["dashboard", "analytic", "analysis", "anaysis", "summary", "graph", "chart", "plot", "data", "dataset"]
    if intent != "UNKNOWN" or any(kw in query.lower() for kw in fallback_keywords):
        return get_executive_summary(df)
        
    return None # Return None if not an analytics query, so RAG can handle it
