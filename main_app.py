import streamlit as st
import pandas as pd
import io
import requests
from urllib.parse import urlparse
import re
import base64
from datetime import datetime

# 다른 모듈들
from sample_data import generate_sample_data
from friendship_analyzer import FriendshipAnalyzer
from seating_optimizer import SeatingOptimizer

def main():
    st.set_page_config(
        page_title="우리 반 친구관계 요약",
        page_icon="📊",
        layout="wide"
    )
    
    # 제목
    st.title("📊 우리 반 친구관계 요약")
    st.markdown("---")
    
    # 세션 상태 초기화
    if 'data' not in st.session_state:
        st.session_state.data = None
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = FriendshipAnalyzer()
    if 'seating_result' not in st.session_state:
        st.session_state.seating_result = None

    # 4개 탭으로 변경 (드롭다운 대신)
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 설문 결과 올리기", 
        "🔍 친구 관계 살펴보기", 
        "🪑 자리 배치 만들기", 
        "💾 결과 내보내기"
    ])
    
    with tab1:
        show_data_upload_tab()
    
    with tab2:
        show_analysis_tab()
    
    with tab3:
        show_seating_tab()
    
    with tab4:
        show_export_tab()

def show_data_upload_tab():
    """설문 결과 올리기 탭"""
    st.header("📝 설문 결과 올리기")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📥 샘플 정보 다운로드")
        st.write("먼저 샘플 파일을 다운로드해서 형식을 확인해보세요!")
        
        if st.button("📄 샘플 CSV 파일 받기"):
            sample_df = generate_sample_data()
            csv_buffer = io.StringIO()
            sample_df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
            csv_string = csv_buffer.getvalue()
            
            st.download_button(
                label="💾 sample_friendship_data.csv 다운로드",
                data=csv_string,
                file_name="sample_friendship_data.csv",
                mime="text/csv"
            )
            st.success("✅ 샘플 파일이 준비되었어요!")
        
        if st.button("🎯 연습용 정보로 체험하기"):
            sample_df = generate_sample_data()
            st.session_state.data = sample_df
            st.session_state.analyzer.load_data(sample_df)
            st.success("✅ 연습용 정보를 불러왔어요!")
            st.dataframe(sample_df.head())
    
    with col2:
        st.subheader("📤 실제 설문 결과 올리기")
        
        upload_method = st.radio(
            "올리기 방법을 선택해주세요:",
            ["💻 파일 직접 올리기", "🔗 구글시트 주소로 가져오기"]
        )
        
        if upload_method == "💻 파일 직접 올리기":
            uploaded_file = st.file_uploader(
                "CSV 파일을 선택해주세요",
                type=['csv'],
                help="구글폼 설문 결과를 CSV로 내보낸 파일을 올려주세요"
            )
            
            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
                    st.session_state.data = df
                    st.session_state.analyzer.load_data(df)
                    st.success(f"✅ 파일이 성공적으로 올라갔어요! ({len(df)}개 응답)")
                    st.dataframe(df.head())
                except Exception as e:
                    st.error(f"❌ 파일을 읽는 중 문제가 생겼어요: {str(e)}")
        
        else:  # 구글시트 URL로 가져오기
            st.write("구글시트를 '링크 있는 모든 사용자'로 공유 설정한 후 주소를 붙여넣어주세요.")
            
            sheet_url = st.text_input("🔗 구글시트 주소를 입력해주세요:")
            
            if sheet_url and st.button("📊 가져오기"):
                try:
                    # 구글시트 URL을 CSV 다운로드 URL로 변환
                    if "docs.google.com/spreadsheets" in sheet_url:
                        # URL에서 파일 ID 추출
                        file_id = extract_file_id(sheet_url)
                        if file_id:
                            csv_url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv"
                            
                            # CSV 정보 가져오기
                            response = requests.get(csv_url)
                            response.raise_for_status()
                            
                            # CSV를 DataFrame으로 변환
                            csv_content = response.content.decode('utf-8-sig')
                            df = pd.read_csv(io.StringIO(csv_content))
                            
                            st.session_state.data = df
                            st.session_state.analyzer.load_data(df)
                            st.success(f"✅ 구글시트 정보를 가져왔어요! ({len(df)}개 응답)")
                            st.dataframe(df.head())
                        else:
                            st.error("❌ 올바른 구글시트 주소가 아니에요.")
                    else:
                        st.error("❌ 구글시트 주소를 다시 확인해주세요.")
                        
                except Exception as e:
                    st.error(f"❌ 정보를 가져오는 중 문제가 생겼어요: {str(e)}")
                    st.write("💡 도움말: 구글시트 공유 설정을 '링크 있는 모든 사용자'로 바꿔주세요.")

def show_analysis_tab():
    """친구 관계 살펴보기 탭"""
    st.header("🔍 친구 관계 살펴보기")
    
    if st.session_state.data is None:
        st.warning("⚠️ 먼저 설문 결과를 올려주세요!")
        return
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["📊 시각화로 보기", "👤 개별 학생 분석", "📈 반 전체 분석"])
    
    with tab1:
        st.subheader("📊 시각화로 보기")
        
        # 네트워크 시각화 선택 드롭다운 추가
        st.markdown("### 🕸️ 네트워크형 인물 관계도")
        
        network_style = st.selectbox(
            "네트워크 시각화 스타일을 선택하세요:",
            [
                "🎯 기본 네트워크 (관계별 색상)",
                "🌡️ 인기도 히트맵 스타일", 
                "🎨 그룹별 색상 네트워크",
                "📊 3D 네트워크 (입체적)",
                "⚡ 힘-기반 레이아웃"
            ]
        )
        
        try:
            if network_style == "🎯 기본 네트워크 (관계별 색상)":
                fig = st.session_state.analyzer.create_network_visualization()
            elif network_style == "🌡️ 인기도 히트맵 스타일":
                fig = st.session_state.analyzer.create_heatmap_network()
            elif network_style == "🎨 그룹별 색상 네트워크":
                fig = st.session_state.analyzer.create_group_colored_network()
            elif network_style == "📊 3D 네트워크 (입체적)":
                fig = st.session_state.analyzer.create_3d_network()
            elif network_style == "⚡ 힘-기반 레이아웃":
                fig = st.session_state.analyzer.create_force_directed_network()
                
            st.plotly_chart(fig, use_container_width=True)
            
            st.info("💡 **사용 방법**: 각 동그라미는 학생이고, 선은 친구관계를 나타내요. 동그라미가 클수록 인기가 많은 친구예요!")
            
        except Exception as e:
            st.error(f"❌ 그래프를 만드는 중 문제가 생겼어요: {str(e)}")
        
        st.markdown("---")
        
        # 시각화 종류 선택 (여러 개 선택 가능)
        viz_options = st.multiselect(
            "추가로 보고 싶은 그래프를 선택해주세요 (여러 개 선택 가능):",
            ["🤝 상호작용 관계도", "🌈 집단별 컬러 구분 원형 관계도", "📊 숫자로 보는 통계"]
        )
        
        # 선택된 시각화들 표시
        for viz_type in viz_options:
            st.markdown("---")
            
            if viz_type == "🤝 상호작용 관계도":
                st.subheader("🤝 상호작용 관계도")
                try:
                    fig = st.session_state.analyzer.create_interactive_relationship_map()
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.info("💡 **설명**: 서로 친하다고 언급한 친구들만 보여줘요. 파란 선으로 연결된 친구들은 서로를 좋아해요!")
                    
                except Exception as e:
                    st.error(f"❌ 그래프를 만드는 중 문제가 생겼어요: {str(e)}")
                    
            elif viz_type == "🌈 집단별 컬러 구분 원형 관계도":
                st.subheader("🌈 집단별 컬러 구분 원형 관계도")
                try:
                    fig = st.session_state.analyzer.create_circular_group_visualization()
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.info("💡 **설명**: 친한 친구들끼리 같은 색깔로 그룹을 만들어서 원 모양으로 배치했어요. 같은 색깔 친구들은 서로 잘 어울려요!")
                    
                except Exception as e:
                    st.error(f"❌ 그래프를 만드는 중 문제가 생겼어요: {str(e)}")
                    
            elif viz_type == "📊 숫자로 보는 통계":
                st.subheader("📊 숫자로 보는 통계")
                try:
                    fig = st.session_state.analyzer.create_statistics_charts()
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.info("💡 **설명**: 인기쟁이, 친절한 친구, 중간 역할을 하는 친구들을 숫자로 보여줘요!")
                    
                except Exception as e:
                    st.error(f"❌ 통계를 만드는 중 문제가 생겼어요: {str(e)}")
    
    with tab2:
        st.subheader("👤 개별 학생 분석")
        
        # 학생 선택
        if st.session_state.analyzer.students:
            selected_student = st.selectbox(
                "분석하고 싶은 학생을 선택해주세요:",
                st.session_state.analyzer.students
            )
            
            if selected_student:
                try:
                    # 개별 분석 결과 표시
                    analysis_text = st.session_state.analyzer.create_individual_analysis_text(selected_student)
                    st.markdown(analysis_text)
                    
                except Exception as e:
                    st.error(f"❌ 분석 중 문제가 생겼어요: {str(e)}")
        else:
            st.warning("⚠️ 학생 정보를 찾을 수 없어요. 데이터를 다시 확인해주세요.")
    
    with tab3:
        st.subheader("📈 반 전체 분석")
        
        try:
            # 반 전체 분석 결과
            overall_analysis = st.session_state.analyzer.get_class_overall_analysis()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🌟 인기가 많은 친구들")
                if overall_analysis['popularity_ranking']:
                    for i, (student, score) in enumerate(overall_analysis['popularity_ranking'], 1):
                        st.write(f"{i}. **{student}** - {score}명이 언급")
                else:
                    st.write("정보가 없어요.")
                
                st.markdown("### 😢 관심이 필요한 친구들")
                if overall_analysis['isolated_students']:
                    for student in overall_analysis['isolated_students']:
                        st.write(f"- **{student}** (소외될 수 있어요)")
                else:
                    st.write("🎉 모든 친구들이 언급되었어요!")
            
            with col2:
                st.markdown("### 😐 조금 더 관심을 가져주면 좋을 친구들")
                if overall_analysis['low_mentioned_students']:
                    for student in overall_analysis['low_mentioned_students']:
                        st.write(f"- **{student}** (2명 이하가 언급)")
                else:
                    st.write("🎉 모든 친구들이 충분히 언급되었어요!")
                
                st.markdown("### 📊 반 전체 요약")
                st.write(f"- 총 학생 수: **{overall_analysis['total_students']}명**")
                st.write(f"- 총 친구관계 수: **{overall_analysis['total_connections']}개**")
                avg_connections = overall_analysis['total_connections'] / overall_analysis['total_students'] if overall_analysis['total_students'] > 0 else 0
                st.write(f"- 평균 친구관계: **{avg_connections:.1f}개/명**")
            
            # 예시처럼 구체적인 관계 분석
            st.markdown("---")
            st.markdown("### 🔍 친구관계 상세 분석")
            
            if overall_analysis['all_students_analysis']:
                # 예시 학생 선택 (인기도 1위)
                if overall_analysis['popularity_ranking']:
                    example_student = overall_analysis['popularity_ranking'][0][0]
                    example_analysis = overall_analysis['all_students_analysis'][example_student]
                    
                    st.markdown(f"#### 예시: {example_student} 친구관계 분석")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # 긍정적인 관계
                        if example_analysis['positive_friends']:
                            positive_names = [name for name, score in example_analysis['positive_friends']]
                            st.markdown(f"**💚 긍정적인 관계**")
                            st.write(f"{example_student} → {', '.join(positive_names)}")
                        
                        # 부정적인 관계
                        if example_analysis['negative_friends']:
                            negative_names = [name for name, score in example_analysis['negative_friends']]
                            st.markdown(f"**💔 부정적인 관계**")
                            st.write(f"{example_student} → {', '.join(negative_names)}")
                    
                    with col2:
                        # 서로 친한 친구
                        if example_analysis['mutual_friends']:
                            st.markdown(f"**🤝 서로 친한 친구**")
                            st.write(f"{example_student} ↔ {', '.join(example_analysis['mutual_friends'])}")
                        
                        # 특성
                        st.markdown(f"**📊 특성**")
                        if example_analysis['is_popular']:
                            st.write("🌟 인기가 많은 친구")
                        if example_analysis['is_isolated']:
                            st.write("😢 관심이 필요한 친구")
                        elif example_analysis['is_low_mentioned']:
                            st.write("😐 조금 더 관심을 가져주면 좋을 친구")
                
        except Exception as e:
            st.error(f"❌ 전체 분석 중 문제가 생겼어요: {str(e)}")

def show_seating_tab():
    """자리 배치 만들기 탭"""
    st.header("🪑 자리 배치 만들기")
    
    if st.session_state.data is None:
        st.warning("⚠️ 먼저 설문 결과를 올려주세요!")
        return
    
    st.write("친구관계를 고려해서 가장 좋은 자리 배치를 만들어드려요!")
    
    # 교실 설정
    col1, col2 = st.columns(2)
    
    with col1:
        rows = st.number_input("교실 세로 줄 수", min_value=3, max_value=8, value=5)
        
    with col2:
        cols = st.number_input("교실 가로 줄 수", min_value=3, max_value=8, value=6)
    
    total_seats = rows * cols
    student_count = len(st.session_state.analyzer.students)
    
    st.info(f"📊 총 자리: {total_seats}개, 학생 수: {student_count}명")
    
    if total_seats < student_count:
        st.error("❌ 자리가 학생 수보다 적어요! 교실 크기를 늘려주세요.")
        return
    
    # 자리 배치 알고리즘 선택
    algorithm = st.selectbox(
        "배치 방법을 선택해주세요:",
        ["🧬 똑똑한 방법 (유전 알고리즘)", "🏃‍♂️ 빠른 방법 (탐욕 알고리즘)"]
    )
    
    if st.button("🎯 자리 배치 만들기"):
        try:
            with st.spinner("🔄 가장 좋은 자리 배치를 찾고 있어요..."):
                # 그래프가 제대로 구축되어 있는지 확인
                if st.session_state.analyzer.graph is None:
                    st.session_state.analyzer.build_relationship_graph()
                
                # 디버깅 정보
                st.info(f"📝 학생 수: {len(st.session_state.analyzer.students)}명")
                st.info(f"📊 그래프 노드 수: {st.session_state.analyzer.graph.number_of_nodes() if st.session_state.analyzer.graph else 0}개")
                
                optimizer = SeatingOptimizer(st.session_state.analyzer.graph)
                
                # 교실 레이아웃 설정
                layout = optimizer.create_classroom_layout(rows, cols)
                st.info(f"🏫 교실 설정: {layout}")
                st.info(f"👥 배치할 학생들: {optimizer.students}")
                
                if "똑똑한" in algorithm:
                    result = optimizer.optimize_seating_genetic(population_size=20, generations=50)
                    if result and len(result) == 2:
                        seating, score = result
                    else:
                        seating = result
                        score = optimizer.calculate_seating_score(seating) if seating else 0
                else:
                    seating = optimizer.optimize_seating_greedy()
                    score = optimizer.calculate_seating_score(seating) if seating else 0
                
                if seating:
                    st.session_state.seating_result = {
                        'seating': seating,
                        'score': score,
                        'layout': {'rows': rows, 'cols': cols}
                    }
                    
                    st.success(f"✅ 자리 배치가 완성되었어요! (점수: {score:.2f})")
                    
                    # 자리 배치 표시
                    st.subheader("🗺️ 자리 배치 결과")
                    
                    # 자리 배치를 표로 표시
                    seating_matrix = []
                    for r in range(rows):
                        row = []
                        for c in range(cols):
                            student = seating.get((r, c), "🪑")
                            row.append(student)
                        seating_matrix.append(row)
                    
                    seating_df = pd.DataFrame(seating_matrix, 
                                            columns=[f"열{i+1}" for i in range(cols)],
                                            index=[f"줄{i+1}" for i in range(rows)])
                    
                    st.dataframe(seating_df, use_container_width=True)
                    
                    # 배치 설명
                    st.markdown("### 📝 배치 설명")
                    st.write("- 친한 친구들은 가까이 앉도록 했어요")
                    st.write("- 갈등이 있는 친구들은 멀리 앉도록 했어요")
                    st.write("- 🪑 표시는 빈 자리예요")
                    
                else:
                    st.error("❌ 자리 배치를 만드는 데 실패했어요.")
                    
        except Exception as e:
            st.error(f"❌ 자리 배치 중 문제가 생겼어요: {str(e)}")
            st.write("디버그 정보:", str(e))

def show_export_tab():
    """결과 내보내기 탭"""
    st.header("💾 결과 내보내기")
    
    if st.session_state.data is None:
        st.warning("⚠️ 먼저 설문 결과를 올려주세요!")
        return
    
    st.write("분석 결과와 자리 배치를 다양한 형식으로 저장할 수 있어요!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 분석 결과 내보내기")
        
        # 내보내기 형식 선택
        export_format = st.selectbox(
            "내보내기 형식을 선택하세요:",
            ["📄 텍스트 보고서 (.txt)", "📊 CSV 데이터 (.csv)", "📋 마크다운 보고서 (.md)", "🌐 HTML 보고서 (.html)"]
        )
        
        if st.button("📈 친구관계 분석 보고서 만들기"):
            try:
                # 분석 데이터 수집
                stats = st.session_state.analyzer.get_friendship_statistics()
                overall_analysis = st.session_state.analyzer.get_class_overall_analysis()
                
                if export_format == "📄 텍스트 보고서 (.txt)":
                    report = create_text_report(stats, overall_analysis)
                    st.download_button(
                        label="📄 텍스트 보고서 다운로드",
                        data=report,
                        file_name=f"friendship_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
                
                elif export_format == "📊 CSV 데이터 (.csv)":
                    csv_data = create_csv_report(stats, overall_analysis)
                    st.download_button(
                        label="📊 CSV 데이터 다운로드",
                        data=csv_data,
                        file_name=f"friendship_analysis_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                
                elif export_format == "📋 마크다운 보고서 (.md)":
                    md_report = create_markdown_report(stats, overall_analysis)
                    st.download_button(
                        label="📋 마크다운 보고서 다운로드",
                        data=md_report,
                        file_name=f"friendship_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown"
                    )
                
                elif export_format == "🌐 HTML 보고서 (.html)":
                    html_report = create_html_report(stats, overall_analysis)
                    st.download_button(
                        label="🌐 HTML 보고서 다운로드",
                        data=html_report,
                        file_name=f"friendship_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                        mime="text/html"
                    )
                
                st.success("✅ 보고서가 준비되었어요!")
                
            except Exception as e:
                st.error(f"❌ 보고서 생성 중 문제가 생겼어요: {str(e)}")
    
    with col2:
        st.subheader("🪑 자리 배치 내보내기")
        
        if st.session_state.seating_result:
            seating_format = st.selectbox(
                "자리 배치 내보내기 형식:",
                ["📊 CSV 표 (.csv)", "📋 텍스트 목록 (.txt)", "🌐 HTML 표 (.html)"]
            )
            
            if st.button("🗺️ 자리 배치표 다운로드"):
                try:
                    seating_data = st.session_state.seating_result
                    
                    if seating_format == "📊 CSV 표 (.csv)":
                        csv_seating = create_seating_csv(seating_data)
                        st.download_button(
                            label="📊 자리배치 CSV 다운로드",
                            data=csv_seating,
                            file_name=f"seating_arrangement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    
                    elif seating_format == "📋 텍스트 목록 (.txt)":
                        txt_seating = create_seating_text(seating_data)
                        st.download_button(
                            label="📋 자리배치 텍스트 다운로드",
                            data=txt_seating,
                            file_name=f"seating_arrangement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain"
                        )
                    
                    elif seating_format == "🌐 HTML 표 (.html)":
                        html_seating = create_seating_html(seating_data)
                        st.download_button(
                            label="🌐 자리배치 HTML 다운로드",
                            data=html_seating,
                            file_name=f"seating_arrangement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                            mime="text/html"
                        )
                    
                    st.success("✅ 자리 배치표가 준비되었어요!")
                    
                except Exception as e:
                    st.error(f"❌ 자리 배치표 생성 중 문제가 생겼어요: {str(e)}")
        else:
            st.info("⚠️ 먼저 자리 배치를 만들어주세요!")
        
        # 구글 시트로 내보내기 옵션
        st.markdown("---")
        st.subheader("🔗 구글 서비스 연동")
        st.info("""
        💡 **구글 시트/문서로 보내는 방법:**
        1. 위에서 CSV나 HTML 파일을 다운로드
        2. 구글 드라이브에 업로드
        3. 구글 시트/문서에서 파일 열기
        """)

# 보고서 생성 함수들
def create_text_report(stats, overall_analysis):
    """텍스트 보고서 생성"""
    report = f"""# 우리 반 친구관계 분석 보고서
생성일시: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}

## 📊 주요 통계
- 총 학생 수: {overall_analysis['total_students']}명
- 총 친구관계 수: {overall_analysis['total_connections']}개
- 평균 친구관계: {overall_analysis['total_connections'] / overall_analysis['total_students'] if overall_analysis['total_students'] > 0 else 0:.1f}개/명

## 🌟 인기쟁이 TOP 5
"""
    for i, (name, score) in enumerate(stats['popular_students'], 1):
        report += f"{i}. {name} (점수: {score:.2f})\n"
    
    report += f"""
## 🤝 친절한 친구 TOP 5
"""
    for i, (name, score) in enumerate(stats['kind_students'], 1):
        report += f"{i}. {name} (점수: {score:.2f})\n"
    
    report += f"""
## 🔗 중간역할 TOP 5
"""
    for i, (name, score) in enumerate(stats['bridge_students'], 1):
        report += f"{i}. {name} (점수: {score:.2f})\n"
    
    if overall_analysis['isolated_students']:
        report += f"""
## 😢 관심이 필요한 친구들
"""
        for student in overall_analysis['isolated_students']:
            report += f"- {student}\n"
    
    if overall_analysis['low_mentioned_students']:
        report += f"""
## 😐 조금 더 관심을 가져주면 좋을 친구들
"""
        for student in overall_analysis['low_mentioned_students']:
            report += f"- {student}\n"
    
    return report

def create_csv_report(stats, overall_analysis):
    """CSV 데이터 생성"""
    data = []
    
    # 인기도 랭킹
    for i, (name, score) in enumerate(stats['popular_students'], 1):
        data.append(['인기도', i, name, f'{score:.3f}'])
    
    # 친절함 랭킹
    for i, (name, score) in enumerate(stats['kind_students'], 1):
        data.append(['친절함', i, name, f'{score:.3f}'])
    
    # 중간역할 랭킹
    for i, (name, score) in enumerate(stats['bridge_students'], 1):
        data.append(['중간역할', i, name, f'{score:.3f}'])
    
    df = pd.DataFrame(data, columns=['분류', '순위', '학생명', '점수'])
    return df.to_csv(index=False, encoding='utf-8-sig')

def create_markdown_report(stats, overall_analysis):
    """마크다운 보고서 생성"""
    report = f"""# 📊 우리 반 친구관계 분석 보고서

> 생성일시: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}

## 📈 주요 통계

| 항목 | 값 |
|------|-----|
| 총 학생 수 | {overall_analysis['total_students']}명 |
| 총 친구관계 수 | {overall_analysis['total_connections']}개 |
| 평균 친구관계 | {overall_analysis['total_connections'] / overall_analysis['total_students'] if overall_analysis['total_students'] > 0 else 0:.1f}개/명 |

## 🏆 랭킹

### 🌟 인기쟁이 TOP 5
| 순위 | 학생명 | 점수 |
|------|--------|------|
"""
    for i, (name, score) in enumerate(stats['popular_students'], 1):
        report += f"| {i} | {name} | {score:.2f} |\n"
    
    report += """
### 🤝 친절한 친구 TOP 5
| 순위 | 학생명 | 점수 |
|------|--------|------|
"""
    for i, (name, score) in enumerate(stats['kind_students'], 1):
        report += f"| {i} | {name} | {score:.2f} |\n"
    
    return report

def create_html_report(stats, overall_analysis):
    """HTML 보고서 생성"""
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>친구관계 분석 보고서</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .highlight {{ background-color: #e8f5e8; }}
    </style>
</head>
<body>
    <h1>📊 우리 반 친구관계 분석 보고서</h1>
    <p><strong>생성일시:</strong> {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}</p>
    
    <h2>📈 주요 통계</h2>
    <table>
        <tr><th>항목</th><th>값</th></tr>
        <tr><td>총 학생 수</td><td>{overall_analysis['total_students']}명</td></tr>
        <tr><td>총 친구관계 수</td><td>{overall_analysis['total_connections']}개</td></tr>
        <tr><td>평균 친구관계</td><td>{overall_analysis['total_connections'] / overall_analysis['total_students'] if overall_analysis['total_students'] > 0 else 0:.1f}개/명</td></tr>
    </table>
    
    <h2>🌟 인기쟁이 TOP 5</h2>
    <table>
        <tr><th>순위</th><th>학생명</th><th>점수</th></tr>
"""
    
    for i, (name, score) in enumerate(stats['popular_students'], 1):
        html += f"        <tr><td>{i}</td><td>{name}</td><td>{score:.2f}</td></tr>\n"
    
    html += """
    </table>
</body>
</html>
"""
    return html

def create_seating_csv(seating_data):
    """자리 배치 CSV 생성"""
    seating = seating_data['seating']
    layout = seating_data['layout']
    
    # 자리 배치를 매트릭스로 변환
    seating_matrix = []
    for r in range(layout['rows']):
        row = []
        for c in range(layout['cols']):
            student = seating.get((r, c), "빈자리")
            row.append(student)
        seating_matrix.append(row)
    
    df = pd.DataFrame(seating_matrix, 
                     columns=[f"열{i+1}" for i in range(layout['cols'])],
                     index=[f"줄{i+1}" for i in range(layout['rows'])])
    
    return df.to_csv(encoding='utf-8-sig')

def create_seating_text(seating_data):
    """자리 배치 텍스트 생성"""
    seating = seating_data['seating']
    
    text = f"""자리 배치 결과
생성일시: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
점수: {seating_data['score']:.2f}

자리 배치 목록:
"""
    
    for (row, col), student in seating.items():
        text += f"({row+1}줄, {col+1}열): {student}\n"
    
    return text

def create_seating_html(seating_data):
    """자리 배치 HTML 표 생성"""
    seating = seating_data['seating']
    layout = seating_data['layout']
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>자리 배치표</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        table {{ border-collapse: collapse; margin: 20px auto; }}
        td {{ border: 2px solid #333; width: 80px; height: 60px; text-align: center; vertical-align: middle; }}
        .student {{ background-color: #e8f5e8; font-weight: bold; }}
        .empty {{ background-color: #f0f0f0; }}
        h1 {{ text-align: center; }}
    </style>
</head>
<body>
    <h1>🪑 자리 배치표</h1>
    <p style="text-align: center;">점수: {seating_data['score']:.2f} | 생성일시: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}</p>
    
    <table>
"""
    
    for r in range(layout['rows']):
        html += "        <tr>\n"
        for c in range(layout['cols']):
            student = seating.get((r, c), "🪑")
            css_class = "student" if student != "🪑" else "empty"
            html += f'            <td class="{css_class}">{student}</td>\n'
        html += "        </tr>\n"
    
    html += """
    </table>
</body>
</html>
"""
    return html

def extract_file_id(url):
    """구글시트 URL에서 파일 ID 추출"""
    patterns = [
        r'/spreadsheets/d/([a-zA-Z0-9-_]+)',
        r'id=([a-zA-Z0-9-_]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

if __name__ == "__main__":
    main()