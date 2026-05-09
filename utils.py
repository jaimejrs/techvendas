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

# ── Paleta de Cores (padrão visual TechVendas) ─────────────────────────────────
# Importe como: from utils import C
class C:
    """Paleta sofisticada e centralizada para todos os gráficos."""
    # Primárias
    VIOLET   = "#7C5CBF"   # Roxo sofisticado — cor principal
    TEAL     = "#2DD4BF"   # Verde-azul moderno — cor de sucesso/margem
    CORAL    = "#F26B6B"   # Coral vibrante — cor de alerta/negativo

    # Tons secundários
    VIOLET_LIGHT = "#C4B5FD"  # Roxo claro para gradientes
    TEAL_LIGHT   = "#99F6E4"  # Teal claro para gradientes
    CORAL_LIGHT  = "#FCA5A5"  # Coral claro

    # Backgrounds
    PAPER     = "rgba(0,0,0,0)"
    PLOT      = "rgba(0,0,0,0)"

    # Escalas para gráficos de uma variável contínua
    SCALE_VIOLET = [[0, "#C4B5FD"], [1, "#7C5CBF"]]
    SCALE_TEAL   = [[0, "#99F6E4"], [1, "#2DD4BF"]]
    SCALE_HEAT   = ["#1E1B4B", "#7C5CBF", "#C4B5FD"]
    SCALE_DIVERG = ["#F26B6B", "#F8FAFC", "#7C5CBF"]

    # Paleta qualitativa para múltiplas categorias (cores harmoniosas)
    QUAL = [
        "#7C5CBF", "#2DD4BF", "#F26B6B", "#F59E0B",
        "#60A5FA", "#A78BFA", "#34D399", "#FB923C",
        "#E879F9", "#38BDF8",
    ]

    # ABC Analysis
    ABC_A = "#7C5CBF"   # Roxo — Classe A (premium)
    ABC_B = "#2DD4BF"   # Teal — Classe B (intermediário)
    ABC_C = "#C4B5FD"   # Roxo claro — Classe C (base)

    @classmethod
    def abc_map(cls):
        return {"A": cls.ABC_A, "B": cls.ABC_B, "C": cls.ABC_C}




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
