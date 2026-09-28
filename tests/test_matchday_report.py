import unittest

from engine.matchday_engine import genera_matchday_report


class MatchdayReportTest(unittest.TestCase):
    def test_report_distingue_dati_completi_e_insufficienti(self):
        report = genera_matchday_report()

        self.assertIn(
            report["stato"],
            {"analizzato", "non_completamente_analizzabile"},
        )
        self.assertGreaterEqual(report["giocatori_analizzati"], 0)
        self.assertIsInstance(report["alternative"], list)
        self.assertIn("copertura_ruoli_panchina", report["metriche"])

        formazione = report["formazione"]
        if formazione is None:
            self.assertEqual(report["stato"], "non_completamente_analizzabile")
            self.assertTrue(report["metriche"].get("motivo"))
            return

        self.assertEqual(report["stato"], "analizzato")
        assegnazioni = formazione["assegnazione"]
        self.assertEqual(len(assegnazioni), 11)
        ids = [a["giocatore"]["giocatore_id"] for a in assegnazioni]
        self.assertEqual(len(ids), len(set(ids)))

        for chiave in (
            "confidence_media",
            "starter_probability_media",
            "disponibilita_percentuale",
            "rischio_indisponibilita_percentuale",
            "copertura_ruoli_panchina",
        ):
            valore = report["metriche"][chiave]
            if valore is not None:
                self.assertGreaterEqual(valore, 0)
                self.assertLessEqual(valore, 100)


if __name__ == "__main__":
    unittest.main()

