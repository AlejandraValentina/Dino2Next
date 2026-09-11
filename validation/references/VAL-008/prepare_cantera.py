"""Export reference-only property samples for a separate Cantera process."""
import json
import numpy as np
import reference as r

def main():
    rows=[]
    for case in r.cases():
        s=r.solve(case);states=[(s.left,s.tl,s.pl),(s.right,s.tr,s.pr)]
        if case.pressure_ratio is not None:
            states+=[(s.left,s.tstar_l,s.pstar),(s.right,s.tstar_r,s.pstar)]
            states +=[(s.left,float(t),float(s.pl*np.exp((s.left.s0(t)-s.left.s0(s.tl))/s.left.r))) for t in np.linspace(s.tstar_l,s.tl,5)]
        for th,t,p in states:
            rows.append(dict(case=case.name,T=t,p=p,Y=th.y.tolist(),cp=float(th.cp(t)),h=float(th.h(t)),e=float(th.h(t)-th.r*t),rho=float(p/(th.r*t)),a=float(th.sound(t))))
    out=r.ROOT/'artifacts/S06-R4/reference008/cantera-inputs.json';out.write_text(json.dumps(rows,indent=2)+'\n')
    print('Exported',len(rows),'independent thermodynamic checkpoints')

if __name__=='__main__':main()
