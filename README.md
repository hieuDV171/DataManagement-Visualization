# Superstore Sales Dashboard

Dashboard phân tích dữ liệu bán hàng Superstore bằng Streamlit và Plotly. Ứng dụng tập trung vào KPI, xu hướng theo tháng, phân tích theo khu vực, sản phẩm, phân khúc và tác động của chiết khấu đến lợi nhuận.

## Chạy dự án

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Nếu dùng Command Prompt:

```bat
.venv\Scripts\activate.bat
```

## Cấu trúc chính

- `app.py` - ứng dụng Streamlit chính
- `SuperStoreOrders.csv` - dữ liệu đầu vào
- `requirements.txt` - các thư viện cần cài
