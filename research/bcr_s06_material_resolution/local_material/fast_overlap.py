"""Experimental storage/search optimization; no frozen prototype edits."""
from hashlib import sha256
from pathlib import Path
import inspect,textwrap

BASELINE_SHA256='c2f9d81ce57a8cae741839b5522185e10485c7cabe1070a935500a13387d3eee'

class MonotoneTargets:
    """Ordered partition intersections, identical overlap expressions/order."""
    def __init__(self,edges):
        self.edges=edges;self.start=0
    def __call__(self,left,right):
        edges=self.edges;n=len(edges)-1;j=self.start
        while j<n and edges[j+1]<=left:j+=1
        self.start=j;result=[]
        while j<n and edges[j]<right:
            a,b=edges[j],edges[j+1]
            if min(right,b)>max(left,a):
                result.append((j,max(0.,min(right,b)-max(left,a))))
            j+=1
        return result

def experimental_solver(base):
    """Subclass using original reorganize except its target enumeration.

    Original donor/remainder/amount/accumulation/recovery/record statements are
    compiled unchanged. Not installed into or monkeypatched onto the baseline.
    """
    path=Path(inspect.getfile(base))
    if sha256(path.read_bytes()).hexdigest()!=BASELINE_SHA256:
        raise ValueError('OVERLAP_BASELINE_CHANGED')
    source=textwrap.dedent(inspect.getsource(base.reorganize))
    old='''        targets = [(j, max(0., min(right, b)-max(left, a)))
                   for j, (a, b) in enumerate(zip(edges[:-1], edges[1:]))
                   if min(right, b) > max(left, a)]'''
    # inspect/dedent retains four spaces per indentation level.
    assert source.count(old)==1
    source=source.replace('    for i, (left, right) in enumerate',
                          '    sweep = MonotoneTargets(edges)\n    for i, (left, right) in enumerate',1)
    source=source.replace(old,'        targets = sweep(left, right)')
    namespace=dict(base.reorganize.__globals__,MonotoneTargets=MonotoneTargets)
    exec(compile(source,str(Path(__file__).with_name('generated_fast_reorganize.py')),'exec'),namespace)
    return type('ExperimentalFastOverlapSolver',(base,),{'reorganize':namespace['reorganize'],
                                                        'overlap_source':source})
