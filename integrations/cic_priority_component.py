"""Reusable responsive QA priority cards for CIC Pro reports.

Visible as 3 aligned columns on wide screens and vertical cards on phones.
Do not modify the financial QA status or original severity; presentation only.
"""
from html import escape

QA_CSS = '''
.priority-stack{display:grid;grid-template-columns:1fr;gap:9px}
.priority{display:grid;grid-template-columns:minmax(0,23%) minmax(0,19%) minmax(0,58%);border:1px solid #dbe3e4;border-radius:9px;background:#fff;overflow:hidden;align-items:start;break-inside:avoid}
.priority .phead,.priority .pids,.priority .pwork{padding:11px 12px;min-width:0;overflow-wrap:break-word;hyphens:auto}
.priority .phead{font-weight:800;background:#eaf3f1;color:#154550;height:100%}
.priority .pids{font-size:10px;font-weight:700;color:#325060}
.priority .pwork{font-size:10.5px;line-height:1.46}
.priority .phead,.priority .pids{border-right:1px solid #e1e7e9}
@media(max-width:750px){.priority{display:flex;flex-direction:column;padding:0}
.priority .phead,.priority .pids,.priority .pwork{width:100%;padding:9px 12px;border-right:0}
.priority .phead{background:#eaf3f1}.priority .pids{border-bottom:1px solid #e8edef}
.priority .pwork{font-size:11px}}
@media print{.priority{break-inside:avoid}}
'''

def priority_cards(items):
    """Items have 'title','controls','work'; escape untrusted strings safely."""
    cards=[]
    for r in items:
        if any(k not in r for k in ('title','controls','work')):
            raise ValueError('Faltan título, controles o trabajo del QA')
        parts=[escape(str(r[k]),quote=True) for k in ('title','controls','work')]
        cards.append('<section class="priority" data-role="priority">'
             +f'<div class="phead">{parts[0]}</div>'
             +f'<div class="pids">{parts[1]}</div>'
             +f'<div class="pwork">{parts[2]}</div></section>')
    return '<div class="priority-stack" id="prioridades-qa">'+''.join(cards)+'</div>'
