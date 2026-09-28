import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).parent / "fantamantra.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def crea_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS partite (
            id TEXT PRIMARY KEY,
            campionato TEXT,
            giornata TEXT,
            squadra_casa TEXT,
            squadra_trasferta TEXT,
            kickoff_utc TEXT,
            stato TEXT,
            gol_casa INTEGER,
            gol_trasferta INTEGER
        )
    """)

    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS
    idx_partite_data_squadre
    ON partite (
        kickoff_utc,
        squadra_casa,
        squadra_trasferta
    )
""")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS giocatori (
            id TEXT PRIMARY KEY,
            nome TEXT,
            squadra TEXT,
            ruoli_mantra TEXT,
            posizione_generica TEXT,
            numero_maglia INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rosa (
            giocatore_id TEXT PRIMARY KEY,
            costo_acquisto REAL,
            quotazione_attuale REAL,
            fvm REAL,
            media_voto REAL,
            fanta_media REAL,
            partite_giocate INTEGER,
            prestito TEXT,
            FOREIGN KEY (giocatore_id) REFERENCES giocatori(id)
        )
    """)    

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS giocatori_fonti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            giocatore_id TEXT NOT NULL,
            fonte TEXT NOT NULL,
            fonte_id TEXT NOT NULL,
            ultimo_aggiornamento TEXT,
            UNIQUE (giocatore_id, fonte),
            FOREIGN KEY (giocatore_id) REFERENCES giocatori(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS presenze (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            giocatore_id TEXT,
            partita_id TEXT,
            titolare INTEGER,
            minuti INTEGER,
            posizione TEXT,
            numero_maglia INTEGER,
            voto REAL,
            gol INTEGER,
            assist INTEGER,
            ammonizioni INTEGER,
            espulsioni INTEGER,
            FOREIGN KEY (giocatore_id) REFERENCES giocatori(id),
            FOREIGN KEY (partita_id) REFERENCES partite(id)
        )
    """)

    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS
    idx_presenze_giocatore_partita
    ON presenze (giocatore_id, partita_id)
""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS player_sources (
        giocatore_id TEXT,
        fonte TEXT,
        fonte_id TEXT,
        PRIMARY KEY (fonte, fonte_id),
        FOREIGN KEY (giocatore_id)
            REFERENCES giocatori(id)
    )
""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS infortuni (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        giocatore_id TEXT,
        fonte TEXT,
        fonte_id TEXT,
        tipo TEXT,
        descrizione TEXT,
        data_inizio TEXT,
        data_rientro TEXT,
        stato TEXT,
        ultimo_aggiornamento TEXT,
        FOREIGN KEY (giocatore_id)
            REFERENCES giocatori(id)
    )
""")

    conn.commit()
    conn.close()

def salva_player_source(giocatore_id, fonte, fonte_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR REPLACE INTO player_sources (
            giocatore_id,
            fonte,
            fonte_id
        )
        VALUES (?, ?, ?)
        """,
        (
            giocatore_id,
            fonte,
            fonte_id,
        )
    )

    conn.commit()
    conn.close()

def trova_giocatore_per_source(fonte, fonte_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT giocatore_id
        FROM player_sources
        WHERE fonte = ?
        AND fonte_id = ?
        """,
        (
            fonte,
            fonte_id,
        )
    )

    risultato = cursor.fetchone()

    conn.close()

    if risultato:
        return risultato[0]

    return None


def aggiorna_schema_giocatori():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(giocatori)")
    colonne = [riga[1] for riga in cursor.fetchall()]

    if "fonte_id" not in colonne:
        cursor.execute(
            "ALTER TABLE giocatori ADD COLUMN fonte_id TEXT"
        )

    if "fonte" not in colonne:
        cursor.execute(
            "ALTER TABLE giocatori ADD COLUMN fonte TEXT"
        )

    if "ultimo_aggiornamento" not in colonne:
        cursor.execute(
            "ALTER TABLE giocatori ADD COLUMN ultimo_aggiornamento TEXT"
        )

    conn.commit()
    conn.close()


def salva_partite(partite):
    conn = get_connection()
    cursor = conn.cursor()

    for partita in partite:
        cursor.execute(
            """
            INSERT OR REPLACE INTO partite (
                id,
                campionato,
                giornata,
                squadra_casa,
                squadra_trasferta,
                kickoff_utc,
                stato,
                gol_casa,
                gol_trasferta
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                partita.get("id"),
                partita.get("campionato"),
                partita.get("giornata"),
                partita.get("squadra_casa"),
                partita.get("squadra_trasferta"),
                partita.get("kickoff_utc"),
                partita.get("stato"),
                partita.get("gol_casa"),
                partita.get("gol_trasferta"),
            ),
        )

    conn.commit()
    conn.close()


def conta_partite():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM partite")
    risultato = cursor.fetchone()[0]

    conn.close()

    return risultato


def leggi_partite():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            campionato,
            giornata,
            squadra_casa,
            squadra_trasferta,
            kickoff_utc,
            stato,
            gol_casa,
            gol_trasferta
        FROM partite
    """)

    risultati = cursor.fetchall()

    conn.close()

    return risultati


def salva_giocatori(giocatori):
    conn = get_connection()
    cursor = conn.cursor()

    for giocatore in giocatori:
        cursor.execute(
            """
            INSERT OR REPLACE INTO giocatori (
                id,
                nome,
                squadra,
                ruoli_mantra,
                posizione_generica,
                numero_maglia,
                fonte_id,
                fonte,
                ultimo_aggiornamento
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                giocatore.get("id"),
                giocatore.get("nome"),
                giocatore.get("squadra"),
                giocatore.get("ruoli_mantra"),
                giocatore.get("posizione_generica"),
                giocatore.get("numero_maglia"),
                giocatore.get("fonte_id"),
                giocatore.get("fonte"),
                giocatore.get("ultimo_aggiornamento"),
            ),
        )

    conn.commit()
    conn.close()


def conta_giocatori():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM giocatori")
    risultato = cursor.fetchone()[0]

    conn.close()

    return risultato


def aggiorna_ruoli_mantra(giocatore_id, ruoli_mantra):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE giocatori
        SET ruoli_mantra = ?
        WHERE id = ?
        """,
        (ruoli_mantra, giocatore_id),
    )

    conn.commit()
    conn.close()


def leggi_giocatori():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            nome,
            squadra,
            ruoli_mantra,
            posizione_generica,
            numero_maglia
        FROM giocatori
    """)

    risultati = cursor.fetchall()

    conn.close()

    return risultati


def salva_presenze(presenze):
    conn = get_connection()
    cursor = conn.cursor()

    for presenza in presenze:
        cursor.execute(
            """
            INSERT OR REPLACE INTO presenze (
                giocatore_id,
                partita_id,
                titolare,
                minuti,
                posizione,
                numero_maglia,
                voto,
                gol,
                assist,
                ammonizioni,
                espulsioni
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                presenza["giocatore_id"],
                presenza["partita_id"],
                presenza["titolare"],
                presenza["minuti"],
                presenza["posizione"],
                presenza["numero_maglia"],
                presenza["voto"],
                presenza["gol"],
                presenza["assist"],
                presenza["ammonizioni"],
                presenza["espulsioni"],
            ),
        )

    conn.commit()
    conn.close()


def elimina_presenza_test():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM presenze
        WHERE giocatore_id = ?
        """,
        ("test-001",),
    )

    conn.commit()
    conn.close()

def salva_identificativo_fonte(
    giocatore_id,
    fonte,
    fonte_id,
    ultimo_aggiornamento=None
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO giocatori_fonti (
            giocatore_id,
            fonte,
            fonte_id,
            ultimo_aggiornamento
        )
        VALUES (?, ?, ?, ?)
        ON CONFLICT(giocatore_id, fonte)
        DO UPDATE SET
            fonte_id = excluded.fonte_id,
            ultimo_aggiornamento = excluded.ultimo_aggiornamento
        """,
        (
            giocatore_id,
            fonte,
            fonte_id,
            ultimo_aggiornamento,
        ),
    )

    # Mantieni aggiornato anche il registro storico usato dalle prime
    # importazioni. I due registri restano leggibili, ma condividono ora lo
    # stesso collegamento canonico.
    try:
        cursor.execute(
            """
            INSERT OR REPLACE INTO giocatori_fonti
                (giocatore_id, fonte, fonte_id, ultimo_aggiornamento)
            VALUES (?, ?, ?, date('now'))
            """,
            (giocatore_id, fonte, str(fonte_id)),
        )
    except sqlite3.OperationalError:
        # Compatibilità con database non ancora passati dalla migrazione.
        pass

    conn.commit()
    conn.close()


def trova_id_fonte(giocatore_id, fonte):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT fonte_id
        FROM giocatori_fonti
        WHERE giocatore_id = ?
        AND fonte = ?
        """,
        (
            giocatore_id,
            fonte,
        ),
    )

    risultato = cursor.fetchone()

    conn.close()

    if risultato:
        return risultato[0]

    return None

def crea_tabella_rosa():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rosa (
            giocatore_id TEXT PRIMARY KEY,
            costo_acquisto REAL,
            quotazione_attuale REAL,
            fvm REAL,
            media_voto REAL,
            fanta_media REAL,
            partite_giocate INTEGER,
            prestito TEXT,
            FOREIGN KEY (giocatore_id) REFERENCES giocatori(id)
        )
    """)

    conn.commit()
    conn.close()
