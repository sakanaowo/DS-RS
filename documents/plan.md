---

````markdown
# SPECIFICATION & PLAN: JOB RECOMMENDATION SYSTEM

**Project Name:** Intelligent Job Matching System
**Author:** [Tên Của Bạn]
**Date:** [Ngày bắt đầu]
**Tech Stack:** Python, Streamlit, Scikit-learn, Sentence-Transformers, Pandas.

---

## I. TỔNG QUAN (Overview)

Xây dựng hệ thống gợi ý việc làm dựa trên nội dung (Content-Based Filtering). Hệ thống phân tích mô tả công việc (Job Description) và so khớp với kỹ năng/mong muốn của người dùng để đưa ra các gợi ý phù hợp nhất bằng công nghệ Vector Search (Embeddings).

### Mục tiêu

1.  **Input:** Người dùng nhập kỹ năng hoặc tiêu đề mong muốn (ví dụ: "Python Backend Developer").
2.  **Process:** Hệ thống vector hóa input và tìm kiếm trong cơ sở dữ liệu việc làm.
3.  **Output:** Danh sách Top-K công việc phù hợp nhất, kèm theo độ tương đồng (Similarity Score).

---

## II. KIẾN TRÚC HỆ THỐNG (System Architecture)

### 1. Cấu trúc thư mục (Directory Structure)

Tuân thủ mô hình Clean Architecture đơn giản hóa cho Data Science.

```text
job-recommendation-system/
├── data/
│   ├── raw/                 # Chứa file CSV gốc (VD: linkedin_jobs.csv)
│   └── processed/           # Chứa file đã làm sạch & file vectors (.pkl)
├── notebooks/               # Jupyter Notebooks để nháp và vẽ biểu đồ
├── src/                     # Source code logic chính
│   ├── loader.py            # Hàm load dữ liệu
│   ├── preprocessing.py     # Hàm xử lý text (NLP cleaning)
│   └── recommender.py       # Hàm tính toán Similarity & Vectorization
├── app.py                   # Main UI (Streamlit)
├── requirements.txt         # Danh sách thư viện
└── README.md                # Tài liệu này
```

### 2\. Công nghệ sử dụng (Tech Stack)

- **Ngôn ngữ:** Python 3.9+
- **Data Processing:** Pandas, NumPy.
- **NLP & Vectorization:**
  - _Cơ bản:_ Scikit-learn (TF-IDF).
  - _Nâng cao:_ Sentence-Transformers (HuggingFace models).
- **Recommendation Core:** Cosine Similarity.
- **User Interface:** Streamlit.
- **Visualization:** Matplotlib / Seaborn.

---

## III. LUỒNG XỬ LÝ DỮ LIỆU (Data Pipeline)

### Bước 1: Thu thập & Tiền xử lý (Data Preprocessing)

- **Nguồn dữ liệu:** LinkedIn Job Postings (\> 2.000 bản ghi).
- **Làm sạch (Cleaning):**
  - Xử lý giá trị `NULL` (Fill 'Unknown').
  - Loại bỏ các bản ghi trùng lặp (Drop duplicates).
  - Gộp các cột text quan trọng: `content = job_title + " " + job_description`.
- **Chuẩn hóa Text (NLP):**
  - Chuyển về chữ thường (Lowercase).
  - Loại bỏ ký tự đặc biệt, dấu câu, HTML tags.
  - Loại bỏ Stop-words (the, a, an, is...).

### Bước 2: Vector hóa (Feature Engineering)

- Sử dụng mô hình **`all-MiniLM-L6-v2`** (hoặc TF-IDF) để biến đổi cột `content` thành ma trận Vector.
- Lưu trữ ma trận này (hoặc tính toán in-memory khi chạy app) để tái sử dụng.

### Bước 3: Cơ chế Gợi ý (Inference)

1.  Nhận `user_query` từ giao diện.
2.  Tiền xử lý & Vector hóa `user_query` (dùng cùng model với Bước 2).
3.  Tính **Cosine Similarity** giữa `vector_query` và `Matrix_Jobs`.
4.  Sắp xếp giảm dần theo điểm số (Score).
5.  Lấy Top 5-10 kết quả.

---

## IV. KHÁM PHÁ DỮ LIỆU HIỆN CÓ (Dataset Audit)

### 1. Tổng quan thư mục `data/archive/`

- `postings.csv`: 123.849 bản ghi, 31 cột mô tả job (title, description, compensation, remote flag, location, work type...). Các trường liên quan lương (`pay_period`, `currency`, `min_salary`, `max_salary`) thiếu ~70% dữ liệu; `formatted_work_type` phủ 98% bản ghi (đa số Full-time). `remote_allowed` chỉ có dữ liệu cho ~12% bản ghi (15.246 job đánh dấu remote). Top location hiện tại tập trung ở US (New York, Chicago, Houston...).
- `jobs/benefits.csv`: 67.943 dòng/30.023 job, liệt kê lợi ích (Medical insurance, 401k...). `job_skills.csv`: 213.768 dòng/126.807 job; top skill groups gồm Information Technology (IT), Sales (SALE), Management (MGMT), Manufacturing (MNFC), Health Care Provider (HCPR). `job_industries.csv`: 164.808 dòng/127.125 job; các ngành nổi bật: Hospitals & Health Care, Retail, IT Services, Staffing & Recruiting. `salaries.csv`: 40.785 job có cấu trúc lương riêng (23k yearly, 16k hourly, số ít monthly/weekly).
- `companies/companies.csv`: 141.027 công ty với mô tả chi tiết, địa điểm, quy mô. Đi kèm các bảng phụ: `company_industries.csv`, `company_specialities.csv`, `employee_counts.csv` cho phép làm phong phú thông tin employer.
- `mappings/skills.csv` (36 kỹ năng) và `mappings/industries.csv` (422 ngành) dùng để join với bảng job tương ứng.

### 2. Gợi ý tích hợp & vấn đề cần lưu ý

1.  Khoá chính để nối dữ liệu job là `job_id`. Cần chuẩn hóa pipeline để merge `postings` với `job_skills`, `job_industries`, `salaries`, `benefits`, và enrich thông tin công ty qua `company_id`.
2.  Thiếu dữ liệu lương và remote khá lớn ⇒ nên ưu tiên tạo cờ nhị phân (has_salary_info, has_remote_flag) và cân nhắc suy ra khoảng lương trung bình theo ngành/kỹ năng nếu cần.
3.  Cột văn bản `description` dài, chứa nhiều dòng; cần làm sạch (loại bỏ xuống dòng dư, HTML) trước khi vector hóa.
4.  Bộ kỹ năng/industry dạng mã ⇒ phải map sang tên đầy đủ để hiển thị đẹp và tạo feature phân loại.
5.  Khối lượng dữ liệu đủ lớn (120k job) nhưng vẫn vừa phải để tiền xử lý offline và lưu vector hoá (~120k \* 384 dims < 200 MB).

---

## V. KẾ HOẠCH TRIỂN KHAI CHI TIẾT (10 Ngày)

### Giai đoạn 1: Dữ liệu & Phân tích (Ngày 1 - 3)

- [x] **Ngày 1: Setup & Load Data**
  - [x] Cố định cấu trúc thư mục (`data/raw`, `data/processed`) và script copy từ `data/archive`.
  - [x] Viết notebook/script audit: thống kê missing, phân bố `pay_period`, `formatted_work_type`, `remote_allowed`, top kỹ năng/ngành; lưu kết quả vào `reports/data_audit.md`.
  - [x] Tạo `loader.py` để đọc `postings`, join với bảng phụ (kỹ năng, ngành, lương, benefits) dựa trên `job_id`/`company_id`.
- [x] **Ngày 2: Làm sạch dữ liệu (Data Cleaning)**
  - [x] Chuẩn hóa văn bản: bỏ HTML, xuống dòng, ký tự đặc biệt; chuẩn hóa unicode.
  - [x] Loại bỏ job thiếu `title` hoặc `description`, drop duplicates theo (`job_id`, `listed_time`).
  - [x] Chuẩn hóa trường location (tách city/state), xử lý value trống bằng "Unknown".
  - [x] Viết `clean_text()` + `prepare_features()` trong `preprocessing.py` và lưu `data/processed/clean_jobs.parquet` + metadata (mapping kỹ năng/ngành).
- [x] **Ngày 3: EDA & Trực quan hóa**
  - [x] Sinh biểu đồ: phân bố job theo top 10 industry/skill group, heatmap số job theo (state, experience level), histogram normalized_salary vs work_type.
  - [x] Tạo WordCloud kỹ năng + biểu đồ tỉ lệ Full-time/Contract/Part-time, remote vs onsite.
  - [x] Xuất ảnh `.png` vào `images/` và ghép insight vào `reports/data_exploration.md`.

### Giai đoạn 2: Xây dựng Model (Ngày 4 - 6)

- [ ] **Ngày 4: Vector hóa (Core Logic)**
  - Thử nghiệm TF-IDF vs `all-MiniLM-L6-v2` trên sample để so sánh tốc độ/kích thước; quyết định mô hình chính.
  - Viết module `src/vector_store.py` để sinh & cache embeddings (pickle/parquet) + metadata (dim, model_name, updated_at).
- [ ] **Ngày 5: Xây dựng hàm Recommend**
  - Implement `get_recommendations(query, filters)` với pipeline: preprocess query → embedding → cosine similarity (faiss hoặc sklearn) → enrich thông tin lương/kỹ năng.
  - Viết unit test cho các trường hợp filter location/industry.
  - Dùng notebook kiểm thử với ít nhất 5 persona (Python dev, Nurse, Sales manager...).
- [ ] **Ngày 6: Tối ưu & Đánh giá**
  - Đánh giá bằng Precision@5/10 dựa trên bộ query thủ công + heuristic (matching skill keywords).
  - Benchmark thời gian đáp ứng, tối ưu cache, tune số lượng kết quả, thêm rerank nếu cần.
  - Điều chỉnh bước tiền xử lý (n-grams, bổ sung keyword expansion) dựa trên feedback.

### Giai đoạn 3: Giao diện & Hoàn thiện (Ngày 7 - 9)

- [ ] **Ngày 7: Streamlit UI cơ bản**
  - Layout Streamlit: sidebar filter (Location, Work Type, Experience), main area hiển thị cards.
  - Kết nối tới vector store + loader, bảo đảm cache dữ liệu khi app khởi động.
  - Thêm khối insight nhỏ (summary dataset) để người dùng biết nguồn dữ liệu.
- [ ] **Ngày 8: Tính năng Nâng cao (Context-Aware)**
  - Bổ sung lọc theo industry/skills, slider salary range (dựa trên normalized_salary).
  - Thêm explainability: hiển thị highlight kỹ năng/keyword match giữa query và job.
  - Viết logging truy vết query để dùng cho đánh giá sau.
- [ ] **Ngày 9: Viết báo cáo**
  - Tài liệu hóa quy trình: mô tả dataset, cleaning, EDA, model, UI.
  - Đính kèm biểu đồ từ `images/`, bảng so sánh mô hình, hướng dẫn chạy.
  - Chuẩn bị phụ lục: danh sách câu hỏi kiểm thử, feedback.

### Giai đoạn 4: Đóng gói (Ngày 10)

- [ ] **Ngày 10: Final Polish**
  - Quay video demo (3-5 phút).
  - Clean code, thêm comments.
  - Zip toàn bộ project theo đúng quy cách nộp bài.

---

## VI. YÊU CẦU PHẦN MỀM (Dependencies)

Nội dung file `requirements.txt`:

```text
pandas==2.0.3
numpy==1.24.3
scikit-learn==1.3.0
sentence-transformers==2.2.2
streamlit==1.25.0
matplotlib==3.7.2
seaborn==0.12.2
wordcloud==1.9.2
```

```

```
