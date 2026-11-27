"""Plot native B0 stocks at sample times and depot receipts at DES event times."""
import csv
import re
import sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main(run):
    with (run/'hourly.csv').open() as f:
        rows=list(csv.DictReader(f))
    with (run/'events.csv').open() as f:
        events=list(csv.DictReader(f))
    t=[float(r['time_hr']) for r in rows]
    fig,(ax,bx)=plt.subplots(2,1,sharex=True,figsize=(7.0,5.0),layout='constrained')
    def series(key):
        return [float(r[key]) for r in rows]
    for key,label,color in [('lox_credited_total_kg','Credited at batch admission','#163e63'),
                            ('lox_plant_stock_total_kg','Held at plants','#ac582b')]:
        ax.step(t,series(key),where='post',label=label,color=color,linewidth=1.65)
    receipts=[(float(e['time_hr']),float(m[1])) for e in events if (m:=re.search(r'kg LOX to PropellantDepot \(total there: ([\d.]+)',e['event']))]
    x=[v[0] for v in receipts]; y=[v[1] for v in receipts]
    ax.step([0,*x,60],[0,*y,y[-1]],where='post',color='#187365',label='Received at depot')
    ax.scatter(x,y,color='#187365',s=16,zorder=3)
    ax.set(ylabel='LOX (kg)',title='Oxygen production and distribution')
    for i,color in [(1,'#163e63'),(2,'#ac582b')]:
        feed=[(a-b)/1000 for a,b in zip(series(f'feed_delivered_{i}_kg'), series(f'feed_admitted_{i}_kg'))]
        bx.step(t,feed,where='post',label=f'Plant {i}',color=color,linewidth=1.65)
    bx.set(xlabel='Simulated time (h)',ylabel='Regolith in buffer (t)',title='Feedstock awaiting processing',xlim=(0,60),ylim=(-0.9,24))
    for axis in (ax,bx):
        axis.spines[['right','top']].set_visible(False)
        axis.grid(axis='y',alpha=.2)
        axis.legend(loc='upper left',frameon=False,fontsize=8)
        axis.title.set_fontsize(11)
    fig.savefig(run/'operations.pdf')
    plt.close(fig)
if __name__=='__main__':
    main(Path(sys.argv[1]))
