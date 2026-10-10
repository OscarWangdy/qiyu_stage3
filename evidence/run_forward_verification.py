"""Real loaded-model inference with a forward hook. No model or weight mutation."""
import json, sys, time
from pathlib import Path
from hashlib import sha256
from datetime import datetime
import torch
PROJECT=Path('/Users/oscar/人工智能选修课/qiyu_v3_candidate_package')
sys.path.insert(0,str(PROJECT))
from qiyu.agent import QiYuAgent
from qiyu.rules import initial_board, RED
checkpoint=PROJECT/'artifacts/training_v3_long/best_model.pt'
book=PROJECT/'artifacts/master_data_v3/opening_book.json'
agent=QiYuAgent(checkpoint=checkpoint,opening_book=book,device=torch.device('cpu'))
calls=[]
def hook(module,args,result):
    calls.append({'time_monotonic':time.monotonic(),'input_shape':list(args[0].shape),'outputs':len(result)})
handle=agent.model.register_forward_hook(hook)
started=time.monotonic()
decision=agent.decide(initial_board(),RED)
handle.remove()
record={'executed_at':datetime.now().astimezone().isoformat(),'method':'Actual QiYuAgent.decide with loaded frozen v3 model, initial red board, forward hook, CPU. No mock.','checkpoint':'artifacts/training_v3_long/best_model.pt','checkpoint_sha256':sha256(checkpoint.read_bytes()).hexdigest(),'opening_book_sha256':sha256(book.read_bytes()).hexdigest(),'forward_calls':len(calls),'forward_events':calls,'elapsed_seconds':time.monotonic()-started,'move':decision.move.key,'engine':decision.engine,'search':decision.search,'candidates':decision.candidates,'attention_length':len(decision.attention),'scope':'One opening-book position, not a causal attention intervention, not a win-rate or playing-strength experiment.'}
out=Path(__file__).parent/'supplement_20261010/forward_runtime_verification.json'
out.write_text(json.dumps(record,ensure_ascii=False,indent=2))
print(json.dumps(record,ensure_ascii=False,indent=2))
