# from huggingface_hub import HfApi
#
# # Thay thế bằng API key của bạn
# api_key = "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"
# username = "datnguyentien204"  # Thay bằng tên người dùng hoặc tổ chức của bạn
#
# # Khởi tạo đối tượng API với token
# api = HfApi(token=api_key)
#
# def get_user_datasets(username):
#     try:
#         # Lấy danh sách các datasets, bao gồm cả private
#         datasets = api.list_datasets(author=username, use_auth_token=True)
#
#         # Trích xuất tên của các datasets
#         repositories = [dataset.id for dataset in datasets]
#         return repositories
#
#     except Exception as e:
#         print(f"Đã xảy ra lỗi: {e}")
#         return []
#
# repos = get_user_datasets(username=username)
# print("Danh sách datasets từ tài khoản của bạn (bao gồm cả private):")
# for repo in repos:
#     print(repo)

from huggingface_hub import HfApi
from cryptography.fernet import Fernet
import json
import os
# Hàm tạo và lưu key mã hóa
def generate_encryption_key():
    if not os.path.exists("encryption_key.key"):
        key = Fernet.generate_key()
        with open("encryption_key.key", "wb") as key_file:
            key_file.write(key)
        print("Key mã hóa đã được tạo và lưu.")
    else:
        print("Key mã hóa đã tồn tại, không tạo mới.")

# Hàm tải key mã hóa từ file
def load_encryption_key():
    with open("encryption_key.key", "rb") as key_file:
        return key_file.read()

# Hàm mã hóa và lưu dữ liệu vào file
def encrypt_and_save_data(data, filename="user_data.enc"):
    key = load_encryption_key()
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(json.dumps(data).encode())
    with open(filename, "wb") as file:
        file.write(encrypted_data)

# Hàm giải mã và đọc dữ liệu từ file
def decrypt_and_load_data(filename="user_data.enc"):
    key = load_encryption_key()
    fernet = Fernet(key)
    with open(filename, "rb") as file:
        encrypted_data = file.read()
    decrypted_data = fernet.decrypt(encrypted_data)
    return json.loads(decrypted_data.decode())

# Hàm kiểm tra tính hợp lệ của API key và username
def check_login(api_key, username):
    api = HfApi(token=api_key)
    try:
        # Kiểm tra thông tin người dùng từ API
        user_info = api.whoami()
        if user_info['name'] == username:
            print("Thông tin đăng nhập hợp lệ.")
            return True
        else:
            print("Tên người dùng không hợp lệ.")
            return False
    except Exception as e:
        print(f"API key không hợp lệ: {e}")
        return False

# Hàm xử lý dựa trên status
def handle_status(status, api_key=None, username=None):
    if status == 1:
        # Nếu status là 1, kiểm tra và ghi thông tin vào file mã hóa
        if check_login(api_key, username):
            encrypt_and_save_data({"api_key": api_key, "username": username})
            print("Thông tin đã được ghi vào file mã hóa.")
        else:
            print("Thông tin đăng nhập không hợp lệ, không ghi vào file.")
    elif status == 2:
        # Nếu status là 2, đọc thông tin từ file mã hóa
        try:
            data = decrypt_and_load_data()
            x=check_login(data["api_key"], data["username"])
            if x:
                print("Thông tin đã giải mã từ file:", data)
        except Exception as e:
            print(f"Lỗi khi đọc file mã hóa: {e}")
    else:
        print("Giá trị status không hợp lệ. Vui lòng sử dụng 1 hoặc 2.")

# Khởi tạo key mã hóa (chỉ cần chạy một lần khi chưa có key)
generate_encryption_key()

# Ví dụ sử dụng
# status = 1  # Thay đổi giá trị status để kiểm tra
# api_key = "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"
# username = "datnguyentien204"  # Thay bằng tên người dùng hoặc tổ chức của bạn
# #
# # # Gọi hàm xử lý với status và thông tin đầu vào
# handle_status(status, api_key, username)

# Đổi status sang 2 để kiểm tra đọc từ file
status = 2
handle_status(status)
