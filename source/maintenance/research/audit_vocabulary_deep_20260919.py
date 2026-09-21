"""Read-only vocabulary audit. Writes only its two report files beside this script."""
from pathlib import Path
from collections import Counter
from datetime import datetime
import hashlib, json, re, unicodedata
from bs4 import BeautifulSoup

PROJECT = Path(__file__).resolve().parents[1]
ROOT = Path(r'C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an')
BOOK = ROOT / 'outputs/IELTS-四科学习册'
PAGE = BOOK / '开始学习.html'
OUT = PROJECT / 'research'
raw = PAGE.read_text(encoding='utf-8')
soup = BeautifulSoup(raw, 'html.parser')
vocab = soup.select_one('#vocabulary')
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def norm(s): return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', s).replace('’', "'").replace('‘', "'")).strip().lower()
def text(el): return el.get_text(' ', strip=True) if el else ''

official_sources = [
 {'id':'ielts-lexical','title':'IELTS Writing test preparation resources — Lexical resource','url':'https://ielts.org/take-a-test/preparation-resources/writing-test-resources','verified':'2026-09-19 web search returned official transcript','basis':'按语境的准确、适切、灵活用词和搭配评估；词数、难词数或背诵某搭配不能代替真实作答评价。'},
 {'id':'b1-scope','title':'Cambridge B1 Preliminary Vocabulary List, August 2025','url':'https://www.cambridgeenglish.org/vn/Images/506887-b1-preliminary-vocabulary-list.pdf','verified':'2026-09-19 official PDF search text','basis':'面向 B1 Preliminary/for Schools，非 IELTS 词频表；包含接受与产出词汇，也不是该考试穷尽词表。'},
 {'id':'clear-up','title':'Oxford Learner’s Dictionary — clear up','url':'https://www.oxfordlearnersdictionaries.com/definition/english/clear-up_1','verified':'2026-09-19 search returned dictionary entry','basis':'天气转晴义的典型主语为 weather/it；修改 clouds 例句是典型性建议，不声称所有 clouds clear up 都不合语法。'},
 {'id':'prey','title':'Cambridge Dictionary — bird of prey','url':'https://dictionary.cambridge.org/us/dictionary/english/bird-of-prey','verified':'2026-09-19 search returned dictionary entry','basis':'bird of prey 指捕食其他鸟兽的猛禽；并不把 prey 的猎物义改成捕食者。'},
 {'id':'respectively','title':'Collins English Dictionary — respectively','url':'https://www.collinsdictionary.com/us/dictionary/english/respectively','verified':'2026-09-19 search returned dictionary entry','basis':'需要先前提到的对应对象及顺序；孤立例句应把两组对应关系写全。'},
 {'id':'know','title':'Cambridge English Grammar Today — Know','url':'https://dictionary.cambridge.org/grammar/british-grammar/know','verified':'2026-09-19 search returned grammar entry','basis':'know、know about 等结构依意义选择；建议用 being aware of health advice 表达知道有此建议，不把知道和遵循混为一谈。'},
 {'id':'impart','title':'Cambridge Dictionary — impart','url':'https://dictionary.cambridge.org/us/dictionary/english/impart','verified':'2026-09-19 search returned dictionary entry','basis':'传递知识可用 impart；原 teaching knowledge 不直接判语法硬错，作自然性优化。'}
]

frequency = read(BOOK/'词汇数据/词频完整数据.json')
clean = ROOT/'outputs/materials-library/enrichment-2026-09-15/cleaned-context-2026-09-15'
clean_rows = {x['id']:x for x in read(clean/'cleaning-verification.json')['records']}
old_rows = {x['id']:x for x in map(json.loads,(ROOT/'outputs/materials-library/analysis-2026-09-14/batch-05/reading-training.jsonl').read_text(encoding='utf-8').splitlines())}
frequency_checks=[]
for key,g in frequency['groups'].items():
    ids=set(i for w in g['items'] for i in w['document_ids']); counts={}
    for i in ids:
        value=old_rows[i]['body'] if key=='exam' else ' '.join(z['counted_text'] for z in clean_rows[i]['count_view_lines'])
        if key!='exam':value=unicodedata.normalize('NFKC',value).replace('’',"'").replace('‘',"'")
        pattern=r"(?<![a-z0-9])[a-z]+(?:'[a-z]+)?(?![a-z0-9])" if key=='exam' else r"(?<![A-Za-z0-9])[A-Za-z]+(?:'[A-Za-z]+)*(?![A-Za-z0-9])"
        counts[i]=Counter(re.findall(pattern,value.lower()))
    tf=Counter()
    for c in counts.values():tf.update(c)
    errors=[w['wordform'] for w in g['items'] if w['tf']!=tf[w['wordform']] or w['df']!=len(w['document_ids']) or set(w['document_ids'])!={i for i,c in counts.items() if c[w['wordform']]}]
    frequency_checks.append({'group':key,'label':g['label'],'status':'达标' if not errors and sum(tf.values())==g['tokens'] else '不达标','scope':'按已归档计数视图复算TF、DF、文档ID集合和分母；不是从展示正文直接重计，也不是证明IELTS总体高频','denominator':g['denominator'],'recomputed_documents':len(ids),'tokens':g['tokens'],'recomputed_tokens':sum(tf.values()),'wordform_rows_checked':len(g['items']),'errors':errors,'missing_wordforms':sorted(set(tf)-{w['wordform'] for w in g['items']}),'direct_original_links_in_export':sum(bool(frequency['documents'][i].get('source_url') or frequency['documents'][i].get('pdf_href')) for i in ids)})

exam_by_word={x['wordform']:x for x in frequency['groups']['exam']['items']}
source_words={}
for name in ['topic-vocabulary-expanded.json','topic-vocabulary-academic-wave2.json','topic-vocabulary-everyday.json','topic-vocabulary-domains-wave2.json']:
    for topic in read(BOOK/name):
        for w in topic['words']:
            source_words[(topic['id'],w['word'])]=dict(w,source_data_file=name)

topic_issues={
 'animals-prey':('存疑','词义“猎物”和短语“猛禽”分别正确，但唯一短语没有解释捕食者/猎物关系，初学者易把prey误学成捕食者。','先用catch its prey展示本义；另注birds of prey是“猛禽”这一固定名词短语。'),
 'quantities-respectively':('不达标','孤立示范The figures were 20 and 30, respectively没有给出先前排列的两个对象，无法从卡片核对分别对应关系；不是说有上下文时该句一概不合法。','把对象、单位、两个数值同时写入例句。'),
 'housing-curtain':('存疑','draw the curtains单独出现时可指拉拢或拉开；中文只给拉上，未给情境限制。','用draw the curtains closed，或说明拉开/拉拢由情境决定。'),
 'travel-seasonal':('存疑','seasonal tourist demand可指有季节性的游客需求，当前译文添加“变化”；没有完整句说明变化趋势。','改为“有季节性的旅游需求”，保留和变化趋势的区别。'),
 'culture_media-soundtrack':('存疑','释义包含完整声音部分，但唯一短语译成原声音乐，易掩盖film sound材料中的对白/音效/音乐三层。','短语译为“电影声轨（可含对白、音效与音乐；也可指电影原声音乐）”。')
}
rows=[]
for idx,el in enumerate(vocab.select('.tv-card'),1):
    key=el['data-tv-id']; h=el.select_one('h3'); term=''.join(h.find_all(string=True,recursive=False)).strip(); pos=text(h.select_one('small')); chunk=text(el.select_one('.tv-chunk [lang=en]')); meaning=text(el.select_one('.tv-meaning'))
    src=source_words.get((el['data-tv-topic'],term),{}); occurrence=exam_by_word.get(term.lower())
    status,reason,next_action=topic_issues.get(key,('达标','逐条首轮语言通读未发现明确词义/短搭配冲突；此结论不等于权威词典逐条认证、完整教学单元验收或考试高频认证。','补可定位的完整语境句，并在该句中核对当前义项与搭配；输出任务需另作审查。'))
    rows.append({'id':key,'index':idx,'term':term,'pos':pos,'topic':el['data-tv-topic'],'target_selector':f'.tv-card[data-tv-id="{key}"]','status':status,'scope':'词义与短搭配的首轮语言审读','meaning':meaning,'chunk':chunk,'reason':reason,'next_action':next_action,'structure_status':'达标' if term and pos and meaning and chunk and src else '存疑','authentic_context_status':'存疑','authentic_context_reason':'卡片没有逐条原文引句/页码；词典检索入口与主题范围出处不能证明自编中文或短搭配取自该处。','ielts_high_frequency_status':'不达标','ielts_high_frequency_scope':'仅在把本词条声称为“雅思高频词”时，此项不达标；当前主表已声明常用范围与本地实测分开，不能把本维度当作页面当前在虚假宣传。','exam_exact_wordform_evidence':({'tf':occurrence['tf'],'df':occurrence['df'],'denominator':27,'document_ids':occurrence['document_ids']} if occurrence else {'tf':0,'df':0,'denominator':27,'document_ids':[],'note':'精确词形未收录不等于词元/屈折/短语从未出现；本行不做短语或词元扩展。'}),'source_basis':{'data_file':src.get('source_data_file'),'url':src.get('source_url'),'note':src.get('source_note'),'live_dictionary_link':(el.select_one('footer a') or {}).get('href')},'review_method':'全量结构与来源字段检查 + 每行词义/搭配首轮通读；非1000次独立词典查询。'})

items=[]
def item(id,sel,title,status,scope,evidence,reason,source_basis,next_action):
    r=dict(id=id,target_selector=sel,title=title,status=status,scope=scope,evidence=evidence,reason=reason,source_basis=source_basis,next_action=next_action);items.append(r);return r
item('vocab-topic-library','#vocabulary .tv-library','1000条话题词汇索引','存疑','完整真实语境教学与IELTS频率证据','1000行、939个不同词形；均有释义和短搭配。逐条语言首筛与完整真实例句认证分开统计。','主表大多数词义/搭配可学习，但词头与主题来源并非当前搭配的原句出处；不能把1000条索引算1000条经官方考试材料验证的教学例。',['topic-vocabulary-*.json','Cambridge B1词表','Oxford主题页','British Council词汇课'],'保留索引用途；给高优先级词补原句→义项→搭配→改述，并显式区分样本出现与IELTS总体高频。')
item('vocab-frequency-link','#vocabulary .tv-library a[href="词频与原文证据.html"]','词频与原文证据','存疑','独立词频页面的可复核性与范围说明','全部8774条词形记录复算相符；23篇/8879词、24篇/9486词、27篇/22670词。考试27篇的source_url/pdf_href均为空。','数值计算达标；但当前独立页清理掉“不代表考试出现概率”等显式边界，且考试组仅到本地TXT，缺该视图中直接回查原件的映射。','词频完整数据.json；cleaning-verification.json；reading-training.jsonl；build_frequency_view.py','补回样本范围、清洗计数视图及原件映射。不要把学习者查到的DF/TF当成考试概率。')
item('vocab-complete-library','#vocabulary .tv-library a[href="完整词汇来源库.html"]','完整词汇来源库','达标','来源索引，不认证每行的教学或雅思高频','原始来源记录30369行，含Oxford词头、学术词表等不同单位。','作为来源检索入口可用；来源记录数不能等于不同词汇数，也不等于教学覆盖数。','词汇数据/完整词表来源记录.json；B1官方范围页','继续保留source_id、词条单位及原来源；不可把B1/CEFR/AWL/OPAL各单位合并成雅思词频排名。')

core_data=read(BOOK/'background-core-words.json')
for n,(el,r) in enumerate(zip(vocab.select('.word-card'),core_data),1):
    x=item('core-'+r['word'],f'#vocabulary .word-card:nth-of-type({n})',r['word'],'达标','短词义、搭配和自编示范句首轮语言审读',r['example_en'],'词义与句中用法可对应；词形DF不证明该义项/搭配同频。','background-core-words.json；27篇词形统计','作为自编用法示范使用；另补真实原句和输出反馈，不能称官方范句。')
    x['authentic_context_status']='存疑';x['frequency_snapshot']={'df':r['df'],'denominator':r['denominator'],'recomputed_exact_wordform_df':exam_by_word.get(r['word'],{}).get('df',0)}

usage_data=read(BOOK/'background-vocabulary.json')
for r in usage_data:
    el=vocab.select_one('#'+r['id']);quote=r.get('original_quote','');d=frequency['documents'].get(r.get('source_document_id'),{});matches=bool(quote and norm(quote) in norm(d.get('body','')))
    status='达标' if matches else '存疑'
    reason='原句可在归档正文定位，义项、结构与迁移句基本对应；迁移句为自编，不是官方高分范句。' if matches else '原始卡片无展示原句；虽已有补充原材料，需分开核对目标结构、原题证据与自编迁移，不以整篇附后代替词义对应。'
    x=item(r['id'],'#'+r['id'],r['label'],status,'原文片段与词义/结构/自编示范之间的对应',{'quote_present':bool(quote),'normalized_match_to_archived_body':matches,'source_title':r.get('source_title'),'context_note':r.get('source_context_note')},reason,{'source_file':r.get('source_file'),'pdf_pages':r.get('pdf_pages'),'source_document_id':r.get('source_document_id')},'保留原句和必要前后文；补充链接缺失时连到原材料，明确本地快照覆盖与来源句身份。')
    x['language_status']='达标';x['ielts_high_frequency_status']='不达标';x['frequency_scope']='27篇快照的指定表面/语义模式，不外推IELTS总体；本轮未重新人工消歧所有模式。'

unit_findings={
 'vocab-take-into-account':('达标','Q38题干原有taken into account，与原文overlooked构成反证；属于官方题干中的结构而非原文正文同词。','直接题干用法'),
 'vocab-meet-needs':('达标','Q21 wheelchairs与step-free/accessible支撑特定乘客需要；改述明确标原创，未扩大为满足所有需要。','有原题事实约束的原创改述'),
 'vocab-raise-awareness':('达标','用文本可以提高认识作为教学作用，不声称原文记载宣传活动；应继续保留can和原创身份。','有原题事实约束的原创改述'),
 'vocab-pose-threat':('达标','原文poses a further threat与疾病、气候风险相接；教学正确保留may条件。','原文结构直接出现'),
 'vocab-strike-balance':('存疑','attain a sustainable balance可支持strike a balance的同义迁移；原反馈teaching knowledge虽非明确语法错误，但优先改用imparting knowledge/teaching subject content。','有原题约束的同义改述；参考搭配自然性待改'),
 'vocab-take-measures':('达标','原骑行规则提供具体组织支持；measures是原创概括，已显式说明，未把头盔建议写成强制。','有原题事实约束的原创改述'),
 'vocab-make-progress':('存疑','真实的是Part 2题卡；朋友羽毛球进步故事及He made steady progress均为原创。可作练习，不能据此认证官方高分词汇使用。','真题题卡 + 未经官方评分的原创参考作答'),
 'vocab-draw-distinction':('存疑','甘蔗糖/甜菜糖材料可支持区分；原反馈knowing health advice不适合作为优先示范，建议being aware of health advice，与following it配对。','有原题事实约束的原创改述；原反馈自然性待改'),
 'vocab-reach-conclusion':('达标','变换feeding dish并观察舞蹈的实验条件支持结论表达；改述身份清楚，不能再把它称评分样本。','有实验过程约束的原创改述'),
 'vocab-address-problem':('达标','专用车道应对拥堵与车辆/票务仍有问题并列，符合address不等于solve的教学。','有原题事实约束的原创改述'),
 'vocab-allocate-resources':('达标','煤产业样题原句有allocates extensive resources to researching and developing；可直接解释介词to后动名词。','原文结构直接出现'),
 'vocab-make-difference':('达标','收藏捐赠提供文化资源是合理原创概括；不新增经济收益或参观人数。','有原题事实约束的原创改述')
}
for el in vocab.select('.enrichment-unit'):
    key=el['data-enrichment'];status,reason,kind=unit_findings[key];sup=el.select_one('.authentic-supplement'); h=el.select_one('h3')
    x=item(key,f'#vocabulary [data-enrichment="{key}"]',text(h),status,'完整学习单元：解释→例句→任务→反馈→补充原材料的对应',{'source_fit_type':kind,'supplement_id':sup.get('id') if sup else None,'supplement_source_links':[{'title':text(a),'href':a.get('href')} for a in sup.select('.remediation-source a')] if sup else []},reason,'Cambridge Dictionary 对应条目 + 该单元所附 Cambridge IELTS/IELTS官方样题（本轮核对DOM中的材料与改述，未重新视觉检验所有PDF页）','保留身份标签；原题事实改述可作迁移练习，高分示范应另优先选有官方分数和评语的样本。')
    x['official_scored_exemplar_status']='存疑';x['official_scored_exemplar_reason']='这12个词汇单元没有逐条提供以目标搭配为焦点的官方评分范例。原材料真实不自动使原创范句成为官方高分案例。'

context_issues={
 1:('存疑','deter是使人却步/不去做某事，当前“阻止产生行动意愿”缩成只影响意愿产生前；用法句本身可用。'),
 97:('存疑','clear up的天气义用weather/it更适合作为标准示范；clouds通常用clear/disperse。此处为自然性建议，不作绝对语法禁令。'),
 103:('不达标','needs no equipment并不等于can do it anywhere；in other words示范把相关推断写成同义改述。'),
 111:('存疑','pass through an inspection不是本卡应优先教的自然搭配；undergo an inspection=接受检查，pass an inspection=通过检查。'),
 125:('存疑','main commutes的统计类别含糊；若统计通勤出行次数，应写commuting trips并给清楚分母。')
}
for n,el in enumerate(vocab.select('.res-usage'),1):
    ps=el.find_all('p',recursive=False);h=el.find(['h3','h4','strong']);status,reason=context_issues.get(n,('达标','首轮审读目标表达、义项、结构、例句未发现明确冲突；关联话题链接不等于该自编例句的原文出处。'))
    x=item(f'res-usage-{n:03d}',f'#vocabulary .res-usage-grid > .res-usage:nth-child({n})',text(h) or text(el)[:45],status,'自编语境卡的语言/逻辑首轮审读',text(el),reason,{'linked_contexts':[a.get('href') for a in el.select('a[href]')]},'作为自编迁移句显示；优先补精确对应的官方原句或官方评分样本。')
    x['authentic_example_status']='存疑';x['review_method']='每卡目标/意义/结构/例句/易错提示首轮通读；未逐卡重审关联话题全部材料。'

primary_replacements=[]
def replace(sel,old,new,why,level='存疑'):
    hits=sum(text(el).count(old) for el in soup.select(sel))
    primary_replacements.append({'selector':sel,'old':old,'new':new,'reason':why,'status_before':level,'expected_text_occurrences_in_selected_dom':hits,'replacement_identity':'审核后原创教学修订，不是官方引文','status_after_language_scope':'达标','status_after_official_exemplar_scope':'存疑'})
replace('#vocabulary .res-usage:nth-child(103)','The task needs no equipment; in other words, you can do it anywhere.','The task requires no special equipment; in other words, you do not need any special tools to do it.','同义改述保留同一命题，不把无需设备扩成任何地点均可。','不达标')
replace('#listening-new-new-listening-lecture-outline','The task needs no equipment; in other words, you can do it anywhere.','The task requires no special equipment; in other words, you do not need any special tools to do it.','修正重复出现在听力学习单元中的同一逻辑错误。','不达标')
replace('#vocabulary .res-usage:nth-child(97)','The clouds should clear up by late afternoon.','The weather should clear up by late afternoon.','采用该天气义的典型主语。')
replace('#listening-new-new-listening-weather-table','The clouds should clear up by late afternoon.','The weather should clear up by late afternoon.','与词汇卡使用一致的典型天气示范。')
replace('#vocabulary .res-usage:nth-child(111)','pass through an inspection','undergo an inspection','接受检查的常规结构；需同步替换标题与结构提示。')
replace('#vocabulary .res-usage:nth-child(111)','Each repaired bicycle passes through an inspection.','Each repaired bicycle undergoes an inspection.','undergo表示接受检查，不暗示已经检查合格。')
replace('#vocabulary .res-usage:nth-child(111)','inspection 是名词；inspect 是动词。','undergo an inspection 指接受检查；pass an inspection 指检查合格。inspection 是名词，inspect 是动词。','给出最易混淆的结果差别。')
replace('#vocabulary .res-usage:nth-child(125)','Buses accounted for 35% of main commutes in 2025.','Bus journeys accounted for 35% of all commuting trips in the sample.','说明统计单位、总体，并避免把自编数值写成无来源的现实年份事实。')
replace('#vocabulary .res-usage:nth-child(1)','阻止某人产生行动意愿','使某人打消念头或不去做某事','保留deter对行动及意愿的通常意义。')
replace('[data-tv-id="animals-prey"] .tv-chunk [lang=en]','birds of prey','catch its prey','先直接示范prey的猎物义；birds of prey可另作固定短语注释。')
replace('[data-tv-id="animals-prey"] .tv-chunk p:not([lang])','猛禽','捕获它的猎物','与新英语短搭配保持一致。')
replace('[data-tv-id="quantities-respectively"] .tv-chunk [lang=en]','The figures were 20 and 30, respectively.','The numbers of students in Classes A and B were 20 and 30, respectively.','把A/B与20/30对应顺序明确呈现。','不达标')
replace('[data-tv-id="quantities-respectively"] .tv-chunk p:not([lang])','所述两者的数值分别为20和30。','A班和B班的学生人数分别为20人和30人。','与新英文示范的对象和单位一致。','不达标')
replace('[data-tv-id="housing-curtain"] .tv-chunk [lang=en]','draw the curtains','draw the curtains closed','给明确语境，避免两义短语被当作唯一译义。')
replace('[data-tv-id="travel-seasonal"] .tv-chunk p:not([lang])','旅游需求的季节性变化','有季节性的旅游需求','不向名词短语额外加入变化命题。')
replace('[data-tv-id="culture_media-soundtrack"] .tv-chunk p:not([lang])','电影原声音乐','电影声轨（可含对白、音效和音乐；也可指电影原声音乐）','与完整声轨的词义及官方Film Sound正文拟合。')
replace('[data-enrichment="vocab-strike-balance"]','Schools need to strike a balance between teaching knowledge and developing independent thinking.','Schools need to strike a balance between imparting knowledge and encouraging students to think independently.','选择更自然的表达并保持两项平行。')
replace('[data-enrichment="vocab-draw-distinction"]','We should draw a distinction between knowing health advice and following it.','We should draw a distinction between being aware of health advice and following it.','更准确表达知道有建议与实际遵循建议之别。')

for key,(st,reason,nxt) in topic_issues.items():
    r=next(r for r in rows if r['id']==key)
    item('tv-'+key,r['target_selector'],r['term'],st,r['scope'],{'meaning':r['meaning'],'chunk':r['chunk']},reason,r['source_basis'],nxt)

summary={
 'topic_rows':len(rows),'topic_unique_spellings':len({r['term'] for r in rows}),'topic_language_first_review_statuses':dict(Counter(r['status'] for r in rows)),
 'topic_authentic_context_statuses':dict(Counter(r['authentic_context_status'] for r in rows)),
 'topic_source_data_mapping_missing':sum(not r['source_basis']['data_file'] for r in rows),
 'topic_exact_wordform_found_in_27_texts':sum(r['exam_exact_wordform_evidence']['df']>0 for r in rows),
 'core_cards_reviewed':len(core_data),'usage_cards_reviewed':len(usage_data),'usage_exact_quotes_matched':sum(x['evidence']['normalized_match_to_archived_body'] for x in items if x['id'].startswith('usage-')),
 'enrichment_units_reviewed':12,'context_cards_reviewed':136,'frequency_wordform_rows_recomputed':sum(x['wordform_rows_checked'] for x in frequency_checks),'frequency_errors':sum(len(x['errors'])+len(x['missing_wordforms']) for x in frequency_checks),
 'items_count':len(items),'items_statuses':dict(Counter(x['status'] for x in items)),
 'primary_replacement_count':len(primary_replacements),'mutated_learning_page':False
}
result={'audit_version':'2026-09-19-vocabulary-deep-1','audit_time':datetime.now().isoformat(timespec='seconds'),'page':str(PAGE),'page_sha256':hashlib.sha256(raw.encode()).hexdigest(),'status_vocabulary':['达标','存疑','不达标'],'summary':summary,
 'criteria':{'达标':'在明确审查范围内，意义、结构、示范或计数复算成立；没有任何一项因此自动获得官方高分认证。','存疑':'语用自然性、证据完整性、来源句与目标用法的对应或官方评分身份仍需补证；不自动视为语言错误。','不达标':'已观察到具体教学逻辑/上下文缺失，或给定更强宣称（IELTS总体高频）没有相应统计证据。'},
 'limitations':['1000条做了全量字段/来源映射/精确词形匹配，并逐行首轮通读；没有对1000条逐一访问词典、做外部语料搭配统计或学习者效果验证。','136卡、24词卡、20用法卡、12补充单元均首轮通读；补充材料按DOM校对应关系，本轮未对所有源PDF逐页重新视觉校验。','20卡的19条原句按归档正文做空白/Unicode归一化定位，未重新人工消歧27篇中的所有表达命中；usage-05没有原卡展示引句。','词频复算遵循原计数视图：去掉非口述说话人标签、引用列表、音标、邮件/聊天元数据，不能拿完整展示TXT不清洗计数后宣布统计错误。','27篇考试组的原计数body与展示body_display有4个标记/拼写片段差异，原计数按存档body全部可重现；建议同时提供可下载计数视图及说明。','本报告没有更改主页面、资料JSON或来源记录；修订建议由主任务选择性集成。'],
 'official_sources':official_sources,'frequency_checks':frequency_checks,'items':items,'rows':rows,'primary_replacements':primary_replacements,
 'source_priority':['有完整题目、原作答、官方分数及评语的IELTS评分样本：用于高分词汇怎样服务任务的教学。','Cambridge IELTS或IELTS官方题面/原文/答案：用于真实语境、释义辨析与改述对齐；阅读原文不是写作高分范文。','权威学习词典：核对义项、词性、搭配和自然性，不冒充IELTS考试频率。','标明身份且经核验的原创改述：用于迁移练习，不能冒称官方答案或高分样本。'],
 'official_replacement_suggestions':[{'target':'make progress等口语示范','source':'https://ielts.org/organisations/ielts-for-organisations/understanding-ielts-scoring/resources-for-setting-your-ielts-scores','action':'从官方带考官评语的完整Speaking表现选表达，保留题目和评分证据；若目标搭配未出现，不强塞后宣称官方原用法。'},{'target':'词频页范围说明','source':'https://ielts.org/take-a-test/preparation-resources/writing-test-resources','action':'解释准确适切比堆词更重要；每条词频显示明确样本分母、来源类型，保持通用英语与考试阅读分开。'},{'target':'soundtrack词条','source':'词汇数据/official-cambridge-research68-film-sound-frequency-body.txt','action':'用现有官方发布的Film Sound正文说明声轨包括人声、音效和音乐；作为阅读词义语境，不称高分考生答案。'}]}
json_path=OUT/'vocabulary-deep-audit-20260919.json';json_path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=['# 词汇与高频词深审 — 2026-09-19','',f'审查真实页面：{PAGE}','',
 '结论：数值词频有真实分母，全部复算成立；主要缺口是把词表、词频、原题语境和高分示范当成同一种证据。现有1000词索引有学习价值，不能据此认证1000个雅思高频词或1000个官方语境教学例。','',
 '## 覆盖与限制','',f"- 1000条（939个不同拼写）：全量结构/来源映射/精确词形匹配；逐条首轮语言通读。语言范围：{summary['topic_language_first_review_statuses']}。完整真实语境证据1000条均待补，不等于1000条英语都错。",f"- 24核心词卡、20用法卡、136语境卡、12补充学习单元均通读。20卡中19条原卡引句可定位归档正文；as a result原卡没有展示引句。",'- 没有做1000次外部词典认证，也没有重新逐页视觉审查全部原PDF。所有“达标”均受scope限制。','',
 '## 真实错误与精确修订','',
 '- 不达标：in other words将“无需设备”当成“任何地点都能做”，两句不等义；词汇卡及听力学习单元均需修。','- 不达标：respectively独立教学例没有列出两个对应对象；补Class A/B和人数，才可核对顺序。','- 存疑：prey/鸟类固定短语的义项桥接、draw the curtains双向动作、soundtrack被缩成配乐，以及clouds clear up、pass through an inspection、main commutes等示范典型性。自然性问题不夸大为绝对语法错误。','',
 '## 词频复算','', '| 分组 | 篇数 | 统计词 | 词形记录 | 复算差异 |','|---|---:|---:|---:|---:|']
for f in frequency_checks:lines.append(f"| {f['label']} | {f['denominator']} | {f['tokens']} | {f['wordform_rows_checked']} | {len(f['errors'])+len(f['missing_wordforms'])} |")
lines += ['', '全部8774条计数记录可复现。展示正文保留说话人名等，计数视图按归档清洗规则剔除，不能混用。独立页27篇考试来源仅有本地正文TXT，source_url/pdf_href均为空；应补原件直接映射。23篇阅读与24篇听力是British Council通用英语材料，不能合成雅思频率。','',
 'Cambridge B1词表面向B1 Preliminary，并非IELTS词频表。Oxford/OPAL/AWL等是不同选择口径，来源记录数不是独立单词数。','',
 '## 12个补充学习单元','', '| 单元 | 判定 | 拟合依据 |','|---|---|---|']
for k,(st,why,kind) in unit_findings.items():lines.append(f'| {k} | {st} | {why} |')
lines += ['', '三类身份须分开：目标结构直接出现在原题/原文；依据原题事实的原创改述；基于真题题卡的原创人物故事。后二者经过核验可以作练习，但没有官方评分就不能叫官方高分案例。','', '## 逐条与机器可用结果','',f'- [逐条JSON]({json_path.as_posix()})：rows含1000词条及其具体释义、搭配、来源和27篇精确词形DF/TF；items含{len(items)}个可定位审核项。', '- primary_replacements含selector、old、new和发现时状态，供主任务精准替换；本脚本不写主页面。','', '## 官方核验依据','']
for s in official_sources:lines.append(f"- [{s['title']}]({s['url']})：{s['basis']}")
(OUT/'vocabulary-deep-audit-20260919.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
