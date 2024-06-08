import os
import requests
import threading
import time
from urllib.parse import urlsplit
from tkinter import Tk, Label, Entry, Button, filedialog, messagebox, IntVar
from tkinter.ttk import Progressbar


class DownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Downloader")
        self.root.geometry("400x220")

        self.url_label = Label(root, text="Download URL:")
        self.url_label.pack(pady=5)

        self.url_input = Entry(root, width=50)
        self.url_input.pack(pady=5)

        self.download_button = Button(root, text="Download", command=self.start_download)
        self.download_button.pack(pady=5)

        self.cancel_button = Button(root, text="Cancel", command=self.cancel_download)
        self.cancel_button.pack(pady=5)
        self.cancel_button.config(state="disabled")

        self.progress = IntVar()
        self.progress_bar = Progressbar(root, orient="horizontal", length=300, mode="determinate",
                                        variable=self.progress)
        self.progress_bar.pack(pady=5)

        self.progress_label = Label(root, text="Progress: 0%")
        self.progress_label.pack(pady=5)

        self.speed_label = Label(root, text="Speed: 0 MB/s")
        self.speed_label.pack(pady=5)

        self.download_thread = None
        self.cancel_download_flag = threading.Event()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def start_download(self):
        url = self.url_input.get()
        if url:
            save_path = self.get_save_path(url)
            if save_path:
                self.cancel_download_flag.clear()
                self.download_button.config(state="disabled")
                self.cancel_button.config(state="normal")
                self.download_thread = threading.Thread(target=self.download_file, args=(url, save_path))
                self.download_thread.start()
        else:
            messagebox.showwarning("Error", "Please provide a valid URL")

    def get_save_path(self, url):
        file_name = os.path.basename(urlsplit(url).path)
        if not file_name:
            file_name = 'downloaded_file'
        save_path = filedialog.asksaveasfilename(initialfile=file_name, defaultextension="",
                                                 filetypes=[("All Files", "*.*")])
        return save_path

    def format_size(self, size):
        if size < 1024:
            return f"{size} B"
        elif size < 1024 ** 2:
            return f"{size / 1024:.2f} KB"
        elif size < 1024 ** 3:
            return f"{size / 1024 ** 2:.2f} MB"
        else:
            return f"{size / 1024 ** 3:.2f} GB"

    def download_file(self, url, save_path):
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            total_length = int(response.headers.get('content-length', 0))

            start_time = time.time()
            with open(save_path, 'wb') as file:
                downloaded = 0
                for data in response.iter_content(chunk_size=4096):
                    if self.cancel_download_flag.is_set():
                        self.on_download_cancelled()
                        return
                    file.write(data)
                    downloaded += len(data)
                    percentage = downloaded * 100 // total_length
                    elapsed_time = time.time() - start_time
                    speed = downloaded / (elapsed_time * 1024 * 1024)  # Convert to MB/s
                    self.progress.set(percentage)
                    self.progress_label.config(
                        text=f"Progress: {percentage}% ({self.format_size(downloaded)} / {self.format_size(total_length)})")
                    self.speed_label.config(text=f"Speed: {speed:.2f} MB/s")

            self.on_download_finished()
        except Exception as e:
            self.on_download_failed(str(e))

    def cancel_download(self):
        self.cancel_download_flag.set()

    def on_download_finished(self):
        messagebox.showinfo("Success", "Download completed successfully!")
        self.reset_ui()

    def on_download_failed(self, error_message):
        messagebox.showerror("Error", error_message)
        self.reset_ui()

    def on_download_cancelled(self):
        messagebox.showinfo("Cancelled", "Download cancelled.")
        self.reset_ui()

    def reset_ui(self):
        self.progress.set(0)
        self.progress_label.config(text="Progress: 0%")
        self.speed_label.config(text="Speed: 0 MB/s")
        self.download_button.config(state="normal")
        self.cancel_button.config(state="disabled")

    def on_closing(self):
        if self.download_thread and self.download_thread.is_alive():
            self.cancel_download_flag.set()
            self.download_thread.join()
        self.root.destroy()


if __name__ == "__main__":
    root = Tk()
    app = DownloaderApp(root)
    root.mainloop()
