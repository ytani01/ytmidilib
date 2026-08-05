#
# (c) 2020 Yoichi Tanibayashi
#
"""
my_logger.py
"""
__author__ = 'Yoichi Tanibayashi'
__date__ = '2021'

import inspect
from logging import DEBUG, INFO, Formatter, Logger, StreamHandler, getLogger

FMT_HDR = '%(asctime)s %(levelname)s '
FMT_LOC = '%(name)s.%(funcName)s:%(lineno)d> '
HANDLER_FMT = Formatter(FMT_HDR + FMT_LOC + '%(message)s',
                        datefmt='%H:%M:%S')

CONSOLE_HANDLER = StreamHandler()
CONSOLE_HANDLER.setFormatter(HANDLER_FMT)
CONSOLE_HANDLER.setLevel(DEBUG)


def get_logger(name: str, dbg: bool | int = False) -> Logger:
    """get logger

    Parameters
    ----------
    name: str
        logger name。呼び出し元のファイル名が前置される
    dbg: bool | int
        bool の場合はデバッグフラグ、int の場合はログレベルそのもの

    Returns
    -------
    logger: Logger
    """
    filename = inspect.stack()[1].filename.split('/')[-1]
    logger = getLogger(f'{filename}.{name}')
    logger.propagate = False
    logger.addHandler(CONSOLE_HANDLER)

    # [Important !! ]
    # isinstance()では、boolもintと判定されるので、
    # 先に bool かどうかを判定する

    if isinstance(dbg, bool):
        logger.setLevel(DEBUG if dbg else INFO)
    else:
        # 不正な値は logging.setLevel() 自身が弾く
        logger.setLevel(dbg)

    return logger
