from pathlib import Path
import re, html
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle

BASE = Path(r'D:\创新实验')
SOURCE = BASE / 'output' / '激光晶体温度场实验方案.md'
OUT = BASE / 'output' / 'pdf' / '激光晶体温度场测量_文献解读与实验方案.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)
pdfmetrics.registerFont(TTFont('CN', r'C:\Windows\Fonts\simsun.ttc', subfontIndex=0))
pdfmetrics.registerFont(TTFont('CNBold', r'C:\Windows\Fonts\simhei.ttf'))
pdfmetrics.registerFont(TTFont('Latin', r'C:\Windows\Fonts\cambria.ttc', subfontIndex=0))
pdfmetrics.registerFontFamily('CN', normal='CN', bold='CNBold', italic='CN', boldItalic='CNBold')
NAVY = colors.HexColor('#16364d')
TEAL = colors.HexColor('#147b83')
GREY = colors.HexColor('#5b6973')
W, H = A4
styles = {
 'h1': ParagraphStyle('h1',fontName='CNBold',fontSize=19,leading=26,textColor=NAVY,spaceAfter=13,wordWrap='CJK'),
 'h2': ParagraphStyle('h2',fontName='CNBold',fontSize=13.5,leading=20,textColor=TEAL,spaceBefore=5,spaceAfter=8,wordWrap='CJK'),
 'h3': ParagraphStyle('h3',fontName='CNBold',fontSize=11.2,leading=17,textColor=TEAL,spaceBefore=9,spaceAfter=5,wordWrap='CJK'),
 'body': ParagraphStyle('body',fontName='CN',fontSize=10.3,leading=16.7,textColor=colors.HexColor('#263440'),spaceAfter=7,wordWrap='CJK'),
 'list': ParagraphStyle('list',fontName='CN',fontSize=10.3,leading=16.5,leftIndent=12,firstLineIndent=-10,spaceAfter=5,wordWrap='CJK'),
 'cell': ParagraphStyle('cell',fontName='CN',fontSize=9.15,leading=14,textColor=colors.HexColor('#263440'),wordWrap='CJK'),
 'th': ParagraphStyle('th',fontName='CNBold',fontSize=9.15,leading=14,textColor=NAVY,wordWrap='CJK'),
 'code': ParagraphStyle('code',fontName='CN',fontSize=9.4,leading=15.2,textColor=NAVY,wordWrap='CJK'),
 'meta': ParagraphStyle('meta',fontName='CN',fontSize=8.9,leading=14.5,textColor=GREY,spaceAfter=12,wordWrap='CJK')
}

def markup(txt):
 txt = html.escape(txt)
 txt = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', txt)
 sup = str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻','0123456789+-')
 sub = str.maketrans('₀₁₂₃₄₅₆₇₈₉','0123456789')
 txt = re.sub(r'[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻]+',lambda m:'<super>'+m.group().translate(sup)+'</super>',txt)
 txt = re.sub(r'[₀₁₂₃₄₅₆₇₈₉]+(?:/[₀₁₂₃₄₅₆₇₈₉]+)?',lambda m:'<sub>'+m.group().translate(sub)+'</sub>',txt)
 for ch in '∂∇ö': txt=txt.replace(ch,'<font name="Latin">'+ch+'</font>')
 return re.sub(r'(https://[^\s<]+)',r'<link href="\1" color="#147b83">\1</link>',txt)

def footer(c, doc):
 c.saveState()
 c.setStrokeColor(colors.HexColor('#ced8df')); c.setLineWidth(.5)
 c.line(43,40,W-43,40)
 c.setFont('CN',8); c.setFillColor(GREY)
 c.drawString(43,27,'激光晶体温度场测量  /  文献解读与实验方案')
 c.drawRightString(W-43,27,str(doc.page)); c.restoreState()

story = []
for pi,page in enumerate(SOURCE.read_text(encoding='utf-8').split('<!-- PAGE -->')):
 if pi: story.append(PageBreak())
 lines = page.strip().splitlines(); i = 0
 while i < len(lines):
  line = lines[i].strip()
  if not line: i += 1; continue
  if line.startswith('```'):
   code=[]; i+=1
   while i<len(lines) and not lines[i].strip().startswith('```'):
    code.append(lines[i]); i+=1
   p=Paragraph('<br/>'.join(markup(l) for l in code),styles['code'])
   box=Table([[p]],colWidths=[W-86],hAlign='LEFT')
   box.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f0f5f8')),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
   story.extend([box,Spacer(1,9)]); i+=1; continue
  if line.startswith('|'):
   rows=[]
   while i<len(lines) and lines[i].strip().startswith('|'):
    parts=[s.strip() for s in lines[i].strip().strip('|').split('|')]
    if not all(re.fullmatch(r':?-+:?',s) for s in parts): rows.append(parts)
    i+=1
   n=len(rows[0]); ratios={2:[.23,.77],3:[.23,.385,.385],4:[.18,.25,.30,.27]}[n]
   content=[[Paragraph(markup(s),styles['th' if ri==0 else 'cell']) for s in row] for ri,row in enumerate(rows)]
   table=Table(content,colWidths=[(W-86)*r for r in ratios],repeatRows=1,hAlign='LEFT')
   table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7f0f4')),('LINEBELOW',(0,0),(-1,0),.8,colors.HexColor('#9eb5c2')),('LINEBELOW',(0,1),(-1,-1),.4,colors.HexColor('#d6e0e6')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
   story.extend([table,Spacer(1,10)]); continue
  if line.startswith('### '): story.append(Paragraph(markup(line[4:]),styles['h3']))
  elif line.startswith('## '): story.append(Paragraph(markup(line[3:]),styles['h2']))
  elif line.startswith('# '): story.append(Paragraph(markup(line[2:]),styles['h1']))
  elif line.startswith('- '): story.append(Paragraph('• '+markup(line[2:]),styles['list']))
  elif re.match(r'^\d+\. ',line): story.append(Paragraph(markup(line),styles['list']))
  else: story.append(Paragraph(markup(line),styles['meta'] if line.startswith('编制日期') else styles['body']))
  i+=1

doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=43,leftMargin=43,topMargin=43,bottomMargin=56,title='激光晶体温度场测量：文献解读与实验方案',author='实验方案',pageCompression=1)
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(str(OUT))
