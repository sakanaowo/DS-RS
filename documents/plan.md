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

- [x] **Ngày 4: Vector hóa (Core Logic)**
  - [x] Thử nghiệm TF-IDF vs `all-MiniLM-L6-v2` trên sample để so sánh tốc độ/kích thước; quyết định mô hình chính.
  - [x] Tích hợp FAISS cho similarity search hiệu suất cao.
  - [x] Tạo notebook `3_model_experiment.ipynb` với đầy đủ benchmark và comparison.
  - [x] Lưu embeddings và models vào `models/` (tfidf_vectorizer.pkl, tfidf_matrix.npz, minilm_embeddings.npy, faiss_index.bin).
  - [x] Viết module `src/vector_store.py` để load models và thực hiện search.
- [x] **Ngày 5: Xây dựng hàm Recommend & Đánh giá** _(Hoàn thành 25/11/2025)_
  - [x] Implement `get_recommendations(query, filters)` với pipeline: preprocess query → embedding → cosine similarity (faiss/sklearn) → enrich thông tin.
  - [x] Viết `src/recommender.py` với 3 search methods (TF-IDF, MiniLM, FAISS) + 7 filter types.
  - [x] Viết 20+ unit tests trong `tests/test_recommender.py`.
  - [x] Tạo notebook `4_evaluation.ipynb` kiểm thử với 7 personas (Python dev, Data Scientist, Nurse, Sales, PM, Frontend, DevOps).
  - [x] Đánh giá Precision@5/10: đạt **94.3% P@5** và **90.0% P@10** (vượt target 70%).
  - [x] Benchmark tốc độ: FAISS 14.6ms, MiniLM 13.3ms, TF-IDF 49.1ms (tất cả <100ms target).
  - [x] Tạo visualizations và báo cáo trong `documents/day5/`.
- [x] **Ngày 6: Streamlit UI** _(Hoàn thành 25/11/2025)_
  - [x] Build giao diện với sidebar filters (7 types), result cards, dataset summary.
  - [x] Tích hợp `JobRecommender` vào Streamlit app với @st.cache_resource.
  - [x] Thêm explainability (highlight matched keywords/skills trong job cards).
  - [x] Tạo app.py (340 lines) với professional styling và custom CSS.
  - [x] 3 search methods selector (FAISS/MiniLM/TF-IDF).
  - [x] 4 stat boxes: Total Jobs (123,842), Companies (~50k), Locations (~10k), Indexed (10k).
  - [x] Welcome screen với instructions và example queries.
  - [x] Job cards hiển thị: title, company, location, work type, salary, matched skills, similarity score.

### Giai đoạn 3: Giao diện & Hoàn thiện (Ngày 6 - 8)

- [x] **Ngày 6: Streamlit UI** _(Hoàn thành 25/11/2025)_
  - [x] Layout Streamlit: sidebar filter (Location, Work Type, Experience, Salary, Remote, Industry/Skills), main area hiển thị cards.
  - [x] Kết nối tới `JobRecommender` + `VectorStore`, cache dữ liệu khi app khởi động.
  - [x] Thêm khối insight/summary dataset để người dùng biết nguồn dữ liệu.
  - [x] Hiển thị matched skills/keywords trong result cards (explainability).
  - [x] Method comparison: 3 search options cho user chọn.
  - [x] Performance display: Hiển thị search time và số kết quả.
- [x] **Ngày 7: Tính năng Nâng cao** _(Hoàn thành 26/11/2025)_
  - [x] Method selector (TF-IDF/MiniLM/FAISS) - Already done in Day 6.
  - [x] Performance metrics display với interactive Plotly chart (dual-axis: speed vs precision).
  - [x] Export results to CSV/JSON với download buttons và metadata.
  - [x] Logging truy vết query vào `logs/query_history.json` để analytics.
  - [x] Sidebar toggle "Show Method Comparison" với quick stats.
  - [x] Performance analysis panel: chart + 4 metrics cards (time, count, method, relevance).
  - [x] Enhanced 3-column layout: success message + CSV button + JSON button.
- [ ] **Ngày 8: Viết báo cáo cuối**
  - Tài liệu hóa quy trình: dataset audit → cleaning → EDA → modeling → evaluation → UI.
  - Đính kèm biểu đồ từ `images/`, bảng so sánh mô hình (Day 4-5 results).
  - Hướng dẫn deployment và future improvements.
  - Chuẩn bị phụ lục: test personas, evaluation metrics.

### Giai đoạn 4: Đóng gói (Ngày 9)

- [ ] **Ngày 9: Final Polish & Packaging**
  - Clean code, thêm docstrings và comments cần thiết.
  - Update README.md với hướng dẫn chạy đầy đủ.
  - Quay video demo (3-5 phút) nếu cần.
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
