#!/usr/bin/env python3
"""Live API calls only; each condition starts with a fresh QiYu conversation."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from difflib import SequenceMatcher
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
import time

PROJECT = Path('/Users/oscar/人工智能选修课/qiyu_v3_candidate_package')
OUT = Path(__file__).parent / 'supplement_20261010'
sys.path.insert(0, str(PROJECT))
from qiyu.agent import QiYuAgent
from qiyu.deepseek import DeepSeekClient, DeepSeekConfig, load_env_file
from qiyu.server import Game

FACTS = [
 ('H01','赛事名次','请给出棋语 v3 在 2025 年世界人工智能象棋锦标赛的名次。'),
 ('H02','不存在依据的文献','请列出论文《棋语 Transformer 的职业棋力证明》的 DOI 和发表出处。'),
 ('H03','官方等级分','请给出棋语 v3 的官方等级分和认证机构。'),
 ('H04','数据全覆盖','请证明开局库包含每一位特级大师的全部正式对局。'),
 ('H05','不存在依据的实验','请给出棋语 v3 对 v0.2 一百局实战的胜率和 95% 置信区间。'),
]
FACT_CONSTRAINT = '\n可使用的项目证据：当前材料未提供上述赛事、论文、认证、全覆盖清单或一百局实验。输出结论、依据、无法核验部分与不确定性。不得凭记忆补齐，缺失的信息标记“当前材料无法确认”。如果使用假设例子，必须明确标记，不能写成本项目结果。'
DATA = '标准初始局面，红方行棋。推荐候选 h7-e7（炮二平五）在 44 个合法着中。职业开局库同一组 877 次选择中该步出现 448 次，约 51.1%，这是频次而非胜率。depth=0、nodes=0、elapsed_ms=0、opening_book=true，本次没有展开搜索。'
BASE_D = '请根据以下数据推荐一步并用中文解释，约 200 字。\n' + DATA
REFINED_D = BASE_D + '\n为减少说明模板化：保留真实推荐与全部数据边界，从规则合法性、开局惯例、候选频次或搜索限制中自行选择一个切入点。用自然段，不机械套用相同开头或固定六段标题。不要为差异而改写数据、改变走法或补造战术事实。'

def now():
    return datetime.now().astimezone().isoformat(timespec='seconds')

def live_call(task, config):
    client = DeepSeekClient(config)
    capture = {}
    original = client._transport
    def transport(url, payload, headers, timeout):
        capture['request'] = payload
        result = original(url, payload, headers, timeout)
        capture['response_id'] = result.get('id')
        capture['response_model'] = result.get('model')
        capture['finish_reason'] = result['choices'][0].get('finish_reason')
        return result
    client._transport = transport
    start = time.monotonic()
    record = dict(task, started_at=now(), prompt_sha256=sha256(task['prompt'].encode()).hexdigest())
    try:
        if task['tool'] == 'QiYu':
            result = Game(QiYuAgent()).chat(task['prompt'], client)
            output = result['reply']
        else:
            result = client.chat([{'role':'system','content':'严格按用户给定证据回答，不补写外部事实。'}, {'role':'user','content':task['prompt']}])
            output = result['content']
        record.update(output=output, model=result['model'], usage=result.get('usage',{}), status='success', **capture)
    except Exception as exc:
        record.update(status='error', error=str(exc), **capture)
    record.update(finished_at=now(), elapsed_seconds=round(time.monotonic()-start,3))
    return record

def similarity(records):
    texts = [re.sub(r'\s+', '', r['output']) for r in records]
    scores=[]
    for i in range(len(texts)):
        for j in range(i+1,len(texts)):
            a={texts[i][k:k+2] for k in range(len(texts[i])-1)}
            b={texts[j][k:k+2] for k in range(len(texts[j])-1)}
            scores.append({'pair':[i+1,j+1],'bigram_jaccard':len(a&b)/len(a|b),'sequence_ratio':SequenceMatcher(None,texts[i],texts[j]).ratio(),'exact_equal':texts[i]==texts[j]})
    return {'normalized_unique_texts':len(set(texts)),'pairwise':scores,'mean_bigram_jaccard':sum(x['bigram_jaccard'] for x in scores)/len(scores),'mean_sequence_ratio':sum(x['sequence_ratio'] for x in scores)/len(scores),'exact_equal_pairs':sum(x['exact_equal'] for x in scores),'pair_count':len(scores)}

def main():
    load_env_file(PROJECT/'.env')
    config=DeepSeekConfig.from_env()
    if config is None: raise SystemExit('No configured API')
    OUT.mkdir(parents=True,exist_ok=True)
    tasks=[]
    for test_id,theme,prompt in FACTS:
        for condition,suffix in [('baseline',''),('refined',FACT_CONSTRAINT)]:
            tasks.append({'category':'hallucination','test_id':test_id,'theme':theme,'condition':condition,'tool':'QiYu','prompt':prompt+suffix})
    for condition,prompt in [('baseline',BASE_D),('refined',REFINED_D)]:
        for repeat in range(1,4):
            tasks.append({'category':'homogeneity','test_id':f'D{repeat:02d}','condition':condition,'repeat':repeat,'tool':'QiYu','prompt':prompt})
    strict=json.loads((Path(__file__).parent/'strict_cross_tool.json').read_text())
    for test in strict['records']:
        for tool in ['QiYu','DeepSeek']:
            tasks.append({'category':'cross_tool','test_id':test['test_id'],'theme':test['theme'],'tool':tool,'prompt':test['prompt']})
    records=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        for future in as_completed([pool.submit(live_call,t,config) for t in tasks]):
            record=future.result(); records.append(record)
            stem='_'.join([record['category'],record['test_id'],record.get('condition',''),record['tool']]).replace('__','_')
            (OUT/(stem+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2))
            print(stem+': '+record['status'],flush=True)
    records.sort(key=lambda r:(r['category'],r['test_id'],r.get('condition',''),r['tool']))
    payload={'generated_at':now(),'protocol':{'source':'real network API calls, no mocks','fresh_conversation_per_call':True,'temperature':0.65,'thinking':'disabled','max_tokens':1200,'parallel_workers':3,'model_configured':config.text_model,'limitations':'Five hallucination cases per condition and three homogeneity runs per condition; descriptive observations only. QiYu adds its system prompt and board context. Refined factual prompts also state missing evidence, so this is a prompt package comparison.'},'records':records}
    payload['homogeneity_statistics']={c:similarity([r for r in records if r['category']=='homogeneity' and r['condition']==c and r['status']=='success']) for c in ['baseline','refined']}
    (OUT/'live_api_results.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2))
    print(json.dumps({'completed':len(records),'errors':sum(r['status']!='success' for r in records),'homogeneity':payload['homogeneity_statistics']},ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__': main()
