# app.py - 新浪财经7x24 智能看板（V2.0 含词云+情绪分析）
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import re

# ---------- 页面配置 ----------
st.set_page_config(page_title="📊 新浪财经7x24 智能看板", layout="wide")
st.title("📰 新浪财经 7x24 实时快讯 智能分析看板")
st.markdown("---")

# ---------- 数据库路径 ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'sina_news.db')

@st.cache_data(ttl=60)
def load_data():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT news_id, publish_time, content, view_num, tags, crawl_time FROM news ORDER BY publish_time DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

df = load_data()

# ---------- 侧边栏：系统状态（升级版） ----------
st.sidebar.header("📌 系统监控面板")

if df.empty:
    st.sidebar.error("暂无数据")
    st.stop()
else:
    # 1. 基础指标
    total_count = len(df)
    latest_time = df['publish_time'].max()
    earliest_time = df['publish_time'].min()
    
    # 2. 计算新增趋势（近1小时新增多少条）
    one_hour_ago = pd.Timestamp.now() - pd.Timedelta(hours=1)
    df['publish_time_dt'] = pd.to_datetime(df['publish_time'])
    new_in_hour = len(df[df['publish_time_dt'] >= one_hour_ago])
    
    # 3. 统计各标签数量
    tag_counts = df['tags'].value_counts().head(3)
    top_tag = tag_counts.index[0] if not tag_counts.empty else "暂无"
    
    # ---------- 显示区 ----------
    st.sidebar.metric("📰 总新闻数", f"{total_count} 条")
    st.sidebar.metric("🚀 近1小时新增", f"{new_in_hour} 条", delta=f"{new_in_hour} 条/小时")
    st.sidebar.metric("🕐 最新时间", latest_time)
    st.sidebar.metric("📅 最早时间", earliest_time)
    
    st.sidebar.markdown("---")
    
    # 4. 热门标签展示（用徽章样式）
    st.sidebar.subheader("🏷️ 热门标签 TOP3")
    for tag, cnt in tag_counts.items():
        if tag:
            st.sidebar.markdown(f"- **{tag}**：{cnt} 条")
    
    st.sidebar.markdown("---")
    
    # 5. 系统运行状态（模拟）
    st.sidebar.subheader("⚙️ 系统状态")
    st.sidebar.success("✅ 爬虫运行中")
    st.sidebar.info(f"📌 当前最热标签：**{top_tag}**")
    
    st.sidebar.markdown("---")
    st.sidebar.caption("🔄 数据每10分钟自动刷新")
    st.sidebar.caption("💡 提示：点击新闻ID可查看完整内容")

# ---------- 1. 数据表格（点击按钮查看完整内容 + 高亮） ----------
st.subheader("📋 最新快讯一览")

# 准备显示数据（截断长文本）
df_display = df.head(20).copy()
df_display['content_short'] = df_display['content'].apply(
    lambda x: x[:60] + '...' if len(str(x)) > 60 else x
)

# 显示表格
display_cols = ['publish_time', 'content_short', 'view_num', 'tags']
st.dataframe(
    df_display[display_cols],
    use_container_width=True,
    column_config={
        "publish_time": "发布时间",
        "content_short": "新闻内容（点击下方ID查看完整）",
        "view_num": "阅读量",
        "tags": "标签"
    },
    height=400,
    hide_index=True
)

# ---------- 【核心】点击按钮显示完整内容 + 高亮当前选中的按钮 ----------
st.markdown("#### 📖 点击下方新闻ID查看完整内容")

# 初始化 session_state（如果还没有 selected_news_id 这个变量）
if "selected_news_id" not in st.session_state:
    st.session_state.selected_news_id = None

# 每行放5个按钮
cols = st.columns(5)

for i, row in df_display.iterrows():
    news_id = row['news_id']
    with cols[i % 5]:
        # 【高亮逻辑】判断这个按钮是不是当前被选中的那个
        is_selected = (st.session_state.selected_news_id == news_id)
        
        if is_selected:
            # 如果是被选中的，显示为“已选中”状态（绿色高亮，不可点击）
            st.button(
                f"✅ {news_id}",
                key=f"selected_{news_id}",
                disabled=True,  # 禁止再次点击
                help="当前正在查看此新闻"
            )
        else:
            # 如果不是被选中的，显示为普通可点击按钮
            if st.button(
                f"📄 {news_id}",
                key=f"btn_{news_id}",
                help="点击查看完整内容"
            ):
                # 点击后更新 session_state，记录被选中的 ID
                st.session_state.selected_news_id = news_id
                # 注意：这里不需要重新运行，Streamlit 会自动 rerun

# ---------- 显示当前选中的完整内容 ----------
if st.session_state.selected_news_id is not None:
    # 从数据中找出被选中的那条新闻
    selected_row = df_display[df_display['news_id'] == st.session_state.selected_news_id]
    if not selected_row.empty:
        row = selected_row.iloc[0]
        st.markdown("---")
        st.markdown(f"##### 📖 完整内容（当前查看 ID: {row['news_id']}）")
        st.info(row['content'])
        st.caption(f"⏰ {row['publish_time']}  |  👁️ {row['view_num']}  |  🏷️ {row['tags']}")
    else:
        # 如果数据被刷新导致选中的 ID 不存在，重置状态
        st.session_state.selected_news_id = None
        st.rerun()
else:
    # 没有任何被选中的新闻时，显示轻量提示
    st.caption("💡 点击上方任意新闻ID按钮，即可查看完整内容")

# ---------- 2. 柱状图：24小时分布（不变） ----------
st.subheader("📈 新闻发布时段分布")
df['hour'] = pd.to_datetime(df['publish_time']).dt.hour
hourly_counts = df.groupby('hour').size().reset_index(name='count')
fig1 = px.bar(hourly_counts, x='hour', y='count', title='各小时新闻量', color='count', color_continuous_scale='Blues')
st.plotly_chart(fig1, use_container_width=True)
st.markdown("---")

# ---------- 3. 【新增】词云图（第2张图） ----------
st.subheader("☁️ 财经热点词云（近期高频词）")

# 清洗文本：把所有新闻拼在一起
text = ' '.join(df['content'].astype(str))
# 只保留中文、字母、数字，去掉标点和特殊符号
text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', ' ', text)

# 尝试导入词云库，如果没装或出错则用柱状图替代
try:
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt
    
    # 【关键修复】尝试查找系统自带的中文字体
    try:
        import os
        # 常见 Linux 中文字体路径
        font_paths = [
            '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            'simhei.ttf'  # Windows 字体，云端没有但保留备用
        ]
        font_path = None
        for fp in font_paths:
            if os.path.exists(fp):
                font_path = fp
                break
        # 如果没有找到任何字体，使用 None（可能显示方块，但不会报错）
        wordcloud = WordCloud(font_path=font_path, width=800, height=400, background_color='white', max_words=100).generate(text)
        
        # 显示词云
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)
    except (OSError, ValueError, Exception) as e:
        # 如果字体加载失败，降级为高频词柱状图
        st.warning("⚠️ 词云生成失败（可能缺少中文字体），自动切换到高频词柱状图展示。")
        # 使用 jieba 分词并统计词频
        import jieba
        from collections import Counter
        words = jieba.lcut(text)
        stopwords = set(['的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'])
        words = [w for w in words if len(w) > 1 and w not in stopwords]
        word_counts = Counter(words).most_common(20)
        word_df = pd.DataFrame(word_counts, columns=['词语', '频次'])
        fig2 = px.bar(word_df, x='词语', y='频次', title='新闻高频词汇 TOP 20', color='频次', color_continuous_scale='Viridis')
        st.plotly_chart(fig2, use_container_width=True)
        
except ImportError:
    # 如果 wordcloud 库没安装，降级为柱状图
    st.info("💡 检测到未安装 wordcloud，自动切换为高频词柱状图（效果一样好）")
    try:
        import jieba
        from collections import Counter
        words = jieba.lcut(text)
        stopwords = set(['的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'])
        words = [w for w in words if len(w) > 1 and w not in stopwords]
        word_counts = Counter(words).most_common(20)
        word_df = pd.DataFrame(word_counts, columns=['词语', '频次'])
        fig2 = px.bar(word_df, x='词语', y='频次', title='新闻高频词汇 TOP 20', color='频次', color_continuous_scale='Viridis')
        st.plotly_chart(fig2, use_container_width=True)
    except:
        st.warning("分词库未安装，跳过词云")
st.markdown("---")

# ---------- 4. 【新增】情绪分析折线图（第3张图） ----------
# ---------- 4. 【升级版】按标签筛选的情绪分析（新增下拉菜单） ----------
st.subheader("📉 财经新闻情绪指数趋势")

try:
    from snownlp import SnowNLP
    import numpy as np

    # 【新增】获取所有标签，生成下拉菜单
    tag_list = df['tags'].unique().tolist()
    # 过滤掉空标签，加上“全部”选项
    tag_options = ['全部'] + [tag for tag in tag_list if tag and tag != '']
    selected_tag = st.selectbox("🏷️ 按新闻类别筛选查看情绪", tag_options, index=0)

    # 根据选择过滤数据
    if selected_tag != '全部':
        df_filtered = df[df['tags'] == selected_tag].copy()
        st.caption(f"📌 当前筛选：**{selected_tag}**，共 {len(df_filtered)} 条新闻")
    else:
        df_filtered = df.copy()
        st.caption(f"📌 当前筛选：**全部类别**，共 {len(df_filtered)} 条新闻")

    # 如果筛选后没有数据，提示并跳过
    if df_filtered.empty:
        st.warning(f"当前类别 **{selected_tag}** 暂无数据，请选择其他类别")
    else:
        # 按时间排序（从旧到新）
        df_sorted = df_filtered.sort_values('publish_time')

        # 计算每条新闻的情绪分数
        sentiments = []
        for content in df_sorted['content']:
            try:
                score = SnowNLP(str(content)).sentiments
                sentiments.append(score)
            except:
                sentiments.append(0.5)
        
        df_sorted['sentiment'] = sentiments
        df_sorted['sentiment_ma'] = df_sorted['sentiment'].rolling(window=5, min_periods=1).mean()

        # 画折线图
        fig3 = px.line(
            df_sorted,
            x='publish_time',
            y='sentiment_ma',
            title=f'{selected_tag} 情绪指数趋势',
            labels={'publish_time': '时间', 'sentiment_ma': '情绪指数 (0=负面, 1=正面)'}
        )
        fig3.add_hline(y=0.5, line_dash="dash", line_color="grey", annotation_text="中性线")
        st.plotly_chart(fig3, use_container_width=True)

        # 整体结论
        avg_sentiment = df_sorted['sentiment'].mean()
        if avg_sentiment > 0.55:
            st.success(f"📊 **{selected_tag}** 整体情绪偏向 **乐观**（平均指数 {avg_sentiment:.2f}）")
        elif avg_sentiment < 0.45:
            st.error(f"📊 **{selected_tag}** 整体情绪偏向 **悲观**（平均指数 {avg_sentiment:.2f}）")
        else:
            st.info(f"📊 **{selected_tag}** 整体情绪 **中性**（平均指数 {avg_sentiment:.2f}）")

except ImportError:
    st.warning("未安装 snownlp 情感分析库，请运行 pip install snownlp")
    
st.markdown("---")
# ---------- 5. 【新增】阅读量深度分析 ----------
st.subheader("🔥 阅读量深度分析（市场关注度透视）")

# 先定义一个清洗阅读量的函数（把“4.14万 阅读”变成 41400）
def parse_view_num(v):
    import re
    if pd.isna(v):
        return 0
    v_str = str(v)
    if '万' in v_str:
        num = re.search(r'([\d.]+)', v_str)
        if num:
            return int(float(num.group(1)) * 10000)
    else:
        num = re.search(r'(\d+)', v_str)
        if num:
            return int(num.group(1))
    return 0

# 应用清洗，生成新列 view_int
df['view_int'] = df['view_num'].apply(parse_view_num)

# 过滤掉阅读量为0的异常数据
df_valid = df[df['view_int'] > 0].copy()

if not df_valid.empty:
    # 布局：分成两列并排显示
    col1, col2 = st.columns(2)
    
    with col1:
        # 图表 A：阅读量 TOP 10
        top10 = df_valid.nlargest(10, 'view_int')[['content', 'view_int', 'tags']]
        top10['content_short'] = top10['content'].apply(lambda x: x[:30] + '...' if len(str(x)) > 30 else x)
        fig_top = px.bar(
            top10,
            x='view_int',
            y='content_short',
            orientation='h',
            title='🏆 阅读量 TOP 10 新闻',
            labels={'view_int': '阅读量 (人次)','content_short': ''},
            color='view_int',
            color_continuous_scale='Reds'
        )
        fig_top.update_layout(height=400)
        st.plotly_chart(fig_top, use_container_width=True)
    
    with col2:
        # 图表 B：各类别平均阅读量
        avg_by_tag = df_valid.groupby('tags')['view_int'].mean().reset_index().sort_values('view_int', ascending=False)
        # 过滤掉空标签
        avg_by_tag = avg_by_tag[avg_by_tag['tags'] != '']
        fig_tag = px.bar(
            avg_by_tag,
            x='tags',
            y='view_int',
            title='📊 各类别新闻平均阅读量',
            labels={'tags': '新闻类别', 'view_int': '平均阅读量'},
            color='view_int',
            color_continuous_scale='Blues'
        )
        fig_tag.update_layout(height=400)
        st.plotly_chart(fig_tag, use_container_width=True)
    
    # 图表 C：阅读量 vs 发布时间（看哪个时段出爆款）
    st.markdown("---")
    st.subheader("⏰ 阅读量随发布时间的变化（寻找黄金时段）")
    
    # 提取小时
    df_valid['hour'] = pd.to_datetime(df_valid['publish_time']).dt.hour
    # 按小时计算平均阅读量
    hourly_view = df_valid.groupby('hour')['view_int'].mean().reset_index()
    
    fig_time = px.line(
        hourly_view,
        x='hour',
        y='view_int',
        title='各小时发布新闻的平均阅读量',
        labels={'hour': '小时 (0-23)', 'view_int': '平均阅读量'},
        markers=True
    )
    # 标注出最高点
    max_hour = hourly_view.loc[hourly_view['view_int'].idxmax()]
    fig_time.add_annotation(
        x=max_hour['hour'],
        y=max_hour['view_int'],
        text=f"峰值 {int(max_hour['view_int'])}",
        showarrow=True,
        arrowhead=1
    )
    st.plotly_chart(fig_time, use_container_width=True)
    
    # 自动生成一句数据洞察（根据当前数据）
    top_news = df_valid.nlargest(1, 'view_int')
    if not top_news.empty:
        top_title = top_news.iloc[0]['content'][:40] + '...'
        top_view = top_news.iloc[0]['view_int']
        st.success(f"💡 **洞察**：当前数据中，阅读量最高的新闻是 **「{top_title}」**，达到 **{top_view:,}** 人次。")
        
        # 判断哪个标签平均阅读最高
        if not avg_by_tag.empty:
            best_tag = avg_by_tag.iloc[0]
            st.info(f"💡 **洞察**：**「{best_tag['tags']}」** 类新闻的平均阅读量最高（{int(best_tag['view_int']):,} 人次），说明该类话题最容易吸引读者眼球。")
else:
    st.warning("暂无有效的阅读量数据，请等待爬虫积累更多数据。")
# ---------- 6. 【新增】关键词提取 + 主题聚类分析 ----------
st.subheader("🔍 关键词提取与主题聚类分析")

try:
    import jieba
    from collections import Counter
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.cluster import KMeans
    import numpy as np
    import re

    # ---------- 准备文本数据 ----------
    # 清洗文本：只保留中文、字母、数字
    def clean_text(text):
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', ' ', str(text))
        return text

    df['clean_content'] = df['content'].apply(clean_text)

    # 停用词表（过滤无意义词）
    stopwords = set([
        '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '它', '来', '与', '等', '或', '及', '为', '对', '从', '将', '把', '被', '给', '让', '而', '但', '却', '又', '还'
    ])

    # ---------- 1. 关键词提取（TOP 20 高频词） ----------
    all_words = []
    for text in df['clean_content']:
        words = jieba.lcut(text)
        words = [w for w in words if len(w) >= 2 and w not in stopwords]
        all_words.extend(words)

    word_counts = Counter(all_words).most_common(30)  # 取前30个
    keyword_df = pd.DataFrame(word_counts, columns=['关键词', '频次'])

    # 展示关键词表格
    col1, col2 = st.columns([2, 1])
    with col1:
        st.dataframe(
            keyword_df.head(20),
            use_container_width=True,
            column_config={
                "关键词": "高频词",
                "频次": st.column_config.NumberColumn("出现次数", format="%d")
            },
            height=300
        )
        st.caption(f"📊 基于 {len(df)} 条新闻提取的 TOP 20 高频关键词")

    with col2:
        # 显示词频统计摘要
        st.metric("📝 总词数", f"{len(all_words):,}")
        st.metric("🏷️ 不同词数", f"{len(word_counts):,}")
        st.metric("🔥 最热词", f"{word_counts[0][0]} ({word_counts[0][1]}次)")

    st.markdown("---")

    # ---------- 2. 主题聚类（将新闻分成 6 类） ----------
    st.subheader("📂 新闻主题自动聚类")

    # 如果新闻条数少于 20 条，跳过聚类（数据太少没有意义）
    if len(df) < 20:
        st.warning("当前数据量较少（少于20条），聚类结果可能不够稳定。建议积累更多数据后再尝试。")
    else:
        # 向量化文本
        vectorizer = CountVectorizer(max_features=100, stop_words=list(stopwords))
        X = vectorizer.fit_transform(df['clean_content'])

        # 【修改】KMeans 聚类（最多 6 类，最少 2 类，根据数据量自动调整）
        n_clusters = min(6, max(2, len(df) // 5))  # 这里改成了 6
        if n_clusters < 2:
            n_clusters = 2

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        df['cluster'] = kmeans.fit_predict(X)

        # 提取每个类别的核心关键词
        feature_names = vectorizer.get_feature_names_out()
        cluster_keywords = {}
        cluster_sizes = {}

        for i in range(n_clusters):
            # 找到属于该类别的所有新闻
            cluster_indices = df[df['cluster'] == i].index
            cluster_sizes[i] = len(cluster_indices)

            # 计算该类别中每个词的平均出现次数
            cluster_vectors = X[cluster_indices].toarray()
            if len(cluster_vectors) == 0:
                continue
            mean_vector = np.mean(cluster_vectors, axis=0)
            # 取出权重最高的前5个词
            top_indices = np.argsort(mean_vector)[-5:][::-1]
            keywords = [feature_names[idx] for idx in top_indices if mean_vector[idx] > 0]
            cluster_keywords[i] = keywords if keywords else ["无显著关键词"]

        # 显示聚类结果
        st.markdown(f"**将 {len(df)} 条新闻自动划分为 {n_clusters} 个主题类别：**")

        # 用列布局展示每个类别（每行显示3个，动态适应）
        cols = st.columns(min(n_clusters, 3))
        for i in range(n_clusters):
            with cols[i % 3]:
                # 获取该类别的前3条代表性新闻
                sample_news = df[df['cluster'] == i]['content'].head(3).tolist()
                sample_text = "、".join([s[:20] + "..." for s in sample_news]) if sample_news else "暂无"

                st.markdown(f"""
                <div style="background-color:#f0f2f6; padding:10px; border-radius:8px; margin-bottom:10px;">
                    <b>📂 主题 {i+1}</b><br>
                    <b>🔑 关键词：</b>{', '.join(cluster_keywords[i][:5])}<br>
                    <b>📄 条数：</b>{cluster_sizes[i]} 条<br>
                    <b>📰 示例：</b>{sample_text}
                </div>
                """, unsafe_allow_html=True)

        # 显示聚类分布的饼图（图例显示为“主题1”、“主题2”……）
        cluster_dist = df['cluster'].value_counts().reset_index()
        cluster_dist.columns = ['类别', '数量']
        # 新增一列“主题”用于图例显示
        cluster_dist['主题'] = cluster_dist['类别'].apply(lambda x: f'主题 {x+1}')

        fig_cluster = px.pie(
            cluster_dist,
            values='数量',
            names='主题',  # 用新列作为图例
            title='新闻主题分布',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_cluster, use_container_width=True)

        # 一条简短洞察（动态显示最大类别）
        largest_cluster = cluster_dist.iloc[0]['类别']
        largest_topic = f'主题 {largest_cluster+1}'
        st.caption(f"💡 当前数据中，**{largest_topic}** 的新闻数量最多（{cluster_dist.iloc[0]['数量']} 条），说明这是近期报道的焦点方向。")
except ImportError as e:
    st.warning(f"缺少必要的库，请运行 `pip install scikit-learn` 安装依赖。错误信息：{e}")
except Exception as e:
    st.error(f"聚类分析出错：{e}")
st.caption(f"📅 数据范围：{df['publish_time'].min()} 至 {df['publish_time'].max()} | 数据来源：新浪财经")