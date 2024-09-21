from huggingface_hub import HfApi,HfFileSystem
from cryptography.fernet import Fernet
import json
import zipfile
import os
import sys
import time
from PyQt5.QtWidgets import QDialog, QApplication, QVBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QFileDialog, QMessageBox,QInputDialog, QProgressBar, QApplication,QComboBox
from PyQt5.QtCore import Qt

### CHECK LOGIN HUGGINGFACE
def check_login(self, api_key, username):
    api = HfApi(token=api_key)
    msg_box = QMessageBox(self)
    try:
        user_info = api.whoami()
        if user_info['name'] == username:
            msg_box.setWindowTitle("Success")
            msg_box.setText("Check login successfully.")
            return True
        else:
            msg_box.setWindowTitle("Error")
            msg_box.setText("Username is invalid. Please check again.")
            msg_box.exec_()
            return False
    except Exception as e:
        print(f"API is invalid: {e}")
        return False

### ENCRYPT AND SAVE DATA
def load_encryption_key():
    with open("encryption_key.key", "rb") as key_file:
        return key_file.read()

def encrypt_and_save_data(data, filename="user_data.enc"):
    key = load_encryption_key()
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(json.dumps(data).encode())
    with open(filename, "wb") as file:
        file.write(encrypted_data)

### DECRYPT AND LOAD DATA
def decrypt_and_load_data(filename="user_data.enc"):
    key = load_encryption_key()
    fernet = Fernet(key)
    with open(filename, "rb") as file:
        encrypted_data = file.read()
    decrypted_data = fernet.decrypt(encrypted_data)
    return json.loads(decrypted_data.decode())

def generate_encryption_key():
    if not os.path.exists("encryption_key.key"):
        key = Fernet.generate_key()
        with open("encryption_key.key", "wb") as key_file:
            key_file.write(key)
        print("Key decrypted successfully.")
    else:
        print("Key decrypted already exists. Skip.")

def login_hugff(self, status, api_key=None, username=None):
    if status == 1:
        # Attempt login with provided API key and username
        if check_login(self, api_key, username):
            # Save credentials if login is successful
            encrypt_and_save_data({"api_key": api_key, "username": username})
            return True,None
        else:
            return False,None
            # # Show error message with options to "Try Again" or "Close"
            # msg_box = QMessageBox(self)
            # msg_box.setWindowTitle("Error")
            # msg_box.setText("Login failed. Please check your API key and username.")
            # msg_box.setStandardButtons(QMessageBox.Retry | QMessageBox.Close)
            # msg_box.setDefaultButton(QMessageBox.Retry)
            # choice = msg_box.exec_()
            # if choice == QMessageBox.Retry:
            #     api_key, ok_key = QInputDialog.getText(self, "API Key", "Enter your Hugging Face API key:")
            #     if not ok_key:
            #         return
            #     username, ok_user = QInputDialog.getText(self, "Username", "Enter your Hugging Face username:")
            #     if not ok_user:
            #         return
            #     login_hugff(self, status , api_key, username)

            # elif choice == QMessageBox.Close:
            #     return

    elif status ==2:
        try:
            data = decrypt_and_load_data()
            x=check_login(self, data["api_key"], data["username"])
            if x:
                return data["api_key"], data["username"]
            else:
                return None, None
        except Exception as e:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Error")
            msg_box.setText("Password and Username are incorrect. Please relogin.")
            msg_box.exec_()


### GET USER LIST DATASETS
def get_user_datasets(self):
    ## CHECKING USER INFORMATION
    api_key, username = login_hugff(self, 2)
    if api_key is None or username is None:
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Error")
        msg_box.setText("Password and Username are incorrect. Please relogin.")
        msg_box.exec_()
        return []

    api = HfApi(token=api_key)
    try:
        datasets = api.list_datasets(author=username, use_auth_token=True,full=True)
        repositories = [dataset.id for dataset in datasets]
        combo_box_dialog = QDialog(self)
        combo_box_dialog.setWindowTitle("Select dataset repository")
        layout = QVBoxLayout(combo_box_dialog)

        label = QLabel("Choose a Huggingface Dataset Repository:")
        layout.addWidget(label)

        # Create a QComboBox and add the repository options
        combo_box = QComboBox(combo_box_dialog)
        combo_box.addItems(repositories)
        layout.addWidget(combo_box)

        # Create an OK button to confirm the selection
        ok_button = QPushButton("OK", combo_box_dialog)
        layout.addWidget(ok_button)

        # Define the function to handle the OK button click
        def on_ok_clicked():
            selected_repo = combo_box.currentText()
            combo_box_dialog.accept()
            return selected_repo

        ok_button.clicked.connect(on_ok_clicked)

        # Execute the dialog and get the selected repository
        if combo_box_dialog.exec_() == QDialog.Accepted:
            repo = combo_box.currentText()
        else:
            QMessageBox.information(self, 'Information!', 'Please select a Huggingface Dataset Repository.')
            return

        return repo

    except Exception as e:
        print(f"Error: {e}")
        return []

### CREATE NEW DATASET REPOSITORY
def create_new_dataset_repository(self):
    class CreateDatasetDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Create New Dataset Repository")
            self.resize(400, 400)

            # Layout
            layout = QVBoxLayout(self)

            # Repository Name
            self.repo_name_label = QLabel("Repository Name:", self)
            self.repo_name_input = QLineEdit(self)
            layout.addWidget(self.repo_name_label)
            layout.addWidget(self.repo_name_input)

            # Upload Option
            self.upload_option_label = QLabel("Upload Option:", self)
            self.upload_option_combo = QComboBox(self)
            self.upload_option_combo.addItems(["No Upload", "Upload Files", "Upload Folder"])
            self.upload_option_combo.currentIndexChanged.connect(self.update_upload_option)
            layout.addWidget(self.upload_option_label)
            layout.addWidget(self.upload_option_combo)

            # Upload Files
            self.files_label = QLabel("Select Files:", self)
            self.files_button = QPushButton("Choose Files", self)
            self.files_button.clicked.connect(self.select_files)
            self.files_button.setVisible(False)
            layout.addWidget(self.files_label)
            layout.addWidget(self.files_button)

            # Upload Folder
            self.folder_label = QLabel("Select Folder:", self)
            self.folder_button = QPushButton("Choose Folder", self)
            self.folder_button.clicked.connect(self.select_folder)
            self.folder_button.setVisible(False)
            layout.addWidget(self.folder_label)
            layout.addWidget(self.folder_button)

            # Private Checkbox
            self.private_checkbox = QCheckBox("Private Repository", self)
            layout.addWidget(self.private_checkbox)

            # Create Button
            self.create_button = QPushButton("Create Repository", self)
            self.create_button.clicked.connect(self.create_repository)
            layout.addWidget(self.create_button)

            self.files = []
            self.folder_path = None

        def update_upload_option(self):
            option = self.upload_option_combo.currentText()
            if option == "Upload Files":
                self.files_button.setVisible(True)
                self.folder_button.setVisible(False)
                self.files = []
            elif option == "Upload Folder":
                self.files_button.setVisible(False)
                self.folder_button.setVisible(True)
                self.folder_path = None
            else:
                self.files_button.setVisible(False)
                self.folder_button.setVisible(False)
                self.files = []
                self.folder_path = None

        def select_files(self):
            self.files, _ = QFileDialog.getOpenFileNames(self, "Select Files to Upload")
            if self.files:
                self.files_label.setText(f"Selected Files: {len(self.files)} file(s)")

        def select_folder(self):
            self.folder_path = QFileDialog.getExistingDirectory(self, "Select Folder to Upload")
            if self.folder_path:
                self.folder_label.setText(f"Selected Folder: {os.path.basename(self.folder_path)}")

        def create_repository(self):
            repo_name = self.repo_name_input.text().strip()
            private = self.private_checkbox.isChecked()
            upload_option = self.upload_option_combo.currentText()

            if not repo_name:
                QMessageBox.warning(self, "Input Error", "Repository name cannot be empty.")
                return

            # Hugging Face API call to create the new dataset repository
            api_key, username = login_hugff(self, 2)
            if not api_key or not username:
                QMessageBox.critical(self, "Error", "Please log in to Hugging Face before creating a repository.")
                return

            api = HfApi(token=api_key)

            try:
                # Create repository
                api.create_repo(repo_id=repo_name, repo_type="dataset", private=private)
                QMessageBox.information(self, "Success", f"Repository '{repo_name}' created successfully!")


                # Handle upload based on selected option
                if upload_option == "Upload Files":
                    if not self.files:
                        QMessageBox.warning(self, "Input Error", "Please select at least one file.")
                        return

                    # Upload files
                    for file in self.files:
                        api.upload_file(
                            path_or_fileobj=file,
                            path_in_repo=os.path.basename(file),
                            repo_id=f"{username}/{repo_name}",
                            repo_type="dataset"
                        )

                    QMessageBox.information(self, "Upload Success", f"Files uploaded to '{repo_name}' successfully!")
                    # CLONE GIT LINK
                    repo_url = f"https://huggingface.co/datasets/{username}/{repo_name}"
                    clone_link = f"git clone {repo_url}"
                    QMessageBox.information(self, "Clone Link",
                                            f"Repository URL: {repo_url}\nClone Command: {clone_link}. Note: If you don't have Git LFS, please run 'git lfs install' before cloning.")

                elif upload_option == "Upload Folder":
                    if not self.folder_path:
                        QMessageBox.warning(self, "Input Error", "Please select a folder.")
                        return

                    # Gather all files from the folder, including subfolders
                    all_files = []
                    for root, _, files in os.walk(self.folder_path):
                        for file in files:
                            all_files.append(os.path.join(root, file))

                    # Check number of files and prompt for zipping if necessary
                    if len(all_files) > 2000:
                        reply = QMessageBox.question(
                            self,
                            "Too Many Files",
                            "The folder contains more than 2000 files. Do you want to zip the folder before uploading?",
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.No
                        )
                        if reply == QMessageBox.Yes:
                            zip_path = os.path.join(os.path.dirname(self.folder_path), os.path.basename(self.folder_path) + ".zip")
                            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                                for file in all_files:
                                    zipf.write(file, os.path.relpath(file, self.folder_path))
                            self.folder_path = zip_path
                        else:
                            QMessageBox.warning(self, "Error", "Cannot upload more than 2000 files without zipping.")
                            return

                    # Upload the folder (or zipped folder)
                    api.upload_folder(
                        folder_path=self.folder_path,
                        repo_id=f"{username}/{repo_name}",
                        repo_type="dataset"
                    )
                    QMessageBox.information(self, "Upload Success", f"Folder uploaded to '{repo_name}' successfully!")

                    # CLONE GIT LINK
                    repo_url = f"https://huggingface.co/datasets/{username}/{repo_name}"
                    clone_link = f"git clone {repo_url}"
                    QMessageBox.information(self, "Clone Link",
                                            f"Repository URL: {repo_url}\nClone Command: {clone_link}. Note: If you don't have Git LFS, please run 'git lfs install' before cloning.")

                self.accept()

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create repository or upload files: {e}")
                self.reject()


    # Show the dialog
    dialog = CreateDatasetDialog(self)
    dialog.exec_()

### UPLOAD FILES OR FOLDER TO HUGGINGFACE
class UploadProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Upload Progress")
        self.resize(500, 300)
        self.layout = QVBoxLayout(self)
        self.status_label = QLabel("Preparing to upload...", self)
        self.progress_bar = QProgressBar(self)
        self.network_speed_label = QLabel("Network Speed: 0 KB/s", self)  # Hiển thị tốc độ mạng
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setRange(0, 100)
        self.layout.addWidget(self.status_label)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.network_speed_label)  # Thêm nhãn cho tốc độ mạng

    def update_status(self, status, progress, speed=0):
        self.status_label.setText(status)
        self.progress_bar.setValue(progress)
        self.network_speed_label.setText(f"Network Speed: {speed:.2f} KB/s")

# Hàm tải file lên với hiển thị tốc độ mạng
def upload_file_with_progress(api, file_path, repo_id, progress_dialog):
    CHUNK_SIZE = 5 * 1024 * 1024  # Chia file thành chunk 5MB
    file_size = os.path.getsize(file_path)
    progress = 0
    start_time = time.time()

    with open(file_path, "rb") as f:
        for chunk_start in range(0, file_size, CHUNK_SIZE):
            chunk = f.read(CHUNK_SIZE)
            api.upload_file(
                path_or_fileobj=chunk,
                path_in_repo=os.path.basename(file_path),
                repo_id=repo_id,
                repo_type="dataset",
                resume_upload=True
            )

            # Cập nhật thanh tiến trình và tốc độ mạng
            progress += len(chunk)
            elapsed_time = time.time() - start_time
            speed = (progress / elapsed_time) / 1024  # Tính KB/s
            percent_done = int((progress / file_size) * 100)
            progress_dialog.update_status(f"Uploading {os.path.basename(file_path)}", percent_done, speed)

def upload_files_to_existing_repo_files(self):
    class UploadProgressDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Upload Progress")
            self.resize(500, 300)
            self.layout = QVBoxLayout(self)
            self.status_label = QLabel("Preparing to upload...", self)
            self.progress_bar = QProgressBar(self)
            self.progress_bar.setAlignment(Qt.AlignCenter)
            self.progress_bar.setRange(0, 100)
            self.layout.addWidget(self.status_label)
            self.layout.addWidget(self.progress_bar)

        def update_status(self, status, progress):
            self.status_label.setText(status)
            self.progress_bar.setValue(progress)

    # Choose repository
    repo = get_user_datasets(self)
    if not repo:
        QMessageBox.warning(self, "Error", "Please select a repository.")
        return

    # Choose files to upload
    files, _ = QFileDialog.getOpenFileNames(self, "Select Files to Upload", "", "All Files (*)")
    if not files:
        QMessageBox.warning(self, "Error", "Please select at least one file.")
        return

    if len(files) > 2000:
        QMessageBox.warning(self, "Error", "You can only select up to 2000 files.")
        return

    # Show progress dialog
    progress_dialog = UploadProgressDialog(self)
    progress_dialog.show()

    # LOGIN HUGGINGFACE
    api_key, username = login_hugff(self, 2)
    if not api_key or not username:
        QMessageBox.critical(self, "Error", "Please log in to Hugging Face before uploading files.")
        progress_dialog.close()
        return

    api = HfApi(token=api_key)

    # Upload files
    total_files = len(files)
    for idx, file in enumerate(files):
        try:
            progress_dialog.update_status(f"Uploading {os.path.basename(file)} ({idx + 1}/{total_files})...",
                                          int((idx / total_files) * 100))
            QApplication.processEvents()

            # Upload file
            api.upload_file(
                path_or_fileobj=file,
                path_in_repo=os.path.basename(file),
                repo_id=repo,
                repo_type="dataset"
            )

            # Update progress
            progress_dialog.update_status(f"Uploaded {os.path.basename(file)} successfully.",
                                          int(((idx + 1) / total_files) * 100))

        except Exception as e:
            ## UPLOAD FAILED
            progress_dialog.update_status(f"Failed to upload {os.path.basename(file)}: {e}",
                                          int((idx / total_files) * 100))
            QMessageBox.critical(self, "Upload Error", f"Failed to upload {os.path.basename(file)}: {e}")

     #UPLOAD SUCCESS
    progress_dialog.update_status("All files uploaded successfully!", 100)
    QMessageBox.information(self, "Upload Completed", "All files uploaded successfully!")
    progress_dialog.close()
    # CLONE GIT LINK
    repo_url = f"https://huggingface.co/datasets/{username}/{repo}"
    clone_link = f"git clone {repo_url}"
    QMessageBox.information(self, "Clone Link",
                            f"Repository URL: {repo_url}\nClone Command: {clone_link}. Note: If you don't have Git LFS, please run 'git lfs install' before cloning.")

def upload_folder_to_existing_repo(self):
    class UploadProgressDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Upload Progress")
            self.resize(500, 300)
            self.layout = QVBoxLayout(self)
            self.status_label = QLabel("Preparing to upload...", self)
            self.progress_bar = QProgressBar(self)
            self.progress_bar.setAlignment(Qt.AlignCenter)
            self.progress_bar.setRange(0, 100)
            self.layout.addWidget(self.status_label)
            self.layout.addWidget(self.progress_bar)

        def update_status(self, status, progress):
            self.status_label.setText(status)
            self.progress_bar.setValue(progress)

    # Choose repository
    repo = get_user_datasets(self)
    if not repo:
        QMessageBox.warning(self, "Error", "Please select a repository.")
        return

    # Choose folder to upload
    folder = QFileDialog.getExistingDirectory(self, "Select Folder to Upload")
    if not folder:
        QMessageBox.warning(self, "Error", "Please select a folder.")
        return

    # Gather all files from the folder, including subfolders
    all_files = []
    for root, _, files in os.walk(folder):
        for file in files:
            all_files.append(os.path.join(root, file))

    if len(all_files) > 2500:
        reply = QMessageBox.question(
            self,
            "Too Many Files",
            "The folder contains more than 2500 files. Do you want to zip the folder before uploading?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            zip_path = os.path.join(os.path.dirname(folder), os.path.basename(folder) + ".zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in all_files:
                    zipf.write(file, os.path.relpath(file, folder))
            folder = zip_path
        else:
            QMessageBox.warning(self, "Error", "Cannot upload more than 2500 files.")
            return

    # Show progress dialog
    progress_dialog = UploadProgressDialog(self)
    progress_dialog.show()

    # LOGIN HUGGINGFACE
    api_key, username = login_hugff(self, 2)
    if not api_key or not username:
        QMessageBox.critical(self, "Error", "Please log in to Hugging Face before uploading files.")
        progress_dialog.close()
        return

    api = HfApi(token=api_key)

    try:
        # Update progress before upload starts
        progress_dialog.update_status("Uploading folder...", 0)
        QApplication.processEvents()

        # Use upload_folder method from huggingface_hub
        api.upload_folder(
            folder_path=folder,
            repo_id=repo,
            repo_type="dataset",
        )

        # Upload completed
        progress_dialog.update_status("All files uploaded successfully!", 100)
        QMessageBox.information(self, "Upload Completed", "All files uploaded successfully!")

        # CLONE GIT LINK
        repo_url = f"https://huggingface.co/datasets/{username}/{repo}"
        clone_link = f"git clone {repo_url}"
        QMessageBox.information(self, "Clone Link",
                                f"Repository URL: {repo_url}\nClone Command: {clone_link}. Note: If you don't have Git LFS, please run 'git lfs install' before cloning.")

    except Exception as e:
        # Upload failed
        progress_dialog.update_status(f"Failed to upload folder: {e}", 0)
        QMessageBox.critical(self, "Upload Error", f"Failed to upload folder: {e}")

    progress_dialog.close()

def delete_datasets_hugff_repo(self):
    # Choose repository
    repo = get_user_datasets(self)
    if not repo:
        QMessageBox.warning(self, "Error", "Please select a repository.")
        return

    # Confirm before deletion
    reply = QMessageBox.question(
        self,
        "Confirm Deletion",
        f"Are you sure you want to delete the repository '{repo}'?",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )

    if reply == QMessageBox.No:
        QMessageBox.information(self, "Canceled", "Deletion canceled.")
        return

    # Login to Hugging Face
    api_key, username = login_hugff(self, 2)
    if not api_key or not username:
        QMessageBox.critical(self, "Error", "Please log in to Hugging Face before deleting a repository.")
        return

    api = HfApi(token=api_key)

    try:
        # Delete the selected repository
        api.delete_repo(repo_id=repo, repo_type="dataset")
        QMessageBox.information(self, "Success", f"Repository '{repo}' deleted successfully!")
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to delete the repository: {e}")