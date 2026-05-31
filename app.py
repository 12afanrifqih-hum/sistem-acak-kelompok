# app.py — Backend Flask oleh Orang 2
import sqlite3, random, os
from flask import Flask, render_template, request, jsonify, g

app = Flask(__name__)
DATABASE = 'kelompok.db'

# ── Koneksi database ──────────────────────────────────────
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row   # agar bisa akses kolom by name
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql') as f:
            db.executescript(f.read().decode('utf-8'))
        db.commit()

# ── Route 1: Halaman utama ────────────────────────────────
@app.route('/')
def index():
    # Selalu ambil data ASLI dari DB (refresh = kembali ke awal)
    db = get_db()
    mahasiswa = db.execute(
        'SELECT * FROM mahasiswa ORDER BY nama'
    ).fetchall()
    return render_template('index.html', mahasiswa=mahasiswa)

# ── Route 2: Ambil semua mahasiswa (JSON) ────────────────
@app.route('/api/mahasiswa', methods=['GET'])
def get_mahasiswa():
    db = get_db()
    rows = db.execute('SELECT * FROM mahasiswa ORDER BY nama').fetchall()
    data = [dict(r) for r in rows]
    return jsonify(data)

# ── Route 3: Tambah mahasiswa ─────────────────────────────
@app.route('/api/mahasiswa', methods=['POST'])
def tambah_mahasiswa():
    body = request.get_json()
    nama = body.get('nama', '').strip()
    if not nama:
        return jsonify({'error': 'Nama tidak boleh kosong'}), 400
    db = get_db()
    try:
        db.execute('INSERT INTO mahasiswa (nama) VALUES (?)', (nama,))
        db.commit()
        return jsonify({'message': f'{nama} berhasil ditambahkan'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Nama sudah ada'}), 409

# ── Route 4: Hapus mahasiswa ──────────────────────────────
@app.route('/api/mahasiswa/<int:id>', methods=['DELETE'])
def hapus_mahasiswa(id):
    db = get_db()
    db.execute('DELETE FROM mahasiswa WHERE id = ?', (id,))
    db.commit()
    return jsonify({'message': 'Mahasiswa dihapus dari sesi'})

# ── Route 5: Generate kelompok acak ──────────────────────
@app.route('/api/kelompok', methods=['POST'])
def generate_kelompok():
    body = request.get_json()
    jumlah_kelompok = body.get('jumlah_kelompok', 6)

    # Ambil daftar mahasiswa dari request (bisa sudah dikurangi di frontend)
    daftar = body.get('daftar', [])
    if not daftar:
        return jsonify({'error': 'Daftar mahasiswa kosong'}), 400

    # Orang 4 bisa replace bagian ini dengan algoritmanya sendiri
    random.shuffle(daftar)
    kelompok = [[] for _ in range(jumlah_kelompok)]
    for i, mhs in enumerate(daftar):
        kelompok[i % jumlah_kelompok].append(mhs)

    hasil = [
        {'nama': f'Kelompok {i+1}', 'anggota': k}
        for i, k in enumerate(kelompok)
    ]
    return jsonify({'kelompok': hasil, 'total': len(daftar)})

# ── Route 6: Reset ke data asli DB ───────────────────────
@app.route('/api/reset', methods=['GET'])
def reset_ke_db():
    # Ini hanya memberi tahu frontend untuk reload data dari DB
    return jsonify({'message': 'Refresh halaman untuk kembali ke data awal DB'})

# ── Jalankan server ───────────────────────────────────────
if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
        print('Database dibuat: kelompok.db')
    app.run(debug=True)
