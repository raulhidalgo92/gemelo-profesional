# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Interfaz de línea de comandos de la ingesta.

Ejemplos (dentro del contenedor):
    python -m ingesta esco-api
    python -m ingesta esco --dir /data/raw/esco
    python -m ingesta onet --dir /data/raw/onet
    python -m ingesta infojobs --consulta "desarrollador" --paginas 5
    python -m ingesta programador
"""

import argparse
import logging
from pathlib import Path

from gemelo_core.config import ajustes


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    raiz = Path(ajustes().directorio_datos) / "raw"

    p = argparse.ArgumentParser(
        prog="ingesta", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = p.add_subparsers(dest="orden", required=True)

    sub.add_parser("esco-api", help="Carga ESCO completo desde su API oficial (recomendado)")

    s = sub.add_parser("esco", help="Carga ocupaciones, competencias y relaciones ESCO (CSV)")
    s.add_argument("--dir", type=Path, default=raiz / "esco")

    s = sub.add_parser("onet", help="Carga ocupaciones O*NET y la matriz de relacionadas")
    s.add_argument("--dir", type=Path, default=raiz / "onet")

    s = sub.add_parser("infojobs", help="Descarga ofertas de la API de InfoJobs")
    s.add_argument("--consulta", default="")
    s.add_argument("--paginas", type=int, default=5)

    sub.add_parser("eures", help="Descarga ofertas de EURES (pendiente)")
    sub.add_parser("programador", help="Proceso en segundo plano con la ingesta nocturna")

    args = p.parse_args()

    if args.orden == "esco-api":
        from ingesta.fuentes import esco_api

        esco_api.cargar()
    elif args.orden == "esco":
        from ingesta.fuentes import esco

        esco.cargar(args.dir)
    elif args.orden == "onet":
        from ingesta.fuentes import onet

        onet.cargar(args.dir)
    elif args.orden == "infojobs":
        from ingesta.fuentes import infojobs

        infojobs.ingerir(consulta=args.consulta, paginas=args.paginas)
    elif args.orden == "eures":
        from ingesta.fuentes import eures

        eures.ingerir()
    elif args.orden == "programador":
        from ingesta import programador

        programador.iniciar()


if __name__ == "__main__":
    main()
