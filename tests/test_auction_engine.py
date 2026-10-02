from auction_engine import offerta_massima


def test_offerta_massima_non_puo_superare_i_crediti_rimasti():
    assert offerta_massima(500, 450) == 49
    assert offerta_massima(500, 500) == 0
