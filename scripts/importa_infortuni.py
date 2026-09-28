from api.injuries import importa_infortuni
from db.database import get_connection
from db.infortuni import salva_infortunio


FONTE = "BBS"


def normalizza_nome(nome):
    if not nome:
        return ""

    return (
        nome.lower()
        .replace(".", "")
        .replace("-", " ")
        .replace("'", "")
        .strip()
    )


def trova_giocatore(nome, fonte_id=None, squadra=None):
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Cerchiamo prima il mapping BBS già presente
    if fonte_id:
        cursor.execute(
            """
            SELECT giocatore_id
            FROM player_sources
            WHERE lower(fonte) = lower(?)
              AND fonte_id = ?
            """,
            (FONTE, fonte_id),
        )

        risultato = cursor.fetchone()

        if risultato:
            conn.close()
            return risultato[0], "player_sources"

    # 2. Fallback: nome
    nome_norm = normalizza_nome(nome)
    squadra_norm = normalizza_nome(squadra)

    cursor.execute(
        """
        SELECT id, nome, squadra
        FROM giocatori
        """
    )

    giocatori = cursor.fetchall()
    conn.close()

    for giocatore_id, nome_db, squadra_db in giocatori:
        if (normalizza_nome(nome_db) == nome_norm and
                (not squadra_norm or normalizza_nome(squadra_db) == squadra_norm)):
            return giocatore_id, "nome"

    return None, None


def main():
    print("IMPORTER AVVIATO")

    risposta = importa_infortuni("seriea")

    injuries_data = risposta.get("data", {}).get("injuries", {})
    records = injuries_data.get("value", [])

    print(f"Infortuni ricevuti da BBS: {len(records)}")

    matchati = 0
    non_matchati = []

    for record in records:
        nome = record.get("full_name") or record.get("display_name")
        fonte_id = record.get("id")

        giocatore_id, metodo = trova_giocatore(
            nome=nome,
            fonte_id=fonte_id,
            squadra=(record.get("team_name") or record.get("team")),
        )

        if not giocatore_id:
            non_matchati.append(
                {
                    "nome": nome,
                    "fonte_id": fonte_id,
                }
            )
            continue

        salva_infortunio(
            giocatore_id=giocatore_id,
            fonte=FONTE,
            fonte_id=fonte_id,
            tipo=None,
            descrizione="Presente nella lista infortuni BBS",
            data_inizio=None,
            data_rientro=None,
            stato="attivo",
        )

        matchati += 1

        print(
            f"[OK] {nome} -> {giocatore_id} ({metodo})"
        )

    print()
    print("=== RISULTATO ===")
    print(f"Matchati: {matchati}")
    print(f"Non matchati: {len(non_matchati)}")

    if non_matchati:
        print()
        print("=== NON MATCHATI ===")

        for giocatore in non_matchati:
            print(
                f"- {giocatore['nome']} | "
                f"{giocatore['fonte_id']}"
            )


if __name__ == "__main__":
    main()
