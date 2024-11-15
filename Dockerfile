# Sử dụng hình ảnh Python 3.10 slim làm cơ sở
FROM python:3.10-slim

# Đặt biến môi trường PYTHONUNBUFFERED để cho phép in ra thông tin trên console ngay lập tức, không đợi đến khi buffer đầy
ENV PYTHONUNBUFFERED=1

# Update and install necessary system dependencies for MySQL
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    default-libmysqlclient-dev \
    pkg-config && \
    rm -rf /var/lib/apt/lists/*  # Giảm dung lượng ảnh Docker bằng cách xóa bộ nhớ cache của apt

# Tạo thư mục làm việc /app trong container
WORKDIR /app

# Sao chép tệp yêu cầu (requirements.txt) vào thư mục làm việc /app
COPY requirements.txt /app/

# Cài đặt các gói yêu cầu được liệt kê trong requirements.txt mà không lưu cache để tiết kiệm dung lượng
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn từ thư mục hiện tại vào thư mục làm việc /app
COPY . /app/

# Thiết lập biến môi trường cho Flask để chỉ định tệp ứng dụng chính
ENV FLASK_APP=app.py

# Thiết lập biến môi trường cho Flask để cho phép ứng dụng lắng nghe trên mọi địa chỉ IP
ENV FLASK_RUN_HOST=0.0.0.0

# Mở cổng 5001 trên container để có thể truy cập ứng dụng từ bên ngoài
EXPOSE 5001

# Chạy ứng dụng Flask với địa chỉ IP là 0.0.0.0 và cổng 5001
CMD ["flask", "run", "--host=0.0.0.0", "--port=5001"]
