# SkinAge API Data Specification Document
**Version:** 1.1.0  
**Target Audience:** Client Service Developers, Backend Engineers, AI Agents  
**Role of SkinAge:** **Pure Skin Diagnostic Data Provider (순수 피부 분석 데이터 제공자)**  
**Endpoint:** `POST /api/v1/analyze` (Content-Type: `multipart/form-data`)  

---

## 1. 역할 및 설계 원칙 (Design Principles)

**SkinAge**는 이미지로부터 객관적이고 과학적인 **피부 분석 데이터(28개 세부 지표, 피부 나이, 부위별 상태, 공간 통계)**만을 순수하게 제공하는 독립적인 AI 분석 엔진입니다.

* **순수 데이터 제공 (Pure Data Engine)**: 
  SkinAge는 주관적인 화장품 추천이나 특정 서비스의 비즈니스 로직에 종속되지 않고, 오직 이미지 기반의 정량적인 피부 상태 측정값만을 반환합니다.
* **비즈니스 로직의 독립성 (Separation of Concerns)**:
  전달받은 정량 데이터를 바탕으로 한 피부 타입 정의, 화장품/성분 매핑, 케어 루틴 구성, 리포트 생성 등 모든 비즈니스 로직은 클라이언트 서비스를 구축하는 개발자가 자체 정책에 맞춰 자유롭게 설계합니다.

---

## 2. API 요청 규격 (Request Specification)

### `POST /api/v1/analyze`

| 파라미터명 | 타입 | 필수 여부 | 기본값 | 설명 |
| :--- | :---: | :---: | :---: | :--- |
| `file` | `Binary/File` | **필수** | - | 분석 대상 전면 얼굴 사진 (JPEG/PNG/WebP, 512×512 이상 권장) |
| `age` | `Integer` | 선택 | `null` | 사용자 실제 만 나이. 전달 시 `age_delta` 계산 |
| `include_heatmaps` | `Boolean` | 선택 | `false` | 4채널 Base64 공간 히트맵 오버레이 포함 여부 |

---

## 3. 표준 JSON 응답 스키마 (Complete Response Payload)

```json
{
  "summary": {
    "predicted_skin_age": 23.2,
    "actual_age": 24,
    "age_delta": -0.8,
    "overall_score": 78.5,
    "skin_health_grade": "Good"
  },
  "zone_scores": [
    {
      "zone": "forehead",
      "composite_score": 76.5,
      "label": "Good",
      "occlusion_confidence": 0.95,
      "concerns": [
        { "concern": "wrinkle", "score": 82.0, "severity": "minimal" },
        { "concern": "pore_texture", "score": 61.0, "severity": "moderate" },
        { "concern": "pigmentation", "score": 75.0, "severity": "mild" },
        { "concern": "redness", "score": 88.0, "severity": "minimal" }
      ]
    },
    {
      "zone": "under_eyes",
      "composite_score": 72.0,
      "label": "Good",
      "occlusion_confidence": 1.0,
      "concerns": [
        { "concern": "wrinkle", "score": 70.0, "severity": "mild" },
        { "concern": "pore_texture", "score": 63.0, "severity": "moderate" },
        { "concern": "pigmentation", "score": 65.0, "severity": "moderate" },
        { "concern": "redness", "score": 90.0, "severity": "minimal" }
      ]
    },
    {
      "zone": "crows_feet",
      "composite_score": 75.0,
      "label": "Good",
      "occlusion_confidence": 0.95,
      "concerns": [
        { "concern": "wrinkle", "score": 72.0, "severity": "mild" },
        { "concern": "pore_texture", "score": 60.0, "severity": "moderate" },
        { "concern": "pigmentation", "score": 80.0, "severity": "minimal" },
        { "concern": "redness", "score": 88.0, "severity": "minimal" }
      ]
    },
    {
      "zone": "cheeks",
      "composite_score": 68.0,
      "label": "Fair",
      "occlusion_confidence": 1.0,
      "concerns": [
        { "concern": "wrinkle", "score": 85.0, "severity": "minimal" },
        { "concern": "pore_texture", "score": 68.0, "severity": "moderate" },
        { "concern": "pigmentation", "score": 70.0, "severity": "mild" },
        { "concern": "redness", "score": 49.0, "severity": "significant" }
      ]
    },
    {
      "zone": "nose",
      "composite_score": 58.2,
      "label": "Needs Attention",
      "occlusion_confidence": 1.0,
      "concerns": [
        { "concern": "wrinkle", "score": 80.0, "severity": "minimal" },
        { "concern": "pore_texture", "score": 42.0, "severity": "significant" },
        { "concern": "pigmentation", "score": 65.0, "severity": "moderate" },
        { "concern": "redness", "score": 46.0, "severity": "significant" }
      ]
    },
    {
      "zone": "nasolabial",
      "composite_score": 69.5,
      "label": "Fair",
      "occlusion_confidence": 1.0,
      "concerns": [
        { "concern": "wrinkle", "score": 62.0, "severity": "moderate" },
        { "concern": "pore_texture", "score": 51.0, "severity": "moderate" },
        { "concern": "pigmentation", "score": 80.0, "severity": "minimal" },
        { "concern": "redness", "score": 85.0, "severity": "minimal" }
      ]
    },
    {
      "zone": "chin",
      "composite_score": 74.0,
      "label": "Good",
      "occlusion_confidence": 1.0,
      "concerns": [
        { "concern": "wrinkle", "score": 82.0, "severity": "minimal" },
        { "concern": "pore_texture", "score": 51.0, "severity": "moderate" },
        { "concern": "pigmentation", "score": 78.0, "severity": "mild" },
        { "concern": "redness", "score": 85.0, "severity": "minimal" }
      ]
    }
  ],
  "aggregate_metrics": {
    "t_zone_score": 67.4,
    "u_zone_score": 70.5,
    "concern_averages": {
      "wrinkle": 76.1,
      "pore_texture": 56.6,
      "pigmentation": 73.3,
      "redness": 75.9
    },
    "priority_concerns": [
      {
        "rank": 1,
        "zone": "nose",
        "concern": "pore_texture",
        "score": 42.0,
        "severity": "significant"
      },
      {
        "rank": 2,
        "zone": "nose",
        "concern": "redness",
        "score": 46.0,
        "severity": "significant"
      },
      {
        "rank": 3,
        "zone": "cheeks",
        "concern": "redness",
        "score": 49.0,
        "severity": "significant"
      }
    ]
  },
  "heatmaps": null,
  "metadata": {
    "processing_time_ms": 59.9,
    "model_version": "1.0.0",
    "device": "cuda",
    "input_size": 512
  }
}
```

---

## 4. 데이터 딕셔너리 (Data Dictionary)

### 4.1. 거시 지표 (`summary`)
* **`predicted_skin_age`** (`float`): 딥러닝 모델이 추정한 생체 피부 나이 (단위: 세)
* **`actual_age`** (`int | null`): 사용자가 입력한 실제 만 나이
* **`age_delta`** (`float | null`): `predicted_skin_age - actual_age` (음수면 실제보다 젊음, 양수면 노화 진행)
* **`overall_score`** (`float`, 0~100): 가중치 적용 종합 피부 건강 점수 (100점에 가까울수록 완벽함)
* **`skin_health_grade`** (`string`): 종합 등급 (`Excellent`, `Great`, `Good`, `Fair`, `Needs Attention`, `Significant Concerns`)

---

### 4.2. 28개 부위별 세부 지표 (`zone_scores`)

총 7개 안면 구역 배열이며, 각 구역마다 4대 피부 고민을 독립 측정합니다 ($7 \times 4 = 28$개 지표).

#### 1) 7개 안면 구역 식별자 (`zone`)
* `forehead`: 이마 부위
* `under_eyes`: 눈 밑 부위
* `crows_feet`: 눈가/눈꼬리 부위
* `cheeks`: 양 볼 부위
* `nose`: 코 및 나비존 부위
* `nasolabial`: 팔자주름 부위
* `chin`: 턱 부위

#### 2) 4대 피부 고민 식별자 (`concern`)
* `wrinkle`: 주름 및 탄력 저하도
* `pore_texture`: 모공 확장 및 피부결 요철
* `pigmentation`: 기미, 잡티, 색소 불균일도
* `redness`: 붉은기, 모세혈관 확장, 홍조

#### 3) 구역별/고민별 세부 필드
| 필드명 | 타입 | 값의 범위 | 설명 |
| :--- | :---: | :---: | :--- |
| `composite_score` | `float` | `0.0 ~ 100.0` | 해당 구역의 4대 고민 산술 평균 점수 |
| `label` | `string` | 6단계 등급 | `Excellent` (90+), `Great` (80+), `Good` (70+), `Fair` (60+), `Needs Attention` (50+), `Significant Concerns` (<50) |
| `occlusion_confidence` | `float` | `0.1 ~ 1.0` | 앞머리/안경 가림 신뢰도 (1.0: 완벽 노출, <0.7: 가림 감지) |
| `concerns[].score` | `float` | `0.0 ~ 100.0` | 해당 고민의 정량 점수 (높을수록 건강/결점 없음) |
| `concerns[].severity` | `string` | 4단계 등급 | `minimal` (정상), `mild` (경미), `moderate` (주의), `significant` (집중 관리 필요) |

---

### 4.3. 부위별 집계 및 결함 순위 (`aggregate_metrics`)
서비스 개발자가 직접 반복문을 돌려 계산하지 않고 바로 통계/정렬에 활용할 수 있도록 제공되는 객관적 집계 데이터입니다:
* **`t_zone_score`** (`float`): 이마 + 코 구역의 평균 점수
* **`u_zone_score`** (`float`): 볼 + 턱 구역의 평균 점수
* **`concern_averages`** (`object`): 4대 고민 각각의 얼굴 전체 평균 점수
* **`priority_concerns`** (`array`): 28개 지표 중 점수가 가장 낮은 취약 항목 Top 3 (가림 신뢰도 반영 정렬)

---

## 5. TypeScript 인터페이스 (Front-end / Node.js)

```typescript
export type FacialZone = 
  | "forehead" 
  | "under_eyes" 
  | "crows_feet" 
  | "cheeks" 
  | "nose" 
  | "nasolabial" 
  | "chin";

export type ConcernType = 
  | "wrinkle" 
  | "pore_texture" 
  | "pigmentation" 
  | "redness";

export type SeverityGrade = 
  | "minimal" 
  | "mild" 
  | "moderate" 
  | "significant";

export interface ConcernScore {
  concern: ConcernType;
  score: number;       // 0.0 - 100.0
  severity: SeverityGrade;
}

export interface ZoneScore {
  zone: FacialZone;
  composite_score: number;
  label: string;
  occlusion_confidence: number;
  concerns: ConcernScore[];
}

export interface PriorityConcernItem {
  rank: number;
  zone: FacialZone;
  concern: ConcernType;
  score: number;
  severity: SeverityGrade;
}

export interface AggregateMetrics {
  t_zone_score: number;
  u_zone_score: number;
  concern_averages: Record<ConcernType, number>;
  priority_concerns: PriorityConcernItem[];
}

export interface SkinAgeAnalysisResult {
  summary: {
    predicted_skin_age: number;
    actual_age: number | null;
    age_delta: number | null;
    overall_score: number;
    skin_health_grade: string;
  };
  zone_scores: ZoneScore[];
  aggregate_metrics: AggregateMetrics;
  heatmaps?: {
    wrinkle?: string;
    pore_texture?: string;
    pigmentation?: string;
    redness?: string;
  } | null;
  metadata: {
    processing_time_ms: number;
    model_version: string;
    device: string;
    input_size: number;
  };
}
```

---

## 6. 클라이언트 서비스 연동 예제 (Python)

```python
import requests

def fetch_skin_analysis(image_bytes: bytes, user_age: int = 24) -> dict:
    url = "http://skinage-api:8000/api/v1/analyze"
    files = {"file": ("face.jpg", image_bytes, "image/jpeg")}
    data = {"age": user_age, "include_heatmaps": False}
    
    response = requests.post(url, files=files, data=data)
    response.raise_for_status()
    return response.json()
```
