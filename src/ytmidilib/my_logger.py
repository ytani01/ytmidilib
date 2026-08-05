#
# (c) 2020 Yoichi Tanibayashi
#
"""
my_logger.py

ライブラリ側はロガーのレベルを決めるだけで、ハンドラは付けない
（付けると、取り込んだアプリのログ設定を上書きしてしまう）。
出力先の設定はアプリ側で `init_handler()` を呼んで行う。
"""
__author__ = 'Yoichi Tanibayashi'
__date__ = '2021'

from logging import DEBUG, INFO, Formatter, Logger, StreamHandler, getLogger

FMT_HDR = '%(asctime)s %(levelname)s '
FMT_LOC = '%(name)s.%(funcName)s:%(lineno)d> '
HANDLER_FMT = Formatter(FMT_HDR + FMT_LOC + '%(message)s',
                        datefmt='%H:%M:%S')

CONSOLE_HANDLER = StreamHandler()
CONSOLE_HANDLER.setFormatter(HANDLER_FMT)
CONSOLE_HANDLER.setLevel(DEBUG)

ROOT_LOGGER_NAME = __name__.split('.')[0]
"""このパッケージのロガーの根。ハンドラはここにだけ付ける。"""


def init_handler() -> None:
    """コンソールへのハンドラを、このパッケージのロガーに付ける

    アプリケーション側から 1 回だけ呼ぶ。ライブラリとして取り込んで
    使う場合は呼ばないこと(呼び出し側のログ設定に任せる)。
    """
    logger = getLogger(ROOT_LOGGER_NAME)

    if CONSOLE_HANDLER not in logger.handlers:
        logger.addHandler(CONSOLE_HANDLER)

    logger.propagate = False


def get_logger(name: str, dbg: bool | int = False) -> Logger:
    """get logger

    Parameters
    ----------
    name: str
        logger name。このパッケージ名が前置される
    dbg: bool | int
        bool の場合はデバッグフラグ、int の場合はログレベルそのもの

    Returns
    -------
    logger: Logger
    """
    if name == ROOT_LOGGER_NAME or name.startswith(f'{ROOT_LOGGER_NAME}.'):
        # モジュールから __name__ を渡された場合
        logger = getLogger(name)
    else:
        logger = getLogger(f'{ROOT_LOGGER_NAME}.{name}')

    # [Important !! ]
    # isinstance()では、boolもintと判定されるので、
    # 先に bool かどうかを判定する

    if isinstance(dbg, bool):
        logger.setLevel(DEBUG if dbg else INFO)
    else:
        # 不正な値は logging.setLevel() 自身が弾く
        logger.setLevel(dbg)

    return logger
