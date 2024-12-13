import os
import shutil
import re
import time

try:
    import streamlit as st
    from yt_dlp import YoutubeDL
except ModuleNotFoundError as e:
    print("Required modules are not installed in this environment.")
    raise 
os.system("apt-get install ffmpeg")
class DownloadManager:
    def __init__(self, ffmpeg_path=None):
        self.ffmpeg_path = ffmpeg_path or shutil.which("ffmpeg")
        if not self.ffmpeg_path:
            raise FileNotFoundError(
                "FFmpeg not found. Please install FFmpeg and ensure it is in your PATH."
            )

    def sanitize_filename(self, title):
        return re.sub(r'[\\/:*?"<>|]+', "_", title)

    def download(self, query, quality="192"):
        dl_opts = {
            'ffmpeg_location': self.ffmpeg_path,
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,
            }],
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }

        progress_bar = st.progress(0)
        progress_text = st.empty()

        def progress_hook(d):
            if d['status'] == 'downloading':
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes', 1)
                progress = downloaded / total
                progress_bar.progress(min(progress, 1.0))
                progress_text.text(f"Downloading... {progress:.1%}")
            elif d['status'] == 'finished':
                progress_text.text("Download complete, processing file...")

        dl_opts['progress_hooks'] = [progress_hook]

        try:
            with YoutubeDL(dl_opts) as dl:
                result = dl.extract_info(f"ytsearch:{query}", download=True)

            title = result['entries'][0]['title'] if 'entries' in result else result['title']
            sanitized_title = self.sanitize_filename(title)
            file_name = f"{sanitized_title}.mp3"

            if not os.path.exists(file_name):
                return None, f"Expected file '{file_name}' not found. Check post-processing logs."

            return file_name, None

        except Exception as e:
            return None, str(e)

def main():
    try:
        st.set_page_config(page_title="Audio Downloader", page_icon="🎵")

        st.title("Audio Downloader")
        st.write("Enter the song or playlist name below:")

        query = st.text_input("Search", placeholder="Enter song name, artist, or keywords...")
        format_option = st.selectbox("Select format:", ["High Quality MP3", "Low Quality MP3"])
        quality = "192" if format_option == "High Quality MP3" else "64"

        if st.button("Download"):
            if not query.strip():
                st.warning("Please enter a valid search term.")
                return

            try:
                downloader = DownloadManager()
            except FileNotFoundError as e:
                st.error(str(e))
                return

            with st.spinner("Processing your request..."):
                output_path, error = downloader.download(query, quality)

                if error:
                    st.error(f"Error: {error}")
                    return

                if output_path and os.path.exists(output_path):
                    with open(output_path, "rb") as file:
                        st.success("Your download is ready!")
                        st.download_button(
                            label="Download MP3",
                            data=file,
                            file_name=os.path.basename(output_path),
                            mime="audio/mpeg"
                        )
                    os.remove(output_path)  # Clean up the downloaded file

    except ModuleNotFoundError:
        print("Streamlit is not available in this environment.")

if __name__ == "__main__":
    main()
