# 🛒 E-commerce Purchase Prediction System

> 실시간 구매 가능성 예측 시스템 구축

## 📊 시스템 아키텍처

### 🔄 전체 파이프라인

| Layer | Components | Description |
|-------|-----------|-------------|
| **🎯 Orchestration** | Airflow Scheduler | ETL + Retraining 자동화 |
| ⬇️ | | |
| **📥 Data Pipeline** | Filebeat → Logstash → Elasticsearch | 로그 수집 및 처리 |
| | MinIO | 데이터 저장소 |
| | Spark / Delta Lake | ETL 처리 |
| | Data Warehouse / Data Mart | 분석용 데이터 적재 |
| ⬇️ | | |
| **🤖 ML Pipeline** | Feature Engineering | 피처 생성 및 변환 |
| | LGBM / XGB / CatBoost | 모델 학습 |
| | SHAP | 모델 해석 |
| | Feast Feature Store | 피처 저장 및 관리 |
| ⬇️ | | |
| **🚀 Serving Layer** | FastAPI | REST API 서버 |
| | Redis (Online Store) | 실시간 피처 캐싱 |
| | Streamlit | 웹 UI |
| ⬇️ | | |
| **👤 User** | Web Interface | 예측 결과 확인 |

### 📊 상세 데이터 흐름

**1️⃣ Data Collection**
- Filebeat → Logstash → Elasticsearch → MinIO

**2️⃣ Data Processing**  
- MinIO → Spark/Delta Lake (ETL) → Data Warehouse

**3️⃣ Model Training**
- Data Warehouse → Feature Engineering → ML Models → Feast

**4️⃣ Inference**
- Feast → FastAPI → Redis → Streamlit → User

## 🔧 기술 스택

### 📥 Data Ingestion
```
[Logstash] → [S3 Data Lake] → [Elasticsearch] → [Kibana Dashboard]
    ↓            ↓                  ↓                   ↓
실시간 수집   원본 저장         로그 검색          시각화/모니터링
```

### ⚙️ Data Processing
```
[AWS Glue] → [PySpark] → [Delta Lake] → [Redshift]
     ↓           ↓            ↓              ↓
 ETL 자동화   분산 처리   ACID 보장    Data Warehouse
```

### 🤖 ML & Analytics
```
[Jupyter] → [Spark SQL] → [scikit-learn] → [Feast] → [Model Deploy]
    ↓           ↓              ↓              ↓            ↓
데이터 분석   대용량 쿼리    모델 학습    Feature Store   운영 배포
```

### 🚀 Deployment
```
[ML Model] → [FastAPI Server] → [Streamlit Cloud] → 🌐 Web UI
     ↓              ↓                   ↓
모델 서빙      REST API           사용자 인터페이스
```

### 📊 Quality & Orchestration
```
[Airflow] → [Great Expectations] → [Statistical Tests]
    ↓               ↓                       ↓
워크플로우      데이터 품질 검증      Chi-Square/KS/Z-Test
```

## 🗂️ Data Lake 구조

```
📦 Data Lake
│
├── 📁 Raw Zone (원본 데이터)
│   └── 실시간 로그 데이터
│   └── 원본 트랜잭션 데이터
│   └── 파티션: year/month/day/hour
│
├── 📁 Processed Zone (변환 데이터)
│   └── 정제된 데이터
│   └── 표준화된 스키마
│   └── Delta Lake 포맷
│
└── 📁 Curated Zone (분석 데이터)
    └── Dimension Tables (고객, 상품, 시간)
    └── Fact Tables (트랜잭션)
    └── Aggregated Data
```

## 🔄 데이터 파이프라인 Flow

```
1. 데이터 수집
   사용자 이벤트 → Logstash → S3 Raw Zone
   
2. 데이터 변환
   S3 Raw → Glue ETL → PySpark 처리 → S3 Processed
   
3. 데이터 적재
   S3 Processed → Redshift DWH (Star Schema)
   
4. 데이터 분석
   Redshift → Spark SQL → Feature Engineering
   
5. 모델 학습
   Features → scikit-learn → Model Training → Feast Store
   
6. 모델 서빙
   Feast → FastAPI → Prediction Service
   
7. 사용자 인터페이스
   FastAPI → Streamlit Cloud → 실시간 예측 결과
```

## 🎯 주요 기능

### 1️⃣ 실시간 데이터 수집
- Logstash를 통한 실시간 로그 수집
- S3에 파티셔닝된 형태로 저장
- Elasticsearch로 실시간 검색

### 2️⃣ ETL 파이프라인
- Glue를 통한 자동화된 데이터 변환
- PySpark 기반 대용량 처리
- Delta Lake ACID 트랜잭션

### 3️⃣ 데이터 품질 관리
- Great Expectations 자동 검증
- 통계적 테스트 (Chi-Square, KS, Z-Test)
- 이상치 탐지 및 처리

### 4️⃣ ML 파이프라인
- Feature Engineering 자동화
- Feast Feature Store 활용
- 모델 학습 및 최적화

### 5️⃣ 예측 서비스
- FastAPI REST API
- Streamlit 웹 인터페이스
- 실시간 예측 결과 제공

## 🌐 데모

### 🔗 Live Demo
**https://live-purchase-predict.streamlit.app/**

### 📸 주요 화면

#### 예측 서비스
- 실시간 구매 확률 예측
- 고객별 추천 상품
- 예측 결과 시각화
```

## ✨ 성과

### 📈 모델 성능
- ✅ **AUC Score: 0.974** (우수한 분류 성능)
- ✅ **구매 예측 F1-Score: 73.42%**
- ✅ **Precision: 78.17%** (예측 정확성)
- ✅ **Recall: 69.22%** (실제 구매자 탐지율)
- ⚠️ 클래스 불균형(1:120) 환경에서 달성한 성과

### 🚀 시스템 성능
- ✅ 실시간 데이터 처리: **1초 이내**
- ✅ 일일 처리 데이터: **100만 건 이상**
- ✅ API 응답 시간: **200ms 이내**
- ✅ Feature Store 조회: **10ms 이내**

```

## 📞 Contact

**김준영 (Data Engineer)**

📧 Email: ks1004mj@gmail.com  
🔗 GitHub: github.com/junyoung137

---
