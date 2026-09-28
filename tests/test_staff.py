import unittest

from staff.roles import CATALOGO_STAFF, RUOLI_STAFF, costruisci_contesto_staff


class StaffDesignTest(unittest.TestCase):
    def test_contesto_coordina_i_ruoli_e_conserva_i_dati(self):
        contesto = "Crediti rimasti: 120\nGiocatore: Esempio"
        prompt = costruisci_contesto_staff(contesto)

        self.assertEqual(len(RUOLI_STAFF), 5)
        self.assertEqual(len(CATALOGO_STAFF), 7)
        for ruolo in RUOLI_STAFF:
            self.assertIn(ruolo["nome"], prompt)
            self.assertIn(ruolo["limite"], prompt)
        self.assertNotIn("Allenatore tattico Matchday", prompt)
        self.assertIn("In pausa", [membro["stato"] for membro in CATALOGO_STAFF])
        self.assertIn(contesto, prompt)
        self.assertIn("offerta massima", prompt.lower())
        self.assertIn("DATI ASTA E ROSA", prompt)


if __name__ == "__main__":
    unittest.main()

