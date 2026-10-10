#!/usr/bin/env python3
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
from run_stage3_supplement import OUT, PROJECT, DATA, live_call, now
from qiyu.deepseek import DeepSeekConfig, load_env_file

load_env_file(PROJECT/'.env')
config=DeepSeekConfig.from_env()
source=json.loads((Path(__file__).parent/'qiyu_logic_prompt_ab.json').read_text())
tasks=[{'category':'logic','test_id':r['test_id'],'theme':r['risk_type'],'condition':c,'tool':'QiYu','prompt':r[c]+'\n共同证据：'+DATA} for r in source['records'] for c in ['baseline','refined']]
records=[]
with ThreadPoolExecutor(max_workers=3) as pool:
    for future in as_completed([pool.submit(live_call,t,config) for t in tasks]):
        r=future.result(); records.append(r)
        (OUT/('logic_'+r['test_id']+'_'+r['condition']+'.json')).write_text(json.dumps(r,ensure_ascii=False,indent=2))
        print(r['test_id']+' '+r['condition']+' '+r['status'],flush=True)
records.sort(key=lambda r:(r['test_id'],r['condition']))
(OUT/'logic_live_results.json').write_text(json.dumps({'generated_at':now(),'protocol':'Both conditions receive exactly the same evidence; prompts differ. Each uses a fresh QiYu conversation, deepseek-flash, temperature 0.65, no thinking, max_tokens 1200.','records':records},ensure_ascii=False,indent=2))
