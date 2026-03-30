"""
Utilitários de formatação no padrão brasileiro (pt-BR).

Uso:
  import utils as u
  u.brl(1234567.89)  → 'R$ 1.234.567,89'
  u.brl(1234567, 0)  → 'R$ 1.234.567'
  u.pct(12.5)     → '12,5%'
  u.num(1234567)   → '1.234.567'
  u.dias(42)     → '42 dias'
"""


def _br(val: float, decimals: int = 0) -> str:
    """Converte número para string no padrão pt-BR (vírgula decimal, ponto milhar)."""
    s = f"{float(val):,.{decimals}f}"  # '1,234,567.89'
    return (
        s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")
    )  # '1.234.567,89'


def brl(val, decimals: int = 0) -> str:
    """Formata como moeda brasileira. Ex: R$ 1.234.567"""
    try:
        return f"R$ {_br(val, decimals)}"
    except (ValueError, TypeError):
        return "R$ -"


def brl2(val) -> str:
    """Formata como moeda brasileira com 2 casas. Ex: R$ 1.234,56"""
    return brl(val, 2)


def pct(val, decimals: int = 1) -> str:
    """Formata como percentual. Ex: 12,5%"""
    try:
        return f"{_br(val, decimals)}%"
    except (ValueError, TypeError):
        return "-%"


def num(val, decimals: int = 0) -> str:
    """Formata número inteiro com separador de milhar. Ex: 1.234"""
    try:
        return _br(val, decimals)
    except (ValueError, TypeError):
        return "-"


def dias(val) -> str:
    """Formata como 'N dias'."""
    try:
        return f"{int(val):,} dias".replace(",", ".")
    except (ValueError, TypeError):
        return "- dias"


# ── Formatadores prontos para pandas .style.format() ──────────────────────────
fmt_brl = lambda v: brl(v, 0)  # R$ 1.234
fmt_brl2 = lambda v: brl(v, 2)  # R$ 1.234,56
fmt_pct = lambda v: pct(v, 1)  # 12,5%
fmt_pct2 = lambda v: pct(v, 2)  # 12,50%
fmt_num = lambda v: num(v, 0)  # 1.234
fmt_dias = lambda v: dias(v)  # 42 dias
