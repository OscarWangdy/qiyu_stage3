#!/usr/bin/env python3
import csv
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evidence'/'supplement_20261010'
PROJECT=Path('/Users/oscar/人工智能选修课/qiyu_v3_candidate_package')
sys.path.insert(0,str(PROJECT))
from qiyu.rules import RED, apply_move, initial_board, legal_moves, parse_square

records=[]
for i,(source,target,reason) in enumerate([('a9','b8','车不能斜走'),('c9','c5','相不能直走'),('e9','e6','帅不能离开九宫'),('a6','a7','兵不能后退'),('a0','a1','红方不能走黑子')],1):
    try:
        apply_move(initial_board(),RED,parse_square(source),parse_square(target)); rejected=False;message='未拒绝'
    except ValueError as error:
        rejected=True;message=str(error)
    records.append({'test_id':f'R{i:02d}','input':source+'-'+target,'expected':reason,'rejected':rejected,'observed':message})
agent_src=(PROJECT/'qiyu'/'agent.py').read_text()
book=json.loads((PROJECT/'artifacts'/'master_data_v3'/'opening_book.json').read_text())
board=''.join(initial_board());entries=book.get(board+'|'+RED,book.get(board+RED,[]))
payload={'generated_at':datetime.now().astimezone().isoformat(),'module':'qiyu.rules','rules_sha256':sha256((PROJECT/'qiyu'/'rules.py').read_bytes()).hexdigest(),'legal_initial_moves':len(legal_moves(initial_board(),RED)),'cases':records,'rejected':sum(r['rejected'] for r in records),'forward_before_book_lookup':agent_src.index('self.model(inputs, capture_attention=True)')<agent_src.index('book_entries ='),'agent_source_sha256':sha256(agent_src.encode()).hexdigest(),'source_excerpt':'\n'.join(agent_src.splitlines()[83:143])}
(OUT/'rule_and_source_verification.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2))
api=json.loads((OUT/'live_api_results.json').read_text())
logic=json.loads((OUT/'logic_live_results.json').read_text())
chat=[json.loads((OUT/f'chatgpt_C{i:02d}.json').read_text()) for i in range(1,4)]
cross=[r for r in api['records'] if r['category']=='cross_tool']
for r in chat:
    r['prompt_sha256']=sha256(r['prompt'].encode()).hexdigest()
for i in range(1,4):
    matches=[r for r in cross+chat if r['test_id']==f'C{i:02d}']
    assert len(matches)==3 and len(set(r['prompt'] for r in matches))==1
(OUT/'three_tool_comparison.json').write_text(json.dumps({'protocol':'Same user prompt bytes for all three tools. QiYu and DeepSeek share deepseek-flash. ChatGPT anonymous default does not disclose model/version, temperature or system prompt. Tool-level observations, not controlled base-model ranking. Fresh conversations for each test.','records':cross+chat},ensure_ascii=False,indent=2))

rows=[]
for r in api['records']+logic['records']:
    if r['category'] not in ['hallucination','logic']:continue
    issue=(r['category']=='hallucination' and r['test_id']=='H04' and r['condition']=='baseline') or (r['category']=='logic' and r['test_id']=='L02' and r['condition']=='baseline')
    note='无证据绝对断言：不能证明被写为不可能覆盖' if r['category']=='hallucination' and issue else '无证据推论：没有搜索被写为没有前向计算' if issue else '未观察到该测试目标的明显错误'
    rows.append([r['category'],r['test_id'],r['condition'],len(r['output']),int(issue),note])
with (OUT/'risk_review.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.writer(f);writer.writerow(['测试类','用例','条件','输出字符数','无证据断言或推论','人工复核说明']);writer.writerows(rows)
print(json.dumps({'rules_rejected':payload['rejected'],'legal_moves':payload['legal_initial_moves'],'forward_before_book_lookup':payload['forward_before_book_lookup'],'api_calls':len(api['records'])+len(logic['records']),'web_calls':len(chat),'matching_prompts':True,'all_complete':all(r.get('finish_reason')=='stop' for r in api['records']+logic['records'])},ensure_ascii=False,indent=2))
