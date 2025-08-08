from pytube import YouTube


def download_youtube_video(url, output_path):
    try:
        yt = YouTube(url)
        video = yt.streams.filter(progressive=True, file_extension="mp3").first()
        if video:
            print(f"Downloading '{yt.title}'...")
            video.download(output_path)
            print("Download complete!")
        else:
            print("Couldn't find a video to download.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


# Replace 'URL_HERE' with the URL of the YouTube video you want to download
video_url = "https://youtu.be/ABy95341Dto"

# Replace 'YOUR_OUTPUT_PATH' with the directory where you want to save the video
output_directory = "./"

download_youtube_video(video_url, output_directory)
