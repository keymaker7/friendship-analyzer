import pandas as pd
import networkx as nx
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import re
import math
try:
    from sklearn.cluster import SpectralClustering
    import community as community_louvain
    HAS_COMMUNITY = True
except ImportError:
    HAS_COMMUNITY = False

class FriendshipAnalyzer:
    def __init__(self):
        self.data = None
        self.graph = None
        self.students = []
        
    def load_data(self, df):
        """정보 불러오기 및 정리"""
        self.data = df.copy()
        
        # 학생 이름 찾기 (이름 컬럼에서)
        name_column = None
        for col in df.columns:
            if '이름' in col or 'name' in col.lower():
                name_column = col
                break
        
        if name_column:
            self.students = df[name_column].dropna().unique().tolist()
        else:
            # 이름 컬럼이 없으면 두 번째 컬럼을 이름으로 가정
            self.students = df.iloc[:, 1].dropna().unique().tolist()
            
        return True
    
    def parse_friends_list(self, text):
        """친구 목록 글자를 리스트로 바꾸기"""
        if pd.isna(text) or text == "":
            return []
        
        # 쉼표, 세미콜론, 슬래시로 분리
        friends = re.split(r'[,;/\n]', str(text))
        friends = [f.strip() for f in friends if f.strip()]
        
        # 우리 반 학생 이름만 골라내기
        valid_friends = []
        for friend in friends:
            # 학생 명단에 있는 이름과 맞는지 확인
            for student in self.students:
                if friend in student or student in friend:
                    valid_friends.append(student)
                    break
        
        return list(set(valid_friends))  # 중복 제거
    
    def build_relationship_graph(self):
        """친구 관계 그래프 만들기"""
        self.graph = nx.DiGraph()
        
        # 모든 학생을 점으로 추가
        for student in self.students:
            self.graph.add_node(student)
        
        # 관계별 점수 정하기
        weights = {
            '가장 친한': 5,
            '자주 대화': 3,
            '도움 요청': 4,
            '도와준': 3,
            '갈등': -2,
            '친해지고 싶은': 2
        }
        
        for idx, row in self.data.iterrows():
            student_name = None
            
            # 학생 이름 찾기
            for col in self.data.columns:
                if '이름' in col or 'name' in col.lower():
                    student_name = row[col]
                    break
            
            if not student_name:
                student_name = row.iloc[1]  # 두 번째 컬럼을 이름으로 가정
            
            if student_name not in self.students:
                continue
            
            # 각 관계 종류별로 선 추가
            for col in self.data.columns:
                weight = 1
                if '가장 친한' in col:
                    weight = weights['가장 친한']
                elif '자주 대화' in col:
                    weight = weights['자주 대화']
                elif '도움을 요청' in col:
                    weight = weights['도움 요청']
                elif '도와준' in col:
                    weight = weights['도와준']
                elif '갈등' in col:
                    weight = weights['갈등']
                elif '친해지고 싶은' in col:
                    weight = weights['친해지고 싶은']
                else:
                    continue
                
                friends = self.parse_friends_list(row[col])
                for friend in friends:
                    if friend in self.students and friend != student_name:
                        # 이미 연결이 있으면 점수 더하기
                        if self.graph.has_edge(student_name, friend):
                            current_weight = self.graph[student_name][friend].get('weight', 0)
                            self.graph[student_name][friend]['weight'] = current_weight + weight
                        else:
                            self.graph.add_edge(student_name, friend, weight=weight)
        
        return self.graph
    
    def create_network_visualization(self):
        """네트워크형 인물 관계도 만들기 (클릭 인터랙션 포함)"""
        if self.graph is None:
            self.build_relationship_graph()
        
        # 무방향 그래프로 변환하여 레이아웃 계산
        undirected_graph = self.graph.to_undirected()
        
        # 봄-전기 모델로 위치 계산 (더 예쁘게)
        pos = nx.spring_layout(undirected_graph, k=2, iterations=100, seed=42)
        
        # 연결선 그리기
        edge_traces = []
        
        for edge in self.graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            
            weight = self.graph[edge[0]][edge[1]].get('weight', 1)
            
            # 관계별로 다른 색깔과 두께
            if weight > 4:  # 가장 친한 관계
                color = 'red'
                width = 4
            elif weight > 2:  # 친한 관계
                color = 'blue' 
                width = 3
            elif weight > 0:  # 일반 관계
                color = 'gray'
                width = 2
            else:  # 안 좋은 관계
                color = 'orange'
                width = 2
            
            edge_trace = go.Scatter(
                x=[x0, x1, None], 
                y=[y0, y1, None],
                mode='lines',
                line=dict(width=width, color=color),
                hoverinfo='none',
                showlegend=False,
                visible=True,
                # 각 선에 고유 이름 추가 (클릭 기능용)
                name=f"{edge[0]}-{edge[1]}"
            )
            edge_traces.append(edge_trace)
        
        # 학생들 점 그리기
        node_x = []
        node_y = []
        node_text = []
        node_info = []
        node_sizes = []
        node_colors = []
        
        for node in self.graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
            
            # 인기도 계산
            popularity = self.graph.in_degree(node)
            sociability = self.graph.out_degree(node)
            
            node_info.append(f'{node}<br>'
                           f'인기도: {popularity}명이 언급<br>'
                           f'사교성: {sociability}명 언급함<br>'
                           f'💡 클릭하면 이 친구만 보여요!')
            
            # 크기와 색깔 설정
            size = max(30, popularity * 8 + 30)
            node_sizes.append(size)
            node_colors.append(popularity)
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=node_text,
            textposition="middle center",
            textfont=dict(color='black', size=12, family="Arial Black"),  # 글자 색상 검은색으로 변경
            hovertext=node_info,
            hoverinfo='text',
            marker=dict(
                size=node_sizes,
                color=node_colors,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="인기도"),
                line=dict(width=2, color='black')  # 테두리도 검은색
            ),
            showlegend=False
        )
        
        # 그래프 만들기
        fig = go.Figure(data=edge_traces + [node_trace])
        
        # 클릭 인터랙션을 위한 JavaScript 코드 추가
        fig.update_layout(
            title={
                'text': '🕸️ 우리 반 친구 관계망<br><sub>💡 학생 이름을 클릭하면 그 친구만 보여요!</sub>',
                'font': {'color': 'black', 'size': 20}
            },
            showlegend=False,
            hovermode='closest',
            margin=dict(b=60,l=5,r=5,t=80),
            annotations=[
                dict(
                    text="💗빨간선: 가장친한친구 💙파란선: 친한친구 ⚫회색선: 일반친구 🧡주황선: 갈등",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.5, y=-0.05,
                    xanchor="center", yanchor="top",
                    font=dict(size=12, color='black')
                )
            ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        return fig
    
    def create_heatmap_network(self):
        """인기도 히트맵 스타일 네트워크"""
        if self.graph is None:
            self.build_relationship_graph()
        
        undirected_graph = self.graph.to_undirected()
        pos = nx.spring_layout(undirected_graph, k=2, iterations=100, seed=42)
        
        # 연결선
        edge_x = []
        edge_y = []
        
        for edge in self.graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color='lightgray'),
            hoverinfo='none',
            mode='lines',
            showlegend=False
        )
        
        # 노드 (인기도 기반 색상)
        node_x = []
        node_y = []
        node_text = []
        node_color = []
        
        for node in self.graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
            popularity = self.graph.in_degree(node)
            node_color.append(popularity)
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=node_text,
            textposition="middle center",
            textfont=dict(color='white', size=12, family="Arial Black"),
            marker=dict(
                size=40,
                color=node_color,
                colorscale='Hot',
                showscale=True,
                colorbar=dict(title="인기도"),
                line=dict(width=2, color='black')
            ),
            showlegend=False
        )
        
        fig = go.Figure(data=[edge_trace, node_trace])
        fig.update_layout(
            title={'text': '🌡️ 인기도 히트맵 네트워크', 'font': {'color': 'black', 'size': 20}},
            showlegend=False,
            hovermode='closest',
            margin=dict(b=60,l=5,r=5,t=60),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        return fig
    
    def create_group_colored_network(self):
        """그룹별 색상 네트워크"""
        if self.graph is None:
            self.build_relationship_graph()
        
        undirected_graph = self.graph.to_undirected()
        
        if HAS_COMMUNITY and len(undirected_graph.nodes()) > 0:
            try:
                partition = community_louvain.best_partition(undirected_graph)
            except:
                partition = {student: i % 5 for i, student in enumerate(self.students)}
        else:
            partition = {student: i % 5 for i, student in enumerate(self.students)}
        
        pos = nx.spring_layout(undirected_graph, k=2, iterations=100, seed=42)
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
        
        traces = []
        
        # 연결선
        edge_x = []
        edge_y = []
        
        for edge in self.graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color='lightgray'),
            hoverinfo='none',
            mode='lines',
            showlegend=False
        )
        traces.append(edge_trace)
        
        # 그룹별 노드
        groups = {}
        for student, group in partition.items():
            if group not in groups:
                groups[group] = []
            groups[group].append(student)
        
        for group_idx, students in groups.items():
            node_x = []
            node_y = []
            node_text = []
            
            for student in students:
                if student in pos:
                    x, y = pos[student]
                    node_x.append(x)
                    node_y.append(y)
                    node_text.append(student)
            
            if node_x:
                color = colors[group_idx % len(colors)]
                node_trace = go.Scatter(
                    x=node_x, y=node_y,
                    mode='markers+text',
                    text=node_text,
                    textposition="middle center",
                    textfont=dict(color='black', size=11, family="Arial Black"),
                    name=f'그룹 {group_idx + 1}',
                    marker=dict(
                        size=35,
                        color=color,
                        line=dict(width=2, color='white')
                    )
                )
                traces.append(node_trace)
        
        fig = go.Figure(data=traces)
        fig.update_layout(
            title={'text': '🎨 그룹별 색상 네트워크', 'font': {'color': 'black', 'size': 20}},
            showlegend=True,
            hovermode='closest',
            margin=dict(b=60,l=5,r=5,t=60),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        return fig
    
    def create_3d_network(self):
        """3D 네트워크"""
        if self.graph is None:
            self.build_relationship_graph()
        
        undirected_graph = self.graph.to_undirected()
        pos_2d = nx.spring_layout(undirected_graph, k=2, iterations=100, seed=42)
        
        # 3D 좌표 생성
        pos_3d = {}
        for node, (x, y) in pos_2d.items():
            z = self.graph.in_degree(node) * 0.5
            pos_3d[node] = (x, y, z)
        
        # 연결선
        edge_x = []
        edge_y = []
        edge_z = []
        
        for edge in self.graph.edges():
            x0, y0, z0 = pos_3d[edge[0]]
            x1, y1, z1 = pos_3d[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_z.extend([z0, z1, None])
        
        edge_trace = go.Scatter3d(
            x=edge_x, y=edge_y, z=edge_z,
            mode='lines',
            line=dict(color='lightgray', width=2),
            hoverinfo='none',
            showlegend=False
        )
        
        # 노드
        node_x = []
        node_y = []
        node_z = []
        node_text = []
        node_color = []
        
        for node in self.graph.nodes():
            x, y, z = pos_3d[node]
            node_x.append(x)
            node_y.append(y)
            node_z.append(z)
            node_text.append(node)
            node_color.append(self.graph.in_degree(node))
        
        node_trace = go.Scatter3d(
            x=node_x, y=node_y, z=node_z,
            mode='markers+text',
            text=node_text,
            textposition="middle center",
            marker=dict(
                size=8,
                color=node_color,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="인기도"),
                line=dict(width=2, color='black')
            ),
            showlegend=False
        )
        
        fig = go.Figure(data=[edge_trace, node_trace])
        fig.update_layout(
            title={'text': '📊 3D 네트워크 (입체적)', 'font': {'color': 'black', 'size': 20}},
            showlegend=False,
            scene=dict(
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                zaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title="인기도"),
                bgcolor='white'
            ),
            margin=dict(b=60,l=5,r=5,t=60),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        return fig
    
    def create_force_directed_network(self):
        """힘-기반 레이아웃 네트워크"""
        if self.graph is None:
            self.build_relationship_graph()
        
        undirected_graph = self.graph.to_undirected()
        try:
            pos = nx.kamada_kawai_layout(undirected_graph)
        except:
            pos = nx.spring_layout(undirected_graph, k=3, iterations=200, seed=42)
        
        # 연결선
        edge_traces = []
        
        for edge in self.graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            
            weight = self.graph[edge[0]][edge[1]].get('weight', 1)
            
            if weight > 4:
                color = 'red'
                width = 3
            elif weight > 2:
                color = 'blue'
                width = 2
            elif weight > 0:
                color = 'green'
                width = 1
            else:
                color = 'orange'
                width = 1
            
            edge_trace = go.Scatter(
                x=[x0, x1, None], 
                y=[y0, y1, None],
                mode='lines',
                line=dict(width=width, color=color),
                hoverinfo='none',
                showlegend=False
            )
            edge_traces.append(edge_trace)
        
        # 노드
        node_x = []
        node_y = []
        node_text = []
        node_sizes = []
        
        for node in self.graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
            
            degree = undirected_graph.degree(node)
            node_sizes.append(max(20, degree * 5 + 20))
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=node_text,
            textposition="middle center",
            textfont=dict(color='black', size=10, family="Arial Black"),
            marker=dict(
                size=node_sizes,
                color='lightblue',
                line=dict(width=2, color='darkblue')
            ),
            showlegend=False
        )
        
        fig = go.Figure(data=edge_traces + [node_trace])
        fig.update_layout(
            title={'text': '⚡ 힘-기반 레이아웃 네트워크', 'font': {'color': 'black', 'size': 20}},
            showlegend=False,
            hovermode='closest',
            margin=dict(b=60,l=5,r=5,t=60),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        return fig
    
    def create_interactive_relationship_map(self):
        """상호작용 관계도 만들기"""
        if self.graph is None:
            self.build_relationship_graph()
        
        # 상호 연결된 관계만 찾기
        mutual_edges = []
        for edge in self.graph.edges():
            if self.graph.has_edge(edge[1], edge[0]):
                if edge[0] < edge[1]:  # 중복 방지
                    weight1 = self.graph[edge[0]][edge[1]].get('weight', 1)
                    weight2 = self.graph[edge[1]][edge[0]].get('weight', 1)
                    mutual_edges.append((edge[0], edge[1], weight1 + weight2))
        
        # 새로운 무방향 그래프 만들기
        mutual_graph = nx.Graph()
        for student in self.students:
            mutual_graph.add_node(student)
        
        for edge in mutual_edges:
            mutual_graph.add_edge(edge[0], edge[1], weight=edge[2])
        
        # 위치 계산
        pos = nx.spring_layout(mutual_graph, k=3, iterations=150, seed=42)
        
        # 연결선 그리기
        edge_x = []
        edge_y = []
        
        for edge in mutual_graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=4, color='lightblue'),
            hoverinfo='none',
            mode='lines',
            showlegend=False
        )
        
        # 학생들 점 그리기
        node_x = []
        node_y = []
        node_text = []
        node_info = []
        
        for node in mutual_graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
            
            mutual_friends = mutual_graph.degree(node)
            node_info.append(f'{node}<br>서로 친한 친구: {mutual_friends}명')
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=node_text,
            textposition="middle center",
            textfont=dict(color='black', size=12, family="Arial Black"),  # 글자 색상 검은색
            hovertext=node_info,
            hoverinfo='text',
            marker=dict(
                size=50,
                color='lightgreen',
                line=dict(width=3, color='darkgreen')
            ),
            showlegend=False
        )
        
        fig = go.Figure(data=[edge_trace, node_trace])
        fig.update_layout(
            title={
                'text': '🤝 서로 친한 친구들 관계도',
                'font': {'color': 'black', 'size': 20}
            },
            showlegend=False,
            hovermode='closest',
            margin=dict(b=60,l=5,r=5,t=60),
            annotations=[
                dict(
                    text="💙파란 선: 서로 친한 관계 💚초록 동그라미: 학생들",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.5, y=-0.05,
                    xanchor="center", yanchor="top",
                    font=dict(size=12, color='black')
                )
            ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        return fig
    
    def create_circular_group_visualization(self):
        """집단별 컬러 구분이 있는 순환형 관계도 만들기"""
        if self.graph is None:
            self.build_relationship_graph()
        
        # 무방향 그래프로 변환
        undirected_graph = self.graph.to_undirected()
        
        # 그룹 찾기 (커뮤니티 탐지)
        if HAS_COMMUNITY and len(undirected_graph.nodes()) > 0:
            try:
                partition = community_louvain.best_partition(undirected_graph)
            except:
                # 에러가 나면 간단하게 그룹 나누기
                partition = {}
                for i, student in enumerate(self.students):
                    partition[student] = i % 5  # 5개 그룹으로 나누기
        else:
            # 커뮤니티 패키지가 없으면 간단하게 나누기
            partition = {}
            for i, student in enumerate(self.students):
                partition[student] = i % 5  # 5개 그룹으로 나누기
        
        # 예쁜 색깔들 (첨부 이미지 참고)
        colors = [
            '#FF6B6B',  # 빨간색
            '#4ECDC4',  # 청록색
            '#45B7D1',  # 파란색
            '#FFA07A',  # 주황색
            '#98D8C8',  # 민트색
            '#F7DC6F',  # 노란색
            '#BB8FCE',  # 보라색
            '#85C1E9'   # 하늘색
        ]
        
        # 그룹별로 학생들 정리
        groups = {}
        for student, group in partition.items():
            if group not in groups:
                groups[group] = []
            groups[group].append(student)
        
        # 각 그룹을 원의 다른 부분에 배치 (첨부 이미지처럼)
        pos = {}
        group_centers = {}
        
        n_groups = len(groups)
        if n_groups == 0:
            n_groups = 1
            
        for group_idx, (group, students) in enumerate(groups.items()):
            # 그룹 중심 위치 계산
            group_angle = 2 * math.pi * group_idx / n_groups
            group_radius = 2.5  # 그룹 간 거리
            
            center_x = group_radius * math.cos(group_angle)
            center_y = group_radius * math.sin(group_angle)
            group_centers[group] = (center_x, center_y)
            
            # 그룹 내 학생들을 작은 원으로 배치
            n_students = len(students)
            if n_students == 0:
                continue
                
            if n_students == 1:
                pos[students[0]] = (center_x, center_y)
            else:
                inner_radius = 0.8  # 그룹 내 반지름
                for student_idx, student in enumerate(students):
                    student_angle = 2 * math.pi * student_idx / n_students
                    x = center_x + inner_radius * math.cos(student_angle)
                    y = center_y + inner_radius * math.sin(student_angle)
                    pos[student] = (x, y)
        
        # 연결선 그리기
        edge_x = []
        edge_y = []
        
        for edge in self.graph.edges():
            if edge[0] in pos and edge[1] in pos:
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color='lightgray'),
            hoverinfo='none',
            mode='lines',
            showlegend=False
        )
        
        # 그룹별로 학생들 점 그리기
        traces = [edge_trace]
        
        for group_idx, (group, students) in enumerate(groups.items()):
            node_x = []
            node_y = []
            node_text = []
            node_info = []
            
            for student in students:
                if student in pos:
                    x, y = pos[student]
                    node_x.append(x)
                    node_y.append(y)
                    node_text.append(student)
                    
                    # 그룹 정보
                    group_members = [s for s in students if s != student]
                    if group_members:
                        group_member_text = ', '.join(group_members[:3])  # 최대 3명만 표시
                        if len(group_members) > 3:
                            group_member_text += f" 외 {len(group_members)-3}명"
                        node_info.append(f'{student}<br>'
                                       f'🌈 그룹 {group + 1}번<br>'
                                       f'👫 같은 그룹: {group_member_text}')
                    else:
                        node_info.append(f'{student}<br>🌈 그룹 {group + 1}번')
            
            if node_x:  # 학생이 있는 경우만
                color = colors[group_idx % len(colors)]
                
                node_trace = go.Scatter(
                    x=node_x, y=node_y,
                    mode='markers+text',
                    text=node_text,
                    textposition="middle center",
                    textfont=dict(color='black', size=11, family="Arial Black"),  # 글자 색상 검은색
                    hovertext=node_info,
                    hoverinfo='text',
                    name=f'그룹 {group + 1}',
                    marker=dict(
                        size=40,
                        color=color,
                        line=dict(width=3, color='white')
                    )
                )
                
                traces.append(node_trace)
        
        fig = go.Figure(data=traces)
        fig.update_layout(
            title={
                'text': '🌈 친구 그룹별 원형 관계도',
                'font': {'color': 'black', 'size': 20}
            },
            showlegend=True,
            hovermode='closest',
            margin=dict(b=60,l=5,r=5,t=60),
            annotations=[
                dict(
                    text="🎨 같은 색깔 = 친한 친구 그룹, ⭕ 원 모양으로 배치",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.5, y=-0.05,
                    xanchor="center", yanchor="top",
                    font=dict(size=12, color='black')
                )
            ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        return fig
    
    def get_individual_student_analysis(self, student_name):
        """개별 학생 분석 결과"""
        if self.graph is None:
            self.build_relationship_graph()
        
        if student_name not in self.students:
            return None
        
        analysis = {}
        
        # 긍정적인 관계 (weight > 0)
        positive_friends = []
        negative_friends = []
        
        # 나가는 관계 (이 학생이 언급한 친구들)
        for neighbor in self.graph.neighbors(student_name):
            weight = self.graph[student_name][neighbor].get('weight', 1)
            if weight > 0:
                positive_friends.append((neighbor, weight))
            else:
                negative_friends.append((neighbor, abs(weight)))
        
        # 들어오는 관계 (이 학생을 언급한 친구들)
        mentioned_by = []
        for node in self.graph.nodes():
            if self.graph.has_edge(node, student_name):
                weight = self.graph[node][student_name].get('weight', 1)
                mentioned_by.append((node, weight))
        
        # 인기도 계산
        popularity_score = self.graph.in_degree(student_name)
        sociability_score = self.graph.out_degree(student_name)
        
        # 상호 관계 (서로 언급한 경우)
        mutual_friends = []
        for friend, _ in positive_friends:
            if self.graph.has_edge(friend, student_name):
                mutual_friends.append(friend)
        
        analysis = {
            'positive_friends': sorted(positive_friends, key=lambda x: x[1], reverse=True),
            'negative_friends': sorted(negative_friends, key=lambda x: x[1], reverse=True),
            'mentioned_by': sorted(mentioned_by, key=lambda x: x[1], reverse=True),
            'mutual_friends': mutual_friends,
            'popularity_score': popularity_score,
            'sociability_score': sociability_score,
            'is_popular': popularity_score >= len(self.students) * 0.3,  # 30% 이상이 언급하면 인기
            'is_isolated': popularity_score <= 1,  # 1명 이하가 언급하면 고립
            'is_low_mentioned': popularity_score <= 2  # 2명 이하가 언급
        }
        
        return analysis
    
    def get_class_overall_analysis(self):
        """반 전체 분석"""
        if self.graph is None:
            self.build_relationship_graph()
        
        # 모든 학생별 분석
        all_students_analysis = {}
        for student in self.students:
            all_students_analysis[student] = self.get_individual_student_analysis(student)
        
        # 인기 학생들 (인기도 상위)
        popularity_ranking = [(student, analysis['popularity_score']) 
                            for student, analysis in all_students_analysis.items()]
        popularity_ranking.sort(key=lambda x: x[1], reverse=True)
        
        # 고립된 학생들
        isolated_students = [student for student, analysis in all_students_analysis.items() 
                           if analysis['is_isolated']]
        
        # 적게 선택받은 학생들 (2명 이하)
        low_mentioned_students = [student for student, analysis in all_students_analysis.items() 
                                if analysis['is_low_mentioned'] and not analysis['is_isolated']]
        
        return {
            'popularity_ranking': popularity_ranking[:5],  # 상위 5명
            'isolated_students': isolated_students,
            'low_mentioned_students': low_mentioned_students,
            'total_students': len(self.students),
            'total_connections': self.graph.number_of_edges(),
            'all_students_analysis': all_students_analysis
        }
    
    def create_individual_analysis_text(self, student_name):
        """개별 학생 분석을 텍스트로 만들기"""
        analysis = self.get_individual_student_analysis(student_name)
        if not analysis:
            return f"❌ '{student_name}' 학생을 찾을 수 없어요."
        
        result = f"## 👦👧 {student_name} 친구관계 분석\n\n"
        
        # 긍정적인 관계
        if analysis['positive_friends']:
            friends_list = [f"{friend} ({score}점)" for friend, score in analysis['positive_friends']]
            result += f"### 💚 긍정적인 관계\n"
            result += f"**{student_name}** → {', '.join(friends_list)}\n\n"
        
        # 부정적인 관계
        if analysis['negative_friends']:
            conflict_list = [f"{friend} ({score}점)" for friend, score in analysis['negative_friends']]
            result += f"### 💔 부정적인 관계\n"
            result += f"**{student_name}** → {', '.join(conflict_list)}\n\n"
        
        # 서로 친한 친구
        if analysis['mutual_friends']:
            result += f"### 🤝 서로 친한 친구\n"
            result += f"**{student_name}** ↔ {', '.join(analysis['mutual_friends'])}\n\n"
        
        # 나를 언급한 친구들
        if analysis['mentioned_by']:
            mentioned_list = [f"{friend} ({score}점)" for friend, score in analysis['mentioned_by']]
            result += f"### 🌟 나를 언급한 친구들\n"
            result += f"{', '.join(mentioned_list)} → **{student_name}**\n\n"
        
        # 특성 분석
        result += f"### 📊 특성 분석\n"
        result += f"- 인기도: {analysis['popularity_score']}명이 언급\n"
        result += f"- 사교성: {analysis['sociability_score']}명을 언급\n"
        
        if analysis['is_popular']:
            result += f"- 🌟 **인기가 많은 친구**\n"
        if analysis['is_isolated']:
            result += f"- 😢 **관심이 필요한 친구** (소외될 수 있음)\n"
        elif analysis['is_low_mentioned']:
            result += f"- 😐 **조금 더 관심을 가져주면 좋을 친구**\n"
        
        return result
    
    def get_friendship_statistics(self):
        """친구관계 숫자로 살펴보기"""
        if self.graph is None:
            self.build_relationship_graph()
        
        stats = {}
        
        # 중요도 계산
        stats['in_degree_centrality'] = nx.in_degree_centrality(self.graph)
        stats['out_degree_centrality'] = nx.out_degree_centrality(self.graph)
        stats['betweenness_centrality'] = nx.betweenness_centrality(self.graph)
        
        # 인기 학생 (많이 언급받은 학생)
        popular_students = sorted(stats['in_degree_centrality'].items(), 
                                key=lambda x: x[1], reverse=True)[:5]
        
        # 친절한 학생 (많이 언급한 학생)
        kind_students = sorted(stats['out_degree_centrality'].items(), 
                               key=lambda x: x[1], reverse=True)[:5]
        
        # 중간 역할 학생 (친구들 사이를 연결해주는 학생)
        bridge_students = sorted(stats['betweenness_centrality'].items(), 
                                 key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'popular_students': popular_students,
            'kind_students': kind_students,
            'bridge_students': bridge_students,
            'total_students': len(self.students),
            'total_connections': self.graph.number_of_edges(),
            'average_connections': self.graph.number_of_edges() / len(self.students) if self.students else 0
        }
    
    def create_statistics_charts(self):
        """숫자 차트 만들기"""
        try:
            stats = self.get_friendship_statistics()
            
            # 여러 개 차트 만들기
            from plotly.subplots import make_subplots
            
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('🌟 인기쟁이 TOP 5', '🤝 친절한 친구 TOP 5', 
                               '🔗 중간역할 TOP 5', '📊 친구 수 분포'),
                specs=[[{"type": "bar"}, {"type": "bar"}],
                       [{"type": "bar"}, {"type": "histogram"}]]
            )
            
            # 인기도 차트 - 데이터가 있을 때만
            if stats['popular_students']:
                names_pop = [name for name, score in stats['popular_students']]
                scores_pop = [score * 100 for name, score in stats['popular_students']]
                
                fig.add_trace(
                    go.Bar(x=names_pop, y=scores_pop, name='인기도', 
                          marker_color='gold', text=[f'{s:.1f}%' for s in scores_pop], 
                          textposition='auto'),
                    row=1, col=1
                )
            
            # 친절함 차트 - 데이터가 있을 때만
            if stats['kind_students']:
                names_kind = [name for name, score in stats['kind_students']]
                scores_kind = [score * 100 for name, score in stats['kind_students']]
                
                fig.add_trace(
                    go.Bar(x=names_kind, y=scores_kind, name='친절함', 
                          marker_color='lightblue', text=[f'{s:.1f}%' for s in scores_kind], 
                          textposition='auto'),
                    row=1, col=2
                )
            
            # 중간역할 차트 - 데이터가 있을 때만
            if stats['bridge_students']:
                names_bridge = [name for name, score in stats['bridge_students']]
                scores_bridge = [score * 100 for name, score in stats['bridge_students']]
                
                fig.add_trace(
                    go.Bar(x=names_bridge, y=scores_bridge, name='중간역할', 
                          marker_color='lightgreen', text=[f'{s:.1f}%' for s in scores_bridge], 
                          textposition='auto'),
                    row=2, col=1
                )
            
            # 친구 수 분포 (히스토그램)
            if self.graph and self.graph.number_of_nodes() > 0:
                # 각 학생의 친구 수 계산
                friend_counts = []
                for student in self.students:
                    count = self.graph.degree(student)
                    friend_counts.append(count)
                
                fig.add_trace(
                    go.Histogram(x=friend_counts, name='친구 수 분포', 
                                marker_color='orange', nbinsx=10),
                    row=2, col=2
                )
            
            fig.update_layout(
                title_text="📊 친구관계 통계 대시보드",
                title_font_color='black',
                title_font_size=20,
                showlegend=False,
                height=800,
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            
            # 축 제목 설정
            fig.update_xaxes(title_text="학생", row=1, col=1, title_font_color='black')
            fig.update_yaxes(title_text="인기도 점수(%)", row=1, col=1, title_font_color='black')
            fig.update_xaxes(title_text="학생", row=1, col=2, title_font_color='black')
            fig.update_yaxes(title_text="친절함 점수(%)", row=1, col=2, title_font_color='black')
            fig.update_xaxes(title_text="학생", row=2, col=1, title_font_color='black')
            fig.update_yaxes(title_text="중간역할 점수(%)", row=2, col=1, title_font_color='black')
            fig.update_xaxes(title_text="친구 수", row=2, col=2, title_font_color='black')
            fig.update_yaxes(title_text="학생 수", row=2, col=2, title_font_color='black')
            
            return fig
            
        except Exception as e:
            # 오류 발생 시 간단한 차트 반환
            fig = go.Figure()
            fig.add_annotation(
                text=f"📊 통계를 만드는 중 문제가 생겼어요: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                font=dict(size=16, color='red')
            )
            fig.update_layout(
                title="📊 통계 차트",
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            return fig