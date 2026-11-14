"""Original flat illustrations for the preparedness centre (no third-party images).
Palette: navy #1d2b4f, deep #0f1a33, paper #f3efe6, mist #c9d3e3, accent #e4572e (one accent only)."""
N, D, P, M, A, W = "#1d2b4f", "#0f1a33", "#f3efe6", "#c9d3e3", "#e4572e", "#ffffff"

def svg(body, vb="0 0 800 500", label=""):
    return f'<svg viewBox="{vb}" role="img" aria-label="{label}" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice">{body}</svg>'

def contours(cx, cy, n=7, step=34, col=M, op=.55):
    return "".join(f'<ellipse cx="{cx}" cy="{cy}" rx="{60+i*step*1.6:.0f}" ry="{36+i*step:.0f}" fill="none" stroke="{col}" stroke-width="2" opacity="{op}"/>' for i in range(n))

def person(x, y, s=1, col=W, kid=False):
    h = 70 * s * (0.7 if kid else 1)
    return (f'<g transform="translate({x},{y})"><circle cx="0" cy="{-h-14*s}" r="{13*s}" fill="{col}"/>'
            f'<rect x="{-13*s}" y="{-h}" width="{26*s}" height="{h*0.62}" rx="{10*s}" fill="{col}"/>'
            f'<rect x="{-11*s}" y="{-h*0.42}" width="{9*s}" height="{h*0.42}" rx="4" fill="{col}"/><rect x="{2*s}" y="{-h*0.42}" width="{9*s}" height="{h*0.42}" rx="4" fill="{col}"/></g>')

def hero():
    b = f'<rect width="1200" height="700" fill="{N}"/>' + contours(930, 210, 9, 40, M, .25)
    # route from house to shelter
    b += f'<path d="M360 560 C 520 520, 600 420, 760 380 S 960 260, 1010 200" fill="none" stroke="{A}" stroke-width="7" stroke-dasharray="4 18" stroke-linecap="round"/>'
    b += f'<g transform="translate(1010,200)"><rect x="-4" y="-80" width="8" height="90" fill="{W}"/><path d="M4 -80 L70 -62 L4 -44 Z" fill="{A}"/><circle cx="0" cy="12" r="16" fill="{W}" opacity=".9"/></g>'
    # house cross-section
    b += f'<g transform="translate(110,250)"><path d="M0 120 L190 0 L380 120 Z" fill="{P}"/><rect x="20" y="120" width="340" height="300" fill="{P}"/>'
    b += f'<rect x="40" y="140" width="140" height="115" fill="{M}"/><rect x="200" y="140" width="140" height="115" fill="{M}"/>'
    b += f'<rect x="40" y="262" width="300" height="10" fill="{N}"/>'
    # shelf with water + cans
    for i in range(5): b += f'<rect x="{52+i*24}" y="180" width="18" height="70" rx="6" fill="{W}"/><rect x="{55+i*24}" y="170" width="12" height="12" rx="3" fill="{N}"/>'
    for i in range(4): b += f'<rect x="{212+i*30}" y="220" width="24" height="30" rx="4" fill="{N}"/>'
    b += f'<rect x="210" y="154" width="110" height="10" fill="{N}"/><rect x="214" y="184" width="40" height="30" rx="3" fill="{A}"/><rect x="228" y="192" width="12" height="14" fill="{W}"/><rect x="223" y="197" width="22" height="4" fill="{W}"/>'
    b += person(120, 410, 1.15, N) + person(190, 410, 1.0, N) + person(250, 410, .95, N, kid=True)
    # go bag
    b += f'<rect x="290" y="340" width="56" height="70" rx="14" fill="{A}"/><rect x="304" y="326" width="28" height="18" rx="8" fill="none" stroke="{A}" stroke-width="6"/><rect x="300" y="362" width="36" height="10" rx="4" fill="{W}" opacity=".85"/>'
    b += '</g>'
    b += f'<rect x="0" y="668" width="1200" height="32" fill="{D}"/>'
    return svg(b, "0 0 1200 700", "가족이 집에서 비축품을 준비하고 대피 경로를 확인하는 그림")

def gobag():
    b = f'<rect width="800" height="500" fill="{P}"/>' + contours(620, 120, 5, 30, M, .7)
    b += f'<path d="M250 170 Q400 120 550 170 L590 440 Q400 470 210 440 Z" fill="{N}"/><path d="M330 170 Q400 80 470 170" fill="none" stroke="{N}" stroke-width="18"/>'
    b += f'<rect x="270" y="250" width="260" height="120" rx="18" fill="{D}"/>'
    items = [  # bottle, torch, radio, first aid, documents, powerbank
        f'<rect x="120" y="150" width="46" height="130" rx="16" fill="{W}"/><rect x="130" y="130" width="26" height="24" rx="6" fill="{N}"/>',
        f'<rect x="610" y="220" width="120" height="34" rx="12" fill="{W}"/><path d="M730 222 L770 205 L770 270 L730 252 Z" fill="{M}"/>',
        f'<rect x="600" y="320" width="130" height="80" rx="12" fill="{W}"/><circle cx="635" cy="360" r="20" fill="{N}"/><rect x="668" y="340" width="48" height="8" fill="{N}"/><rect x="668" y="358" width="48" height="8" fill="{N}"/><rect x="700" y="300" width="6" height="24" fill="{N}"/>',
        f'<rect x="80" y="320" width="120" height="90" rx="12" fill="{W}"/><rect x="128" y="338" width="24" height="54" fill="{A}"/><rect x="113" y="353" width="54" height="24" fill="{A}"/>',
        f'<rect x="330" y="275" width="140" height="70" rx="6" fill="{W}"/><rect x="345" y="292" width="80" height="8" fill="{N}"/><rect x="345" y="310" width="110" height="6" fill="{M}"/><rect x="345" y="324" width="90" height="6" fill="{M}"/>',
    ]
    b += "".join(items)
    return svg(b, label="생존 가방과 물·조명·라디오·구급함·서류")

def scene(kind):
    """One editorial illustration per hazard, same frame and palette."""
    g = f'<rect width="800" height="500" fill="{N}"/>'
    ground = f'<rect y="410" width="800" height="90" fill="{D}"/>'
    if kind == "war":
        g += contours(600, 140, 6, 30, M, .25) + ground
        g += "".join(f'<rect x="{60+i*90}" y="{250-(i%3)*40}" width="70" height="{160+(i%3)*40}" fill="{M}" opacity=".35"/>' for i in range(8))
        g += f'<path d="M300 410 L300 330 Q400 270 500 330 L500 410 Z" fill="{P}"/><rect x="370" y="350" width="60" height="60" fill="{N}"/>'
        g += f'<path d="M400 300 l0 -30" stroke="{A}" stroke-width="6"/><path d="M360 240 q40 -40 80 0" fill="none" stroke="{A}" stroke-width="6"/><path d="M340 215 q60 -60 120 0" fill="none" stroke="{A}" stroke-width="6" opacity=".6"/>'
        g += person(330, 410, .8, W) + person(470, 410, .8, W)
    elif kind == "famine":
        g += ground + "".join(f'<path d="M{80+i*55} 410 q10 -120 0 -170" stroke="{M}" stroke-width="5" fill="none" opacity="{.25+.08*(i%4)}"/><ellipse cx="{80+i*55}" cy="232" rx="10" ry="26" fill="{M}" opacity=".35"/>' for i in range(14))
        g += f'<ellipse cx="400" cy="330" rx="160" ry="34" fill="{P}"/><path d="M240 330 Q400 470 560 330 Z" fill="{P}"/><ellipse cx="400" cy="330" rx="130" ry="20" fill="{D}"/>'
        g += f'<rect x="560" y="200" width="120" height="150" rx="10" fill="{W}"/><rect x="580" y="225" width="80" height="10" fill="{N}"/>' + "".join(f'<rect x="580" y="{250+i*22}" width="{80-i*12}" height="10" fill="{A if i==3 else M}"/>' for i in range(4))
    elif kind == "epidemic":
        g += contours(400, 250, 6, 34, M, .2)
        g += f'<circle cx="400" cy="230" r="110" fill="{P}"/>' + "".join(f'<g transform="rotate({i*30} 400 230)"><rect x="396" y="100" width="8" height="30" fill="{P}"/><circle cx="400" cy="96" r="12" fill="{A}"/></g>' for i in range(12))
        g += f'<circle cx="370" cy="210" r="18" fill="{N}"/><circle cx="430" cy="255" r="12" fill="{N}"/><circle cx="410" cy="190" r="8" fill="{N}"/>'
        g += f'<path d="M80 450 q60 -90 140 -40 l40 30" fill="none" stroke="{W}" stroke-width="16" stroke-linecap="round"/><path d="M720 450 q-60 -90 -140 -40 l-40 30" fill="none" stroke="{W}" stroke-width="16" stroke-linecap="round"/>' + "".join(f'<circle cx="{350+i*25}" cy="{440-(i%2)*14}" r="7" fill="{M}"/>' for i in range(5))
    elif kind == "volcano":
        g += f'<path d="M140 410 L340 170 L460 170 L660 410 Z" fill="{P}"/><path d="M340 170 L460 170 L430 210 L370 210 Z" fill="{A}"/>' + ground
        g += "".join(f'<circle cx="{360+dx}" cy="{120-dy}" r="{r}" fill="{M}" opacity=".7"/>' for dx, dy, r in [(0,0,40),(50,20,46),(90,50,52),(150,70,56),(220,80,50),(-40,30,34)])
        g += "".join(f'<circle cx="{480+i*40}" cy="{220+(i%3)*50}" r="4" fill="{M}"/>' for i in range(8))
        g += f'<path d="M400 210 q-30 80 -10 200" stroke="{A}" stroke-width="10" fill="none" opacity=".8"/>'
    elif kind == "earthquake":
        g += ground + f'<rect x="230" y="120" width="340" height="290" fill="{P}"/>'
        g += "".join(f'<rect x="{255+c*80}" y="{145+r*70}" width="50" height="45" fill="{M}"/>' for r in range(3) for c in range(4))
        g += f'<path d="M420 120 l-20 60 l30 30 l-25 70 l20 40 l-15 90" fill="none" stroke="{N}" stroke-width="6"/>'
        g += f'<rect x="300" y="350" width="200" height="14" fill="{N}"/><rect x="315" y="364" width="10" height="46" fill="{N}"/><rect x="475" y="364" width="10" height="46" fill="{N}"/>'
        g += f'<g transform="translate(400,410)"><circle cx="-10" cy="-30" r="12" fill="{A}"/><rect x="-40" y="-22" width="60" height="22" rx="10" fill="{A}"/></g>'
        g += "".join(f'<path d="M{60+i*14} {430+i*0} l0 0" />' for i in range(1))
        g += f'<path d="M40 470 q30 -20 60 0 t60 0 t60 0" stroke="{M}" stroke-width="5" fill="none"/><path d="M600 470 q30 -20 60 0 t60 0 t60 0" stroke="{M}" stroke-width="5" fill="none"/>'
    elif kind == "tsunami":
        g += f'<path d="M520 410 L800 160 L800 410 Z" fill="{P}"/><rect x="690" y="150" width="8" height="60" fill="{W}"/><path d="M698 150 L750 165 L698 180 Z" fill="{A}"/>'
        g += f'<path d="M0 300 Q120 150 260 230 Q330 270 300 330 Q420 260 460 410 L0 410 Z" fill="{M}" opacity=".85"/><path d="M0 360 Q160 280 300 330 Q380 350 460 410 L0 410 Z" fill="{W}" opacity=".5"/>' + ground
        g += f'<path d="M470 380 Q560 320 650 230" fill="none" stroke="{A}" stroke-width="8" stroke-dasharray="4 16" stroke-linecap="round"/><path d="M640 222 l20 -4 l-6 20" fill="none" stroke="{A}" stroke-width="8"/>'
        g += person(600, 300, .7, W) + person(640, 262, .7, W)
    elif kind == "wildfire":
        g += f'<rect width="800" height="500" fill="{D}"/>' + "".join(f'<circle cx="{120+i*70}" cy="{140-(i%3)*30}" r="{50+(i%2)*20}" fill="{M}" opacity=".18"/>' for i in range(10)) + ground
        g += "".join(f'<path d="M{80+i*70} 410 l30 -110 l30 110 Z" fill="{N}"/>' for i in range(6))
        g += "".join(f'<path d="M{110+i*70} 300 q-20 -40 0 -80 q20 40 0 80" fill="{A}" opacity=".9"/>' for i in range(3))
        g += f'<path d="M520 410 L520 320 L620 260 L720 320 L720 410 Z" fill="{P}"/><rect x="600" y="350" width="40" height="60" fill="{N}"/><rect x="545" y="335" width="40" height="34" fill="{M}"/>'
    elif kind == "asteroid":
        g += "".join(f'<circle cx="{(i*137)%800}" cy="{(i*71)%380}" r="{1+(i%3)}" fill="{W}" opacity=".7"/>' for i in range(60)) + ground
        g += f'<path d="M120 60 L520 300" stroke="{A}" stroke-width="10" stroke-linecap="round" opacity=".35"/><path d="M300 170 L520 300" stroke="{A}" stroke-width="16" stroke-linecap="round" opacity=".6"/><circle cx="530" cy="306" r="26" fill="{P}"/>'
        g += f'<rect x="80" y="330" width="120" height="80" fill="{M}" opacity=".5"/><rect x="600" y="300" width="140" height="110" fill="{M}" opacity=".5"/>'
        g += f'<rect x="330" y="360" width="140" height="50" rx="6" fill="{W}"/><rect x="345" y="375" width="70" height="8" fill="{N}"/><rect x="345" y="390" width="100" height="6" fill="{M}"/>'
    elif kind == "radiation":
        g += ground + f'<rect x="180" y="150" width="440" height="260" fill="{P}"/><rect x="200" y="300" width="400" height="110" fill="{M}"/>'
        g += f'<rect x="330" y="320" width="140" height="90" fill="{N}"/>' + person(370, 410, .75, W) + person(430, 410, .75, W, kid=True)
        g += "".join(f'<path d="M{200+i*40} 140 l-20 -60" stroke="{M}" stroke-width="3" opacity=".5"/>' for i in range(11))
        g += f'<rect x="676" y="70" width="8" height="90" fill="{W}"/><circle cx="680" cy="66" r="10" fill="{A}"/>' + "".join(f'<path d="M{680-r} {66-r*0.6} q{r} {-r*0.9} {2*r} 0" fill="none" stroke="{A}" stroke-width="6" opacity="{1-i*.25}"/>' for i, r in enumerate((26, 44, 62)))
    return svg(g, label=kind)
