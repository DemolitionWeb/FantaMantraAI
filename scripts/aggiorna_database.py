from db.database import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS
    idx_presenze_giocatore_partita
    ON presenze (
        giocatore_id,
        partita_id
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

print("Database aggiornato.")