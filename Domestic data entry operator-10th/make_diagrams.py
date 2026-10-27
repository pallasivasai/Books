from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
OUT=Path(__file__).parent/'book_illustrations'
OUT.mkdir(exist_ok=True)
W,H=1500,760
navy='#17365D'; teal='#007F86'; gold='#E3A72F'; coral='#D95D50'; violet='#7656A6'; pale='#EAF6F7'; ink='#293746'; white='#FFFFFF'
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
try:
    fnt=ImageFont.truetype(FONT,30); bold=ImageFont.truetype(BOLD,34); small=ImageFont.truetype(FONT,25)
except OSError:
    fnt=bold=small=ImageFont.load_default()
def base(title,subtitle=''):
    im=Image.new('RGB',(W,H),white); d=ImageDraw.Draw(im)
    d.rounded_rectangle((16,16,W-16,H-16),radius=28,outline=navy,width=4)
    d.text((55,45),title,font=bold,fill=navy)
    if subtitle: d.text((58,95),subtitle,font=small,fill=teal)
    return im,d
def box(d,xy,text,fill=pale,outline=teal,font=fnt):
    d.rounded_rectangle(xy,radius=22,fill=fill,outline=outline,width=4)
    x1,y1,x2,y2=xy; lines=text.split('\n'); heights=[]
    for line in lines:
        bb=d.textbbox((0,0),line,font=font); heights.append(bb[3]-bb[1])
    y=(y1+y2-sum(heights)-8*(len(lines)-1))//2
    for line,h in zip(lines,heights):
        bb=d.textbbox((0,0),line,font=font)
        d.text(((x1+x2-(bb[2]-bb[0]))//2,y),line,font=font,fill=ink); y+=h+8
def arrow(d,a,b,fill=gold,width=7):
    import math
    d.line((a,b),fill=fill,width=width); ang=math.atan2(b[1]-a[1],b[0]-a[0]); L=23
    p1=(b[0]-L*math.cos(ang-.5),b[1]-L*math.sin(ang-.5)); p2=(b[0]-L*math.cos(ang+.5),b[1]-L*math.sin(ang+.5))
    d.polygon([b,p1,p2],fill=fill)
im,d=base('A consistent document begins with styles','Apply one named rule to many matching parts of a document')
box(d,(70,260,390,470),'Heading 1\nChapter title',fill='#DCEEFF',outline=navy)
box(d,(585,210,915,330),'Heading 2\nSection title',fill=pale)
box(d,(585,400,915,520),'Body Text\nMain paragraph',fill='#FFF5DD',outline=gold)
box(d,(1110,260,1430,470),'Document\nconsistent\nformatting',fill='#FCEBE8',outline=coral)
arrow(d,(390,330),(565,270)); arrow(d,(390,405),(565,460)); arrow(d,(915,270),(1090,330)); arrow(d,(915,460),(1090,405))
im.save(OUT/'style_categories.png')
im,d=base('Plan, insert and check an image','A useful picture supports the text and stays readable in print')
items=[('Choose','Relevant visual'),('Insert','Place near text'),('Format','Size and wrap'),('Caption','Explain figure'),('Review','Export and inspect')]; xs=[55,350,645,940,1235]
for i,(a,b) in enumerate(items):
    box(d,(xs[i],280,xs[i]+210,450),a+'\n'+b,fill=[pale,'#DCEEFF','#FFF5DD','#FCEBE8','#EAE4F7'][i],outline=[teal,navy,gold,coral,violet][i],font=small)
    if i<4: arrow(d,(xs[i]+210,365),(xs[i+1]-12,365))
im.save(OUT/'image_workflow.png')
im,d=base('Spreadsheet what-if analysis','Keep assumptions visible and verify results independently')
box(d,(65,265,420,475),'Input values\nCost, quantity, rate',fill='#DCEEFF',outline=navy)
box(d,(540,265,900,475),'Formula model\nCalculated result',fill=pale,outline=teal)
box(d,(1020,190,1435,325),'Scenarios\nCompare assumptions',fill='#FFF5DD',outline=gold)
box(d,(1020,410,1435,545),'Goal Seek\nFind an input for a target',fill='#FCEBE8',outline=coral,font=small)
arrow(d,(420,365),(520,365)); arrow(d,(900,315),(1000,260)); arrow(d,(900,420),(1000,475))
im.save(OUT/'scenario_goal_seek.png')
im,d=base('Relational databases connect records through keys','Example: a book may appear in many issue transactions')
box(d,(90,245,590,530),'BOOKS TABLE\nBookID — primary key\nTitle\nCategory',fill='#DCEEFF',outline=navy)
box(d,(900,245,1400,530),'ISSUES TABLE\nIssueID — primary key\nBookID — foreign key\nIssueDate / ReturnDate',fill=pale,outline=teal)
arrow(d,(590,390),(900,390),gold,9); d.text((615,330),'one-to-many',font=bold,fill=coral); d.text((620,430),'key match',font=small,fill=ink)
im.save(OUT/'database_relationships.png')
im,d=base('Forms make entry easier; reports make results readable','Both rely on good source data and correct queries')
box(d,(95,260,520,485),'Form\nInput and edit\nrecords',fill='#DCEEFF',outline=navy)
box(d,(575,260,930,485),'Database\nTables + queries',fill=pale,outline=teal)
box(d,(985,260,1405,485),'Report\nGroup, review\nand present results',fill='#FFF5DD',outline=gold)
arrow(d,(520,370),(555,370)); arrow(d,(930,370),(965,370))
im.save(OUT/'forms_reports.png')
im,d=base('A safer workstation combines comfort and good habits','Adjust to the person and follow local safety requirements')
box(d,(75,235,500,505),'Physical setup\nComfortable screen\nKeyboard and mouse\nClear walkways',fill='#DCEEFF',outline=navy,font=small)
box(d,(540,235,960,505),'Work habits\nChange position\nTake visual breaks\nReport discomfort',fill=pale,outline=teal,font=small)
box(d,(1000,235,1425,505),'Information safety\nLock unattended screen\nProtect credentials\nShare only with approval',fill='#FFF5DD',outline=gold,font=small)
im.save(OUT/'healthy_workstation.png')
im,d=base('Emergency response: know the plan before you need it','Follow the site plan and trained responders; never take an unsafe risk')
box(d,(70,270,380,470),'Recognise\nAlarm / hazard',fill='#FCEBE8',outline=coral)
box(d,(440,270,750,470),'Raise alarm\nGet help',fill='#FFF5DD',outline=gold)
box(d,(810,270,1120,470),'Evacuate\nUse safe route',fill='#DCEEFF',outline=navy)
box(d,(1180,270,1440,470),'Assemble\nReport',fill=pale,outline=teal)
arrow(d,(380,370),(420,370)); arrow(d,(750,370),(790,370)); arrow(d,(1120,370),(1160,370))
im.save(OUT/'emergency_route.png')

# Additional illustrations used by the Class X textbook.
im,d=base('A spreadsheet formula turns inputs into useful results','Label input cells, calculate carefully and check the final value')
box(d,(70,250,390,480),'Input cells\nQuantity\nUnit cost',fill='#DCEEFF',outline=navy)
box(d,(520,250,900,480),'Formula cell\n=Quantity * Unit cost',fill=pale,outline=teal)
box(d,(1030,250,1420,480),'Reviewed result\nValue + units\nChecked against source',fill='#FFF5DD',outline=gold)
arrow(d,(390,365),(500,365)); arrow(d,(900,365),(1010,365))
im.save(OUT/'spreadsheet_formula.png')
im,d=base('A safe macro workflow','Automate a known task; test on a copy before using real records')
items=[('Record','Small sample'),('Review','Understand steps'),('Test','Use a copy'),('Run','Check output')]
xs=[75,435,795,1155]
for i,(a,b) in enumerate(items):
    box(d,(xs[i],280,xs[i]+260,455),a+'\n'+b,fill=[pale,'#DCEEFF','#FFF5DD','#FCEBE8'][i],outline=[teal,navy,gold,coral][i],font=small)
    if i<3: arrow(d,(xs[i]+260,365),(xs[i+1]-12,365))
im.save(OUT/'macro_safety.png')
im,d=base('A query selects the records needed for a task','The quality of results depends on criteria and source data')
box(d,(65,260,370,470),'Source tables\nOriginal records',fill='#DCEEFF',outline=navy)
box(d,(440,260,750,470),'Criteria\nFields + conditions',fill=pale,outline=teal)
box(d,(820,260,1125,470),'Query result\nSelected rows',fill='#FFF5DD',outline=gold)
box(d,(1190,260,1430,470),'Review\nVerify sample',fill='#FCEBE8',outline=coral,font=small)
arrow(d,(370,365),(420,365)); arrow(d,(750,365),(800,365)); arrow(d,(1125,365),(1170,365))
im.save(OUT/'query_process.png')
im,d=base('A final quality check catches avoidable data-entry errors','Compare the entered record with the authorised source')
items=[('Accuracy','Values match'),('Completeness','Required fields'),('Consistency','Same format'),('Duplicates','Check repeated IDs'),('Save','Correct location')]
xs=[45,340,635,930,1225]
for i,(a,b) in enumerate(items):
    box(d,(xs[i],280,xs[i]+220,455),a+'\n'+b,fill=[pale,'#DCEEFF','#FFF5DD','#FCEBE8','#EAE4F7'][i],outline=[teal,navy,gold,coral,violet][i],font=small)
    if i<4: arrow(d,(xs[i]+220,365),(xs[i+1]-10,365))
im.save(OUT/'data_quality_check.png')
im,d=base('Emergency readiness starts with knowing the local plan','Use designated exits and follow trained responders')
box(d,(75,245,470,500),'Before an incident\nKnow exits\nKnow assembly point',fill='#DCEEFF',outline=navy,font=small)
box(d,(550,245,965,500),'During an incident\nRaise alarm\nLeave by safe route',fill='#FFF5DD',outline=gold,font=small)
box(d,(1045,245,1425,500),'After reaching safety\nReport to coordinator\nWait for clearance',fill=pale,outline=teal,font=small)
arrow(d,(470,370),(530,370)); arrow(d,(965,370),(1025,370))
im.save(OUT/'emergency_preparedness.png')

print('Generated',len(list(OUT.glob('*.png'))),'Class X diagrams')
