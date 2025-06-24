import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

st.set_page_config(page_title="교우 관계 시각화", layout="wide")

st.title("학생 교우 관계 네트워크 시각화")
st.write("구글폼으로 조사한 교우관계 csv 파일을 업로드하세요.")

uploaded_file = st.file_uploader("CSV 파일 업로드", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.subheader("업로드한 데이터 미리보기")
    st.dataframe(df)
    
    # 네트워크 그래프 생성
    G = nx.DiGraph()
    for idx, row in df.iterrows():
        source = row[0]
        friends = row[1:].dropna().tolist()
        for friend in friends:
            if friend.strip() != "":
                G.add_edge(source, friend)

    # 네트워크 그래프 시각화
    st.subheader("교우 관계 네트워크 그래프")
    fig, ax = plt.subplots(figsize=(8, 8))
    pos = nx.spring_layout(G, seed=42)
    nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=2000, font_size=12, font_weight='bold', arrowstyle='->', arrowsize=20)
    plt.title("학생 교우 관계 네트워크")
    st.pyplot(fig)
    
    # 추가로 중심성 등 분석 자료 제공 (선택)
    st.subheader("학생별 연결 정도(친구 많이 언급된 순)")
    centrality = nx.in_degree_centrality(G)
    centrality_sorted = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
    st.write(pd.DataFrame(centrality_sorted, columns=["학생", "친구로 언급된 정도(비율)"]))