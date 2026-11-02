import csv, glob
N=18000; RATE=30
def runs(lost):
    out=[];s=None;p=None
    for i in sorted(lost):
        if s is None: s=p=i
        elif i==p+1: p=i
        else: out.append((s,p-s+1)); s=p=i
    if s is not None: out.append((s,p-s+1))
    return out
for sess in ["session1_quiet","session2_busy","session3_far"]:
    L={}
    for r in ("R2","R4"):
        fn=glob.glob(f"{r}/{sess}/*.csv")[0]; got={int(x["seq"]) for x in csv.DictReader(open(fn))}
        L[r]=set(range(N))-got
    print("====",sess)
    for r in ("R2","R4"):
        rr=runs(L[r]); p=len(L[r])/N
        for k in (8,15,30):
            inb=sum(l for _,l in rr if l>=k)
            ev=sum(1 for _,l in rr if l>=k)
            print(f" {r} bursts>={k}pkt ({1000*k/RATE:.0f}ms): events {ev}, time-fraction in such outages {100*inb/N:.2f}%, expected events if iid loss p={p:.3f}: {len(rr)*p**(k-1):.3f}")
        big=[(s/RATE,l/RATE) for s,l in rr if l>=60]
        print(f"  {r} outages >=2 s (start_s,len_s):",[(round(a,1),round(b,1)) for a,b in big])
    # both in burst>=8 simultaneously
    big2={r:{i for s,l in runs(L[r]) if l>=8 for i in range(s,s+l)} for r in L}
    both=len(big2["R2"]&big2["R4"]); print(f" packets inside >=8-pkt outage on BOTH receivers: {both} ({100*both/N:.3f}%)  R2:{len(big2['R2'])} R4:{len(big2['R4'])}")
# receiver-side check of the 9 s R2 outage: arrival timestamps around it
fn=glob.glob("R2/session3_far/*.csv")[0]; rows=list(csv.DictReader(open(fn)))
rr=runs(set(range(N))-{int(x["seq"]) for x in rows}); s,l=max(rr,key=lambda t:t[1]); print("R2 far longest outage at seq",s,"len",l,"= second",s/30)
seqs={int(x["seq"]):float(x["t_rx"]) for x in rows}
print(" t_rx before/after:",seqs.get(s-1),seqs.get(s+l))
fn4=glob.glob("R4/session3_far/*.csv")[0]; g4={int(x["seq"]) for x in csv.DictReader(open(fn4))}
print(" did R4 receive during R2's outage?:",sum(1 for i in range(s,s+l) if i in g4),"of",l)
