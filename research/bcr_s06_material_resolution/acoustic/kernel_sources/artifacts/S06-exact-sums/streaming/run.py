"""Explicit invocation only: predefined N1600 free case, no resolution search."""
import argparse,json
from pathlib import Path
import driver

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--cfl',type=float,choices=(.1,.05),required=True)
    p.add_argument('--epsilon',type=float,choices=(1e-5,5e-6),required=True)
    p.add_argument('--observation',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    fixture=json.loads((driver.ROOT/'validation/fixtures/VAL-010/input.json').read_text())
    case=next(c for c in fixture['cases'] if c['kind']=='free' and c['epsilon']==a.epsilon)
    oracle=driver.load('preflight_observation',a.observation)
    for i in range(101):oracle.observation_reference(1600,i,a.epsilon)
    record,_,_=driver.execute('VAL-010',1600,case,a.cfl,output_root=a.output)
    result=driver.assess_n1600(record,a.output,a.observation)
    result['execution_record']=f"{case['name']}-N1600-CFL{a.cfl}.json"
    path=a.output/f"{case['name']}-N1600-CFL{a.cfl}-observation-assessment.json"
    path.write_text(json.dumps(result,indent=2)+'\n')
    print(path)

if __name__=='__main__':main()
