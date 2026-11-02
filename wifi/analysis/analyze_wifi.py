import csv, glob, json, statistics as st, sys
RATE=30.0; N=18000
def load(fn):
    rows=list(csv.DictReader(open(fn))); seqs=[int(r["seq"]) for r in rows]
    return rows, seqs
def bursts(lost):
    out=[];run=0;prev=None
    for i in sorted(lost):
        if prev is not None and i==prev+1: run+=1
        else:
            if run: out.append(run)
            run=1
        prev=i
    if run: out.append(run)
    return out
res={}
for sess in ["session1_quiet","session2_busy","session3_far"]:
    d={}
    for rcv in ["R2","R4"]:
        fn=glob.glob(f"{rcv}/{sess}/*.csv")[0]; rows,seqs=load(fn)
        u=set(seqs); dup=len(seqs)-len(u)
        label=rows[0]["label"]
        lost=set(range(0,N))-u
        b=bursts(lost)
        reorder=sum(1 for a,c in zip(seqs,seqs[1:]) if c<a)
        loss=len(lost)/N
        mb=sum(b)/len(b) if b else 0
        tail={f">={k}":sum(x>=k for x in b) for k in (2,3,5,8,15,30,45,90)}
        d[rcv]=dict(file=fn.split('/')[-1],label=label,received=len(u),first=min(u),last=max(u),dups=dup,reorder=reorder,
            loss=round(loss,4),n_bursts=len(b),mean_burst_pkts=round(mb,2),mean_burst_ms=round(1000*mb/RATE),
            max_burst_pkts=max(b,default=0),max_burst_s=round(max(b,default=0)/RATE,2),tail=tail,
            top5=sorted(b,reverse=True)[:5],lost=lost,bursts=b)
    L2,L4=d["R2"]["lost"],d["R4"]["lost"]
    both=L2&L4; anyl=L2|L4
    exp_both=len(L2)*len(L4)/N
    d["overlap"]=dict(both=len(both),frac_of_union=round(len(both)/len(anyl),3) if anyl else 0,
        frac_of_R2_losses_also_lost_by_R4=round(len(both)/len(L2),3) if L2 else 0,
        frac_of_R4_losses_also_lost_by_R2=round(len(both)/len(L4),3) if L4 else 0,
        expected_both_if_independent=round(exp_both,1))
    # simultaneous long outage: bursts >=15 pkts overlapping
    res[sess]=d
def show(x):
    return {k:v for k,v in x.items() if k not in("lost","bursts")}
for s,d in res.items():
    print("=====",s)
    for r in ("R2","R4"): print(r,json.dumps(show(d[r])))
    print("overlap",d["overlap"])
json.dump({s:{r:show(d[r]) for r in ("R2","R4")}|{"overlap":d["overlap"]} for s,d in res.items()},open("wifi_fit_all.json","w"),indent=1)
