from flask import Flask, request, send_file, render_template
import yt_dlp
import os
import uuid
import glob

import base64
import tempfile

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video_url = request.form['url']
        format_choice = request.form['format']
        
        # Generate a random base filename
        uid = str(uuid.uuid4())
        output_template = f"{uid}.%(ext)s"
        
        ydl_opts = {
            'outtmpl': output_template,
            'format': 'bestaudio/best' if format_choice == 'audio' else 'bestvideo+bestaudio',
        }

        # Add audio extraction postprocessor if needed
        if format_choice == 'audio':
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }]
        else:  # For video, merge best video and audio into mp4
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
                
            }]
        
        if 'YT_COOKIES_BASE64' in os.environ:
            cookie_data = base64.b64decode(os.environ['YT_COOKIES_BASE64']).decode()
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=True) as f:
                f.write(cookie_data)
                f.flush()
                ydl_opts['cookiefile'] = f.name

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
        except Exception as e:
            return f"<h3>Download failed: {str(e)}</h3>"

        # Find the actual file that got downloaded (by globbing uuid.*)
        file_matches = glob.glob(f"{uid}.*")
        if not file_matches:
            return "<h3>Error: File not found after download.</h3>"

        downloaded_file = file_matches[0]



        return send_file(downloaded_file, as_attachment=True)

    return render_template('index.html',success=True)
    



if __name__ == '__main__':
    app.run(debug=True)

