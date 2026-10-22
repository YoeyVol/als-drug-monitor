'use strict';
const $ = id => document.getElementById(id);
const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const safeUrl = value => { try { const u = new URL(value, location.href); return u.protocol === 'https:' ? escapeHtml(u.href) : '#'; } catch { return '#'; } };
const link = (url, title) => `<a href="${safeUrl(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(title)} ↗</a>`;
const nctLink = id => link(`https://clinicaltrials.gov/study/${encodeURIComponent(id)}`, id);
const statuses = {RECRUITING:'招募中',NOT_YET_RECRUITING:'尚未招募',ACTIVE_NOT_RECRUITING:'进行中，不再招募',COMPLETED:'已完成',TERMINATED:'已终止',WITHDRAWN:'已撤回（未入组）',SUSPENDED:'暂停',ENROLLING_BY_INVITATION:'邀请入组',UNKNOWN:'状态未知',AVAILABLE:'扩展使用可获得',NO_LONGER_AVAILABLE:'不再提供扩展使用',APPROVED_FOR_MARKETING:'已获上市批准'};
const phases = {EARLY_PHASE1:'早期 I 期',PHASE1:'I 期',PHASE2:'II 期',PHASE3:'III 期',PHASE4:'IV 期',NA:'不适用'};
const state = {items:[],trials:[],category:'all'};
function renderUpdates() {
 const q = $('update-search').value.trim().toLowerCase();
 const items = state.items.filter(x => (state.category === 'all' || x.category === state.category) && JSON.stringify([x.drug,x.findings,x.nctIds,x.caveat,x.phase]).toLowerCase().includes(q));
 $('update-count').textContent = `显示 ${items.length} / ${state.items.length} 条记录 · 来源日期不等于本次核查日期`;
 $('update-list').innerHTML = items.length ? items.map(x => `<article class="card"><div class="card-top"><span class="badge ${x.category === 'regulatory' ? 'reg' : ''}">${escapeHtml(x.evidenceType || (x.category === 'regulatory' ? '监管 / 已上市' : '在研治疗'))}</span><time ${x.sourceDate ? `datetime="${escapeHtml(x.sourceDate)}"` : ''}>${escapeHtml(x.sourceDate || '来源未标日期')}</time></div><h3>${escapeHtml(x.drug)}</h3><p class="phase">${escapeHtml(x.phase || '分期请见登记')} · 核查 ${escapeHtml(x.checkedAt)}</p><div class="fact-label">研究发现 / 官方进展</div><p>${escapeHtml(x.findings)}</p>${x.caveat ? `<p class="limitation">${escapeHtml(x.caveat)}</p>` : ''}<p class="approval"><strong>监管：</strong>${escapeHtml(x.regulatoryStatus || '本条证据不构成 ALS 上市批准；具体地区状态须另行核实。')}</p>${x.nctIds?.length ? `<div class="nct-links">${x.nctIds.map(nctLink).join('')}</div>` : ''}<details class="sources"><summary>查看 ${x.sources.length} 个原始来源</summary><ul>${x.sources.map(s => `<li>${link(s.url,s.title)}</li>`).join('')}</ul></details></article>`).join('') : '<p class="empty">没有符合条件的进展，试试其他关键词。</p>';
}
function renderTrials() {
 const q = $('trial-search').value.trim().toLowerCase(), status = $('status-filter').value, phase = $('phase-filter').value;
 const common = ['RECRUITING','NOT_YET_RECRUITING','ACTIVE_NOT_RECRUITING','COMPLETED','TERMINATED'];
 const items = state.trials.filter(x => {
  const ps = x.phase || [];
  return JSON.stringify([x.nctId,x.title,x.interventions,x.sponsor]).toLowerCase().includes(q) && (status === 'all' || (status === 'other' ? !common.includes(x.status) : x.status === status)) && (phase === 'all' || (phase === 'other' ? !ps.some(p => ['PHASE1','PHASE2','PHASE3','PHASE4'].includes(p)) : ps.includes(phase)));
 });
 $('trial-count').textContent = `显示 ${items.length} / ${state.trials.length} 项精选试验 · 按登记更新日期排序`;
 $('trial-list').innerHTML = items.length ? items.map(x => `<article class="trial"><div class="trial-top">${nctLink(x.nctId)}<span class="status ${x.status === 'RECRUITING' ? 'recruiting' : x.status === 'NOT_YET_RECRUITING' ? 'pending' : ''}">${escapeHtml(statuses[x.status] || x.status)}</span></div><h3>${escapeHtml(x.interventions.filter(i => !/^(placebo|placebo .*|.* placebo|standard of care|riluzole \(100 mg\))$/i.test(i)).join(' / ') || x.interventions.join(' / '))}</h3><p class="trial-title" lang="en">${escapeHtml(x.title)}</p><div class="trial-meta"><span>分期：${escapeHtml((x.phase || []).map(p => phases[p] || p).join(' / ') || '未提供')}</span><span>登记更新：${escapeHtml(x.lastUpdatePosted || '未提供')}</span><span>结果上传：${x.hasResults ? '有（不代表有效）' : '无'}</span></div><div class="sponsor">登记申办方：${escapeHtml(x.sponsor || '未提供')} · 疾病：${escapeHtml((x.conditions || []).join(' / '))}</div></article>`).join('') : '<p class="empty">没有符合条件的试验，请调整筛选条件。</p>';
}
async function loadJson(path) { const response = await fetch(path,{cache:'no-store'}); if (!response.ok) throw new Error(`${path}: ${response.status}`); return response.json(); }
async function init() {
 try {
  const [updates,registry] = await Promise.all([loadJson('data/updates.json'),loadJson('data/trials.json')]);
  if (!Array.isArray(updates.items) || !Array.isArray(registry.trials)) throw new Error('数据格式不正确');
  state.items = [...updates.items].sort((a,b) => (b.sourceDate || '').localeCompare(a.sourceDate || ''));
  state.trials = [...registry.trials].sort((a,b) => (b.lastUpdatePosted || '').localeCompare(a.lastUpdatePosted || ''));
  $('updated').textContent = updates.lastUpdated;
  $('coverage-note').textContent = updates.coverage;
  $('count-updates').textContent = state.items.length;
  $('count-trials').textContent = state.trials.length;
  $('count-recruiting').textContent = state.trials.filter(x => x.status === 'RECRUITING').length;
  $('registry-date').textContent = `登记快照读取时间：${registry.retrievedAt.replace('T',' ').replace(/\.\d+Z$/,' UTC').replace(/Z$/,' UTC')} · 每项“登记更新”为注册库自身的更新日期。`;
  const age = Math.floor((Date.now()-Date.parse(`${updates.lastUpdated}T00:00:00Z`))/86400000);
  if(age > 10) { $('freshness').hidden = false; $('freshness').textContent = `更新提醒：研究核查日期距今已 ${age} 天。这是历史快照，请打开原始来源确认最新进展。`; }
  renderUpdates(); renderTrials();
 } catch(error) {
  $('updated').textContent = '数据加载未完成';
  $('update-list').innerHTML = '<p class="empty">研究数据暂时无法读取。请刷新重试，或使用页面底部的 JSON 与 GitHub 来源链接。</p>';
  $('trial-list').innerHTML = '<p class="empty">登记数据暂时无法读取。请刷新重试，或直接访问 ClinicalTrials.gov。</p>';
  console.error(error);
 }
}
$('update-search').addEventListener('input',renderUpdates);
$('trial-search').addEventListener('input',renderTrials);
$('status-filter').addEventListener('change',renderTrials);
$('phase-filter').addEventListener('change',renderTrials);
document.querySelectorAll('[data-category]').forEach(button => button.addEventListener('click',() => { state.category = button.dataset.category; document.querySelectorAll('[data-category]').forEach(b => b.setAttribute('aria-pressed',String(b === button))); renderUpdates(); }));
init();
