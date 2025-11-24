# Day 3: EDA & Visualization - TODO

## Mục tiêu

Tạo các visualization insights từ cleaned dataset để hiểu rõ đặc điểm dữ liệu trước khi vectorization.

## Deliverables

### 1. Visualizations (lưu vào `images/`)

- [ ] **eda_skills_wordcloud.png**: WordCloud top skills từ cột `skills`
- [ ] **eda_industries_top10.png**: Bar chart top 10 industries
- [ ] **eda_work_type_distribution.png**: Pie chart phân bố Full-time/Contract/Part-time
- [ ] **eda_salary_distribution.png**: Histogram normalized_salary (filter outliers)
- [ ] **eda_salary_by_worktype.png**: Boxplot salary theo work_type
- [ ] **eda_location_heatmap.png**: Heatmap số jobs theo (state, experience_level)
- [ ] **eda_remote_vs_onsite.png**: Stacked bar chart remote vs onsite
- [ ] **eda_content_length.png**: Distribution of content length
- [ ] **eda_top_companies.png**: Top 20 companies by job count

### 2. Statistical Analysis

- [ ] Correlation analysis: salary vs (skills, experience, industry)
- [ ] Missing data patterns: visualize missing % across columns
- [ ] Outlier detection: salary, content_length

### 3. Reports

- [ ] `reports/data_exploration.md`: Tổng hợp insights
  - Dataset overview với key metrics
  - Top findings (3-5 bullet points)
  - Recommendations for modeling

## Notebook structure

### Cell 1-5: Setup & Load

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from pathlib import Path

# Load cleaned data
df = pd.read_parquet('data/processed/clean_jobs.parquet')
```

### Cell 6-10: Skills Analysis

- WordCloud từ `skills` column
- Top 20 skills bar chart
- Skills co-occurrence matrix

### Cell 11-15: Industry & Work Type

- Top 10 industries
- Work type distribution
- Industry by work_type cross-tab

### Cell 16-20: Salary Analysis

- Filter outliers (99th percentile)
- Distribution histogram
- Boxplot by work_type
- Violin plot by experience_level

### Cell 21-25: Location & Remote

- Heatmap state × experience
- Remote flag analysis
- Top cities bar chart

### Cell 26-30: Content Analysis

- Content length distribution
- Average length by industry
- Correlation: content_length vs applies/views

### Cell 31-35: Company Insights

- Top companies by job count
- Company size distribution
- Specialities wordcloud

### Cell 36-40: Generate Report

- Compile all insights
- Save to markdown
- Create summary statistics table

## Success Criteria

✅ All 9 visualizations generated and saved
✅ Report contains actionable insights
✅ Figures are high-quality (dpi=150, readable labels)
✅ No errors in notebook execution

## Estimated time: 2-3 hours

## Notes

- Use seaborn style 'whitegrid' for consistency
- Save all plots with `bbox_inches='tight'`
- Include figure captions in report
- Filter extreme outliers for better visualization
