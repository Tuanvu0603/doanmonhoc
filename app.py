# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from functools import wraps
from werkzeug.utils import secure_filename


app = Flask(__name__)

app.jinja_env.globals.update(enumerate=enumerate)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')
serializer = URLSafeTimedSerializer(os.getenv('SALT', 'default_salt'))


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '123456'
app.config['MYSQL_DB'] = 'music_streaming'
app.config['UPLOAD_FOLDER'] = 'static/music'
app.config['MYSQL_CHARSET'] = 'utf8mb4'  
mysql = MySQL(app)


ALLOWED_EXTENSIONS = {'mp3'}


if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Bạn cần đăng nhập để truy cập trang này.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    cursor = mysql.connection.cursor()
    
    # Lấy 5 bài hát mới nhất
    cursor.execute("SELECT song_name, contributing_artist, upload_date FROM songs_list ORDER BY upload_date DESC LIMIT 5")
    latest_songs = cursor.fetchall()
    
    # Lấy top 5 bài hát có lượt nghe cao nhất
    cursor.execute("SELECT song_name, contributing_artist, views FROM songs_list ORDER BY views DESC LIMIT 5")
    top_songs = cursor.fetchall()
    
    cursor.close()
    return render_template("index.html", latest_songs=latest_songs, top_songs=top_songs)



# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password_hash = generate_password_hash(password)  # Encrypt password

        cursor = mysql.connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, password_hash)
            )
            mysql.connection.commit()
            flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
            return redirect(url_for('login'))
        except:
            flash('Tên người dùng hoặc email đã tồn tại.', 'error')
        finally:
            cursor.close()
    return render_template('register.html')


# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()

        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không chính xác.', 'error')
    return render_template('login.html')


# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Đăng xuất thành công!', 'success')
    return redirect(url_for('index'))


# Search route
@app.route('/search')
def search():
    query = request.args.get('q')
    cursor = mysql.connection.cursor()
    sql = """
        SELECT * FROM songs_list
        WHERE song_name LIKE %s OR album LIKE %s OR contributing_artist LIKE %s
    """
    val = (f"%{query}%", f"%{query}%", f"%{query}%")
    cursor.execute(sql, val)
    results = cursor.fetchall()
    cursor.close()
    return render_template('search.html', results=results)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Bạn cần đăng nhập để truy cập trang này.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/allsongs', methods=['GET', 'POST'])
@login_required
def allsongs():
    if request.method == 'POST':
        song_file = request.files['song-file']
        song_name = request.form['song-name']
        song_artist = request.form['song-artist']
        song_album = request.form['song-album']
        user_id = session['user_id']  # Lấy ID của người dùng từ session

        if song_file and allowed_file(song_file.filename):
            filename = secure_filename(song_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            song_file.save(filepath)

            # Thêm thông tin bài hát vào cơ sở dữ liệu cùng với ID người dùng
            cursor = mysql.connection.cursor()
            cursor.execute(
                "INSERT INTO songs_list (path, song_name, contributing_artist, album, uploaded_by) VALUES (%s, %s, %s, %s, %s)",
                (filepath, song_name, song_artist, song_album, user_id)
            )
            mysql.connection.commit()
            cursor.close()
            flash('Đăng tải bài hát thành công!', 'success')
        else:
            flash('Chỉ chấp nhận tệp MP3.', 'error')
    return render_template('allsongs.html')



# Button click route to view all songs
@app.route('/button_click')
def button_click():
    return redirect(url_for('songs'))


# View all songs route
@app.route('/songs', methods=['GET'])
@login_required
def songs():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, path, album, song_name, contributing_artist, views FROM songs_list")
    songs = cursor.fetchall()
    cursor.close()
    return render_template('songs.html', songs=songs)



# Delete song route
@app.route('/song/delete/<int:song_id>', methods=['POST'])
@login_required
def delete_song(song_id):
    cursor = mysql.connection.cursor()
    
    # Truy vấn để lấy ID người dùng đã đăng bài
    cursor.execute("SELECT uploaded_by FROM songs_list WHERE id = %s", (song_id,))
    song = cursor.fetchone()

    if song:
        if song[0] == session['user_id']:
            # Nếu ID người dùng khớp với ID người đã đăng bài, cho phép xóa
            cursor.execute("DELETE FROM songs_list WHERE id = %s", (song_id,))
            mysql.connection.commit()
            flash('Xóa bài hát thành công!', 'success')
        else:
            # Thông báo lỗi khi người dùng không có quyền xóa
            flash('Bạn không có quyền xóa bài hát này.', 'error')
    else:
        flash('Không tìm thấy bài hát.', 'error')

    cursor.close()
    return redirect(url_for('songs'))




# Play song route
@app.route('/play_song/<int:song_id>', methods=['GET'])
@login_required
def play_song(song_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT song_name, path, views FROM songs_list WHERE id = %s", (song_id,))
    song = cursor.fetchone()

    if song is not None:
        # Tăng lượt nghe lên 1
        cursor.execute("UPDATE songs_list SET views = views + 1 WHERE id = %s", (song_id,))
        mysql.connection.commit()

        song_path = f"music/{os.path.basename(song[1])}"
        cursor.close()
        return render_template('play_song.html', song_name=song[0], views=song[2] + 1, src=url_for('static', filename=song_path))
    else:
        cursor.close()
        return "Không tìm thấy bài hát"


if __name__ == '__main__':
    app.run(debug=True)
