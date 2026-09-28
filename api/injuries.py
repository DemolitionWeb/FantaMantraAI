from api.bigballs import get_injuries


def importa_infortuni(league="seriea"):
    return get_injuries(league)