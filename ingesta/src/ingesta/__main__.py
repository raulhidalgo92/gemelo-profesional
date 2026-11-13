# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Interfaz de línea de comandos de la ingesta.

Ejemplos (dentro del contenedor):
    python -m ingesta esco-api
    python -m ingesta esco --dir /data/raw/esco
    python -m ingesta onet
    python -m ingesta esco-onet
    python -m ingesta embeddings
    python -m ingesta ine
    python -m ingesta ofertas
    python -m ingesta competencias-ofertas --limite 50
    python -m ingesta sepe-formacion
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

    s = sub.add_parser("esco-onet", help="Carga la tabla de correspondencias ESCO ↔ O*NET")
    s.add_argument("--dir", type=Path, default=raiz / "esco_onet")

    s = sub.add_parser("embeddings", help="Calcula los vectores semánticos de ESCO")
    s.add_argument("--limite", type=int, default=None, help="Máximo por tipo (para pruebas)")

    s = sub.add_parser("ine", help="Carga salarios por ocupación del INE y la tabla CNO ↔ ISCO")
    s.add_argument("--dir", type=Path, default=raiz / "ine")

    sub.add_parser("ofertas", help="Descarga ofertas y cursos de los servicios públicos de empleo")

    s = sub.add_parser("competencias-ofertas", help="Extrae competencias ESCO de las ofertas")
    s.add_argument("--limite", type=int, default=ajustes().extraccion_max_ofertas)

    s = sub.add_parser("sepe-formacion", help="Carga el catálogo de especialidades del SEPE")
    s.add_argument("--dir", type=Path, default=raiz / "sepe")

    s = sub.add_parser(
        "infojobs", help="Descarga ofertas de la API de InfoJobs (requiere credenciales)"
    )
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
    elif args.orden == "esco-onet":
        from ingesta.fuentes import esco_onet

        esco_onet.cargar(args.dir)
    elif args.orden == "embeddings":
        from ingesta.fuentes import embeddings

        embeddings.cargar(limite=args.limite)
    elif args.orden == "ine":
        from ingesta.fuentes import ine

        ine.cargar(args.dir)
    elif args.orden == "competencias-ofertas":
        from ingesta import competencias_ofertas

        competencias_ofertas.procesar(args.limite)
    elif args.orden == "sepe-formacion":
        from ingesta.fuentes import sepe_formacion

        sepe_formacion.cargar(args.dir)
    elif args.orden == "ofertas":
        from ingesta import programador

        programador.ingesta_nocturna()
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
