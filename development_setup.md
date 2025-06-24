# 💻 다른 컴퓨터에서 개발하기

## 🚀 빠른 시작 가이드

### 1단계: Git 설치 (필요한 경우)
- **Windows**: [Git for Windows](https://git-scm.com/download/win) 다운로드 및 설치
- **Mac**: `brew install git` 또는 [Git 공식 사이트](https://git-scm.com/download/mac)
- **Linux**: `sudo apt install git` (Ubuntu/Debian) 또는 `sudo yum install git` (CentOS/RHEL)

### 2단계: Python 설치 (필요한 경우)
- [Python 공식 사이트](https://www.python.org/downloads/)에서 Python 3.8 이상 다운로드
- 설치 시 "Add Python to PATH" 체크박스 반드시 선택

### 3단계: 프로젝트 클론
```bash
# 원하는 폴더로 이동 후
git clone https://github.com/keymaker7/friendship-analyzer.git
cd friendship-analyzer
```

### 4단계: 가상환경 생성 (권장)
```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 5단계: 패키지 설치
```bash
pip install -r requirements.txt
```

### 6단계: 앱 실행
```bash
streamlit run main_app.py
```

브라우저에서 `http://localhost:8501`로 접속하면 앱을 확인할 수 있습니다!

---

## 🔄 수정 후 업데이트하기

### 코드 수정 후 GitHub에 반영
```bash
# 변경사항 확인
git status

# 변경된 파일 추가
git add .

# 커밋 메시지와 함께 저장
git commit -m "수정 내용 설명"

# GitHub에 업로드
git push origin main
```

### 다른 컴퓨터에서 최신 코드 받기
```bash
# 최신 코드 가져오기
git pull origin main
```

---

## 🛠️ 개발 도구 추천

### 코드 에디터
- **VS Code** (추천): 무료, 강력한 기능
- **PyCharm**: 전문 Python IDE
- **Sublime Text**: 가볍고 빠름

### VS Code 확장프로그램 (권장)
- Python
- Streamlit Snippets
- GitLens
- Prettier - Code formatter

---

## 🔧 문제 해결

### 패키지 설치 오류
```bash
# pip 업그레이드
pip install --upgrade pip

# 개별 패키지 설치 (문제 발생 시)
pip install streamlit pandas networkx plotly matplotlib seaborn numpy
```

### 포트 충돌
```bash
# 다른 포트로 실행
streamlit run main_app.py --server.port 8502
```

### Git 설정 (첫 사용 시)
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

---

## 📁 프로젝트 구조

```
friendship-analyzer/
├── main_app.py              # 메인 Streamlit 앱
├── friendship_analyzer.py   # 친구관계 분석 모듈
├── seating_optimizer.py     # 자리배치 최적화 모듈
├── sample_data.py          # 샘플 데이터 생성
├── requirements.txt        # 필요 패키지 목록
├── README.md              # 프로젝트 설명
├── deployment_guide.md    # 배포 가이드
├── development_setup.md   # 이 파일
└── .gitignore            # Git 무시 파일 목록
```

---

## 🚀 Streamlit Cloud 자동 배포

GitHub에 코드를 푸시하면 Streamlit Cloud에서 자동으로 배포가 업데이트됩니다!

1. 코드 수정
2. `git push origin main`
3. 2-3분 후 배포 사이트에 자동 반영

---

## 💡 개발 팁

1. **가상환경 사용**: 다른 프로젝트와 패키지 충돌 방지
2. **작은 단위로 커밋**: 변경사항을 작은 단위로 나누어 커밋
3. **의미있는 커밋 메시지**: 무엇을 왜 변경했는지 명확히 작성
4. **정기적인 pull**: 다른 곳에서 수정했다면 최신 코드 받기

---

## 📞 도움이 필요하면

1. GitHub Issues에 질문 등록
2. 이메일로 문의
3. 에러 메시지와 함께 상황 설명

Happy coding! 🎉 