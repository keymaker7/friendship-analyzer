import pandas as pd
import csv
import io

def generate_sample_data():
    """구글폼 설문에 맞는 샘플 데이터 생성"""
    
    # 샘플 학생 명단
    students = [
        "김민수", "이지우", "박서연", "최다혜", "정준호", 
        "한지민", "강태완", "송유진", "윤서현", "임도현",
        "오예린", "신재원", "배하늘", "조민기", "홍수빈",
        "안지호", "권나연", "이승민", "박채원", "김도연"
    ]
    
    # 컬럼명 정의 (구글폼 질문에 맞춤)
    columns = [
        "타임스탬프",
        "이름",
        "가장 친한 친구 3명",
        "자주 대화하는 친구들",
        "도움을 요청하는 친구",
        "내가 도와준 친구들", 
        "갈등이 있었던 친구들",
        "친해지고 싶은 친구들",
        "나의 영향력 (1-5점)",
        "친구들의 영향 (1-5점)",
        "자유 의견"
    ]
    
    # 샘플 데이터 생성
    sample_data = []
    
    import random
    from datetime import datetime, timedelta
    
    base_time = datetime.now() - timedelta(days=7)
    
    for i, student in enumerate(students):
        # 다른 학생들 목록 (자기 제외)
        other_students = [s for s in students if s != student]
        
        # 랜덤하게 친구 관계 생성
        close_friends = random.sample(other_students, min(3, len(other_students)))
        frequent_friends = random.sample(other_students, random.randint(2, 6))
        help_friend = random.choice(other_students)
        helped_friends = random.sample(other_students, random.randint(1, 4))
        conflict_friends = random.sample(other_students, random.randint(0, 2)) if random.random() > 0.7 else []
        want_close_friends = random.sample(other_students, random.randint(1, 3))
        
        row_data = [
            (base_time + timedelta(hours=i*2)).strftime("%Y/%m/%d %H:%M:%S"),
            student,
            ", ".join(close_friends),
            ", ".join(frequent_friends),
            help_friend,
            ", ".join(helped_friends),
            ", ".join(conflict_friends) if conflict_friends else "",
            ", ".join(want_close_friends),
            random.randint(3, 5),
            random.randint(3, 5),
            f"{student}의 교우관계에 대한 의견입니다." if random.random() > 0.5 else ""
        ]
        
        sample_data.append(row_data)
    
    # DataFrame 생성
    df = pd.DataFrame(sample_data, columns=columns)
    
    return df

def get_sample_csv():
    """샘플 CSV 파일 내용을 문자열로 반환"""
    df = generate_sample_data()
    output = io.StringIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    return output.getvalue()

if __name__ == "__main__":
    # 샘플 파일 저장
    df = generate_sample_data()
    df.to_csv("sample_friendship_survey.csv", index=False, encoding='utf-8-sig')
    print("샘플 데이터가 생성되었습니다: sample_friendship_survey.csv") 