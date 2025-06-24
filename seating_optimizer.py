import numpy as np
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
from itertools import combinations
import random
from typing import List, Tuple, Dict
import math

class SeatingOptimizer:
    def __init__(self, friendship_graph=None):
        self.graph = friendship_graph
        self.students = []
        self.classroom_layout = None
        self.current_seating = None
        
        # 그래프가 있으면 학생 목록 설정
        if friendship_graph is not None:
            self.students = list(friendship_graph.nodes())
        
    def set_friendship_graph(self, graph):
        """친구 관계 그래프 설정하기"""
        self.graph = graph
        self.students = list(graph.nodes())
        
    def create_classroom_layout(self, rows, cols, teacher_position='front'):
        """교실 배치 만들기"""
        self.classroom_layout = {
            'rows': rows,
            'cols': cols,
            'total_seats': rows * cols,
            'teacher_position': teacher_position
        }
        
        # 자리 위치 만들기 (세로줄, 가로줄) 형태
        self.seat_positions = []
        for r in range(rows):
            for c in range(cols):
                self.seat_positions.append((r, c))
                
        return self.classroom_layout
    
    def calculate_distance(self, pos1, pos2):
        """두 자리 사이의 거리 계산하기"""
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
    
    def get_adjacent_seats(self, position, radius=1):
        """주변 자리 찾기"""
        row, col = position
        adjacent = []
        
        for r in range(max(0, row-radius), min(self.classroom_layout['rows'], row+radius+1)):
            for c in range(max(0, col-radius), min(self.classroom_layout['cols'], col+radius+1)):
                if (r, c) != position:
                    adjacent.append((r, c))
        
        return adjacent
    
    def calculate_seating_score(self, seating_arrangement):
        """자리 배치의 점수 계산하기"""
        if not self.graph or not seating_arrangement:
            return 0
        
        total_score = 0
        student_positions = {student: pos for pos, student in seating_arrangement.items()}
        
        # 친한 친구들 간의 거리 고려하기
        for student1, student2 in self.graph.edges():
            if student1 in student_positions and student2 in student_positions:
                pos1 = student_positions[student1]
                pos2 = student_positions[student2]
                distance = self.calculate_distance(pos1, pos2)
                
                # 관계 점수 가져오기
                weight = self.graph[student1][student2].get('weight', 1)
                
                # 좋은 관계는 가까이, 안 좋은 관계는 멀리
                if weight > 0:
                    # 가까울수록 높은 점수 (좋은 관계)
                    score = weight * (1 / (1 + distance))
                else:
                    # 멀수록 높은 점수 (안 좋은 관계)
                    score = abs(weight) * distance
                
                total_score += score
        
        # 선생님과의 거리 고려하기 (집중이 필요한 학생을 앞자리에)
        teacher_position = self.get_teacher_position()
        for student, position in student_positions.items():
            distance_to_teacher = self.calculate_distance(position, teacher_position)
            
            # 학생의 특성에 따라 점수 주기 (예: 도움이 필요한 학생)
            if self.graph.in_degree(student) < self.graph.out_degree(student):
                # 도움을 많이 주는 학생은 중간에
                total_score += 0.5 * (1 / (1 + abs(distance_to_teacher - 2)))
            elif self.graph.in_degree(student) > self.graph.out_degree(student):
                # 도움을 많이 받는 학생은 앞쪽에
                total_score += 0.3 * (1 / (1 + distance_to_teacher))
        
        return total_score
    
    def get_teacher_position(self):
        """선생님 위치 알려주기"""
        if self.classroom_layout['teacher_position'] == 'front':
            return (-1, self.classroom_layout['cols'] // 2)
        elif self.classroom_layout['teacher_position'] == 'back':
            return (self.classroom_layout['rows'], self.classroom_layout['cols'] // 2)
        else:
            return (0, 0)  # 기본값
    
    def random_seating(self):
        """무작위 자리 배치"""
        students_copy = self.students.copy()
        random.shuffle(students_copy)
        
        seating = {}
        for i, student in enumerate(students_copy[:len(self.seat_positions)]):
            seating[self.seat_positions[i]] = student
            
        return seating
    
    def optimize_seating_genetic(self, population_size=50, generations=100, mutation_rate=0.1):
        """똑똑한 방법으로 자리 배치 찾기"""
        if not self.students or not hasattr(self, 'seat_positions') or not self.seat_positions:
            return None
        
        try:
            def create_individual():
                """새로운 자리 배치 만들기"""
                return self.random_seating()
            
            def crossover(parent1, parent2):
                """두 배치를 섞어서 새로운 배치 만들기"""
                child = {}
                positions = list(self.seat_positions)
                
                # 절반은 parent1에서, 절반은 parent2에서
                split_point = len(positions) // 2
                
                used_students = set()
                
                # Parent1에서 절반 가져오기
                for i in range(split_point):
                    pos = positions[i]
                    if pos in parent1 and parent1[pos] not in used_students:
                        child[pos] = parent1[pos]
                        used_students.add(parent1[pos])
                
                # Parent2에서 나머지 채우기
                remaining_positions = [pos for pos in positions if pos not in child]
                remaining_students = [s for s in self.students if s not in used_students]
                
                for pos in remaining_positions:
                    if remaining_students:
                        student = remaining_students.pop(0)
                        child[pos] = student
                
                return child
            
            def mutate(individual):
                """조금씩 바꿔보기"""
                if random.random() < mutation_rate:
                    # 두 학생의 자리를 바꿈
                    positions = list(individual.keys())
                    if len(positions) >= 2:
                        pos1, pos2 = random.sample(positions, 2)
                        individual[pos1], individual[pos2] = individual[pos2], individual[pos1]
                return individual
            
            # 처음 배치들 만들기
            population = [create_individual() for _ in range(population_size)]
            
            best_individual = None
            best_score = float('-inf')
            
            for generation in range(generations):
                # 점수 계산하기
                scores = [(individual, self.calculate_seating_score(individual)) 
                         for individual in population]
                scores.sort(key=lambda x: x[1], reverse=True)
                
                # 가장 좋은 배치 업데이트
                if scores[0][1] > best_score:
                    best_score = scores[0][1]
                    best_individual = scores[0][0].copy()
                
                # 좋은 배치들 골라내기 (상위 50% 유지)
                elite_size = population_size // 2
                elite = [individual for individual, score in scores[:elite_size]]
                
                # 새로운 배치들 만들기
                new_population = elite.copy()
                
                # 섞기와 바꾸기로 나머지 채우기
                while len(new_population) < population_size:
                    parent1, parent2 = random.sample(elite, 2)
                    child = crossover(parent1, parent2)
                    child = mutate(child)
                    new_population.append(child)
                
                population = new_population
            
            self.current_seating = best_individual
            return best_individual, best_score
            
        except Exception as e:
            # 오류 발생 시 간단한 무작위 배치 반환
            seating = self.random_seating()
            score = self.calculate_seating_score(seating) if seating else 0
            self.current_seating = seating
            return seating, score
    
    def optimize_seating_greedy(self):
        """빠른 방법으로 자리 배치 찾기"""
        if not self.students or not self.seat_positions:
            return None
        
        try:
            seating = {}
            remaining_students = self.students.copy()
            remaining_positions = self.seat_positions.copy()
            
            # 간단하게 무작위 배치로 시작
            random.shuffle(remaining_students)
            
            # 학생들을 순서대로 배치
            for i, student in enumerate(remaining_students):
                if i < len(remaining_positions):
                    position = remaining_positions[i]
                    seating[position] = student
            
            # 최적화: 몇 번 학생들 위치 바꿔보기
            for _ in range(min(50, len(self.students) * 2)):
                # 무작위로 두 학생 선택
                positions = list(seating.keys())
                if len(positions) >= 2:
                    pos1, pos2 = random.sample(positions, 2)
                    
                    # 원래 점수
                    original_score = self.calculate_seating_score(seating)
                    
                    # 위치 바꿔보기
                    seating[pos1], seating[pos2] = seating[pos2], seating[pos1]
                    new_score = self.calculate_seating_score(seating)
                    
                    # 점수가 나빠지면 원래대로
                    if new_score < original_score:
                        seating[pos1], seating[pos2] = seating[pos2], seating[pos1]
            
            self.current_seating = seating
            return seating
            
        except Exception as e:
            # 오류 발생 시 간단한 무작위 배치
            seating = self.random_seating()
            self.current_seating = seating
            return seating
    
    def create_seating_visualization(self, seating_arrangement=None):
        """자리 배치를 그림으로 보여주기"""
        if seating_arrangement is None:
            seating_arrangement = self.current_seating
        
        if not seating_arrangement or not self.classroom_layout:
            return None
        
        rows = self.classroom_layout['rows']
        cols = self.classroom_layout['cols']
        
        # 교실 표 만들기
        classroom_matrix = np.full((rows, cols), "", dtype=object)
        
        for (row, col), student in seating_arrangement.items():
            if 0 <= row < rows and 0 <= col < cols:
                classroom_matrix[row][col] = student
        
        # 예쁜 그림 만들기
        fig = go.Figure(data=go.Heatmap(
            z=np.ones((rows, cols)),  # 색깔용 가짜 정보
            text=classroom_matrix,
            texttemplate="%{text}",
            textfont={"size": 10},
            colorscale=[[0, 'lightblue'], [1, 'lightblue']],
            showscale=False,
            hovertemplate='자리: (%{y}, %{x})<br>학생: %{text}<extra></extra>'
        ))
        
        fig.update_layout(
            title='우리 교실 자리 배치',
            xaxis_title='가로줄',
            yaxis_title='세로줄',
            xaxis=dict(side='top'),
            yaxis=dict(autorange='reversed'),
            width=800,
            height=600
        )
        
        # 선생님 위치 표시하기
        teacher_pos = self.get_teacher_position()
        fig.add_annotation(
            x=teacher_pos[1],
            y=teacher_pos[0],
            text="👨‍🏫 선생님",
            showarrow=True,
            arrowhead=2,
            arrowcolor="red",
            font=dict(size=12, color="red")
        )
        
        return fig
    
    def get_seating_report(self, seating_arrangement=None):
        """자리 배치 보고서 만들기"""
        if seating_arrangement is None:
            seating_arrangement = self.current_seating
        
        if not seating_arrangement:
            return None
        
        report = {
            'total_score': self.calculate_seating_score(seating_arrangement),
            'student_positions': seating_arrangement,
            'friendship_pairs_nearby': [],
            'conflict_pairs_separated': [],
            'recommendations': []
        }
        
        student_positions = {student: pos for pos, student in seating_arrangement.items()}
        
        # 친한 친구들이 가까이 앉았는지 확인하기
        for student1, student2 in self.graph.edges():
            if student1 in student_positions and student2 in student_positions:
                pos1 = student_positions[student1]
                pos2 = student_positions[student2]
                distance = self.calculate_distance(pos1, pos2)
                weight = self.graph[student1][student2].get('weight', 1)
                
                if weight > 0 and distance <= 2:  # 좋은 관계이고 가까이 앉음
                    report['friendship_pairs_nearby'].append({
                        'student1': student1,
                        'student2': student2,
                        'distance': distance,
                        'relationship_strength': weight
                    })
                elif weight < 0 and distance > 2:  # 안 좋은 관계이고 멀리 앉음
                    report['conflict_pairs_separated'].append({
                        'student1': student1,
                        'student2': student2,
                        'distance': distance,
                        'conflict_level': abs(weight)
                    })
        
        # 선생님께 드리는 말씀 만들기
        if len(report['friendship_pairs_nearby']) > len(self.students) * 0.3:
            report['recommendations'].append("친한 친구들이 적절히 가까이 앉았어요.")
        else:
            report['recommendations'].append("친한 친구들을 더 가까이 앉히는 것을 생각해보세요.")
        
        if len(report['conflict_pairs_separated']) > 0:
            report['recommendations'].append("안 좋은 관계의 학생들이 잘 떨어져 앉았어요.")
        
        return report 